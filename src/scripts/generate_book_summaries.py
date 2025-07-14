#!/usr/bin/env python3
"""
Enhanced script to generate book-level summaries and embeddings for improved search accuracy.
This version creates longer, more detailed summaries with better semantic content.
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
        start_markers = [
            "*** START OF THE PROJECT GUTENBERG EBOOK",
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "The Project Gutenberg eBook of"
        ]
        
        for marker in start_markers:
            if marker in text:
                text = text.split(marker, 1)[1]
                break
        
        end_markers = [
            "*** END OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK"
        ]
        
        for marker in end_markers:
            if marker in text:
                text = text.split(marker, 1)[0]
                break
        
        # Clean up the text
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[^\w\s\n.,!?;:()\'"-]', '', text)
        text = text.strip()
        
        return text
    
    def chunk_text_large(self, text: str, chunk_size: int = 8000, overlap: int = 500) -> List[str]:
        """Split text into larger chunks for hierarchical summarization."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                last_paragraph = text.rfind('\n\n', start, end)
                if last_paragraph > start + chunk_size // 2:
                    end = last_paragraph + 2
                else:
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
    
    def generate_chunk_summary(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Generate a summary for a text chunk with more detail."""
        try:
            prompt = f"""You are analyzing section {chunk_index} of {total_chunks} from a book. 
Please provide a detailed summary of this section that captures:

1. Key plot developments and events
2. Important character interactions and developments
3. Significant themes, motifs, or symbols
4. Setting details and atmosphere
5. Any notable dialogue or quotes
6. How this section contributes to the overall story

Focus on creating a rich, detailed summary that would help someone understand what happens in this section and why it matters. 
Write in clear, engaging prose without any boilerplate text or meta-commentary.

Text section:
{chunk}

Detailed summary:"""

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,  # Increased from 300
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            summary = response_body['content'][0]['text'].strip()
            
            return summary
            
        except ClientError as e:
            print(f"Error generating chunk summary: {e}")
            return None
    
    def generate_book_summary(self, chunk_summaries: List[str], book_title: str, author: str) -> Dict[str, str]:
        """Generate multiple types of book summaries for better semantic matching."""
        try:
            combined_summaries = "\n\n".join(chunk_summaries)
            
            # Generate comprehensive plot summary
            plot_prompt = f"""Based on these detailed section summaries from "{book_title}" by {author}, 
create a comprehensive plot summary that includes:

1. Complete plot overview with all major events
2. Character arcs and relationships
3. Key conflicts and resolutions
4. Important themes and messages
5. Setting and historical context
6. Notable quotes or memorable moments

Write a detailed, engaging summary that captures the full scope and impact of the story. 
Aim for 8-12 sentences that would help someone understand the complete book.

Section summaries:
{combined_summaries}

Comprehensive plot summary:"""

            # Generate thematic analysis
            theme_prompt = f"""Based on these section summaries from "{book_title}" by {author}, 
analyze the major themes, motifs, and literary elements of this book. Include:

1. Primary themes and their development throughout the story
2. Character motivations and psychological elements
3. Symbolism and allegorical meanings
4. Social commentary or philosophical ideas
5. Literary techniques and style
6. Historical or cultural significance

Write a detailed thematic analysis that explores the deeper meaning and significance of the work.
Aim for 6-10 sentences that capture the intellectual and artistic depth of the book.

Section summaries:
{combined_summaries}

Thematic analysis:"""

            # Generate character-focused summary
            character_prompt = f"""Based on these section summaries from "{book_title}" by {author}, 
create a character-focused summary that highlights:

1. Main characters and their personalities
2. Character relationships and dynamics
3. Character development and growth
4. Motivations and conflicts
5. Supporting characters and their roles
6. Character-driven plot elements

Write a detailed character analysis that shows how characters drive the story and relate to each other.
Aim for 6-10 sentences that capture the human elements and relationships in the book.

Section summaries:
{combined_summaries}

Character-focused summary:"""

            summaries = {}
            
            # Generate all three types of summaries
            for summary_type, prompt in [
                ("plot_summary", plot_prompt),
                ("thematic_analysis", theme_prompt),
                ("character_summary", character_prompt)
            ]:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 800,  # Increased token limit
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                response = self.bedrock_client.invoke_model(
                    modelId=self.summary_model_id,
                    body=json.dumps(request_body)
                )
                
                response_body = json.loads(response['body'].read())
                summaries[summary_type] = response_body['content'][0]['text'].strip()
                
                # Rate limiting
                time.sleep(1)
            
            return summaries
            
        except ClientError as e:
            print(f"Error generating book summaries: {e}")
            return None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Bedrock."""
        try:
            request_body = {
                "inputText": text
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            return embedding
            
        except ClientError as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def extract_author_from_text(self, text: str) -> str:
        """Extract author information from the book text."""
        author_patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Unknown Author"
    
    def upload_book_summary_to_s3(self, book_title: str, book_data: Dict) -> bool:
        """Upload book summary and embeddings to S3."""
        try:
            book_summary_data = {
                "book_title": book_title,
                "author": book_data.get('author', 'Unknown Author'),
                "embedding_model_id": self.embedding_model_id,
                "summary_model_id": self.summary_model_id,
                "plot_summary": book_data.get('plot_summary', ''),
                "thematic_analysis": book_data.get('thematic_analysis', ''),
                "character_summary": book_data.get('character_summary', ''),
                "combined_summary": book_data.get('combined_summary', ''),
                "plot_embedding": book_data.get('plot_embedding', []),
                "thematic_embedding": book_data.get('thematic_embedding', []),
                "character_embedding": book_data.get('character_embedding', []),
                "combined_embedding": book_data.get('combined_embedding', []),
                "total_chunks": book_data.get('total_chunks', 0),
                "chunk_summaries": book_data.get('chunk_summaries', []),
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            safe_title = re.sub(r'[^\w\s-]', '', book_title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            s3_key = f"book-summaries/{safe_title}-summary.json"
            
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
        """Process a single book with summarization."""
        book_title = os.path.basename(s3_key).replace('.txt', '')
        
        print(f"\nProcessing book with summarization: {book_title}")
        print("=" * 60)
        
        # Download and clean book
        text_content = self.download_book_from_s3(s3_key)
        if not text_content:
            return False
        
        cleaned_text = self.clean_text(text_content)
        print(f"Cleaned text length: {len(cleaned_text)} characters")
        
        author = self.extract_author_from_text(cleaned_text)
        print(f"Extracted author: {author}")
        
        # Generate chunk summaries
        chunks = self.chunk_text_large(cleaned_text, chunk_size, overlap)
        print(f"Created {len(chunks)} large text chunks")
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"Generating summary for chunk {i+1}/{len(chunks)}...")
            
            summary = self.generate_chunk_summary(chunk, i+1, len(chunks))
            if summary:
                chunk_summaries.append(summary)
            
            time.sleep(0.5)
        
        print(f"Generated {len(chunk_summaries)} chunk summaries")
        
        # Generate multiple types of book summaries
        print("Generating book summaries...")
        book_summaries = self.generate_book_summary(chunk_summaries, book_title, author)
        if not book_summaries:
            print("Failed to generate book summaries")
            return False
        
        # Create combined summary for primary embedding
        combined_summary = f"{book_summaries['plot_summary']}\n\n{book_summaries['thematic_analysis']}\n\n{book_summaries['character_summary']}"
        
        # Generate embeddings for each summary type
        print("Generating multiple embeddings...")
        embeddings = {}
        
        for summary_type, summary_text in book_summaries.items():
            print(f"Summary type: {summary_type}, text (first 100 chars): {summary_text[:100]}")
            embedding = self.generate_embedding(summary_text)
            if embedding:
                print(f"Embedding for {summary_type} (first 5 values): {embedding[:5]}")
                embeddings[f"{summary_type}_embedding"] = embedding
            else:
                print(f"Embedding for {summary_type} is None or empty!")
            time.sleep(0.5)
        
        # Generate combined embedding
        print("Generating combined embedding...")
        print(f"Combined summary (first 100 chars): {combined_summary[:100]}")
        combined_embedding = self.generate_embedding(combined_summary)
        if combined_embedding:
            print(f"Combined embedding (first 5 values): {combined_embedding[:5]}")
            embeddings["combined_embedding"] = combined_embedding
        else:
            print("Combined embedding is None or empty!")
        
        # Prepare book data
        book_data = {
            'author': author,
            'plot_summary': book_summaries['plot_summary'],
            'thematic_analysis': book_summaries['thematic_analysis'],
            'character_summary': book_summaries['character_summary'],
            'combined_summary': combined_summary,
            'total_chunks': len(chunks),
            'chunk_summaries': chunk_summaries,
            **embeddings
        }
        
        # Upload book summary
        success = self.upload_book_summary_to_s3(book_title, book_data)
        
        return success
    
    def process_all_books(self, chunk_size: int = 8000, overlap: int = 500, max_books: int = None):
        """Process all books with summarization, up to max_books if specified."""
        print(f"Starting book summary generation for books in bucket: {self.bucket_name}")
        print(f"Using embedding model: {self.embedding_model_id}")
        print(f"Using summary model: {self.summary_model_id}")
        print(f"Chunk size: {chunk_size}, Overlap: {overlap}")
        print("=" * 70)
        
        book_keys = self.list_books_in_s3()
        if not book_keys:
            print("No books found to process")
            return
        
        print(f"Found {len(book_keys)} books to process")
        
        if max_books is not None:
            book_keys = book_keys[:max_books]
            print(f"Limiting to {max_books} books")
        
        successful_books = 0
        for book_key in book_keys:
            if self.process_book(book_key, chunk_size, overlap):
                successful_books += 1
            print("\n" + "-" * 50 + "\n")
        
        print(f"Processing complete! Successfully processed {successful_books}/{len(book_keys)} books")

def main():
    """Main function to run the enhanced book summary generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate book-level summaries for improved search accuracy')
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
    parser.add_argument('--max-books', type=int, default=None, help='Maximum number of books to summarize (default: all)')
    
    args = parser.parse_args()
    
    generator = BookSummaryGenerator(args.bucket, args.profile, args.embedding_model, args.summary_model)
    generator.process_all_books(args.chunk_size, args.overlap, args.max_books)

if __name__ == "__main__":
    main() 