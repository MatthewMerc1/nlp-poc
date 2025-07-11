#!/usr/bin/env python3
"""
Script to load book summaries and embeddings into OpenSearch for book-level semantic search.
"""

import boto3
import json
import os
import re
from typing import List, Dict
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError

class BookSummaryLoader:
    def __init__(self, bucket_name: str, opensearch_endpoint: str, aws_profile: str = None):
        """Initialize the book summary loader."""
        self.bucket_name = bucket_name
        self.opensearch_endpoint = opensearch_endpoint
        
        # Initialize AWS clients
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
        
        # Initialize OpenSearch client
        self.opensearch_client = self.create_opensearch_client(aws_profile)
    
    def create_opensearch_client(self, aws_profile: str = None):
        """Create OpenSearch client with AWS authentication."""
        try:
            # Get AWS credentials
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                credentials = session.get_credentials()
            else:
                session = boto3.Session()
                credentials = session.get_credentials()
            
            awsauth = AWS4Auth(
                credentials.access_key,
                credentials.secret_key,
                session.region_name or 'us-east-1',
                'es',
                session_token=credentials.token
            )
            
            # Create OpenSearch client
            host = self.opensearch_endpoint.replace('https://', '')
            client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
            
            return client
            
        except Exception as e:
            print(f"Error creating OpenSearch client: {e}")
            raise
    
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
                print("No book summaries found in S3 bucket")
                return []
                
        except ClientError as e:
            print(f"Error listing book summaries: {e}")
            return []
    
    def download_book_summary_from_s3(self, s3_key: str) -> Dict:
        """Download a book summary from S3 and return its content."""
        try:
            print(f"Downloading {s3_key} from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode('utf-8')
            book_summary_data = json.loads(content)
            
            print(f"Downloaded book summary for: {book_summary_data.get('book_title', 'Unknown')}")
            
            return book_summary_data
            
        except ClientError as e:
            print(f"Error downloading {s3_key}: {e}")
            return None
    
    def create_book_index_if_not_exists(self):
        """Create the OpenSearch index for book summaries if it doesn't exist."""
        try:
            index_name = "book-summaries"
            
            # Check if index exists
            if not self.opensearch_client.indices.exists(index=index_name):
                print(f"Creating index: {index_name}")
                
                # Index mapping for book-level vector search
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
                            "book_title": {"type": "text"},
                            "author": {"type": "text"},
                            "book_summary": {"type": "text"},
                            "book_embedding": {
                                "type": "knn_vector",
                                "dimension": 1536,
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "nmslib"
                                }
                            },
                            "total_chunks": {"type": "integer"},
                            "chunk_summaries": {"type": "text"},
                            "embedding_model_id": {"type": "keyword"},
                            "summary_model_id": {"type": "keyword"},
                            "generated_at": {"type": "date"}
                        }
                    }
                }
                
                self.opensearch_client.indices.create(
                    index=index_name,
                    body=index_mapping
                )
                print(f"Index {index_name} created successfully")
            else:
                print(f"Index {index_name} already exists")
                
        except Exception as e:
            print(f"Error creating index: {e}")
            raise
    
    def load_book_summary_to_opensearch(self, book_summary_data: Dict) -> bool:
        """Load a single book summary into OpenSearch."""
        try:
            # Prepare the document
            doc = {
                "book_title": book_summary_data.get('book_title', ''),
                "author": book_summary_data.get('author', ''),
                "book_summary": book_summary_data.get('book_summary', ''),
                "book_embedding": book_summary_data.get('book_embedding', []),
                "total_chunks": book_summary_data.get('total_chunks', 0),
                "chunk_summaries": "\n\n".join(book_summary_data.get('chunk_summaries', [])),
                "embedding_model_id": book_summary_data.get('embedding_model_id', ''),
                "summary_model_id": book_summary_data.get('summary_model_id', ''),
                "generated_at": book_summary_data.get('generated_at', '')
            }
            
            # Create a unique ID for the book
            book_id = re.sub(r'[^\w\s-]', '', book_summary_data.get('book_title', '')).strip()
            book_id = re.sub(r'[-\s]+', '-', book_id).lower()
            
            # Index the document
            response = self.opensearch_client.index(
                index="book-summaries",
                id=book_id,
                body=doc,
                refresh=True
            )
            
            if response['result'] == 'created' or response['result'] == 'updated':
                print(f"Successfully indexed book: {book_summary_data.get('book_title', '')}")
                return True
            else:
                print(f"Failed to index book: {book_summary_data.get('book_title', '')}")
                return False
                
        except Exception as e:
            print(f"Error loading book summary to OpenSearch: {e}")
            return False
    
    def process_all_book_summaries(self):
        """Process all book summaries in the S3 bucket and load them into OpenSearch."""
        print(f"Starting book summary loading for bucket: {self.bucket_name}")
        print(f"OpenSearch endpoint: {self.opensearch_endpoint}")
        print("=" * 60)
        
        # Create index if it doesn't exist
        self.create_book_index_if_not_exists()
        
        # List all book summaries
        summary_keys = self.list_book_summaries_in_s3()
        if not summary_keys:
            print("No book summaries found to process")
            return
        
        print(f"Found {len(summary_keys)} book summaries to process")
        
        # Process each book summary
        successful_books = 0
        for summary_key in summary_keys:
            book_summary_data = self.download_book_summary_from_s3(summary_key)
            if book_summary_data:
                if self.load_book_summary_to_opensearch(book_summary_data):
                    successful_books += 1
            print("-" * 40)
        
        print(f"Loading complete! Successfully loaded {successful_books}/{len(summary_keys)} book summaries")
    
    def check_index_status(self):
        """Check the status of the book-summaries index."""
        try:
            index_name = "book-summaries"
            
            # Check if index exists
            if not self.opensearch_client.indices.exists(index=index_name):
                print(f"Index {index_name} does not exist")
                return
            
            # Get document count
            count_response = self.opensearch_client.count(index=index_name)
            document_count = count_response['count']
            
            # Get index stats
            stats_response = self.opensearch_client.indices.stats(index=index_name)
            index_stats = stats_response['indices'][index_name]
            
            print(f"Index: {index_name}")
            print(f"Document count: {document_count}")
            print(f"Total size: {index_stats['total']['store']['size_in_bytes']} bytes")
            print(f"Primary shards: {index_stats['primaries']['docs']['count']} documents")
            
        except Exception as e:
            print(f"Error checking index status: {e}")

def main():
    """Main function to run the book summary loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load book summaries into OpenSearch for book-level search')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint URL')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--check-status', action='store_true', help='Check index status only')
    
    args = parser.parse_args()
    
    loader = BookSummaryLoader(args.bucket, args.opensearch_endpoint, args.profile)
    
    if args.check_status:
        loader.check_index_status()
    else:
        loader.process_all_book_summaries()

if __name__ == "__main__":
    main() 