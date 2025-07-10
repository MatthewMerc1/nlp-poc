#!/usr/bin/env python3
"""
Test script for the semantic search API
"""

import requests
import json
import sys
import subprocess

def get_api_url():
    try:
        url = subprocess.check_output(
            ["terraform", "output", "-raw", "api_gateway_url"],
            cwd="infrastructure/terraform/environments/dev"
        ).decode("utf-8").strip()
        return url
    except Exception as e:
        print("Could not get API Gateway URL from Terraform:", e)
        return None

def get_api_key():
    try:
        api_key = subprocess.check_output(
            ["terraform", "output", "-raw", "api_key"],
            cwd="infrastructure/terraform/environments/dev"
        ).decode("utf-8").strip()
        return api_key
    except Exception as e:
        print("Could not get API key from Terraform:", e)
        return None

def test_semantic_search(api_url, api_key, query, size=5):
    """
    Test the semantic search API
    
    Args:
        api_url (str): The API Gateway URL
        api_key (str): The API key for authentication
        query (str): The search query
        size (int): Number of results to return
    """
    
    payload = {
        "query": query,
        "size": size
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    try:
        print(f"Searching for: '{query}'")
        print(f"API URL: {api_url}")
        print(f"API Key: {api_key[:8]}...{api_key[-4:]}")  # Show first 8 and last 4 chars
        print("-" * 50)
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Total results: {data['total_results']}")
            print("\nResults:")
            
            for i, result in enumerate(data['results'], 1):
                print(f"\n{i}. Score: {result['score']:.4f}")
                print(f"   Title: {result['title']}")
                print(f"   Author: {result['author']}")
                print(f"   Book ID: {result['book_id']}")
                print(f"   Chapter: {result['chapter']}")
                print(f"   Content: {result['content'][:200]}...")
                
        elif response.status_code == 403:
            print("Error: 403 Forbidden - Check your API key")
            print(f"Response: {response.text}")
        elif response.status_code == 429:
            print("Error: 429 Too Many Requests - Rate limit exceeded")
            print(f"Response: {response.text}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {str(e)}")

def main():
    # Get API URL and key from Terraform
    api_url = get_api_url()
    api_key = get_api_key()
    
    if not api_url or not api_key:
        print("Could not get API URL or API key from Terraform")
        print("Make sure you're in the correct directory and Terraform is deployed")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        query = input("Enter your query: ")
        size = 5
    else:
        query = sys.argv[1]
        size = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    test_semantic_search(api_url, api_key, query, size)

if __name__ == "__main__":
    main() 