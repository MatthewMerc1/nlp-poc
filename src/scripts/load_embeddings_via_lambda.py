#!/usr/bin/env python3
"""
Script to load embeddings into OpenSearch via Lambda function
This avoids direct connection issues by using the Lambda function that's already in the VPC
"""

import boto3
import json
import time
from typing import List, Dict

class LambdaEmbeddingLoader:
    def __init__(self, aws_profile: str = None):
        """Initialize the loader with AWS credentials."""
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.lambda_client = session.client('lambda')
            self.s3_client = session.client('s3')
        else:
            self.lambda_client = boto3.client('lambda')
            self.s3_client = boto3.client('s3')
    
    def list_embedding_files(self, bucket_name: str) -> List[str]:
        """List all embedding files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='embeddings/'
            )
            
            embedding_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.json'):
                        embedding_files.append(obj['Key'])
            
            return embedding_files
        except Exception as e:
            print(f"Error listing embedding files: {e}")
            return []
    
    def load_embeddings_from_s3(self, bucket_name: str, embedding_key: str) -> Dict:
        """Load embeddings from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=embedding_key
            )
            
            embeddings_data = json.loads(response['Body'].read().decode('utf-8'))
            return embeddings_data
        except Exception as e:
            print(f"Error loading embeddings from S3: {e}")
            return None
    
    def invoke_lambda_to_load_embeddings(self, embeddings_data: Dict) -> bool:
        """Invoke Lambda function to load embeddings into OpenSearch."""
        try:
            book_title = embeddings_data.get('book_title', 'Unknown')
            author = embeddings_data.get('author', 'Unknown')
            embeddings = embeddings_data.get('embeddings', [])
            
            print(f"Processing {len(embeddings)} embeddings for: {book_title}")
            
            # Split embeddings into chunks to avoid Lambda payload size limits
            # Lambda has a 6MB payload limit, so we'll use 5MB to be safe
            MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB
            CHUNK_SIZE = 50  # Start with 50 embeddings per chunk
            
            successful_chunks = 0
            total_chunks = 0
            
            for i in range(0, len(embeddings), CHUNK_SIZE):
                chunk = embeddings[i:i + CHUNK_SIZE]
                chunk_data = {
                    "book_title": book_title,
                    "author": author,
                    "embeddings": chunk
                }
                
                # Check payload size
                payload = {
                    "action": "load_embeddings",
                    "embeddings_data": chunk_data
                }
                
                payload_size = len(json.dumps(payload).encode('utf-8'))
                
                if payload_size > MAX_PAYLOAD_SIZE:
                    print(f"Warning: Payload size ({payload_size} bytes) exceeds limit. Reducing chunk size.")
                    # Reduce chunk size and retry
                    CHUNK_SIZE = max(1, CHUNK_SIZE // 2)
                    chunk = embeddings[i:i + CHUNK_SIZE]
                    chunk_data = {
                        "book_title": book_title,
                        "author": author,
                        "embeddings": chunk
                    }
                    payload = {
                        "action": "load_embeddings",
                        "embeddings_data": chunk_data
                    }
                
                total_chunks += 1
                print(f"  Loading chunk {total_chunks} ({len(chunk)} embeddings)...")
                
                # Invoke Lambda function
                response = self.lambda_client.invoke(
                    FunctionName='nlp-poc-semantic-search',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                # Parse response
                response_payload = json.loads(response['Payload'].read().decode('utf-8'))
                
                if response['StatusCode'] == 200:
                    successful_chunks += 1
                else:
                    print(f"Error loading chunk {total_chunks}: {response_payload}")
                    return False
            
            if successful_chunks == total_chunks:
                print(f"Successfully loaded all {total_chunks} chunks for: {book_title}")
                return True
            else:
                print(f"Failed to load {total_chunks - successful_chunks} out of {total_chunks} chunks for: {book_title}")
                return False
                
        except Exception as e:
            print(f"Error invoking Lambda: {e}")
            return False
    
    def load_all_embeddings(self, bucket_name: str):
        """Load all embeddings from S3 into OpenSearch via Lambda."""
        print(f"Loading embeddings from bucket: {bucket_name}")
        print("=" * 60)
        
        # List all embedding files
        embedding_files = self.list_embedding_files(bucket_name)
        if not embedding_files:
            print("No embedding files found in S3")
            return
        
        print(f"Found {len(embedding_files)} embedding files")
        
        # Load each embedding file
        successful_loads = 0
        for embedding_key in embedding_files:
            print(f"\nProcessing: {embedding_key}")
            
            # Load embeddings from S3
            embeddings_data = self.load_embeddings_from_s3(bucket_name, embedding_key)
            if not embeddings_data:
                continue
            
            # Load into OpenSearch via Lambda
            if self.invoke_lambda_to_load_embeddings(embeddings_data):
                successful_loads += 1
            
            # Rate limiting
            time.sleep(1)
        
        print(f"\nLoad complete! Successfully loaded {successful_loads}/{len(embedding_files)} embedding files")

def main():
    """Main function to run the embedding loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load embeddings into OpenSearch via Lambda')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    
    args = parser.parse_args()
    
    loader = LambdaEmbeddingLoader(args.profile)
    loader.load_all_embeddings(args.bucket)

if __name__ == "__main__":
    main() 