#!/usr/bin/env python3
"""
Script to load book embeddings from S3 into OpenSearch for book recommendations.
"""

import boto3
import json
import requests
from typing import List, Dict
import time
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth
import base64

class BookOpenSearchLoader:
    def __init__(self, bucket_name: str, opensearch_endpoint: str, aws_profile: str = None):
        """Initialize the OpenSearch loader for books."""
        self.bucket_name = bucket_name
        self.opensearch_endpoint = opensearch_endpoint.rstrip('/')
        
        # Initialize AWS clients
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
        
        # OpenSearch connection
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def list_book_embeddings_in_s3(self) -> List[str]:
        """List all book embedding files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='book-recommendations/'
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.json')]
            else:
                print("No book embeddings found in S3 bucket")
                return []
                
        except ClientError as e:
            print(f"Error listing book embeddings: {e}")
            return []
    
    def download_book_embedding_from_s3(self, s3_key: str) -> Dict:
        """Download book embedding from S3."""
        try:
            print(f"Downloading {s3_key} from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"Downloaded book embedding for {data.get('book_title', 'Unknown')}")
            
            return data
            
        except ClientError as e:
            print(f"Error downloading {s3_key}: {e}")
            return None
    
    def create_book_index_mapping(self, index_name: str = "book-recommendations") -> bool:
        """Create OpenSearch index with vector mapping for books."""
        mapping = {
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
                    "genre": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "gutenberg_id": {
                        "type": "keyword"
                    },
                    "book_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 16
                            }
                        }
                    },
                    "model_id": {
                        "type": "keyword"
                    },
                    "uploaded_at": {
                        "type": "date"
                    }
                }
            },
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            }
        }
        
        try:
            url = f"{self.opensearch_endpoint}/{index_name}"
            response = self.session.put(url, json=mapping)
            
            if response.status_code in [200, 201]:
                print(f"Successfully created index: {index_name}")
                return True
            else:
                print(f"Error creating index: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    def index_exists(self, index_name: str = "book-recommendations") -> bool:
        """Check if index exists."""
        try:
            url = f"{self.opensearch_endpoint}/{index_name}"
            response = self.session.head(url)
            return response.status_code == 200
        except:
            return False
    
    def index_book_embedding(self, book_data: Dict, index_name: str = "book-recommendations") -> bool:
        """Index a single book embedding into OpenSearch."""
        if not book_data or 'embedding' not in book_data:
            print("No book data to index")
            return False
        
        book_title = book_data.get('book_title', 'Unknown')
        
        # Prepare document for indexing
        document = {
            "book_title": book_data.get('book_title'),
            "author": book_data.get('author'),
            "genre": book_data.get('genre'),
            "description": book_data.get('description'),
            "gutenberg_id": book_data.get('gutenberg_id'),
            "book_vector": book_data.get('embedding'),
            "model_id": book_data.get('model_id'),
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        # Create document ID
        doc_id = f"{book_title}-{book_data.get('gutenberg_id', 'unknown')}"
        
        try:
            url = f"{self.opensearch_endpoint}/{index_name}/_doc/{doc_id}"
            response = self.session.put(url, json=document)
            
            if response.status_code in [200, 201]:
                print(f"Successfully indexed book: {book_title}")
                return True
            else:
                print(f"Error indexing {book_title}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error indexing {book_title}: {e}")
            return False
    
    def search_similar_books(self, query_text: str, embedding: List[float], k: int = 5, index_name: str = "book-recommendations"):
        """Search for similar books using vector similarity."""
        search_body = {
            "size": k,
            "query": {
                "knn": {
                    "book_vector": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": ["book_title", "author", "genre", "description", "gutenberg_id"]
        }
        
        try:
            url = f"{self.opensearch_endpoint}/{index_name}/_search"
            response = self.session.post(url, json=search_body)
            
            if response.status_code == 200:
                results = response.json()
                hits = results.get('hits', {}).get('hits', [])
                
                print(f"\nSearch results for: '{query_text}'")
                print("=" * 50)
                
                for i, hit in enumerate(hits, 1):
                    source = hit['_source']
                    print(f"\n{i}. Score: {hit['_score']:.4f}")
                    print(f"   Title: {source.get('book_title', 'Unknown')}")
                    print(f"   Author: {source.get('author', 'Unknown')}")
                    print(f"   Genre: {source.get('genre', 'Unknown')}")
                    print(f"   Description: {source.get('description', 'No description')[:100]}...")
                
                return hits
            else:
                print(f"Error searching: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def load_all_book_embeddings(self, index_name: str = "book-recommendations"):
        """Load all book embeddings into OpenSearch."""
        print(f"Starting to load book embeddings into OpenSearch")
        print(f"Index: {index_name}")
        print(f"Endpoint: {self.opensearch_endpoint}")
        print("=" * 60)
        
        # Check if index exists, create if not
        if not self.index_exists(index_name):
            print(f"Index {index_name} does not exist. Creating...")
            if not self.create_book_index_mapping(index_name):
                print("Failed to create index. Exiting.")
                return
        else:
            print(f"Index {index_name} already exists.")
        
        # List all book embeddings
        embedding_keys = self.list_book_embeddings_in_s3()
        if not embedding_keys:
            print("No book embeddings found to load")
            return
        
        print(f"Found {len(embedding_keys)} book embeddings to load")
        
        # Load each book embedding
        successful_books = 0
        for embedding_key in embedding_keys:
            book_data = self.download_book_embedding_from_s3(embedding_key)
            if book_data and self.index_book_embedding(book_data, index_name):
                successful_books += 1
            
            # Small delay between operations
            time.sleep(0.5)
        
        print(f"\nLoading complete! Successfully loaded {successful_books}/{len(embedding_keys)} books")
        
        # Test search functionality
        print("\nTesting search functionality...")
        test_query = "gothic horror with female protagonist"
        print(f"Test query: '{test_query}'")
        
        # For testing, we'll use a simple embedding (in practice, you'd generate this from the query)
        # This is just a placeholder - in the real system, you'd generate the embedding from the query
        test_embedding = [0.1] * 1536  # Placeholder embedding
        
        self.search_similar_books(test_query, test_embedding, k=3, index_name=index_name)

def main():
    """Main function to run the book embedding loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load book embeddings into OpenSearch')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint URL')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--index', default='book-recommendations', help='OpenSearch index name')
    
    args = parser.parse_args()
    
    loader = BookOpenSearchLoader(args.bucket, args.opensearch_endpoint, args.profile)
    loader.load_all_book_embeddings(args.index)

if __name__ == "__main__":
    main() 