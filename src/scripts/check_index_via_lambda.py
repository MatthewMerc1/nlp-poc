#!/usr/bin/env python3
"""
Script to check OpenSearch index status via Lambda function
This avoids direct connection issues by using the Lambda function that's already in the VPC
"""

import boto3
import json
import argparse

def check_index_via_lambda(aws_profile=None):
    """Check OpenSearch index status via Lambda function."""
    try:
        # Initialize AWS clients
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            lambda_client = session.client('lambda')
        else:
            lambda_client = boto3.client('lambda')
        
        print("🔍 Checking OpenSearch index via Lambda...")
        
        # Prepare the payload for Lambda
        payload = {
            "action": "check_index"
        }
        
        # Invoke Lambda function
        response = lambda_client.invoke(
            FunctionName='nlp-poc-semantic-search',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        if response['StatusCode'] == 200:
            result = json.loads(response_payload['body'])
            
            print(f"✅ Index Status: {result['message']}")
            print(f"📊 Document Count: {result['document_count']}")
            
            if result['index_exists'] and 'index_stats' in result:
                stats = result['index_stats']
                print(f"📈 Index Statistics:")
                print(f"   - Total Documents: {stats['total_docs']}")
                print(f"   - Total Size: {stats['total_size']:,} bytes")
                print(f"   - Primary Documents: {stats['primaries_docs']}")
                print(f"   - Primary Size: {stats['primaries_size']:,} bytes")
            
            return result
        else:
            print(f"❌ Error: {response_payload}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking index: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Check OpenSearch index via Lambda')
    parser.add_argument('--profile', default='caylent-dev-test', help='AWS profile to use')
    
    args = parser.parse_args()
    
    result = check_index_via_lambda(args.profile)
    
    if result:
        print("\n🎉 Index check completed successfully!")
    else:
        print("\n💥 Index check failed!")
        exit(1)

if __name__ == "__main__":
    main() 