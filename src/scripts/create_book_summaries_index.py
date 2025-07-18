#!/usr/bin/env python3
"""
Delete and recreate the 'book-summaries' index in OpenSearch with knn_vector fields for all embeddings (dimension 1536).
Compatible with OpenSearch Serverless (AWS4Auth).
"""
import argparse
import json
import logging
import sys
import requests
import boto3
from requests_aws4auth import AWS4Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_NAME = "book-summaries"
EMBEDDING_DIM = 1536

KNN_VECTOR_FIELD = {
    "type": "knn_vector",
    "dimension": EMBEDDING_DIM
}

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

def delete_index(session, endpoint, index):
    url = f"{endpoint}/{index}"
    response = session.delete(url)
    if response.status_code in (200, 404):
        logger.info(f"Index {index} deleted or did not exist.")
    else:
        logger.error(f"Failed to delete index: {response.status_code} {response.text}")
        sys.exit(1)

def create_index(session, endpoint, index):
    url = f"{endpoint}/{index}"
    mapping = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "book_title": {"type": "text"},
                "author": {"type": "text"},
                "plot_summary": {"type": "text"},
                "thematic_analysis": {"type": "text"},
                "character_summary": {"type": "text"},
                "combined_summary": {"type": "text"},
                "plot_embedding": KNN_VECTOR_FIELD,
                "thematic_embedding": KNN_VECTOR_FIELD,
                "character_embedding": KNN_VECTOR_FIELD,
                "combined_embedding": KNN_VECTOR_FIELD,
                "total_chunks": {"type": "integer"},
                "chunk_summaries": {"type": "text"},
                "embedding_model_id": {"type": "keyword"},
                "summary_model_id": {"type": "keyword"},
                "generated_at": {"type": "date"}
            }
        }
    }
    response = session.put(url, data=json.dumps(mapping))
    if response.status_code in (200, 201):
        logger.info(f"Index {index} created successfully.")
    else:
        logger.error(f"Failed to create index: {response.status_code} {response.text}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Recreate book-summaries index with knn_vector fields.")
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()

    awsauth = get_aws_auth(args.profile, args.region)
    session = requests.Session()
    session.auth = awsauth
    session.headers.update({"Content-Type": "application/json"})
    session.verify = True

    logger.info(f"Deleting index {INDEX_NAME} if it exists...")
    delete_index(session, args.opensearch_endpoint, INDEX_NAME)
    logger.info(f"Creating index {INDEX_NAME} with knn_vector fields...")
    create_index(session, args.opensearch_endpoint, INDEX_NAME)
    logger.info("Done.")

if __name__ == "__main__":
    main() 