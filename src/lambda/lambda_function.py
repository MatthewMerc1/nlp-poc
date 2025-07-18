#!/usr/bin/env python3
"""
Lambda function for semantic search using OpenSearch Serverless VECTORSEARCH
"""

import json
import logging
import os
import boto3
import requests
from requests_aws4auth import AWS4Auth
import socket

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
OPENSEARCH_INDEX = "book-summaries"  # Index
BEDROCK_MODEL_ID = "amazon.titan-embed-text-v1"


def get_aws_credentials():
    """Get AWS credentials from the Lambda environment."""
    session = boto3.Session()
    credentials = session.get_credentials()
    if not credentials:
        logger.error("No AWS credentials found in Lambda environment.")
        raise Exception("No AWS credentials available.")
    return credentials


def create_opensearch_auth():
    endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
    region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
    return endpoint, awsauth, region


def generate_embedding(text):
    """Generate embedding using Amazon Bedrock"""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        request_body = {"inputText": text}
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        response_body = json.loads(response['body'].read())
        embedding = response_body['embedding']
        logger.info(f"Generated embedding length: {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def test_opensearch_access():
    """Test basic OpenSearch access without k-NN search"""
    try:
        logger.info("Testing basic OpenSearch access...")
        endpoint, awsauth, _ = create_opensearch_auth()
        try:
            url = f"{endpoint}/_cluster/health"
            response = requests.get(url, auth=awsauth)
            response.raise_for_status()
            logger.info(f"Cluster info response: {response.json()}")
            logger.info("Basic OpenSearch access successful")
            return True
        except Exception as e:
            logger.error(f"Cluster info request failed: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error testing OpenSearch access: {str(e)}")
        return False


def search_opensearch(query_embedding, search_type="combined", size=5):
    """Search OpenSearch Serverless using embeddings"""
    try:
        endpoint, awsauth, _ = create_opensearch_auth()
        embedding_field_map = {
            "plot": "plot_summary_embedding",
            "thematic": "thematic_analysis_embedding",
            "character": "character_summary_embedding",
            "combined": "combined_embedding"
        }
        embedding_field = embedding_field_map.get(search_type, "combined_embedding")
        search_body = {
            "size": size,
            "query": {
                "knn": {
                    embedding_field: {
                        "vector": query_embedding,
                        "k": size
                    }
                }
            }
        }
        url = f"{endpoint}/book-summaries/_search"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, auth=awsauth, headers=headers, json=search_body)
        response.raise_for_status()
        search_result = response.json()
        hits = search_result['hits']['hits']
        results = []
        for hit in hits:
            source = hit['_source']
            results.append({
                'book_title': source.get('book_title', ''),
                'author': source.get('author', ''),
                'plot_summary': source.get('plot_summary', ''),
                'thematic_analysis': source.get('thematic_analysis', ''),
                'character_summary': source.get('character_summary', ''),
                'combined_summary': source.get('combined_summary', ''),
                'score': hit['_score'],
                'search_type': search_type
            })
        logger.info(f"Found {len(results)} book results")
        return results
    except Exception as e:
        logger.error(f"Error searching OpenSearch: {str(e)}")
        raise


def search_opensearch_multi_strategy(query_embedding, size=5):
    """Search using multiple strategies and combine results"""
    try:
        logger.info("Performing multi-strategy search...")
        strategies = ["combined", "plot", "thematic", "character"]
        all_results = []
        for strategy in strategies:
            try:
                results = search_opensearch(query_embedding, strategy, size)
                for result in results:
                    result['strategy'] = strategy
                    all_results.append(result)
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed: {str(e)}")
                continue
        seen_books = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x['score'], reverse=True):
            book_key = f"{result['book_title']}_{result['author']}"
            if book_key not in seen_books:
                seen_books.add(book_key)
                unique_results.append(result)
                if len(unique_results) >= size:
                    break
        logger.info(f"Multi-strategy search returned {len(unique_results)} unique results")
        return unique_results
    except Exception as e:
        logger.error(f"Error in multi-strategy search: {str(e)}")
        raise


def check_opensearch_index():
    """Check OpenSearch Serverless index status"""
    try:
        endpoint, awsauth, _ = create_opensearch_auth()
        url = f"{endpoint}/book-summaries"
        response = requests.head(url, auth=awsauth)
        if response.status_code == 404:
            logger.info(f"Index book-summaries does not exist")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'index_exists': False,
                    'document_count': 0,
                    'message': f'Index book-summaries does not exist'
                })
            }
        # Get document count
        count_url = f"{endpoint}/book-summaries/_count"
        count_response = requests.get(count_url, auth=awsauth)
        document_count = count_response.json().get('count', 0)
        logger.info(f"Health check completed successfully. Document count: {document_count}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'index_exists': True,
                'document_count': document_count,
                'message': f'Index book-summaries exists with {document_count} documents'
            })
        }
    except Exception as e:
        logger.error(f"Error checking OpenSearch index: {str(e)}")
        raise


def lambda_handler(event, context):
    """Lambda handler with multi-strategy search for OpenSearch Serverless"""
    import traceback
    try:
        # Add /info action for debugging OpenSearch connectivity
        if 'action' in event:
            if event['action'] == 'check_index':
                logger.info("Processing check_index action")
                return check_opensearch_index()
            if event['action'] == 'info':
                logger.info("Processing info action (OpenSearch client.info())")
                try:
                    endpoint, awsauth, _ = create_opensearch_auth()
                    url = f"{endpoint}/_cluster/health"
                    response = requests.get(url, auth=awsauth)
                    response.raise_for_status()
                    logger.info(f"OpenSearch client.info() response: {response.json()}")
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'info': response.json()})
                    }
                except Exception as e:
                    logger.error(f"Error in client.info(): {str(e)}\n{traceback.format_exc()}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps({'error': f'OpenSearch client.info() failed: {str(e)}', 'traceback': traceback.format_exc()})
                    }
        if 'body' in event:
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid JSON in request body'})
                }
            query = body.get('query', '')
            size = body.get('size', 5)
            search_strategy = body.get('search_strategy', 'multi')
            if not query:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Query parameter is required'})
                }
            logger.info(f"Processing query: {query}")
            logger.info(f"Search strategy: {search_strategy}")
            query_embedding = generate_embedding(query)
            logger.info(f"Generated embedding successfully")
            if search_strategy == 'multi':
                results = search_opensearch_multi_strategy(query_embedding, size)
            else:
                results = search_opensearch(query_embedding, search_strategy, size)
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
                    'search_strategy': search_strategy,
                    'results': results,
                    'total_results': len(results)
                })
            }
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request format'})
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}\n{traceback.format_exc()}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}', 'traceback': traceback.format_exc()})
        } 