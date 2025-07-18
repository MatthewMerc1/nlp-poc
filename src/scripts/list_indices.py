#!/usr/bin/env python3
import boto3
import requests
from requests_aws4auth import AWS4Auth
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--opensearch-endpoint', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--region', required=True)
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    credentials = session.get_credentials().get_frozen_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, args.region, 'aoss', session_token=credentials.token)

    url = f"{args.opensearch_endpoint}/_cat/indices?v"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, auth=awsauth, headers=headers)
    if response.status_code == 200:
        print(response.text)
    else:
        print(f"Error: {response.status_code} {response.text}")

if __name__ == "__main__":
    main()