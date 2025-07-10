#!/usr/bin/env python3
"""
Lambda function for semantic search using OpenSearch and Amazon Bedrock
"""

import json
import logging
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
OPENSEARCH_INDEX = "book-embeddings"
BEDROCK_MODEL_ID = "amazon.titan-embed-text-v1"

def get_aws_auth():
    """Get AWS authentication for OpenSearch"""
    try:
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            'es',
            session_token=credentials.token
        )
        return awsauth
    except Exception as e:
        logger.error(f"Error getting AWS auth: {str(e)}")
        raise

def create_opensearch_client():
    """Create OpenSearch client"""
    try:
        awsauth = get_aws_auth()
        host = os.environ.get('OPENSEARCH_ENDPOINT')
        
        if not host:
            raise ValueError("OPENSEARCH_ENDPOINT environment variable not set")
        
        client = OpenSearch(
            hosts=[{'host': host.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        return client
    except Exception as e:
        logger.error(f"Error creating OpenSearch client: {str(e)}")
        raise

def generate_embedding(text):
    """Generate embedding using Amazon Bedrock"""
    try:
        bedrock = boto3.client('bedrock-runtime')
        
        # Prepare the request
        request_body = {
            "inputText": text
        }
        
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        embedding = response_body['embedding']
        
        logger.info(f"Generated embedding length: {len(embedding)}")
        logger.info(f"Generated embedding first 5 values: {embedding[:5]}")
        
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def search_opensearch(query_embedding, size=5):
    """Search OpenSearch using k-NN"""
    try:
        client = create_opensearch_client()
        
        # Prepare the search query
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            }
        }
        
        logger.info(f"Search body: {json.dumps(search_body, indent=2)}")
        
        # Execute search
        response = client.search(
            index=OPENSEARCH_INDEX,
            body=search_body
        )
        
        # Process results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            source = hit['_source']
            results.append({
                'book_title': source.get('book_title', ''),
                'author': source.get('author', ''),
                'text': source.get('text', ''),
                'chunk_index': source.get('chunk_index', 0),
                'score': hit['_score']
            })
        
        logger.info(f"Found {len(results)} results")
        return results
        
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
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.space_type": "cosinesimil",
                        "knn.algo_param.ef_search": 512,
                        "knn.algo_param.ef_construction": 512,
                        "knn.algo_param.m": 16,
                        "number_of_shards": 5,
                        "number_of_replicas": 1
                    }
                },
                "mappings": {
                    "properties": {
                        "book_title": {"type": "text"},
                        "author": {"type": "text"},
                        "text": {"type": "text"},
                        "chunk_index": {"type": "integer"},
                        "text_vector": {
                            "type": "knn_vector",
                            "dimension": 1536,
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
        # Handle direct Lambda invocations (for loading embeddings)
        if 'action' in event:
            if event['action'] == 'load_embeddings':
                logger.info("Processing load_embeddings action")
                embeddings_data = event.get('embeddings_data', {})
                success = load_embeddings_to_opensearch(embeddings_data)
                return {
                    'statusCode': 200 if success else 500,
                    'body': json.dumps({'success': success})
                }
            elif event['action'] == 'check_index':
                logger.info("Processing check_index action")
                return check_opensearch_index()
        
        # Handle API Gateway requests (search functionality)
        if 'body' in event:
            # Parse the request body
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
            
            query = body.get('query', '')
            size = body.get('size', 5)
            
            if not query:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Query parameter is required'})
                }
            
            logger.info(f"Processing query: {query}")
            
            # Generate embedding for the query
            logger.info(f"Generating embedding for text: '{query}'")
            query_embedding = generate_embedding(query)
            logger.info(f"Generated embedding successfully")
            
            # Search OpenSearch
            logger.info(f"Query embedding length: {len(query_embedding)}")
            logger.info(f"Query embedding first 5 values: {query_embedding[:5]}")
            results = search_opensearch(query_embedding, size)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'query': query,
                    'results': results,
                    'total_results': len(results)
                })
            }
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request format'})
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        } 