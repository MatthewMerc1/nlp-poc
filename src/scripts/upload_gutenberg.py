#!/usr/bin/env python3
"""
Script to download books from Project Gutenberg and upload them to S3 bucket.
"""

import boto3
import requests
import os
import re
from urllib.parse import urljoin
import time
from typing import List, Dict

class GutenbergUploader:
    def __init__(self, bucket_name: str, aws_profile: str = None):
        """Initialize the uploader with S3 bucket details."""
        self.bucket_name = bucket_name
        
        # Initialize S3 client
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            self.s3_client = boto3.client('s3')
    
    def get_gutendex_books(self, limit=100) -> List[Dict]:
        """Fetch a list of English book metadata from Gutendex API."""
        books = []
        page = 1
        while len(books) < limit:
            resp = requests.get(f"https://gutendex.com/books/?languages=en&page={page}")
            data = resp.json()
            for book in data['results']:
                txt_url = None
                for fmt, url in book['formats'].items():
                    if fmt.startswith("text/plain") and url.endswith('.txt'):
                        txt_url = url
                        break
                if txt_url:
                    books.append({
                        'title': book['title'],
                        'author': book['authors'][0]['name'] if book['authors'] else 'Unknown',
                        'gutenberg_id': str(book['id']),
                        'url': txt_url
                    })
                if len(books) >= limit:
                    break
            if not data['next']:
                break
            page += 1
        return books[:limit]

    def get_gutenberg_book_urls(self, limit: int = 100) -> List[Dict]:
        """Get a list of books from Gutendex API (replaces static list)."""
        return self.get_gutendex_books(limit)
    
    def download_book(self, book: Dict) -> str:
        """Download a book from Project Gutenberg."""
        print(f"Downloading: {book['title']} by {book['author']}")
        
        try:
            response = requests.get(book['url'], timeout=30)
            response.raise_for_status()
            
            # Clean the filename
            clean_title = re.sub(r'[^\w\s-]', '', book['title']).strip()
            clean_title = re.sub(r'[-\s]+', '-', clean_title)
            clean_author = re.sub(r'[^\w\s-]', '', book['author']).strip()
            clean_author = re.sub(r'[-\s]+', '-', clean_author)
            filename = f"{clean_title}__by__{clean_author}.txt"
            
            # Save locally first
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Downloaded: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error downloading {book['title']}: {e}")
            return None
    
    def upload_to_s3(self, local_file: str, s3_key: str) -> bool:
        """Upload a file to S3 bucket."""
        try:
            print(f"Uploading {local_file} to s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                local_file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'text/plain',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            print(f"Successfully uploaded: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            print(f"Error uploading {local_file}: {e}")
            return False
    
    def cleanup_local_file(self, filename: str):
        """Remove local file after upload."""
        try:
            os.remove(filename)
            print(f"Cleaned up local file: {filename}")
        except Exception as e:
            print(f"Error cleaning up {filename}: {e}")
    
    def upload_books(self, limit: int = 5):
        """Main method to download and upload books."""
        print(f"Starting upload of {limit} books to S3 bucket: {self.bucket_name}")
        
        books = self.get_gutenberg_book_urls(limit)
        uploaded_count = 0
        
        for book in books:
            # Download book
            local_file = self.download_book(book)
            if not local_file:
                continue
            
            # Create S3 key
            s3_key = f"books/{local_file}"
            
            # Upload to S3
            if self.upload_to_s3(local_file, s3_key):
                uploaded_count += 1
            
            # Cleanup local file
            self.cleanup_local_file(local_file)
            
            # Be respectful to Project Gutenberg servers
            time.sleep(1)
        
        print(f"\nUpload complete! Successfully uploaded {uploaded_count} books to S3.")

def main():
    """Main function to run the uploader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload Project Gutenberg books to S3')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--limit', type=int, default=100, help='Number of books to upload (default: 100)')
    
    args = parser.parse_args()
    
    uploader = GutenbergUploader(args.bucket, args.profile)
    uploader.upload_books(args.limit)

if __name__ == "__main__":
    main() 