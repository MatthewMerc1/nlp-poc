#!/usr/bin/env python3
"""
Enhanced test script for the semantic search API with multiple strategies
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

def test_enhanced_semantic_search(api_url, api_key, query, search_strategy="multi", size=5):
    """
    Test the enhanced semantic search API with multiple strategies
    
    Args:
        api_url (str): The API Gateway URL
        api_key (str): The API key for authentication
        query (str): The search query
        search_strategy (str): Search strategy ('multi', 'plot', 'thematic', 'character', 'combined')
        size (int): Number of results to return
    """
    
    payload = {
        "query": query,
        "search_strategy": search_strategy,
        "size": size
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    try:
        print(f"Enhanced Search for: '{query}'")
        print(f"Strategy: {search_strategy}")
        print(f"API URL: {api_url}")
        print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
        print("-" * 60)
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Strategy: {data['search_strategy']}")
            print(f"Total results: {data['total_results']}")
            print("\nResults:")
            
            for i, result in enumerate(data['results'], 1):
                print(f"\n{i}. Score: {result['score']:.4f}")
                if 'strategy' in result:
                    print(f"   Strategy: {result['strategy']}")
                print(f"   Title: {result['book_title']}")
                print(f"   Author: {result['author']}")
                
                # Show different summary types based on what's available
                if result.get('plot_summary'):
                    print(f"   Plot Summary: {result['plot_summary'][:200]}...")
                elif result.get('combined_summary'):
                    print(f"   Summary: {result['combined_summary'][:200]}...")
                elif result.get('book_summary'):
                    print(f"   Summary: {result['book_summary'][:200]}...")
                
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

def compare_search_strategies(api_url, api_key, query, size=3):
    """Compare different search strategies for the same query"""
    print(f"\n{'='*80}")
    print(f"COMPARING SEARCH STRATEGIES FOR: '{query}'")
    print(f"{'='*80}")
    
    strategies = ["multi", "plot", "thematic", "character", "combined"]
    
    for strategy in strategies:
        print(f"\n{'='*40}")
        print(f"STRATEGY: {strategy.upper()}")
        print(f"{'='*40}")
        test_enhanced_semantic_search(api_url, api_key, query, strategy, size)

def test_accuracy_improvements(api_url, api_key):
    """Test specific queries to demonstrate accuracy improvements"""
    test_queries = [
        "wonderland",
        "detective mystery investigation",
        "love romance marriage",
        "monster creation science",
        "time travel future",
        "vampire supernatural horror"
    ]
    
    print(f"\n{'='*80}")
    print("TESTING ACCURACY IMPROVEMENTS")
    print(f"{'='*80}")
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: '{query}'")
        print(f"{'='*60}")
        test_enhanced_semantic_search(api_url, api_key, query, "multi", 3)

def main():
    # Get API URL and key from Terraform
    api_url = get_api_url()
    api_key = get_api_key()
    
    if not api_url or not api_key:
        print("Could not get API URL or API key from Terraform")
        print("Make sure you're in the correct directory and Terraform is deployed")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_enhanced_api.py <query> [strategy] [size]")
        print("  python test_enhanced_api.py --compare <query>")
        print("  python test_enhanced_api.py --accuracy")
        print("\nStrategies: multi, plot, thematic, character, combined")
        print("\nExamples:")
        print("  python test_enhanced_api.py 'wonderland'")
        print("  python test_enhanced_api.py 'detective mystery' plot 3")
        print("  python test_enhanced_api.py --compare 'love story'")
        print("  python test_enhanced_api.py --accuracy")
        sys.exit(1)
    
    if sys.argv[1] == "--compare":
        if len(sys.argv) < 3:
            print("Please provide a query for comparison")
            sys.exit(1)
        query = sys.argv[2]
        compare_search_strategies(api_url, api_key, query)
    elif sys.argv[1] == "--accuracy":
        test_accuracy_improvements(api_url, api_key)
    else:
        query = sys.argv[1]
        search_strategy = sys.argv[2] if len(sys.argv) > 2 else "multi"
        size = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        test_enhanced_semantic_search(api_url, api_key, query, search_strategy, size)

if __name__ == "__main__":
    main() 