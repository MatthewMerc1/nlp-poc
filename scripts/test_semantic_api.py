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
            cwd="terraform"
        ).decode("utf-8").strip()
        return url
    except Exception as e:
        print("Could not get API Gateway URL from Terraform:", e)
        return None

def test_semantic_search(api_url, query, size=5):
    """
    Test the semantic search API
    
    Args:
        api_url (str): The API Gateway URL
        query (str): The search query
        size (int): Number of results to return
    """
    
    payload = {
        "query": query,
        "size": size
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Searching for: '{query}'")
        print(f"API URL: {api_url}")
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
                
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error making request: {str(e)}")

def main():
    if len(sys.argv) < 2:
        api_url = get_api_url()
        if not api_url:
            print("Usage: python test_semantic_api.py <api_url> <query> [size]")
            sys.exit(1)
        query = input("Enter your query: ")
        size = 5
    else:
        api_url = sys.argv[1]
        query = sys.argv[2] if len(sys.argv) > 2 else input("Enter your query: ")
        size = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    test_semantic_search(api_url, query, size)

if __name__ == "__main__":
    main() 