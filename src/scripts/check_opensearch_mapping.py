#!/usr/bin/env python3
"""
Check and print the mapping for a given OpenSearch index (Serverless-compatible, AWS4Auth)
"""
import argparse
import json
import logging
import sys
import requests
import boto3
from requests_aws4auth import AWS4Auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_aws_auth(profile_name, region):
    session = boto3.Session(profile_name=profile_name)
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        session.region_name or region,
        'aoss',
        session_token=credentials.token
    )
    return awsauth

def main():
    parser = argparse.ArgumentParser(description="Check OpenSearch index mapping")
    parser.add_argument('--opensearch-endpoint', required=True, help='OpenSearch endpoint')
    parser.add_argument('--index', required=True, help='Index name to check')
    parser.add_argument('--profile', default='caylent-test', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()

    awsauth = get_aws_auth(args.profile, args.region)
    session = requests.Session()
    session.auth = awsauth
    session.headers.update({"Content-Type": "application/json"})
    session.verify = True

    url = f"{args.opensearch_endpoint}/{args.index}/_mapping"
    logger.info(f"Fetching mapping for index: {args.index}")
    response = session.get(url)
    if response.status_code == 200:
        mapping = response.json()
        print(json.dumps(mapping, indent=2))
    else:
        logger.error(f"Failed to fetch mapping: {response.status_code} {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main() 