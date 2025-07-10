import boto3
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import os

region = "us-east-1"
host = "vpc-nlp-poc-dev-opensearch-zvegkj7ce5w6env4yhhznrh64i.us-east-1.es.amazonaws.com"  # e.g., vpc-...us-east-1.es.amazonaws.com
index = "book-embeddings"

credentials = boto3.Session(profile_name="caylent-dev-test").get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    "es",
    session_token=credentials.token
)

client = OpenSearch(
    hosts=[{"host": host, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

count = client.count(index=index)["count"]
print(f"Documents in '{index}': {count}")