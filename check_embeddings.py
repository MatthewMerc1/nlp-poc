#!/usr/bin/env python3
"""
Script to check and display information about generated embeddings.
"""

import boto3
import json
from typing import List, Dict
from botocore.exceptions import ClientError

class EmbeddingChecker:
    def __init__(self, bucket_name: str, aws_profile: str = None):
        """Initialize the embedding checker."""
        self.bucket_name = bucket_name
        
        # Initialize S3 client
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
    
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
    
    def get_embedding_info(self, s3_key: str) -> Dict:
        """Get information about a specific embedding file."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                'book_title': data.get('book_title', 'Unknown'),
                'model_id': data.get('model_id', 'Unknown'),
                'total_chunks': data.get('total_chunks', 0),
                'generated_at': data.get('generated_at', 'Unknown'),
                'embedding_dimensions': len(data.get('embeddings', [{}])[0].get('embedding', [])) if data.get('embeddings') else 0
            }
            
        except ClientError as e:
            print(f"Error reading {s3_key}: {e}")
            return {}
    
    def display_embeddings_summary(self):
        """Display a summary of all embeddings."""
        print(f"Embeddings Summary for bucket: {self.bucket_name}")
        print("=" * 60)
        
        embedding_keys = self.list_embeddings_in_s3()
        
        if not embedding_keys:
            print("No embeddings found. Run generate_embeddings.sh first.")
            return
        
        print(f"Found {len(embedding_keys)} embedding files:")
        print()
        
        total_chunks = 0
        for key in embedding_keys:
            info = self.get_embedding_info(key)
            if info:
                print(f"📚 {info['book_title']}")
                print(f"   Model: {info['model_id']}")
                print(f"   Chunks: {info['total_chunks']}")
                print(f"   Dimensions: {info['embedding_dimensions']}")
                print(f"   Generated: {info['generated_at']}")
                print(f"   File: {key}")
                print()
                total_chunks += info['total_chunks']
        
        print(f"Total chunks across all books: {total_chunks}")
    
    def show_sample_embedding(self, book_title: str = None):
        """Show a sample embedding for a specific book."""
        embedding_keys = self.list_embeddings_in_s3()
        
        if not embedding_keys:
            print("No embeddings found.")
            return
        
        # Find the book to show
        target_key = None
        if book_title:
            for key in embedding_keys:
                if book_title.lower() in key.lower():
                    target_key = key
                    break
        else:
            target_key = embedding_keys[0]  # Show first book
        
        if not target_key:
            print(f"Book '{book_title}' not found in embeddings.")
            return
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=target_key
            )
            
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            print(f"Sample embedding for: {data['book_title']}")
            print("=" * 50)
            print(f"Model: {data['model_id']}")
            print(f"Total chunks: {data['total_chunks']}")
            print(f"Generated: {data['generated_at']}")
            print()
            
            if data['embeddings']:
                sample = data['embeddings'][0]
                print("Sample chunk:")
                print(f"Index: {sample['chunk_index']}")
                print(f"Text preview: {sample['text'][:300]}...")
                print(f"Embedding dimensions: {len(sample['embedding'])}")
                print(f"First 10 values: {sample['embedding'][:10]}")
            
        except ClientError as e:
            print(f"Error reading embedding: {e}")

def main():
    """Main function to run the embedding checker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check and display information about generated embeddings')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--book', help='Show sample embedding for specific book')
    
    args = parser.parse_args()
    
    checker = EmbeddingChecker(args.bucket, args.profile)
    
    if args.book:
        checker.show_sample_embedding(args.book)
    else:
        checker.display_embeddings_summary()

if __name__ == "__main__":
    main() 