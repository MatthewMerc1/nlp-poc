#!/usr/bin/env python3
"""
Lambda function for book recommendations using OpenSearch and Amazon Bedrock
"""

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
    """Create OpenSearch client with AWS authentication"""
    auth = get_aws_auth()
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT.replace('https://', ''), 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    return client

def generate_embedding(text):
    """Generate embedding using Bedrock"""
    try:
        request_body = {
            "inputText": text
        }
        logger.info(f"Generating embedding for query: {text}")
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        logger.info(f"Response: {response}")
        response_body = json.loads(response.get('body').read())
        embedding = response_body.get('embedding')
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise

def search_opensearch(query_embedding, size=5):
    """Search OpenSearch with vector similarity for book recommendations"""
    try:
        client = create_opensearch_client()
        
        # Vector search query for book recommendations
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    "book_vector": {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            },
            "_source": ["book_title", "author", "genre", "description", "gutenberg_id"]
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
    """Main Lambda handler for book recommendations"""
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
        
        logger.info(f"Processing book recommendation query: {query_text}")
        
        # Generate embedding for the query
        query_embedding = generate_embedding(query_text)
        logger.info("Generated embedding successfully")
        
        # Search OpenSearch for book recommendations
        search_results = search_opensearch(query_embedding, size)
        logger.info(f"Found {len(search_results)} book recommendations")
        
        # Format results for book recommendations
        formatted_results = []
        for hit in search_results:
            source = hit['_source']
            formatted_results.append({
                'score': hit['_score'],
                'title': source.get('book_title', 'Unknown'),
                'author': source.get('author', 'Unknown'),
                'genre': source.get('genre', 'Unknown'),
                'description': source.get('description', 'No description available'),
                'gutenberg_id': source.get('gutenberg_id', 'Unknown')
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
                'total_results': len(formatted_results),
                'recommendations': formatted_results
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
                'error': f'Internal server error: {str(e)}'
            })
        } 