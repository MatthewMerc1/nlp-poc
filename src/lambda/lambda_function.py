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
OPENSEARCH_INDEX = "book-summaries"  # Book-level index
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
    """Create OpenSearch client with proper timeout and retry configuration"""
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
            connection_class=RequestsHttpConnection,
            timeout=30,  # Increase timeout to 30 seconds
            max_retries=3,  # Add retry logic
            retry_on_timeout=True,
            retry_on_status=[429, 500, 502, 503, 504]  # Retry on these status codes
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
    """Search OpenSearch using k-NN for book-level results"""
    try:
        logger.info("Creating OpenSearch client for search...")
        client = create_opensearch_client()
        logger.info("OpenSearch client created successfully")
        
        # Prepare the search query
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    "book_embedding": {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            }
        }
        
        logger.info(f"Search body: {json.dumps(search_body, indent=2)}")
        logger.info(f"Searching index: {OPENSEARCH_INDEX}")
        
        # Execute search with timeout
        logger.info("Executing search request...")
        response = client.search(
            index=OPENSEARCH_INDEX,
            body=search_body,
            request_timeout=30  # 30 second timeout for the search request
        )
        logger.info("Search request completed successfully")
        
        # Process results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            source = hit['_source']
            results.append({
                'book_title': source.get('book_title', ''),
                'author': source.get('author', ''),
                'book_summary': source.get('book_summary', ''),
                'score': hit['_score']
            })
        
        logger.info(f"Found {len(results)} book results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching OpenSearch: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise

def create_index_if_not_exists():
    """Create the OpenSearch index if it doesn't exist"""
    try:
        client = create_opensearch_client()
        
        # Check if index exists
        if not client.indices.exists(index=OPENSEARCH_INDEX):
            logger.info(f"Creating index: {OPENSEARCH_INDEX}")
            
            # Index mapping for book-level vector search
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
                        "book_summary": {"type": "text"},
                        "book_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "total_chunks": {"type": "integer"},
                        "chunk_summaries": {"type": "text"},
                        "embedding_model_id": {"type": "keyword"},
                        "summary_model_id": {"type": "keyword"},
                        "generated_at": {"type": "date"}
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

def load_book_summary_to_opensearch(book_summary_data):
    """Load book summary data into OpenSearch"""
    try:
        client = create_opensearch_client()
        
        # Create index if it doesn't exist
        create_index_if_not_exists()
        
        book_title = book_summary_data.get('book_title', 'Unknown')
        author = book_summary_data.get('author', 'Unknown')
        book_summary = book_summary_data.get('book_summary', '')
        book_embedding = book_summary_data.get('book_embedding', [])
        
        logger.info(f"Loading book summary for: {book_title}")
        
        # Fix generated_at to ISO 8601 format if possible
        generated_at = book_summary_data.get('generated_at', '')
        if generated_at:
            import datetime
            try:
                dt = datetime.datetime.strptime(generated_at, "%Y-%m-%d %H:%M:%S")
                generated_at = dt.isoformat()
            except Exception:
                # If parsing fails, leave as is
                pass
        
        # Prepare document
        doc = {
            "book_title": book_title,
            "author": author,
            "book_summary": book_summary,
            "book_embedding": book_embedding,
            "total_chunks": book_summary_data.get('total_chunks', 0),
            "chunk_summaries": "\n\n".join(book_summary_data.get('chunk_summaries', [])),
            "embedding_model_id": book_summary_data.get('embedding_model_id', ''),
            "summary_model_id": book_summary_data.get('summary_model_id', ''),
            "generated_at": generated_at
        }
        
        # Create a unique ID for the book
        import re
        book_id = re.sub(r'[^\w\s-]', '', book_title).strip()
        book_id = re.sub(r'[-\s]+', '-', book_id).lower()
        
        # Index the document
        response = client.index(
            index=OPENSEARCH_INDEX,
            id=book_id,
            body=doc,
            refresh=True
        )
        
        if response['result'] == 'created' or response['result'] == 'updated':
            logger.info(f"Successfully loaded book summary for {book_title}")
            return True
        else:
            logger.error(f"Failed to load book summary for {book_title}")
            return False
            
    except Exception as e:
        logger.error(f"Error loading book summary to OpenSearch: {str(e)}")
        return False

def check_opensearch_index():
    """Check OpenSearch index status and document count"""
    try:
        logger.info("Creating OpenSearch client for health check...")
        client = create_opensearch_client()
        logger.info("OpenSearch client created successfully for health check")
        
        # Test basic connectivity first
        logger.info("Testing OpenSearch connectivity...")
        cluster_info = client.info()
        logger.info(f"Connected to OpenSearch cluster: {cluster_info.get('cluster_name', 'unknown')}")
        
        # Check if index exists
        logger.info(f"Checking if index {OPENSEARCH_INDEX} exists...")
        index_exists = client.indices.exists(index=OPENSEARCH_INDEX)
        
        if not index_exists:
            logger.info(f"Index {OPENSEARCH_INDEX} does not exist")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'index_exists': False,
                    'document_count': 0,
                    'message': f'Index {OPENSEARCH_INDEX} does not exist'
                })
            }
        
        logger.info(f"Index {OPENSEARCH_INDEX} exists, getting document count...")
        # Get document count
        count_response = client.count(index=OPENSEARCH_INDEX)
        document_count = count_response['count']
        
        # Get index stats
        logger.info("Getting index statistics...")
        stats_response = client.indices.stats(index=OPENSEARCH_INDEX)
        index_stats = stats_response['indices'][OPENSEARCH_INDEX]
        
        logger.info(f"Health check completed successfully. Document count: {document_count}")
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
        logger.error(f"Error type: {type(e).__name__}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to check index: {str(e)}'
            })
        }

def purge_opensearch_index():
    """Delete and recreate the OpenSearch index for book summaries."""
    try:
        client = create_opensearch_client()
        if client.indices.exists(index=OPENSEARCH_INDEX):
            client.indices.delete(index=OPENSEARCH_INDEX)
            logger.info(f"Deleted index: {OPENSEARCH_INDEX}")
        # Recreate the index
        create_index_if_not_exists()
        logger.info(f"Recreated index: {OPENSEARCH_INDEX}")
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'message': f'Index {OPENSEARCH_INDEX} purged and recreated.'})
        }
    except Exception as e:
        logger.error(f"Error purging OpenSearch index: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        # Handle direct Lambda invocations (for loading book summaries)
        if 'action' in event:
            if event['action'] == 'load_book_summary':
                logger.info("Processing load_book_summary action")
                book_summary_data = event.get('book_summary_data', {})
                success = load_book_summary_to_opensearch(book_summary_data)
                return {
                    'statusCode': 200 if success else 500,
                    'body': json.dumps({'success': success})
                }
            elif event['action'] == 'check_index':
                logger.info("Processing check_index action")
                return check_opensearch_index()
            elif event['action'] == 'purge_index':
                logger.info("Processing purge_index action")
                return purge_opensearch_index()
        
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