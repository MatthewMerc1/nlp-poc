import json
import os
import boto3
import requests
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Get environment variables
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
OPENSEARCH_INDEX = os.environ['OPENSEARCH_INDEX']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']

def get_aws_auth():
    """Get AWS authentication for OpenSearch"""
    credentials = boto3.Session().get_credentials()
    return AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        os.environ.get('AWS_REGION', 'us-east-1'),
        'es',
        session_token=credentials.token
    )

def create_opensearch_client():
    """Create OpenSearch client"""
    auth = get_aws_auth()
    
    return OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT.replace('https://', ''), 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

def generate_embedding(text):
    """Generate embedding using Bedrock"""
    try:
        request_body = {
            "inputText": text
        }
        logger.info(f"Generating embedding for text: '{text}'")
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        response_body = json.loads(response.get('body').read())
        embedding = response_body.get('embedding')
        logger.info(f"Generated embedding length: {len(embedding) if embedding else 'None'}")
        logger.info(f"Generated embedding first 5 values: {embedding[:5] if embedding else 'None'}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def search_opensearch(query_embedding, size=5):
    """Search OpenSearch with vector similarity"""
    try:
        client = create_opensearch_client()
        
        # Log the query embedding for debugging
        logger.info(f"Query embedding length: {len(query_embedding) if query_embedding else 'None'}")
        logger.info(f"Query embedding first 5 values: {query_embedding[:5] if query_embedding else 'None'}")
        
        # Vector search query
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            },
            "_source": ["book_title", "author", "text", "chunk_index"]
        }
        
        logger.info(f"Search body: {json.dumps(search_body, indent=2)}")
        
        response = client.search(
            body=search_body,
            index=OPENSEARCH_INDEX
        )
        
        logger.info(f"Search response hits total: {response['hits']['total']}")
        logger.info(f"Search response hits: {len(response['hits']['hits'])}")
        
        return response['hits']['hits']
    except Exception as e:
        logger.error(f"Error searching OpenSearch: {str(e)}")
        raise

def create_index_if_not_exists():
    """Create the OpenSearch index if it doesn't exist"""
    try:
        client = create_opensearch_client()
        
        # Check if index exists
        if not client.indices.exists(index=OPENSEARCH_INDEX):
            logger.info(f"Creating index: {OPENSEARCH_INDEX}")
            
            # Index mapping for vector search
            index_mapping = {
                "mappings": {
                    "properties": {
                        "book_title": {"type": "text"},
                        "author": {"type": "text"},
                        "text": {"type": "text"},
                        "chunk_index": {"type": "integer"},
                        "text_vector": {
                            "type": "knn_vector",
                            "dimension": 1536,  # Titan embedding dimension
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        }
                    }
                }
            }
            
            client.indices.create(
                index=OPENSEARCH_INDEX,
                body=index_mapping
            )
            logger.info(f"Index {OPENSEARCH_INDEX} created successfully")
        else:
            logger.info(f"Index {OPENSEARCH_INDEX} already exists")
            
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def load_embeddings_to_opensearch(embeddings_data):
    """Load embeddings data into OpenSearch"""
    try:
        client = create_opensearch_client()
        
        # Create index if it doesn't exist
        create_index_if_not_exists()
        
        book_title = embeddings_data.get('book_title', 'Unknown')
        author = embeddings_data.get('author', 'Unknown')
        embeddings = embeddings_data.get('embeddings', [])
        
        logger.info(f"Loading {len(embeddings)} embeddings for book: {book_title}")
        
        # Bulk index the embeddings
        bulk_data = []
        for i, embedding in enumerate(embeddings):
            # Prepare document
            doc = {
                "book_title": book_title,
                "author": author,
                "text": embedding.get('text', ''),
                "chunk_index": embedding.get('chunk_index', i),
                "text_vector": embedding.get('embedding', [])
            }
            
            # Add to bulk data
            bulk_data.append({"index": {"_index": OPENSEARCH_INDEX}})
            bulk_data.append(doc)
        
        # Execute bulk operation
        if bulk_data:
            response = client.bulk(body=bulk_data, refresh=True)
            
            # Check for errors
            if response.get('errors', False):
                logger.error(f"Bulk indexing errors: {response}")
                return False
            
            logger.info(f"Successfully loaded {len(embeddings)} embeddings for {book_title}")
            return True
        else:
            logger.warning(f"No embeddings to load for {book_title}")
            return True
            
    except Exception as e:
        logger.error(f"Error loading embeddings to OpenSearch: {str(e)}")
        return False

def check_opensearch_index():
    """Check OpenSearch index status and document count"""
    try:
        client = create_opensearch_client()
        
        # Check if index exists
        index_exists = client.indices.exists(index=OPENSEARCH_INDEX)
        
        if not index_exists:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'index_exists': False,
                    'document_count': 0,
                    'message': f'Index {OPENSEARCH_INDEX} does not exist'
                })
            }
        
        # Get document count
        count_response = client.count(index=OPENSEARCH_INDEX)
        document_count = count_response['count']
        
        # Get index stats
        stats_response = client.indices.stats(index=OPENSEARCH_INDEX)
        index_stats = stats_response['indices'][OPENSEARCH_INDEX]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'index_exists': True,
                'document_count': document_count,
                'index_stats': {
                    'total_docs': index_stats['total']['docs']['count'],
                    'total_size': index_stats['total']['store']['size_in_bytes'],
                    'primaries_docs': index_stats['primaries']['docs']['count'],
                    'primaries_size': index_stats['primaries']['store']['size_in_bytes']
                },
                'message': f'Index {OPENSEARCH_INDEX} has {document_count} documents'
            })
        }
        
    except Exception as e:
        logger.error(f"Error checking OpenSearch index: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to check index: {str(e)}'
            })
        }

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        # Check if this is a direct Lambda invocation (for loading embeddings or checking index)
        if 'action' in event:
            if event['action'] == 'load_embeddings':
                logger.info("Processing load_embeddings action")
                embeddings_data = event.get('embeddings_data', {})
                
                if load_embeddings_to_opensearch(embeddings_data):
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'message': 'Embeddings loaded successfully',
                            'book_title': embeddings_data.get('book_title', 'Unknown')
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'body': json.dumps({
                            'error': 'Failed to load embeddings'
                        })
                    }
            elif event['action'] == 'check_index':
                logger.info("Processing check_index action")
                return check_opensearch_index()
        
        # Handle API Gateway requests (search functionality)
        # Parse request body
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']
        
        query_text = body.get('query')
        size = body.get('size', 5)
        
        if not query_text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST,OPTIONS'
                },
                'body': json.dumps({
                    'error': 'Query text is required'
                })
            }
        
        logger.info(f"Processing query: {query_text}")
        
        # Generate embedding for the query
        query_embedding = generate_embedding(query_text)
        logger.info("Generated embedding successfully")
        
        # Search OpenSearch
        search_results = search_opensearch(query_embedding, size)
        logger.info(f"Found {len(search_results)} results")
        
        # Format results
        formatted_results = []
        for hit in search_results:
            source = hit['_source']
            formatted_results.append({
                'score': hit['_score'],
                'title': source.get('book_title', 'Unknown'),
                'author': source.get('author', 'Unknown'),
                'book_id': source.get('book_title', 'Unknown'),
                'chapter': source.get('chunk_index', 'Unknown'),
                'content': source.get('text', '')[:500] + '...' if len(source.get('text', '')) > 500 else source.get('text', '')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'query': query_text,
                'results': formatted_results,
                'total_results': len(formatted_results)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

# Add this to your Lambda for debugging
try:
    # Check if index exists
    client = create_opensearch_client()
    index_response = client.indices.exists(index=OPENSEARCH_INDEX)
    logger.info(f"Index {OPENSEARCH_INDEX} exists: {index_response}")
    
    # List all indices
    indices_response = client.cat.indices(format='json')
    logger.info(f"All indices: {indices_response}")
    
except Exception as e:
    logger.error(f"Error checking indices: {str(e)}") 