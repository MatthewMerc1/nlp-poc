#!/usr/bin/env python3
"""
Script to generate vector embeddings of books from S3 using Amazon Bedrock.
"""

import boto3
import json
import os
import re
from typing import List, Dict, Tuple
import time
from botocore.exceptions import ClientError

class BedrockEmbeddingGenerator:
    def __init__(self, bucket_name: str, aws_profile: str = None, model_id: str = "amazon.titan-embed-text-v1"):
        """Initialize the embedding generator."""
        self.bucket_name = bucket_name
        self.model_id = model_id
        
        # Initialize AWS clients
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
            self.bedrock_client = session.client('bedrock-runtime')
        else:
            self.s3_client = boto3.client('s3')
            self.bedrock_client = boto3.client('bedrock-runtime')
    
    def list_books_in_s3(self) -> List[str]:
        """List all book files in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='books/'
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.txt')]
            else:
                print("No books found in S3 bucket")
                return []
                
        except ClientError as e:
            print(f"Error listing books: {e}")
            return []
    
    def download_book_from_s3(self, s3_key: str) -> str:
        """Download a book from S3 and return its content."""
        try:
            print(f"Downloading {s3_key} from S3...")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode('utf-8')
            print(f"Downloaded {len(content)} characters from {s3_key}")
            
            return content
            
        except ClientError as e:
            print(f"Error downloading {s3_key}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess the text."""
        # Remove Project Gutenberg header and footer
        # Find the start of the actual book content
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
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_endings = ['.', '!', '?']
                for ending in sentence_endings:
                    last_ending = text.rfind(ending, start, end)
                    if last_ending > start + chunk_size // 2:  # Only break if it's not too early
                        end = last_ending + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text chunk using Bedrock."""
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
    
    def upload_embeddings_to_s3(self, book_title: str, embeddings: List[Dict]) -> bool:
        """Upload embeddings to S3 as JSON."""
        try:
            # Create the embeddings data structure
            embeddings_data = {
                "book_title": book_title,
                "model_id": self.model_id,
                "total_chunks": len(embeddings),
                "embeddings": embeddings,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Create S3 key
            safe_title = re.sub(r'[^\w\s-]', '', book_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            s3_key = f"embeddings/{safe_title}-embeddings.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(embeddings_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            print(f"Uploaded embeddings to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            print(f"Error uploading embeddings: {e}")
            return False
    
    def process_book(self, s3_key: str, chunk_size: int = 1000, overlap: int = 100) -> bool:
        """Process a single book: download, chunk, embed, and upload."""
        # Extract book title from S3 key
        book_title = os.path.basename(s3_key).replace('.txt', '')
        
        print(f"\nProcessing book: {book_title}")
        print("=" * 50)
        
        # Download book from S3
        text_content = self.download_book_from_s3(s3_key)
        if not text_content:
            return False
        
        # Clean the text
        cleaned_text = self.clean_text(text_content)
        print(f"Cleaned text length: {len(cleaned_text)} characters")
        
        # Chunk the text
        chunks = self.chunk_text(cleaned_text, chunk_size, overlap)
        print(f"Created {len(chunks)} text chunks")
        
        # Generate embeddings for each chunk
        embeddings = []
        for i, chunk in enumerate(chunks):
            print(f"Generating embedding for chunk {i+1}/{len(chunks)}...")
            
            embedding = self.generate_embedding(chunk)
            if embedding:
                embeddings.append({
                    "chunk_index": i,
                    "text": chunk[:200] + "..." if len(chunk) > 200 else chunk,  # Store first 200 chars
                    "embedding": embedding
                })
            
            # Rate limiting - be respectful to Bedrock API
            time.sleep(0.1)
        
        print(f"Generated {len(embeddings)} embeddings")
        
        # Upload embeddings to S3
        success = self.upload_embeddings_to_s3(book_title, embeddings)
        
        return success
    
    def process_all_books(self, chunk_size: int = 1000, overlap: int = 100):
        """Process all books in the S3 bucket."""
        print(f"Starting embedding generation for books in bucket: {self.bucket_name}")
        print(f"Using model: {self.model_id}")
        print(f"Chunk size: {chunk_size}, Overlap: {overlap}")
        print("=" * 60)
        
        # List all books
        book_keys = self.list_books_in_s3()
        if not book_keys:
            print("No books found to process")
            return
        
        print(f"Found {len(book_keys)} books to process")
        
        # Process each book
        successful_books = 0
        for book_key in book_keys:
            if self.process_book(book_key, chunk_size, overlap):
                successful_books += 1
            print("\n" + "-" * 40 + "\n")
        
        print(f"Processing complete! Successfully processed {successful_books}/{len(book_keys)} books")

def main():
    """Main function to run the embedding generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for books using Amazon Bedrock')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--model', default='amazon.titan-embed-text-v1', 
                       help='Bedrock model ID for embeddings')
    parser.add_argument('--chunk-size', type=int, default=1000, 
                       help='Size of text chunks (default: 1000)')
    parser.add_argument('--overlap', type=int, default=100, 
                       help='Overlap between chunks (default: 100)')
    
    args = parser.parse_args()
    
    generator = BedrockEmbeddingGenerator(args.bucket, args.profile, args.model)
    generator.process_all_books(args.chunk_size, args.overlap)

if __name__ == "__main__":
    main() 