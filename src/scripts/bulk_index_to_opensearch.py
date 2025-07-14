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
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
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
    
    def create_opensearch_client(self, endpoint: str, username: str = 'admin', password: str = 'admin') -> OpenSearch:
        """Create OpenSearch client with proper configuration."""
        try:
            # Remove protocol from endpoint
            host = endpoint.replace('https://', '').replace('http://', '')
            
            client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=(username, password),
                use_ssl=True,
                verify_certs=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            cluster_info = client.info()
            logger.info(f"Connected to OpenSearch cluster: {cluster_info.get('cluster_name', 'unknown')}")
            
            return client
            
        except Exception as e:
            logger.error(f"Error creating OpenSearch client: {e}")
            raise
    
    def create_index_if_not_exists(self, client: OpenSearch, index_name: str = "book-summaries"):
        """Create the OpenSearch index if it doesn't exist."""
        try:
            # Check if index exists
            if not client.indices.exists(index=index_name):
                logger.info(f"Creating index: {index_name}")
                
                # Index mapping with multiple embedding fields
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
                
                # Create index
                response = client.indices.create(
                    index=index_name,
                    body=index_mapping
                )
                
                if response.get('acknowledged'):
                    logger.info(f"Successfully created index: {index_name}")
                else:
                    logger.error(f"Failed to create index: {index_name}")
                    return False
            else:
                logger.info(f"Index {index_name} already exists")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
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
                        username: str = 'admin', password: str = 'admin') -> bool:
        """Bulk index books to OpenSearch."""
        try:
            logger.info(f"Starting bulk indexing to OpenSearch...")
            logger.info(f"Endpoint: {opensearch_endpoint}")
            logger.info(f"Index: {index_name}")
            logger.info(f"Batch size: {batch_size}")
            
            # Create OpenSearch client
            client = self.create_opensearch_client(opensearch_endpoint, username, password)
            
            # Create index if it doesn't exist
            if not self.create_index_if_not_exists(client, index_name):
                logger.error("Failed to create index")
                return False
            
            # Get list of book summaries
            book_summary_keys = self.list_book_summaries_in_s3()
            if not book_summary_keys:
                logger.error("No book summaries found to index")
                return False
            
            logger.info(f"Found {len(book_summary_keys)} book summaries to index")
            
            # Apply max_books limit
            if max_books is not None:
                book_summary_keys = book_summary_keys[:max_books]
                logger.info(f"Limiting to {max_books} books")
            
            # Process books in batches
            total_indexed = 0
            total_errors = 0
            
            for i in range(0, len(book_summary_keys), batch_size):
                batch_keys = book_summary_keys[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(book_summary_keys) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_keys)} books)")
                
                # Download book summaries for this batch
                batch_books = []
                for s3_key in batch_keys:
                    book_data = self.download_book_summary_from_s3(s3_key)
                    if book_data:
                        batch_books.append(book_data)
                    else:
                        logger.warning(f"Failed to download book summary: {s3_key}")
                
                if not batch_books:
                    logger.warning(f"No valid book summaries in batch {batch_num}")
                    continue
                
                # Bulk index this batch
                try:
                    success_count, errors = bulk(
                        client, 
                        self.generate_documents(batch_books, index_name),
                        chunk_size=50,  # Smaller chunks for better error handling
                        request_timeout=60,
                        max_retries=3
                    )
                    
                    total_indexed += success_count
                    total_errors += len(errors) if errors else 0
                    
                    logger.info(f"Batch {batch_num} complete: {success_count} indexed, {len(errors) if errors else 0} errors")
                    
                    if errors:
                        logger.error(f"Errors in batch {batch_num}:")
                        for error in errors[:3]:  # Show first 3 errors
                            logger.error(f"  - {error}")
                    
                    # Small delay between batches to avoid overwhelming the cluster
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error indexing batch {batch_num}: {e}")
                    total_errors += len(batch_books)
            
            logger.info(f"Bulk indexing complete!")
            logger.info(f"Total indexed: {total_indexed}")
            logger.info(f"Total errors: {total_errors}")
            
            # Verify indexing
            try:
                count_response = client.count(index=index_name)
                actual_count = count_response['count']
                logger.info(f"Documents in index: {actual_count}")
                
                if actual_count != total_indexed:
                    logger.warning(f"Count mismatch: expected {total_indexed}, actual {actual_count}")
                
            except Exception as e:
                logger.error(f"Error verifying index count: {e}")
            
            return total_errors == 0
            
        except Exception as e:
            logger.error(f"Error during bulk indexing: {e}")
            return False
    
    def purge_index(self, opensearch_endpoint: str, index_name: str = "book-summaries",
                   username: str = 'admin', password: str = 'admin') -> bool:
        """Purge all documents from the index."""
        try:
            logger.info(f"Purging index: {index_name}")
            
            # Create OpenSearch client
            client = self.create_opensearch_client(opensearch_endpoint, username, password)
            
            # Check if index exists
            if not client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} does not exist")
                return True
            
            # Delete all documents
            response = client.delete_by_query(
                index=index_name,
                body={"query": {"match_all": {}}}
            )
            
            deleted_count = response.get('deleted', 0)
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
        if not indexer.purge_index(args.opensearch_endpoint, args.index_name, args.username, args.password):
            logger.error("Failed to purge index")
            exit(1)
    
    # Perform bulk indexing
    success = indexer.bulk_index_books(
        args.opensearch_endpoint,
        args.index_name,
        args.batch_size,
        args.max_books,
        args.username,
        args.password
    )
    
    if success:
        logger.info("Bulk indexing completed successfully!")
    else:
        logger.error("Bulk indexing failed!")
        exit(1)

if __name__ == "__main__":
    main() 