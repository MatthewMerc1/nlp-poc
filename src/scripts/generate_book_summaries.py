#!/usr/bin/env python3
"""
Script to generate book-level summaries and embeddings using hierarchical summarization.
This script creates high-level summaries of entire books instead of chunk-level embeddings.
"""

import boto3
import json
import os
import re
from typing import List, Dict, Tuple
import time
from botocore.exceptions import ClientError

class BookSummaryGenerator:
    def __init__(self, bucket_name: str, aws_profile: str = None, 
                 embedding_model_id: str = "amazon.titan-embed-text-v1",
                 summary_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """Initialize the book summary generator."""
        self.bucket_name = bucket_name
        self.embedding_model_id = embedding_model_id
        self.summary_model_id = summary_model_id
        
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
    
    def chunk_text_large(self, text: str, chunk_size: int = 8000, overlap: int = 500) -> List[str]:
        """Split text into larger chunks for hierarchical summarization."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a paragraph boundary
            if end < len(text):
                # Look for paragraph breaks (double newlines)
                last_paragraph = text.rfind('\n\n', start, end)
                if last_paragraph > start + chunk_size // 2:  # Only break if it's not too early
                    end = last_paragraph + 2
                else:
                    # Fall back to sentence boundary
                    sentence_endings = ['.', '!', '?']
                    for ending in sentence_endings:
                        last_ending = text.rfind(ending, start, end)
                        if last_ending > start + chunk_size // 2:
                            end = last_ending + 1
                            break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def generate_chunk_summary(self, chunk: str) -> str:
        """Generate a summary for a large text chunk using Claude."""
        try:
            # Prepare the prompt for summarization
            prompt = f"""Please provide a concise summary of the following text excerpt from a book. 
Focus on the main themes, key events, and important characters. Keep the summary to 2-3 sentences.

Text excerpt:
{chunk}

Summary:"""

            # Prepare the request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            summary = response_body['content'][0]['text'].strip()
            
            return summary
            
        except ClientError as e:
            print(f"Error generating chunk summary: {e}")
            return None
    
    def generate_book_summary(self, chunk_summaries: List[str]) -> str:
        """Generate a final book summary from chunk summaries using Claude."""
        try:
            # Combine all chunk summaries
            combined_summaries = "\n\n".join(chunk_summaries)
            
            # Prepare the prompt for final book summary
            prompt = f"""Based on the following summaries of different sections of a book, 
please provide a comprehensive high-level summary of the entire book. 
Include the main plot, key themes, important characters, and the overall message or purpose of the book.
Keep the summary to 4-6 sentences and make it engaging for someone who wants to understand what the book is about.

Section summaries:
{combined_summaries}

Book summary:"""

            # Prepare the request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            book_summary = response_body['content'][0]['text'].strip()
            
            return book_summary
            
        except ClientError as e:
            print(f"Error generating book summary: {e}")
            return None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Bedrock."""
        try:
            # Prepare the request body
            request_body = {
                "inputText": text
            }
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(request_body)
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            return embedding
            
        except ClientError as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def extract_author_from_text(self, text: str) -> str:
        """Extract author information from the book text."""
        # Common patterns for author attribution
        author_patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)  # Search in first 2000 chars
            if match:
                return match.group(1).strip()
        
        return "Unknown Author"
    
    def upload_book_summary_to_s3(self, book_title: str, book_data: Dict) -> bool:
        """Upload book summary and embedding to S3 as JSON."""
        try:
            # Create the book data structure
            book_summary_data = {
                "book_title": book_title,
                "author": book_data.get('author', 'Unknown Author'),
                "embedding_model_id": self.embedding_model_id,
                "summary_model_id": self.summary_model_id,
                "book_summary": book_data.get('book_summary', ''),
                "book_embedding": book_data.get('book_embedding', []),
                "total_chunks": book_data.get('total_chunks', 0),
                "chunk_summaries": book_data.get('chunk_summaries', []),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Create S3 key
            safe_title = re.sub(r'[^\w\s-]', '', book_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            s3_key = f"book-summaries/{safe_title}-summary.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(book_summary_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            print(f"Uploaded book summary to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            print(f"Error uploading book summary: {e}")
            return False
    
    def process_book(self, s3_key: str, chunk_size: int = 8000, overlap: int = 500) -> bool:
        """Process a single book: download, chunk, summarize hierarchically, and upload."""
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
        
        # Extract author information
        author = self.extract_author_from_text(cleaned_text)
        print(f"Extracted author: {author}")
        
        # Chunk the text into large chunks
        chunks = self.chunk_text_large(cleaned_text, chunk_size, overlap)
        print(f"Created {len(chunks)} large text chunks")
        
        # Generate summaries for each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"Generating summary for chunk {i+1}/{len(chunks)}...")
            
            summary = self.generate_chunk_summary(chunk)
            if summary:
                chunk_summaries.append(summary)
            
            # Rate limiting - be respectful to Bedrock API
            time.sleep(0.5)
        
        print(f"Generated {len(chunk_summaries)} chunk summaries")
        
        # Generate final book summary from chunk summaries
        print("Generating final book summary...")
        book_summary = self.generate_book_summary(chunk_summaries)
        if not book_summary:
            print("Failed to generate book summary")
            return False
        
        print(f"Book summary: {book_summary[:200]}...")
        
        # Generate embedding for the book summary
        print("Generating book embedding...")
        book_embedding = self.generate_embedding(book_summary)
        if not book_embedding:
            print("Failed to generate book embedding")
            return False
        
        # Prepare book data
        book_data = {
            'author': author,
            'book_summary': book_summary,
            'book_embedding': book_embedding,
            'total_chunks': len(chunks),
            'chunk_summaries': chunk_summaries
        }
        
        # Upload book summary to S3
        success = self.upload_book_summary_to_s3(book_title, book_data)
        
        return success
    
    def process_all_books(self, chunk_size: int = 8000, overlap: int = 500):
        """Process all books in the S3 bucket."""
        print(f"Starting book summary generation for books in bucket: {self.bucket_name}")
        print(f"Using embedding model: {self.embedding_model_id}")
        print(f"Using summary model: {self.summary_model_id}")
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
    """Main function to run the book summary generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate book-level summaries using hierarchical summarization')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--embedding-model', default='amazon.titan-embed-text-v1', 
                       help='Bedrock model ID for embeddings')
    parser.add_argument('--summary-model', default='anthropic.claude-3-sonnet-20240229-v1:0', 
                       help='Bedrock model ID for summarization')
    parser.add_argument('--chunk-size', type=int, default=8000, 
                       help='Size of text chunks for summarization (default: 8000)')
    parser.add_argument('--overlap', type=int, default=500, 
                       help='Overlap between chunks (default: 500)')
    
    args = parser.parse_args()
    
    generator = BookSummaryGenerator(args.bucket, args.profile, args.embedding_model, args.summary_model)
    generator.process_all_books(args.chunk_size, args.overlap)

if __name__ == "__main__":
    main() 