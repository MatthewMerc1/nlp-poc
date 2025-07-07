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
    
    def get_gutenberg_book_urls(self, limit: int = 10) -> List[Dict]:
        """Get a list of popular books from Project Gutenberg."""
        # Popular books from Project Gutenberg
        books = [
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'gutenberg_id': '1342',
                'url': 'https://www.gutenberg.org/files/1342/1342-0.txt'
            },
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'gutenberg_id': '64317',
                'url': 'https://www.gutenberg.org/files/64317/64317-0.txt'
            },
            {
                'title': 'Alice\'s Adventures in Wonderland',
                'author': 'Lewis Carroll',
                'gutenberg_id': '11',
                'url': 'https://www.gutenberg.org/files/11/11-0.txt'
            },
            {
                'title': 'Frankenstein',
                'author': 'Mary Shelley',
                'gutenberg_id': '84',
                'url': 'https://www.gutenberg.org/files/84/84-0.txt'
            },
            {
                'title': 'The Adventures of Sherlock Holmes',
                'author': 'Arthur Conan Doyle',
                'gutenberg_id': '1661',
                'url': 'https://www.gutenberg.org/files/1661/1661-0.txt'
            },
            {
                'title': 'Dracula',
                'author': 'Bram Stoker',
                'gutenberg_id': '345',
                'url': 'https://www.gutenberg.org/files/345/345-0.txt'
            },
            {
                'title': 'The Picture of Dorian Gray',
                'author': 'Oscar Wilde',
                'gutenberg_id': '174',
                'url': 'https://www.gutenberg.org/files/174/174-0.txt'
            },
            {
                'title': 'The Time Machine',
                'author': 'H.G. Wells',
                'gutenberg_id': '35',
                'url': 'https://www.gutenberg.org/files/35/35-0.txt'
            },
            {
                'title': 'A Christmas Carol',
                'author': 'Charles Dickens',
                'gutenberg_id': '46',
                'url': 'https://www.gutenberg.org/files/46/46-0.txt'
            },
            {
                'title': 'The War of the Worlds',
                'author': 'H.G. Wells',
                'gutenberg_id': '36',
                'url': 'https://www.gutenberg.org/files/36/36-0.txt'
            }
        ]
        
        return books[:limit]
    
    def download_book(self, book: Dict) -> str:
        """Download a book from Project Gutenberg."""
        print(f"Downloading: {book['title']} by {book['author']}")
        
        try:
            response = requests.get(book['url'], timeout=30)
            response.raise_for_status()
            
            # Clean the filename
            filename = re.sub(r'[^\w\s-]', '', book['title']).strip()
            filename = re.sub(r'[-\s]+', '-', filename)
            filename = f"{filename}-{book['author'].replace(' ', '-')}.txt"
            
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
                ExtraArgs={'ContentType': 'text/plain'}
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
    parser.add_argument('--limit', type=int, default=5, help='Number of books to upload (default: 5)')
    
    args = parser.parse_args()
    
    uploader = GutenbergUploader(args.bucket, args.profile)
    uploader.upload_books(args.limit)

if __name__ == "__main__":
    main() 