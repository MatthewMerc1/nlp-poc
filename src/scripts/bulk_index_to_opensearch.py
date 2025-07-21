#!/usr/bin/env python3
"""
Bulk indexing script for loading book summaries to OpenSearch efficiently.
This script can index large numbers of book summaries using OpenSearch's bulk API.
"""

import boto3
import json
import os
import re
import logging
import argparse
from typing import List, Dict, Generator
from botocore.exceptions import ClientError
import requests
from requests_aws4auth import AWS4Auth
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BulkIndexer:
    def __init__(self, bucket_name: str, aws_profile: str = None):
        """Initialize the bulk indexer."""
        self.bucket_name = bucket_name
        
        # Initialize AWS client
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
    
    def list_book_summaries_in_s3(self) -> List[str]:
        """List all book summary files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='book-summaries/'
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('-summary.json')]
            else:
                logger.info("No book summaries found in S3 bucket")
                return []
                
        except ClientError as e:
            logger.error(f"Error listing book summaries: {e}")
            return []
    
    def download_book_summary_from_s3(self, s3_key: str) -> Dict:
        """Download a book summary from S3 and return its content."""
        try:
            logger.info(f"Downloading {s3_key} from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode('utf-8')
            book_data = json.loads(content)
            
            logger.info(f"Downloaded book summary for: {book_data.get('book_title', 'Unknown')}")
            return book_data
            
        except ClientError as e:
            logger.error(f"Error downloading {s3_key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {s3_key}: {e}")
            return None
    
    def create_opensearch_client(self, endpoint: str, username: str = 'admin', password: str = 'admin'):
        """(REMOVED) No longer needed, replaced by requests-based calls."""
        pass
    
    def create_index_if_not_exists(self, endpoint: str, index_name: str = "book-summaries", awsauth=None):
        """Create the OpenSearch index if it doesn't exist using requests."""
        url = f"{endpoint}/{index_name}"
        headers = {"Content-Type": "application/json"}
        # Check if index exists
        response = requests.head(url, auth=awsauth, headers=headers)
        if response.status_code == 404:
            logger.info(f"Creating index: {index_name}")
            # Define your index mapping here (reuse from previous code)
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
                        "book_title": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "author": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "plot_summary": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "thematic_analysis": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "character_summary": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "combined_summary": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "plot_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "thematic_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "character_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "combined_embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "total_chunks": {
                            "type": "integer"
                        },
                        "chunk_summaries": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "embedding_model_id": {
                            "type": "keyword"
                        },
                        "summary_model_id": {
                            "type": "keyword"
                        },
                        "generated_at": {
                            "type": "date"
                        }
                    }
                }
            }
            response = requests.put(url, auth=awsauth, headers=headers, json=index_mapping)
            if response.status_code not in (200, 201):
                logger.error(f"Failed to create index: {response.text}")
        elif response.status_code != 200:
            logger.error(f"Error checking index: {response.text}")
    
    def generate_documents(self, book_summaries: List[Dict], index_name: str = "book-summaries") -> Generator[Dict, None, None]:
        """Generate documents for bulk indexing."""
        for book_data in book_summaries:
            # Create a unique ID for the book
            book_title = book_data.get('book_title', 'Unknown')
            book_id = re.sub(r'[^\w\s-]', '', book_title).strip()
            book_id = re.sub(r'[-\s]+', '-', book_id).lower()
            
            # Prepare document for indexing
            doc = {
                "_index": index_name,
                "_id": book_id,
                "_source": {
                    "book_title": book_title,
                    "author": book_data.get('author', 'Unknown Author'),
                    "plot_summary": book_data.get('plot_summary', ''),
                    "thematic_analysis": book_data.get('thematic_analysis', ''),
                    "character_summary": book_data.get('character_summary', ''),
                    "combined_summary": book_data.get('combined_summary', ''),
                    "plot_embedding": book_data.get('plot_embedding', []),
                    "thematic_embedding": book_data.get('thematic_embedding', []),
                    "character_embedding": book_data.get('character_embedding', []),
                    "combined_embedding": book_data.get('combined_embedding', []),
                    "total_chunks": book_data.get('total_chunks', 0),
                    "chunk_summaries": "\n\n".join(book_data.get('chunk_summaries', [])),
                    "embedding_model_id": book_data.get('embedding_model_id', ''),
                    "summary_model_id": book_data.get('summary_model_id', ''),
                    "generated_at": book_data.get('generated_at', '')
                }
            }
            
            yield doc
    
    def bulk_index_books(self, opensearch_endpoint: str, index_name: str = "book-summaries",
                        batch_size: int = 100, max_books: int = None,
                        aws_profile: str = None, region: str = "us-east-1") -> bool:
        """Bulk index books to OpenSearch using the bulk API via requests."""
        # Setup AWS auth
        session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)
        # Create index if needed
        self.create_index_if_not_exists(opensearch_endpoint, index_name, awsauth)
        # Prepare bulk payload
        def generate_bulk_payload(book_summaries):
            for book in book_summaries:
                book_id = re.sub(r'[^\w\s-]', '', book['book_title']).strip()
                book_id = re.sub(r'[-\s]+', '-', book_id).lower()
                meta = {"index": {"_index": index_name, "_id": book_id}}
                yield json.dumps(meta)
                yield json.dumps(book)
        # List and download summaries
        keys = self.list_book_summaries_in_s3()
        if max_books:
            keys = keys[:max_books]
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i:i+batch_size]
            books = [self.download_book_summary_from_s3(k) for k in batch_keys if self.download_book_summary_from_s3(k)]
            bulk_lines = '\n'.join(generate_bulk_payload(books)) + '\n'
            url = f"{opensearch_endpoint}/_bulk"
            headers = {"Content-Type": "application/x-ndjson"}
            response = requests.post(url, auth=awsauth, headers=headers, data=bulk_lines)
            if response.status_code not in (200, 201):
                logger.error(f"Bulk index failed: {response.text}")
                return False
            logger.info(f"Bulk indexed {len(books)} books.")
        return True
    
    def purge_index(self, opensearch_endpoint: str, index_name: str = "book-summaries",
                   aws_profile: str = None, region: str = "us-east-1") -> bool:
        """Purge all documents from the index."""
        try:
            logger.info(f"Purging index: {index_name}")
            
            # Setup AWS auth
            session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
            credentials = session.get_credentials().get_frozen_credentials()
            awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'aoss', session_token=credentials.token)

            # Check if index exists
            url = f"{opensearch_endpoint}/{index_name}"
            response = requests.head(url, auth=awsauth)
            if response.status_code == 404:
                logger.info(f"Index {index_name} does not exist")
                return True
            
            # Delete all documents
            url = f"{opensearch_endpoint}/{index_name}/_delete_by_query"
            response = requests.post(url, auth=awsauth, json={"query": {"match_all": {}}})
            
            deleted_count = response.json().get('deleted', 0)
            logger.info(f"Deleted {deleted_count} documents from index {index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error purging index: {e}")
            return False

def main():
    """Main function to run the bulk indexer."""
    parser = argparse.ArgumentParser(description='Bulk index book summaries to OpenSearch')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--index-name', default='book-summaries', help='OpenSearch index name')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--max-books', type=int, default=None, help='Maximum number of books to index')
    parser.add_argument('--username', default='admin', help='OpenSearch username')
    parser.add_argument('--password', default='admin', help='OpenSearch password')
    parser.add_argument('--purge', action='store_true', help='Purge index before indexing')
    
    args = parser.parse_args()
    
    indexer = BulkIndexer(args.bucket, args.profile)
    
    # Purge index if requested
    if args.purge:
        logger.info("Purging index before indexing...")
        if not indexer.purge_index(args.opensearch_endpoint, args.index_name, args.profile):
            logger.error("Failed to purge index")
            exit(1)
    
    # Perform bulk indexing
    success = indexer.bulk_index_books(
        args.opensearch_endpoint,
        args.index_name,
        args.batch_size,
        args.max_books,
        args.profile
    )
    
    if success:
        logger.info("Bulk indexing completed successfully!")
    else:
        logger.error("Bulk indexing failed!")
        exit(1)

if __name__ == "__main__":
    main() 