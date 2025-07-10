#!/usr/bin/env python3
"""
Test script for the book-level semantic search API
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

def test_book_search(api_url, api_key, query, size=5):
    """
    Test the book-level semantic search API
    
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
        print(f"🔍 Searching for books matching: '{query}'")
        print(f"🌐 API URL: {api_url}")
        print(f"🔑 API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
        print("=" * 60)
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Query: {data['query']}")
            print(f"📈 Total results: {data['total_results']}")
            print("\n📚 Book Recommendations:")
            
            for i, result in enumerate(data['results'], 1):
                print(f"\n{i}. 📖 {result['book_title']}")
                print(f"   👤 Author: {result['author']}")
                print(f"   ⭐ Score: {result['score']:.4f}")
                print(f"   📝 Summary: {result['book_summary'][:200]}...")
                print("-" * 50)
                
        elif response.status_code == 403:
            print("❌ Error: 403 Forbidden - Check your API key")
            print(f"Response: {response.text}")
        elif response.status_code == 429:
            print("❌ Error: 429 Too Many Requests - Rate limit exceeded")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")

def main():
    """Main function to run the book search test."""
    if len(sys.argv) < 2:
        print("Usage: python test_book_search.py <query> [size]")
        print("Example: python test_book_search.py 'What is the meaning of life?' 5")
        sys.exit(1)
    
    query = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Get API configuration
    api_url = get_api_url()
    api_key = get_api_key()
    
    if not api_url or not api_key:
        print("❌ Could not get API configuration from Terraform")
        print("Make sure infrastructure is deployed and you're in the correct directory")
        sys.exit(1)
    
    # Test the book search
    test_book_search(api_url, api_key, query, size)

if __name__ == "__main__":
    main() 