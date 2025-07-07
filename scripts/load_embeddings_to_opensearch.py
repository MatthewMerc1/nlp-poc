#!/usr/bin/env python3
"""
Script to load embeddings from S3 into OpenSearch for vector search.
"""

import boto3
import json
import requests
from typing import List, Dict
import time
from botocore.exceptions import ClientError
from requests.auth import HTTPBasicAuth
import base64

class OpenSearchLoader:
    def __init__(self, bucket_name: str, opensearch_endpoint: str, aws_profile: str = None):
        """Initialize the OpenSearch loader."""
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
    
    def list_embeddings_in_s3(self) -> List[str]:
        """List all embedding files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='embeddings/'
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.json')]
            else:
                print("No embeddings found in S3 bucket")
                return []
                
        except ClientError as e:
            print(f"Error listing embeddings: {e}")
            return []
    
    def download_embeddings_from_s3(self, s3_key: str) -> Dict:
        """Download embeddings from S3."""
        try:
            print(f"Downloading {s3_key} from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"Downloaded embeddings for {data.get('book_title', 'Unknown')}")
            
            return data
            
        except ClientError as e:
            print(f"Error downloading {s3_key}: {e}")
            return None
    
    def create_index_mapping(self, index_name: str = "book-embeddings") -> bool:
        """Create OpenSearch index with vector mapping."""
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
                    "chunk_index": {
                        "type": "integer"
                    },
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "text_vector": {
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
    
    def index_exists(self, index_name: str = "book-embeddings") -> bool:
        """Check if index exists."""
        try:
            url = f"{self.opensearch_endpoint}/{index_name}"
            response = self.session.head(url)
            return response.status_code == 200
        except:
            return False
    
    def bulk_index_embeddings(self, embeddings_data: Dict, index_name: str = "book-embeddings") -> int:
        """Bulk index embeddings into OpenSearch."""
        if not embeddings_data or 'embeddings' not in embeddings_data:
            print("No embeddings data to index")
            return 0
        
        book_title = embeddings_data.get('book_title', 'Unknown')
        model_id = embeddings_data.get('model_id', 'Unknown')
        
        # Extract author from book title if possible
        author = "Unknown"
        if '-' in book_title:
            parts = book_title.split('-')
            if len(parts) > 1:
                author = parts[-1].strip()
        
        print(f"Indexing {len(embeddings_data['embeddings'])} embeddings for {book_title}")
        
        # Prepare bulk indexing data
        bulk_data = []
        for embedding_doc in embeddings_data['embeddings']:
            # Index action
            bulk_data.append({
                "index": {
                    "_index": index_name,
                    "_id": f"{book_title}-{embedding_doc['chunk_index']}"
                }
            })
            
            # Document data
            bulk_data.append({
                "book_title": book_title,
                "author": author,
                "chunk_index": embedding_doc['chunk_index'],
                "text": embedding_doc['text'],
                "text_vector": embedding_doc['embedding'],
                "model_id": model_id,
                "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
        
        # Perform bulk indexing
        try:
            url = f"{self.opensearch_endpoint}/_bulk"
            payload = "\n".join([json.dumps(doc) for doc in bulk_data]) + "\n"
            
            response = self.session.post(url, data=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errors', True):
                    print(f"Some errors occurred during bulk indexing: {result}")
                    return 0
                else:
                    indexed_count = len(result.get('items', []))
                    print(f"Successfully indexed {indexed_count} documents")
                    return indexed_count
            else:
                print(f"Error during bulk indexing: {response.status_code} - {response.text}")
                return 0
                
        except Exception as e:
            print(f"Error during bulk indexing: {e}")
            return 0
    
    def search_similar_text(self, query_text: str, embedding: List[float], k: int = 5, index_name: str = "book-embeddings"):
        """Search for similar text using vector similarity."""
        search_body = {
            "size": k,
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": embedding,
                        "k": k
                    }
                }
            },
            "_source": ["book_title", "author", "chunk_index", "text"]
        }
        
        try:
            url = f"{self.opensearch_endpoint}/{index_name}/_search"
            response = self.session.post(url, json=search_body)
            
            if response.status_code == 200:
                results = response.json()
                hits = results.get('hits', {}).get('hits', [])
                
                print(f"\nSearch results for: '{query_text[:100]}...'")
                print("=" * 60)
                
                for i, hit in enumerate(hits):
                    source = hit['_source']
                    score = hit['_score']
                    print(f"{i+1}. Score: {score:.4f}")
                    print(f"   Book: {source['book_title']}")
                    print(f"   Author: {source['author']}")
                    print(f"   Chunk: {source['chunk_index']}")
                    print(f"   Text: {source['text'][:200]}...")
                    print()
                
                return hits
            else:
                print(f"Error searching: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def load_all_embeddings(self, index_name: str = "book-embeddings"):
        """Load all embeddings from S3 into OpenSearch."""
        print(f"Loading embeddings into OpenSearch: {self.opensearch_endpoint}")
        print("=" * 60)
        
        # Create index if it doesn't exist
        if not self.index_exists(index_name):
            print("Creating index...")
            if not self.create_index_mapping(index_name):
                print("Failed to create index")
                return
        
        # List all embedding files
        embedding_keys = self.list_embeddings_in_s3()
        if not embedding_keys:
            print("No embeddings found to load")
            return
        
        print(f"Found {len(embedding_keys)} embedding files to load")
        
        # Load each embedding file
        total_indexed = 0
        for s3_key in embedding_keys:
            print(f"\nProcessing: {s3_key}")
            
            # Download embeddings
            embeddings_data = self.download_embeddings_from_s3(s3_key)
            if not embeddings_data:
                continue
            
            # Index embeddings
            indexed_count = self.bulk_index_embeddings(embeddings_data, index_name)
            total_indexed += indexed_count
            
            # Small delay between files
            time.sleep(1)
        
        print(f"\nLoad complete! Total documents indexed: {total_indexed}")
        
        # Refresh index
        try:
            url = f"{self.opensearch_endpoint}/{index_name}/_refresh"
            self.session.post(url)
            print("Index refreshed")
        except Exception as e:
            print(f"Error refreshing index: {e}")

def main():
    """Main function to run the OpenSearch loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load embeddings into OpenSearch')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch domain endpoint')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--index', default='book-embeddings', help='OpenSearch index name')
    
    args = parser.parse_args()
    
    loader = OpenSearchLoader(args.bucket, args.opensearch_endpoint, args.profile)
    loader.load_all_embeddings(args.index)

if __name__ == "__main__":
    main() 