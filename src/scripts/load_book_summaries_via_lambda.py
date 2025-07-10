#!/usr/bin/env python3
"""
Script to load book summaries into OpenSearch via Lambda function
This avoids direct connection issues by using the Lambda function that's already in the VPC
"""

import boto3
import json
import time
from typing import List, Dict

class LambdaBookSummaryLoader:
    def __init__(self, aws_profile: str = None):
        """Initialize the loader with AWS credentials."""
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.lambda_client = session.client('lambda')
            self.s3_client = session.client('s3')
        else:
            self.lambda_client = boto3.client('lambda')
            self.s3_client = boto3.client('s3')
    
    def list_book_summary_files(self, bucket_name: str) -> List[str]:
        """List all book summary files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='book-summaries/'
            )
            
            summary_files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.json'):
                        summary_files.append(obj['Key'])
            
            return summary_files
        except Exception as e:
            print(f"Error listing book summary files: {e}")
            return []
    
    def load_book_summary_from_s3(self, bucket_name: str, summary_key: str) -> Dict:
        """Load book summary from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=summary_key
            )
            
            summary_data = json.loads(response['Body'].read().decode('utf-8'))
            return summary_data
        except Exception as e:
            print(f"Error loading book summary from S3: {e}")
            return None
    
    def invoke_lambda_to_load_book_summary(self, summary_data: Dict) -> bool:
        """Invoke Lambda function to load book summary into OpenSearch."""
        try:
            book_title = summary_data.get('book_title', 'Unknown')
            author = summary_data.get('author', 'Unknown')
            summary = summary_data.get('book_summary', '')
            
            print(f"Processing book summary for: {book_title}")
            
            # Prepare payload for Lambda
            payload = {
                "action": "load_book_summary",
                "book_summary_data": summary_data
            }
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName='nlp-poc-semantic-search',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            
            if response['StatusCode'] == 200:
                print(f"Successfully loaded book summary for: {book_title}")
                return True
            else:
                print(f"Error loading book summary for {book_title}: {response_payload}")
                return False
                
        except Exception as e:
            print(f"Error invoking Lambda: {e}")
            return False
    
    def invoke_lambda_to_purge_index(self):
        """Invoke Lambda function to purge the OpenSearch index."""
        try:
            print("Purging OpenSearch index via Lambda...")
            payload = {"action": "purge_index"}
            response = self.lambda_client.invoke(
                FunctionName='nlp-poc-semantic-search',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            print(f"Purge response: {response_payload}")
            return response_payload
        except Exception as e:
            print(f"Error invoking Lambda to purge index: {e}")
            return None
    
    def load_all_book_summaries(self, bucket_name: str):
        """Load all book summaries from S3 into OpenSearch via Lambda."""
        print(f"Loading book summaries from bucket: {bucket_name}")
        print("=" * 60)
        
        # List all book summary files
        summary_files = self.list_book_summary_files(bucket_name)
        if not summary_files:
            print("No book summary files found in S3")
            return
        
        print(f"Found {len(summary_files)} book summary files")
        
        # Load each book summary file
        successful_loads = 0
        for summary_key in summary_files:
            print(f"\nProcessing: {summary_key}")
            
            # Load book summary from S3
            summary_data = self.load_book_summary_from_s3(bucket_name, summary_key)
            if not summary_data:
                continue
            
            # Load into OpenSearch via Lambda
            if self.invoke_lambda_to_load_book_summary(summary_data):
                successful_loads += 1
            
            # Rate limiting
            time.sleep(1)
        
        print(f"\nLoad complete! Successfully loaded {successful_loads}/{len(summary_files)} book summary files")

def main():
    """Main function to run the book summary loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load book summaries into OpenSearch via Lambda')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--purge-index', action='store_true', help='Purge the OpenSearch index before loading')
    
    args = parser.parse_args()
    
    loader = LambdaBookSummaryLoader(args.profile)
    if args.purge_index:
        loader.invoke_lambda_to_purge_index()
        return
    loader.load_all_book_summaries(args.bucket)

if __name__ == "__main__":
    main() 