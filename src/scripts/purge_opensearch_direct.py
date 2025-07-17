#!/usr/bin/env python3
"""
Script to purge the current OpenSearch index directly
"""

import argparse
import requests
import json
import subprocess
import sys
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_opensearch_endpoint():
    """Get OpenSearch endpoint from Terraform"""
    try:
        endpoint = subprocess.check_output(
            ["terraform", "output", "-raw", "opensearch_serverless_collection_endpoint"],
            cwd="infrastructure/terraform/environments/dev"
        ).decode("utf-8").strip()
        return endpoint
    except Exception as e:
        print(f"Could not get OpenSearch endpoint from Terraform: {e}")
        return None

def purge_index_direct(opensearch_endpoint, aws_profile=None):
    """Purge OpenSearch index directly"""
    try:
        print(f"🔍 Purging OpenSearch index at: {opensearch_endpoint}")
        
        # Construct the URL for deleting the index
        url = f"https://{opensearch_endpoint}/book-summaries"
        
        print(f"🗑️  Deleting index: {url}")
        
        # Make the DELETE request
        response = requests.delete(url, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Successfully purged book-summaries index")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            return True
        elif response.status_code == 404:
            print("ℹ️  Index 'book-summaries' does not exist (already deleted or never created)")
            return True
        else:
            print(f"❌ Failed to purge index. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error purging index: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Purge OpenSearch index directly')
    parser.add_argument('--opensearch-endpoint', help='OpenSearch endpoint (e.g., localhost:8443)')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile to use')
    
    args = parser.parse_args()
    
    # Get OpenSearch endpoint
    opensearch_endpoint = args.opensearch_endpoint
    if not opensearch_endpoint:
        opensearch_endpoint = get_opensearch_endpoint()
        if not opensearch_endpoint:
            print("❌ Could not get OpenSearch endpoint")
            sys.exit(1)
    
    # Purge the index
    success = purge_index_direct(opensearch_endpoint, args.profile)
    
    if success:
        print("\n🎉 Index purge completed successfully!")
        print("You can now run the pipeline to populate with new summaries.")
    else:
        print("\n💥 Index purge failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 