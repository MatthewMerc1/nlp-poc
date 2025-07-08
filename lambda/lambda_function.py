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
        logger.info(f"Generating embedding for text: {text}")
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        logger.info(f"Response: {response}")
        response_body = json.loads(response.get('body').read())
        embedding = response_body.get('embedding')
        logger.info(f"Embedding: {embedding}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def search_opensearch(query_embedding, size=5):
    """Search OpenSearch with vector similarity"""
    try:
        client = create_opensearch_client()
        
        # Vector search query
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            },
            "_source": ["title", "author", "content", "book_id", "chapter"]
        }
        
        response = client.search(
            body=search_body,
            index=OPENSEARCH_INDEX
        )
        
        return response['hits']['hits']
    except Exception as e:
        logger.error(f"Error searching OpenSearch: {str(e)}")
        raise

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
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
                'title': source.get('title', 'Unknown'),
                'author': source.get('author', 'Unknown'),
                'book_id': source.get('book_id', 'Unknown'),
                'chapter': source.get('chapter', 'Unknown'),
                'content': source.get('content', '')[:500] + '...' if len(source.get('content', '')) > 500 else source.get('content', '')
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