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
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from opensearchpy.exceptions import NotFoundError
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENSEARCH_INDEX = "book-summaries"
BEDROCK_MODEL_ID = "amazon.titan-embed-text-v1"

def get_aws_auth(profile_name):
    """Get AWS authentication for OpenSearch"""
    try:
        session = boto3.Session(profile_name=profile_name)
        credentials = session.get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            session.region_name or 'us-east-1',
            'aoss',  # Use 'aoss' for OpenSearch Serverless instead of 'es'
            session_token=credentials.token
        )
        return awsauth
    except Exception as e:
        logger.error(f"Error getting AWS auth: {str(e)}")
        raise

def create_opensearch_client(endpoint, profile_name):
    """Create OpenSearch client"""
    try:
        # Check if this is a local endpoint (for development)
        is_local = endpoint.startswith('localhost') or endpoint.startswith('127.0.0.1')
        
        # These options disable sniffing and root endpoint health checks, which cause 404s on OpenSearch Serverless
        sniffing_options = {
            'sniff_on_start': False,
            'sniff_on_connection_fail': False,
            'sniffer_timeout': None
        }
        
        if is_local:
            # For local development, use basic auth or no auth
            logger.info(f"Connecting to local OpenSearch endpoint: {endpoint}")
            client = OpenSearch(
                hosts=[{'host': endpoint.split(':')[0], 'port': int(endpoint.split(':')[1])}],
                use_ssl=True,
                verify_certs=False,  # Disable SSL verification for local development
                connection_class=RequestsHttpConnection,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
                retry_on_status=[429, 500, 502, 503, 504],
                **sniffing_options
            )
        else:
            # For AWS OpenSearch, use AWS auth
            awsauth = get_aws_auth(profile_name)
            client = OpenSearch(
                hosts=[{'host': endpoint.replace('https://', ''), 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
                retry_on_status=[429, 500, 502, 503, 504],
                **sniffing_options
            )
    except Exception as e:
        logger.error(f"Error creating OpenSearch client: {str(e)}")
        traceback.print_exc()
        raise

    # Now test with an index-specific call to ensure connectivity
    try:
        client.indices.exists(index=OPENSEARCH_INDEX)
    except NotFoundError:
        # This is fine, means the index doesn't exist yet
        pass
    except Exception as e:
        logger.warning(f"Unexpected error when testing index existence: {e}")
        traceback.print_exc()
    return client

def create_index_if_not_exists(client):
    """Create the OpenSearch index if it doesn't exist"""
    try:
        # Check if index exists
        if not client.indices.exists(index=OPENSEARCH_INDEX):
            logger.info(f"Creating index: {OPENSEARCH_INDEX}")
            
            # Enhanced index mapping for SEARCH collection type (no KNN support)
            index_mapping = {
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
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
                        "plot_embedding": {"type": "binary"},
                        "thematic_embedding": {"type": "binary"},
                        "character_embedding": {"type": "binary"},
                        "combined_embedding": {"type": "binary"},
                        "total_chunks": {"type": "integer"},
                        "chunk_summaries": {"type": "text"},
                        "embedding_model_id": {"type": "keyword"},
                        "summary_model_id": {"type": "keyword"},
                        "generated_at": {"type": "date"}
                    }
                }
            }
            
            client.indices.create(index=OPENSEARCH_INDEX, body=index_mapping)
            logger.info(f"Index {OPENSEARCH_INDEX} created successfully")
        else:
            logger.info(f"Index {OPENSEARCH_INDEX} already exists")
            
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def load_book_summary_to_opensearch(client, book_summary_data):
    """Load book summary data into OpenSearch"""
    try:
        book_title = book_summary_data.get('book_title', 'Unknown')
        author = book_summary_data.get('author', 'Unknown')
        
        logger.info(f"Loading book summary for: {book_title}")
        
        # Fix generated_at to ISO 8601 format if possible
        generated_at = book_summary_data.get('generated_at', '')
        if generated_at:
            import datetime
            try:
                dt = datetime.datetime.strptime(generated_at, "%Y-%m-%d %H:%M:%S")
                generated_at = dt.isoformat()
            except Exception:
                pass
        
        # Prepare document with all embedding types
        doc = {
            "book_title": book_title,
            "author": author,
            "plot_summary": book_summary_data.get('plot_summary', ''),
            "thematic_analysis": book_summary_data.get('thematic_analysis', ''),
            "character_summary": book_summary_data.get('character_summary', ''),
            "combined_summary": book_summary_data.get('combined_summary', ''),
            "plot_embedding": book_summary_data.get('plot_embedding', []),
            "thematic_embedding": book_summary_data.get('thematic_embedding', []),
            "character_embedding": book_summary_data.get('character_embedding', []),
            "combined_embedding": book_summary_data.get('combined_embedding', []),
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

def list_summaries(s3_client, bucket_name):
    """List book summaries in S3"""
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='book-summaries/'
        )
        
        summaries = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('summary.json'):
                summaries.append(obj['Key'])
        
        return summaries
    except Exception as e:
        logger.error(f"Error listing summaries: {str(e)}")
        raise

def download_and_load_summary(s3_client, bucket_name, summary_key, opensearch_client):
    """Download and load a single summary"""
    try:
        logger.info(f"Processing: {summary_key}")
        
        # Download from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=summary_key)
        book_summary_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Load to OpenSearch
        success = load_book_summary_to_opensearch(opensearch_client, book_summary_data)
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing {summary_key}: {str(e)}")
        return False

def check_index_status(client):
    """Check index status"""
    try:
        # Check if index exists
        index_exists = client.indices.exists(index=OPENSEARCH_INDEX)
        if not index_exists:
            logger.info(f"Index {OPENSEARCH_INDEX} does not exist")
            return {
                'index_exists': False,
                'document_count': 0,
                'message': f'Index {OPENSEARCH_INDEX} does not exist'
            }

        # Get document count
        count_response = client.count(index=OPENSEARCH_INDEX)
        document_count = count_response['count']

        # Try to get index stats, but handle 404 gracefully
        stats = None
        try:
            stats_response = client.indices.stats(index=OPENSEARCH_INDEX)
            index_stats = stats_response['indices'][OPENSEARCH_INDEX]
            stats = {
                'total_docs': index_stats['total']['docs']['count'],
                'total_size': index_stats['total']['store']['size_in_bytes'],
                'primaries_docs': index_stats['primaries']['docs']['count'],
                'primaries_size': index_stats['primaries']['store']['size_in_bytes']
            }
        except Exception as e:
            logger.warning(f"Could not fetch index stats: {e}")
            stats = None

        return {
            'index_exists': True,
            'document_count': document_count,
            'index_stats': stats,
            'message': f'Index {OPENSEARCH_INDEX} has {document_count} documents'
        }

    except Exception as e:
        logger.error(f"Error checking index: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Load book summaries directly to OpenSearch')
    parser.add_argument('--bucket', required=False, help='S3 bucket name')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--check-only', action='store_true', help='Only check index status')
    
    args = parser.parse_args()
    
    try:
        # Create OpenSearch client
        opensearch_client = create_opensearch_client(args.opensearch_endpoint, args.profile)
        
        if args.check_only:
            # Only check index status
            status = check_index_status(opensearch_client)
            print(json.dumps(status, indent=2))
            return
        
        # For loading, bucket is required
        if not args.bucket:
            parser.error("--bucket is required when not using --check-only")
        
        # Create S3 client
        s3_client = boto3.Session(profile_name=args.profile).client('s3', region_name=args.region)
        
        # Create index if it doesn't exist
        create_index_if_not_exists(opensearch_client)
        
        # List summaries
        logger.info("Listing book summaries in S3...")
        summaries = list_summaries(s3_client, args.bucket)
        
        if not summaries:
            logger.error("No book summaries found in S3!")
            sys.exit(1)
        
        logger.info(f"Found {len(summaries)} summaries")
        
        # Load each summary
        success_count = 0
        total_count = len(summaries)
        
        for summary_key in summaries:
            success = download_and_load_summary(s3_client, args.bucket, summary_key, opensearch_client)
            if success:
                success_count += 1
            
            # Rate limiting
            import time
            time.sleep(1)
        
        logger.info("==================================")
        logger.info("Summary loading complete!")
        logger.info(f"Successfully loaded: {success_count}/{total_count} summaries")
        
        # Check final status
        logger.info("Checking final index status...")
        status = check_index_status(opensearch_client)
        print(json.dumps(status, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 