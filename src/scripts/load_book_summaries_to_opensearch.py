#!/usr/bin/env python3
"""
Direct script to load book summaries into OpenSearch
Avoids Lambda payload size limitations by loading directly
"""

import json
import logging
import os
import sys
import boto3
import argparse
import requests
from requests_aws4auth import AWS4Auth
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENSEARCH_INDEX = "book-summaries"
BEDROCK_MODEL_ID = "amazon.titan-embed-text-v1"

def get_aws_auth(profile_name, region):
    """Get AWS authentication for OpenSearch"""
    try:
        session = boto3.Session(profile_name=profile_name)
        credentials = session.get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            session.region_name or region,
            'aoss',  # Use 'aoss' for OpenSearch Serverless instead of 'es'
            session_token=credentials.token
        )
        return awsauth
    except Exception as e:
        logger.error(f"Error getting AWS auth: {str(e)}")
        raise

def create_opensearch_session(endpoint, profile_name, region):
    """Create a requests session with AWS4Auth for OpenSearch Serverless"""
    awsauth = get_aws_auth(profile_name, region)
    session = requests.Session()
    session.auth = awsauth
    session.headers.update({"Content-Type": "application/json"})
    session.verify = True
    return session

def index_exists(session, endpoint, index):
    url = f"{endpoint}/{index}"
    response = session.head(url)
    return response.status_code == 200

def create_index(session, endpoint, index, index_mapping):
    url = f"{endpoint}/{index}"
    response = session.put(url, data=json.dumps(index_mapping))
    if response.status_code in (200, 201):
        logger.info(f"Index {index} created successfully")
        return True
    elif response.status_code == 400 and 'resource_already_exists_exception' in response.text:
        logger.info(f"Index {index} already exists")
        return True
    else:
        logger.error(f"Error creating index: {response.status_code} {response.text}")
        return False

def index_document(session, endpoint, index, doc_id, doc):
    url = f"{endpoint}/{index}/_doc/{doc_id}"
    logger.info(f"Indexing document: {doc_id} to URL: {url}")
    response = session.put(url, data=json.dumps(doc))
    logger.info(f"Indexing response status: {response.status_code}, body: {response.text}")
    if response.status_code in (200, 201):
        logger.info(f"Successfully indexed document {doc_id}")
        return True
    else:
        logger.error(f"Failed to index document {doc_id}: {response.status_code} {response.text}")
        return False

def count_documents(session, endpoint, index):
    url = f"{endpoint}/{index}/_count"
    response = session.post(url)
    if response.status_code == 200:
        return response.json().get('count', 0)
    else:
        logger.warning(f"Could not count documents: {response.status_code} {response.text}")
        return None

def get_index_stats(session, endpoint, index):
    url = f"{endpoint}/{index}/_stats"
    response = session.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.warning(f"Could not fetch index stats: {response.status_code} {response.text}")
        return None

def create_index_if_not_exists(session, endpoint, index):
    if not index_exists(session, endpoint, index):
        logger.info(f"Creating index: {index}")
        index_mapping = {
            "settings": {
                "index": {
                    "knn": True
                }
            },
            "mappings": {
                "properties": {
                    "book_title": {"type": "text"},
                    "author": {"type": "text"},
                    "plot_summary_embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    },
                    "thematic_analysis_embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    },
                    "character_summary_embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    },
                    "combined_embedding": {
                        "type": "knn_vector",
                        "dimension": 1536
                    }
                }
            }
        }
        return create_index(session, endpoint, index, index_mapping)
    else:
        logger.info(f"Index {index} already exists")
        return True

import os
import re

def parse_title_author_from_filename(filename):
    # Remove path and .json extension
    base = os.path.basename(filename)
    if base.endswith('.json'):
        base = base[:-5]
    # Split on last '-' for title/author
    if '-' in base:
        parts = base.rsplit('-', 1)
        title = parts[0].replace('-', ' ').replace('_', ' ').strip()
        author = parts[1].replace(',', ', ').replace('-', ' ').strip()
    else:
        title = base.replace('-', ' ').replace('_', ' ').strip()
        author = "Unknown"
    return title, author

def load_book_summary_to_opensearch(session, endpoint, book_summary_data, summary_key):
    try:
        # Use filename for ID, title, and author
        book_id = os.path.basename(summary_key)[:-5] if summary_key.endswith('.json') else os.path.basename(summary_key)
        book_title, author = parse_title_author_from_filename(summary_key)
        logger.info(f"Loading book summary for: {book_title} by {author}")
        # Only include fields present in the JSON
        doc = {k: v for k, v in book_summary_data.items() if k.endswith('_embedding')}
        doc["book_title"] = book_title
        doc["author"] = author
        return index_document(session, endpoint, OPENSEARCH_INDEX, book_id, doc)
    except Exception as e:
        logger.error(f"Error loading book summary to OpenSearch: {str(e)}")
        traceback.print_exc()
        return False

def list_summaries(s3_client, bucket_name, s3_prefix):
    try:
        logger.info(f"Listing S3 objects in bucket '{bucket_name}' with prefix '{s3_prefix}'...")
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=s3_prefix
        )
        all_keys = [obj['Key'] for obj in response.get('Contents', [])]
        logger.info(f"Found {len(all_keys)} objects in S3 with prefix '{s3_prefix}': {all_keys}")
        summaries = []
        for key in all_keys:
            if key.endswith('.json'):
                summaries.append(key)
        logger.info(f"Filtered to {len(summaries)} summary files ending with '.json'.")
        return summaries
    except Exception as e:
        logger.error(f"Error listing summaries: {str(e)}")
        raise

def download_and_load_summary(s3_client, bucket_name, summary_key, session, endpoint):
    try:
        logger.info(f"Processing: {summary_key}")
        response = s3_client.get_object(Bucket=bucket_name, Key=summary_key)
        book_summary_data = json.loads(response['Body'].read().decode('utf-8'))
        success = load_book_summary_to_opensearch(session, endpoint, book_summary_data, summary_key)
        return success
    except Exception as e:
        logger.error(f"Error processing {summary_key}: {str(e)}")
        traceback.print_exc()
        return False

def check_index_status(session, endpoint, index):
    try:
        exists = index_exists(session, endpoint, index)
        if not exists:
            logger.info(f"Index {index} does not exist")
            return {
                'index_exists': False,
                'document_count': 0,
                'message': f'Index {index} does not exist'
            }
        document_count = count_documents(session, endpoint, index)
        stats = get_index_stats(session, endpoint, index)
        return {
            'index_exists': True,
            'document_count': document_count,
            'index_stats': stats,
            'message': f'Index {index} has {document_count} documents'
        }
    except Exception as e:
        logger.error(f"Error checking index: {str(e)}")
        traceback.print_exc()
        raise

def build_bulk_body(docs, index_name):
    """Build newline-delimited JSON for the OpenSearch _bulk API."""
    lines = []
    for doc_id, doc in docs.items():
        # For VECTORSEARCH collections, don't specify _id - let OpenSearch auto-generate
        action = {"index": {"_index": index_name}}
        lines.append(json.dumps(action))
        lines.append(json.dumps(doc))
    return '\n'.join(lines) + '\n'


def bulk_index_documents(session, endpoint, index, docs):
    url = f"{endpoint}/{index}/_bulk"
    bulk_body = build_bulk_body(docs, index)
    response = session.post(url, data=bulk_body, headers={"Content-Type": "application/x-ndjson"})
    if response.status_code in (200, 201):
        result = response.json()
        errors = result.get('errors', False)
        if errors:
            logger.error(f"Bulk indexing completed with errors: {result}")
        else:
            logger.info(f"Bulk indexing successful: {result.get('items', [])}")
        return not errors
    else:
        logger.error(f"Bulk indexing failed: {response.status_code} {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Load book summaries directly to OpenSearch (bulk mode)')
    parser.add_argument('--bucket', required=False, help='S3 bucket name')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--check-only', action='store_true', help='Only check index status')
    parser.add_argument('--s3-prefix', default='embeddings/', help='S3 prefix/folder to look for summaries (default: embeddings/)')
    args = parser.parse_args()
    try:
        session = create_opensearch_session(args.opensearch_endpoint, args.profile, args.region)
        if args.check_only:
            status = check_index_status(session, args.opensearch_endpoint, OPENSEARCH_INDEX)
            print(json.dumps(status, indent=2))
            return
        if not args.bucket:
            parser.error("--bucket is required when not using --check-only")
        s3_client = boto3.Session(profile_name=args.profile).client('s3', region_name=args.region)
        create_index_if_not_exists(session, args.opensearch_endpoint, OPENSEARCH_INDEX)
        logger.info("Listing book summaries in S3...")
        summaries = list_summaries(s3_client, args.bucket, args.s3_prefix)
        if not summaries:
            logger.error("No book summaries found in S3!")
            sys.exit(1)
        logger.info(f"Found {len(summaries)} summaries")
        docs = {}
        for summary_key in summaries:
            try:
                response = s3_client.get_object(Bucket=args.bucket, Key=summary_key)
                book_summary_data = json.loads(response['Body'].read().decode('utf-8'))
                book_id = os.path.basename(summary_key)[:-5] if summary_key.endswith('.json') else os.path.basename(summary_key)
                book_title, author = parse_title_author_from_filename(summary_key)
                doc = {k: v for k, v in book_summary_data.items() if k.endswith('_embedding')}
                doc["book_title"] = book_title
                doc["author"] = author
                docs[book_id] = doc
            except Exception as e:
                logger.error(f"Error processing {summary_key}: {str(e)}")
                traceback.print_exc()
        if not docs:
            logger.error("No valid documents to index!")
            sys.exit(1)
        logger.info(f"Bulk indexing {len(docs)} documents...")
        success = bulk_index_documents(session, args.opensearch_endpoint, OPENSEARCH_INDEX, docs)
        if not success:
            logger.error("Bulk indexing failed!")
            sys.exit(1)
        logger.info("Bulk indexing complete!")
        logger.info("Checking final index status...")
        status = check_index_status(session, args.opensearch_endpoint, OPENSEARCH_INDEX)
        print(json.dumps(status, indent=2))
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 