#!/usr/bin/env python3
"""
Test script to verify k-NN search query format for OpenSearch Serverless VECTORSEARCH
"""
import argparse
import json
import logging
import requests
import boto3
from requests_aws4auth import AWS4Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_aws_auth(profile_name, region):
    session = boto3.Session(profile_name=profile_name)
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        session.region_name or region,
        'aoss',
        session_token=credentials.token
    )
    return awsauth

def test_vector_search(session, endpoint, index, embedding_field, query_embedding):
    """Test k-NN vector search with different query formats"""
    url = f"{endpoint}/{index}/_search"
    
    # Test different query formats
    test_queries = [
        # Format 1: Standard k-NN query
        {
            "size": 3,
            "query": {
                "knn": {
                    embedding_field: {
                        "vector": query_embedding,
                        "k": 3
                    }
                }
            }
        },
        # Format 2: k-NN with filter
        {
            "size": 3,
            "query": {
                "knn": {
                    embedding_field: {
                        "vector": query_embedding,
                        "k": 3
                    }
                }
            }
        },
        # Format 3: Simple match_all to test basic access
        {
            "size": 3,
            "query": {
                "match_all": {}
            }
        }
    ]
    
    for i, search_body in enumerate(test_queries, 1):
        logger.info(f"Testing query format {i}: {json.dumps(search_body, indent=2)}")
        
        try:
            response = session.post(url, data=json.dumps(search_body))
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get('hits', {}).get('hits', [])
                logger.info(f"Found {len(hits)} results")
                
                for hit in hits:
                    doc = hit['_source']
                    logger.info(f"Document: {doc.get('book_title', 'N/A')} by {doc.get('author', 'N/A')}")
                
                return True
            else:
                logger.error(f"Query {i} failed: {response.status_code} {response.text}")
                
        except Exception as e:
            logger.error(f"Query {i} exception: {str(e)}")
    
    return False

def generate_test_embedding():
    """Generate a simple test embedding (1536 dimensions)"""
    # Create a simple test embedding with 1536 dimensions
    return [0.1] * 1536

def main():
    parser = argparse.ArgumentParser(description="Test vector search in OpenSearch Serverless")
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--index', default='book-summaries', help='Index name')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()

    awsauth = get_aws_auth(args.profile, args.region)
    session = requests.Session()
    session.auth = awsauth
    session.headers.update({"Content-Type": "application/json"})
    session.verify = True

    logger.info(f"Testing vector search on index: {args.index}")
    
    # Generate test embedding
    test_embedding = generate_test_embedding()
    logger.info(f"Generated test embedding with {len(test_embedding)} dimensions")
    
    # Test with different embedding fields
    embedding_fields = ["combined_embedding", "plot_summary_embedding", "thematic_analysis_embedding", "character_summary_embedding"]
    
    for field in embedding_fields:
        logger.info(f"\nTesting with field: {field}")
        success = test_vector_search(session, args.opensearch_endpoint, args.index, field, test_embedding)
        if success:
            logger.info(f"Success with field: {field}")
            break

if __name__ == "__main__":
    main() 