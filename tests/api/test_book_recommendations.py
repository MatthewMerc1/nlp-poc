#!/usr/bin/env python3
"""
Test script for the semantic book recommendation API.
"""

import requests
import json
import subprocess
import sys
import os

def get_api_url():
    try:
        api_url = subprocess.check_output(
            ["terraform", "output", "-raw", "api_gateway_url"],
            cwd="../../infrastructure/terraform/environments/dev"
        ).decode("utf-8").strip()
        return api_url
    except Exception as e:
        print("Could not get API URL from Terraform:", e)
        return None

def get_api_key():
    try:
        api_key = subprocess.check_output(
            ["terraform", "output", "-raw", "api_key"],
            cwd="../../infrastructure/terraform/environments/dev"
        ).decode("utf-8").strip()
        return api_key
    except Exception as e:
        print("Could not get API key from Terraform:", e)
        return None

def test_book_recommendations(api_url, api_key, query, size=5):
    """
    Test the book recommendation API
    
    Args:
        api_url (str): The API Gateway URL
        api_key (str): The API key for authentication
        query (str): The search query
        size (int): Number of recommendations to return
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
        print(f"Searching for book recommendations: '{query}'")
        print(f"API URL: {api_url}")
        print(f"API Key: {api_key[:8]}...{api_key[-4:]}")  # Show first 8 and last 4 chars
        print("-" * 50)
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Total recommendations: {data['total_results']}")
            print("\nBook Recommendations:")
            
            for i, recommendation in enumerate(data['recommendations'], 1):
                print(f"\n{i}. Score: {recommendation['score']:.4f}")
                print(f"   Title: {recommendation['title']}")
                print(f"   Author: {recommendation['author']}")
                print(f"   Genre: {recommendation['genre']}")
                print(f"   Description: {recommendation['description'][:150]}...")
                
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
        print(f"Error making request: {e}")

def main():
    """Main function to test the API."""
    if len(sys.argv) < 2:
        print("Usage: python test_book_recommendations.py <query> [size]")
        print("Example: python test_book_recommendations.py 'gothic horror with female protagonist' 5")
        sys.exit(1)
    
    query = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Get API details
    api_url = get_api_url()
    api_key = get_api_key()
    
    if not api_url or not api_key:
        print("Could not get API details. Make sure Terraform has been applied.")
        sys.exit(1)
    
    # Test the API
    test_book_recommendations(api_url, api_key, query, size)

if __name__ == "__main__":
    main() 