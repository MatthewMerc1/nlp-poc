#!/usr/bin/env python3
"""
Simple search script to verify documents are indexed in OpenSearch Serverless
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

def search_documents(session, endpoint, index, query=None):
    url = f"{endpoint}/{index}/_search"
    
    if query is None:
        # Simple match_all query to get all documents
        search_body = {
            "size": 10,
            "query": {
                "match_all": {}
            }
        }
    else:
        # Text search query
        search_body = {
            "size": 10,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["book_title", "author"]
                }
            }
        }
    
    response = session.post(url, data=json.dumps(search_body))
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        logger.error(f"Search failed: {response.status_code} {response.text}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Search OpenSearch index")
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--index', default='book-summaries', help='Index name')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--query', help='Search query (optional)')
    args = parser.parse_args()

    awsauth = get_aws_auth(args.profile, args.region)
    session = requests.Session()
    session.auth = awsauth
    session.headers.update({"Content-Type": "application/json"})
    session.verify = True

    logger.info(f"Searching index: {args.index}")
    result = search_documents(session, args.opensearch_endpoint, args.index, args.query)
    
    if result:
        total_hits = result.get('hits', {}).get('total', {}).get('value', 0)
        logger.info(f"Found {total_hits} documents")
        
        for hit in result.get('hits', {}).get('hits', []):
            doc = hit['_source']
            logger.info(f"Document ID: {hit['_id']}")
            logger.info(f"Title: {doc.get('book_title', 'N/A')}")
            logger.info(f"Author: {doc.get('author', 'N/A')}")
            logger.info("---")
        
        print(json.dumps(result, indent=2))
    else:
        logger.error("Search failed")

if __name__ == "__main__":
    main() 