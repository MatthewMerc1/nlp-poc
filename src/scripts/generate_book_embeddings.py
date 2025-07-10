#!/usr/bin/env python3
"""
Script to generate vector embeddings for entire books using Amazon Bedrock.
This is designed for book recommendation systems, not content search.
"""

import boto3
import json
import os
import re
from typing import List, Dict
import time
from botocore.exceptions import ClientError

class BookEmbeddingGenerator:
    def __init__(self, bucket_name: str, aws_profile: str = None, model_id: str = "amazon.titan-embed-text-v1"):
        """Initialize the book embedding generator."""
        self.bucket_name = bucket_name
        self.model_id = model_id
        
        # Initialize AWS clients
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
            self.bedrock_client = session.client('bedrock-runtime')
        else:
            self.s3_client = boto3.client('s3')
            self.bedrock_client = session.client('bedrock-runtime')
    
    def get_book_metadata(self) -> List[Dict]:
        """Get metadata for books including genre and description."""
        books = [
            {
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'genre': 'Romance, Classic Literature',
                'description': 'A classic romance novel about the relationship between Elizabeth Bennet and Mr. Darcy, exploring themes of love, marriage, and social class in 19th century England.',
                'gutenberg_id': '1342',
                'url': 'https://www.gutenberg.org/files/1342/1342-0.txt'
            },
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'genre': 'Literary Fiction, Classic Literature',
                'description': 'A tragic love story set in the Jazz Age, following Jay Gatsby\'s pursuit of the American Dream and his love for Daisy Buchanan.',
                'gutenberg_id': '64317',
                'url': 'https://www.gutenberg.org/files/64317/64317-0.txt'
            },
            {
                'title': 'Alice\'s Adventures in Wonderland',
                'author': 'Lewis Carroll',
                'genre': 'Fantasy, Children\'s Literature',
                'description': 'A whimsical fantasy novel about a young girl who falls down a rabbit hole into a world of talking animals and bizarre characters.',
                'gutenberg_id': '11',
                'url': 'https://www.gutenberg.org/files/11/11-0.txt'
            },
            {
                'title': 'Frankenstein',
                'author': 'Mary Shelley',
                'genre': 'Gothic Fiction, Science Fiction, Horror',
                'description': 'A Gothic horror novel about a scientist who creates a monster and the consequences of playing God, exploring themes of creation and responsibility.',
                'gutenberg_id': '84',
                'url': 'https://www.gutenberg.org/files/84/84-0.txt'
            },
            {
                'title': 'The Adventures of Sherlock Holmes',
                'author': 'Arthur Conan Doyle',
                'genre': 'Mystery, Detective Fiction',
                'description': 'A collection of detective stories featuring the brilliant detective Sherlock Holmes and his loyal friend Dr. Watson solving various mysteries.',
                'gutenberg_id': '1661',
                'url': 'https://www.gutenberg.org/files/1661/1661-0.txt'
            },
            {
                'title': 'Dracula',
                'author': 'Bram Stoker',
                'genre': 'Gothic Fiction, Horror, Vampire Fiction',
                'description': 'A Gothic horror novel about Count Dracula, a vampire who moves from Transylvania to England, and the group of people who try to stop him.',
                'gutenberg_id': '345',
                'url': 'https://www.gutenberg.org/files/345/345-0.txt'
            },
            {
                'title': 'The Picture of Dorian Gray',
                'author': 'Oscar Wilde',
                'genre': 'Gothic Fiction, Philosophical Fiction',
                'description': 'A philosophical novel about a beautiful young man whose portrait ages while he remains youthful, exploring themes of beauty, morality, and corruption.',
                'gutenberg_id': '174',
                'url': 'https://www.gutenberg.org/files/174/174-0.txt'
            },
            {
                'title': 'The Time Machine',
                'author': 'H.G. Wells',
                'genre': 'Science Fiction, Time Travel',
                'description': 'A science fiction novel about a time traveler who journeys to the distant future and discovers a divided human society.',
                'gutenberg_id': '35',
                'url': 'https://www.gutenberg.org/files/35/35-0.txt'
            },
            {
                'title': 'A Christmas Carol',
                'author': 'Charles Dickens',
                'genre': 'Classic Literature, Christmas Fiction',
                'description': 'A Christmas story about Ebenezer Scrooge, a miserly old man who is visited by ghosts and learns the true meaning of Christmas.',
                'gutenberg_id': '46',
                'url': 'https://www.gutenberg.org/files/46/46-0.txt'
            },
            {
                'title': 'The War of the Worlds',
                'author': 'H.G. Wells',
                'genre': 'Science Fiction, Alien Invasion',
                'description': 'A science fiction novel about a Martian invasion of Earth, exploring themes of imperialism and human vulnerability.',
                'gutenberg_id': '36',
                'url': 'https://www.gutenberg.org/files/36/36-0.txt'
            }
        ]
        
        return books
    
    def download_book_content(self, book: Dict) -> str:
        """Download book content from Project Gutenberg."""
        print(f"Downloading: {book['title']} by {book['author']}")
        
        try:
            import requests
            response = requests.get(book['url'], timeout=30)
            response.raise_for_status()
            
            # Clean the text
            text = self.clean_text(response.text)
            print(f"Downloaded and cleaned {len(text)} characters")
            
            return text
            
        except Exception as e:
            print(f"Error downloading {book['title']}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess the text."""
        # Remove Project Gutenberg header and footer
        start_markers = [
            "*** START OF THE PROJECT GUTENBERG EBOOK",
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "The Project Gutenberg eBook of"
        ]
        
        for marker in start_markers:
            if marker in text:
                text = text.split(marker, 1)[1]
                break
        
        # Find the end of the book content
        end_markers = [
            "*** END OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK"
        ]
        
        for marker in end_markers:
            if marker in text:
                text = text.split(marker, 1)[0]
                break
        
        # Clean up the text
        text = re.sub(r'\r\n', '\n', text)  # Normalize line endings
        text = re.sub(r'\n{3,}', '\n\n', text)  # Remove excessive newlines
        text = re.sub(r'[^\w\s\n.,!?;:()\'"-]', '', text)  # Remove special characters
        text = text.strip()
        
        return text
    
    def create_book_summary(self, book: Dict, content: str) -> str:
        """Create a comprehensive summary for embedding generation."""
        # Take first 2000 characters as a sample of the book's style and content
        content_sample = content[:2000] if len(content) > 2000 else content
        
        summary = f"""
Title: {book['title']}
Author: {book['author']}
Genre: {book['genre']}
Description: {book['description']}
Content Sample: {content_sample}
        """.strip()
        
        return summary
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Bedrock."""
        try:
            # Prepare the request body
            request_body = {
                "inputText": text
            }
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            return embedding
            
        except ClientError as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def upload_book_embedding(self, book: Dict, embedding: List[float]) -> bool:
        """Upload book embedding and metadata to S3."""
        try:
            # Create the book data structure
            book_data = {
                "book_title": book['title'],
                "author": book['author'],
                "genre": book['genre'],
                "description": book['description'],
                "gutenberg_id": book['gutenberg_id'],
                "embedding": embedding,
                "model_id": self.model_id,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Create S3 key
            safe_title = re.sub(r'[^\w\s-]', '', book['title']).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            s3_key = f"book-recommendations/{safe_title}-book-embedding.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(book_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            print(f"Uploaded book embedding to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            print(f"Error uploading book embedding: {e}")
            return False
    
    def process_book(self, book: Dict) -> bool:
        """Process a single book: download, create summary, embed, and upload."""
        print(f"\nProcessing book: {book['title']}")
        print("=" * 50)
        
        # Download book content
        content = self.download_book_content(book)
        if not content:
            return False
        
        # Create book summary for embedding
        summary = self.create_book_summary(book, content)
        print(f"Created summary of {len(summary)} characters")
        
        # Generate embedding
        print("Generating embedding...")
        embedding = self.generate_embedding(summary)
        if not embedding:
            return False
        
        print(f"Generated embedding with {len(embedding)} dimensions")
        
        # Upload to S3
        success = self.upload_book_embedding(book, embedding)
        
        return success
    
    def process_all_books(self):
        """Process all books to generate embeddings."""
        print(f"Starting book embedding generation for recommendation system")
        print(f"Using model: {self.model_id}")
        print("=" * 60)
        
        # Get book metadata
        books = self.get_book_metadata()
        print(f"Found {len(books)} books to process")
        
        # Process each book
        successful_books = 0
        for book in books:
            if self.process_book(book):
                successful_books += 1
            print("\n" + "-" * 40 + "\n")
            
            # Rate limiting - be respectful to Bedrock API
            time.sleep(1)
        
        print(f"Processing complete! Successfully processed {successful_books}/{len(books)} books")

def main():
    """Main function to run the book embedding generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for books using Amazon Bedrock')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--model', default='amazon.titan-embed-text-v1', 
                       help='Bedrock model ID for embeddings')
    
    args = parser.parse_args()
    
    generator = BookEmbeddingGenerator(args.bucket, args.profile, args.model)
    generator.process_all_books()

if __name__ == "__main__":
    main() 