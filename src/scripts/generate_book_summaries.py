#!/usr/bin/env python3
"""
Parallel book summary generator with bulk indexing for scalability.
This version processes multiple books in parallel and uses bulk indexing for OpenSearch.
"""

import boto3
import json
import os
import re
import time
import logging
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError
import requests
from requests_aws4auth import AWS4Auth
import argparse
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BookSummaryGenerator:
    def __init__(self, bucket_name: str, aws_profile: str = None, 
                 embedding_model_id: str = "amazon.titan-embed-text-v1",
                 summary_model_id: str = "anthropic.claude-instant-v1",  # Use a faster/cheaper model
                 max_workers: int = 16):  # Increase default workers
        """Initialize the book summary generator."""
        self.bucket_name = bucket_name
        self.embedding_model_id = embedding_model_id
        self.summary_model_id = summary_model_id
        self.max_workers = max_workers
        self.aws_profile = aws_profile
        
        # Initialize AWS clients for main process
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
            self.bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')
        else:
            self.s3_client = boto3.client('s3')
            self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    
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
                logger.info("No books found in S3 bucket")
                return []
                
        except ClientError as e:
            logger.error(f"Error listing books: {e}")
            return []
    
    def download_book_from_s3(self, s3_key: str) -> str:
        """Download a book from S3 and return its content."""
        return self._download_book_from_s3(self.s3_client, s3_key)
    
    def _download_book_from_s3(self, s3_client, s3_key: str) -> str:
        """Download a book from S3 and return its content."""
        try:
            logger.info(f"Downloading {s3_key} from S3...")
            
            response = s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode('utf-8')
            logger.info(f"Downloaded {len(content)} characters from {s3_key}")
            
            return content
            
        except ClientError as e:
            logger.error(f"Error downloading {s3_key}: {e}")
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
        return self._generate_chunk_summary(self.bedrock_client, chunk, chunk_index, total_chunks)
    
    def _generate_chunk_summary(self, bedrock_client, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Generate a summary for a text chunk with more detail."""
        try:
            prompt = f"""Analyze section {chunk_index} of {total_chunks} from a book and provide a detailed summary that captures:

1. Key plot developments and events
2. Important character interactions and developments
3. Significant themes, motifs, or symbols
4. Setting details and atmosphere
5. Any notable dialogue or quotes
6. How this section contributes to the overall story

Write a rich, detailed summary that helps someone understand what happens in this section and why it matters. 
Start directly with the content - no introductory phrases like "This section explores" or "Based on the analysis."

Text section:
{chunk}

Summary:"""

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            summary = response_body['content'][0]['text'].strip()
            
            return summary
            
        except ClientError as e:
            logger.error(f"Error generating chunk summary: {e}")
            return None
    
    def generate_book_summary(self, chunk_summaries: List[str], book_title: str, author: str) -> Dict[str, str]:
        """Generate multiple types of book summaries for better semantic matching."""
        return self._generate_book_summary(self.bedrock_client, chunk_summaries, book_title, author)
    
    def _generate_book_summary(self, bedrock_client, chunk_summaries: List[str], book_title: str, author: str) -> Dict[str, str]:
        """Generate multiple types of book summaries for better semantic matching."""
        try:
            combined_summaries = "\n\n".join(chunk_summaries)
            
            # Generate comprehensive plot summary
            plot_prompt = f"""Create a comprehensive plot summary for "{book_title}" by {author} based on these section summaries. Include:

1. Complete plot overview with all major events
2. Character arcs and relationships
3. Key conflicts and resolutions
4. Important themes and messages
5. Setting and historical context
6. Notable quotes or memorable moments

Write a detailed, engaging summary that captures the full scope and impact of the story. 
Aim for 8-12 sentences that would help someone understand the complete book.
Start directly with the plot - no introductory phrases like "This book explores" or "Based on the summaries."

Section summaries:
{combined_summaries}

Plot summary:"""

            plot_request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "messages": [
                    {
                        "role": "user",
                        "content": plot_prompt
                    }
                ]
            }
            
            plot_response = bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(plot_request_body)
            )
            
            plot_response_body = json.loads(plot_response['body'].read())
            plot_summary = plot_response_body['content'][0]['text'].strip()
            
            # Generate thematic analysis
            thematic_prompt = f"""Analyze the major themes and motifs of "{book_title}" by {author} based on these section summaries. Consider:

1. Central themes and their development throughout the story
2. Symbolic elements and their meanings
3. Social, political, or philosophical commentary
4. Character motivations and their thematic significance
5. The author's message or worldview
6. Historical or cultural context that shapes the themes

Write a detailed thematic analysis that explores the deeper meanings and significance of this work.
Start directly with the themes - no introductory phrases like "This work explores" or "The analysis reveals."

Section summaries:
{combined_summaries}

Thematic analysis:"""

            thematic_request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "messages": [
                    {
                        "role": "user",
                        "content": thematic_prompt
                    }
                ]
            }
            
            thematic_response = bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(thematic_request_body)
            )
            
            thematic_response_body = json.loads(thematic_response['body'].read())
            thematic_analysis = thematic_response_body['content'][0]['text'].strip()
            
            # Generate character summary
            character_prompt = f"""Provide a comprehensive character analysis for "{book_title}" by {author} based on these section summaries. Include:

1. Main characters and their key traits
2. Character relationships and dynamics
3. Character development and arcs throughout the story
4. Supporting characters and their roles
5. Character motivations and conflicts
6. How characters embody or challenge themes

Write a detailed character summary that helps readers understand the people in this story.
Start directly with the characters - no introductory phrases like "The characters in this story" or "Based on the analysis."

Section summaries:
{combined_summaries}

Character summary:"""

            character_request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "messages": [
                    {
                        "role": "user",
                        "content": character_prompt
                    }
                ]
            }
            
            character_response = bedrock_client.invoke_model(
                modelId=self.summary_model_id,
                body=json.dumps(character_request_body)
            )
            
            character_response_body = json.loads(character_response['body'].read())
            character_summary = character_response_body['content'][0]['text'].strip()
            
            return {
                'plot_summary': plot_summary,
                'thematic_analysis': thematic_analysis,
                'character_summary': character_summary
            }
            
        except ClientError as e:
            logger.error(f"Error generating book summary: {e}")
            return None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Amazon Bedrock."""
        return self._generate_embedding(self.bedrock_client, text)
    
    def _generate_embedding(self, bedrock_client, text: str) -> List[float]:
        """Generate embedding using Amazon Bedrock."""
        try:
            request_body = {
                "inputText": text
            }
            
            response = bedrock_client.invoke_model(
                modelId=self.embedding_model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body['embedding']
            
            return embedding
            
        except ClientError as e:
            logger.error(f"Error generating embedding: {e}")
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
    
    def extract_title_and_author(self, s3_key: str, cleaned_text: str) -> (str, str):
        """Extract clean book title and author from S3 key and text, using '__by__' separator if present."""
        base = os.path.basename(s3_key).replace('.txt', '')
        if '__by__' in base:
            title, author = base.split('__by__', 1)
            title = title.replace('-', ' ').strip()
            author = author.replace('-', ' ').strip()
        else:
            # fallback: previous logic
            base = re.sub(r',\s*$', '', base)
            parts = re.split(r' by |,', base)
            title = parts[0].strip()
            author = self.extract_author_from_text(cleaned_text)
        return title, author
    
    def upload_embeddings_to_s3(self, book_title: str, embeddings: dict, s3_client=None):
        """Upload embeddings to S3 under the embeddings/ folder as a JSON file."""
        import io
        s3_key = f"embeddings/{book_title}.json"
        try:
            embeddings_json = json.dumps(embeddings)
            if s3_client is None:
                s3_client = self.s3_client
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=embeddings_json.encode('utf-8'),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            logger.info(f"Uploaded embeddings to S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to upload embeddings to S3 for {book_title}: {e}")
    
    def process_single_book(self, s3_key: str, chunk_size: int = 8000, overlap: int = 500) -> Optional[Dict]:
        """Process a single book and return the book data for bulk indexing."""
        #book_title = os.path.basename(s3_key).replace('.txt', '')
        #logger.info(f"Processing book: {book_title}")
        try:
            # Initialize AWS clients in this process (to avoid pickling issues)
            if hasattr(self, 'aws_profile') and self.aws_profile:
                session = boto3.Session(profile_name=self.aws_profile)
                s3_client = session.client('s3')
                bedrock_client = session.client('bedrock-runtime', region_name='us-east-1')
            else:
                s3_client = boto3.client('s3')
                bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            # Download and clean book
            text_content = self._download_book_from_s3(s3_client, s3_key)
            if not text_content:
                return None
            
            cleaned_text = self.clean_text(text_content)
            logger.info(f"Cleaned text length: {len(cleaned_text)} characters")
            book_title, author = self.extract_title_and_author(s3_key, cleaned_text)
            logger.info(f"Extracted title: {book_title}")
            logger.info(f"Extracted author: {author}")
            
            # Generate chunk summaries
            chunks = self.chunk_text_large(cleaned_text, chunk_size, overlap)
            logger.info(f"Created {len(chunks)} large text chunks")
            
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Generating summary for chunk {i+1}/{len(chunks)}...")
                
                summary = self._generate_chunk_summary(bedrock_client, chunk, i+1, len(chunks))
                if summary:
                    chunk_summaries.append(summary)
                
                time.sleep(0.5)  # Rate limiting
            
            logger.info(f"Generated {len(chunk_summaries)} chunk summaries")
            
            # Generate genre summary
            genre_prompt = f"""Identify the primary literary genre(s) for \"{book_title}\" by {author} based on the text and section summaries. Respond with a short phrase."""
            genre_summary = self._generate_chunk_summary(bedrock_client, genre_prompt, 1, 1)
            logger.info(f"Generated genre summary: {genre_summary}")
            
            # Generate multiple types of book summaries
            logger.info("Generating book summaries...")
            book_summaries = self._generate_book_summary(bedrock_client, chunk_summaries, book_title, author)
            if not book_summaries:
                logger.error("Failed to generate book summaries")
                return None
            
            # Create combined summary for primary embedding
            combined_summary = f"{book_summaries['plot_summary']}\n\n{book_summaries['thematic_analysis']}\n\n{book_summaries['character_summary']}\n\n{genre_summary}"
            
            # Generate embeddings for each summary type
            logger.info("Generating multiple embeddings...")
            embeddings = {}
            for summary_type, summary_text in list(book_summaries.items()) + [("genre", genre_summary)]:
                logger.info(f"Generating embedding for {summary_type}")
                embedding = self._generate_embedding(bedrock_client, summary_text)
                if embedding:
                    embeddings[f"{summary_type}_embedding"] = embedding
                else:
                    logger.error(f"Failed to generate embedding for {summary_type}")
                time.sleep(0.5)  # Rate limiting
            
            # Generate combined embedding
            logger.info("Generating combined embedding...")
            combined_embedding = self._generate_embedding(bedrock_client, combined_summary)
            if combined_embedding:
                embeddings["combined_embedding"] = combined_embedding
            else:
                logger.error("Failed to generate combined embedding")
            
            # Prepare book data for OpenSearch
            book_data = {
                'book_title': book_title,
                'author': author,
                'plot_summary': book_summaries['plot_summary'],
                'thematic_analysis': book_summaries['thematic_analysis'],
                'character_summary': book_summaries['character_summary'],
                'genre': genre_summary,
                'combined_summary': combined_summary,
                'total_chunks': len(chunks),
                'chunk_summaries': chunk_summaries,
                'plot_embedding': embeddings.get('plot_summary_embedding', []),
                'thematic_embedding': embeddings.get('thematic_analysis_embedding', []),
                'character_embedding': embeddings.get('character_summary_embedding', []),
                'genre_embedding': embeddings.get('genre_embedding', []),
                'combined_embedding': embeddings.get('combined_embedding', []),
                'embedding_model_id': self.embedding_model_id,
                'summary_model_id': self.summary_model_id,
                'generated_at': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Upload embeddings to S3 under embeddings/ folder
            self.upload_embeddings_to_s3(book_title, embeddings, s3_client)

            logger.info(f"Successfully processed book: {book_title}")
            return book_data
            
        except Exception as e:
            logger.error(f"Error processing book {book_title}: {e}")
            return None
    
    def process_books_parallel(self, book_keys: List[str], chunk_size: int = 8000, 
                             overlap: int = 500, batch_size: int = 100) -> List[Dict]:
        """Process books and return results for bulk indexing."""
        logger.info(f"Starting processing of {len(book_keys)} books with {self.max_workers} workers")
        
        successful_books = []
        failed_books = []
        
        # Process books
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all book processing tasks
            future_to_book = {
                executor.submit(self.process_single_book, book_key, chunk_size, overlap): book_key 
                for book_key in book_keys
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_book):
                book_key = future_to_book[future]
                book_title = os.path.basename(book_key).replace('.txt', '')
                
                try:
                    book_data = future.result()
                    if book_data:
                        successful_books.append(book_data)
                        logger.info(f"✓ Completed: {book_title}")
                    else:
                        failed_books.append(book_key)
                        logger.error(f"✗ Failed: {book_title}")
                except Exception as e:
                    failed_books.append(book_key)
                    logger.error(f"✗ Exception processing {book_title}: {e}")
        
        logger.info(f"Processing complete!")
        logger.info(f"Successful: {len(successful_books)} books")
        logger.info(f"Failed: {len(failed_books)} books")
        
        if failed_books:
            logger.info("Failed books:")
            for book_key in failed_books:
                logger.info(f"  - {os.path.basename(book_key)}")
        
        return successful_books
    
    def bulk_index_to_opensearch(self, books_data: List[Dict], opensearch_endpoint: str, 
                                index_name: str = "book-summaries") -> bool:
        """Bulk index books to OpenSearch using the bulk API."""
        try:
            logger.info(f"Bulk indexing {len(books_data)} books to OpenSearch...")
            
            # Create OpenSearch client
            client = OpenSearch(
                hosts=[{'host': opensearch_endpoint.replace('https://', ''), 'port': 443}],
                http_auth=('admin', 'admin'),  # Replace with your auth
                use_ssl=True,
                verify_certs=False,
                timeout=30
            )
            
            # Prepare documents for bulk indexing
            def generate_documents():
                for book_data in books_data:
                    # Create a unique ID for the book
                    book_id = re.sub(r'[^\w\s-]', '', book_data['book_title']).strip()
                    book_id = re.sub(r'[-\s]+', '-', book_id).lower()
                    
                    yield {
                        "_index": index_name,
                        "_id": book_id,
                        "_source": book_data
                    }
            
            # Perform bulk indexing
            success_count, errors = bulk(client, generate_documents(), chunk_size=100, request_timeout=60)
            
            logger.info(f"Bulk indexing complete!")
            logger.info(f"Successfully indexed: {success_count} documents")
            
            if errors:
                logger.error(f"Errors during bulk indexing: {len(errors)}")
                for error in errors[:5]:  # Show first 5 errors
                    logger.error(f"  - {error}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during bulk indexing: {e}")
            return False
    
    def save_checkpoint(self, processed_books: List[str], checkpoint_file: str = "processed_books.pkl"):
        """Save checkpoint of processed books."""
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(processed_books, f)
            logger.info(f"Checkpoint saved: {len(processed_books)} books")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
    
    def load_checkpoint(self, checkpoint_file: str = "processed_books.pkl") -> List[str]:
        """Load checkpoint of processed books."""
        try:
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, 'rb') as f:
                    processed_books = pickle.load(f)
                logger.info(f"Checkpoint loaded: {len(processed_books)} books")
                return processed_books
            else:
                logger.info("No checkpoint file found")
                return []
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return []
    
    def process_all_books_scalable(self, chunk_size: int = 8000, overlap: int = 500, 
                                 max_books: int = None, batch_size: int = 100,
                                 opensearch_endpoint: str = None, 
                                 use_checkpoint: bool = True) -> bool:
        """Process all books with scalable processing and bulk indexing."""
        logger.info(f"Starting scalable book processing for bucket: {self.bucket_name}")
        logger.info(f"Max workers: {self.max_workers}")
        logger.info(f"Batch size: {batch_size}")
        logger.info("=" * 70)
        
        # Get all book keys
        book_keys = self.list_books_in_s3()
        if not book_keys:
            logger.error("No books found to process")
            return False
        
        logger.info(f"Found {len(book_keys)} books to process")
        
        # Apply max_books limit
        if max_books is not None:
            book_keys = book_keys[:max_books]
            logger.info(f"Limiting to {max_books} books")
        
        # Load checkpoint if enabled
        processed_books = []
        if use_checkpoint:
            processed_books = self.load_checkpoint()
            # Filter out already processed books
            book_keys = [key for key in book_keys if key not in processed_books]
            logger.info(f"After checkpoint: {len(book_keys)} books remaining")
        
        if not book_keys:
            logger.info("No new books to process")
            return True
        
        # Process books in batches
        all_successful_books = []
        for i in range(0, len(book_keys), batch_size):
            batch_keys = book_keys[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(book_keys) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_keys)} books)")
            
            # Process batch
            batch_results = self.process_books_parallel(batch_keys, chunk_size, overlap, batch_size)
            all_successful_books.extend(batch_results)
            
            # Update checkpoint
            if use_checkpoint:
                processed_books.extend(batch_keys)
                self.save_checkpoint(processed_books)
            
            # Bulk index to OpenSearch if endpoint provided
            if opensearch_endpoint and batch_results:
                logger.info(f"Bulk indexing batch {batch_num} to OpenSearch...")
                success = self.bulk_index_to_opensearch(batch_results, opensearch_endpoint)
                if not success:
                    logger.error(f"Failed to bulk index batch {batch_num}")
            
            logger.info(f"Batch {batch_num} complete. Total processed: {len(all_successful_books)}")
        
        logger.info(f"Scalable processing complete!")
        logger.info(f"Total successful books: {len(all_successful_books)}")
        
        return True

def main():
    """Main function to run the scalable book summary generator."""
    parser = argparse.ArgumentParser(description='Generate book summaries with processing and bulk indexing')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--embedding-model', default='amazon.titan-embed-text-v1', 
                       help='Bedrock model ID for embeddings')
    parser.add_argument('--summary-model', default='anthropic.claude-instant-v1', 
                       help='Bedrock model ID for summarization (default: fast model)')
    parser.add_argument('--chunk-size', type=int, default=16000, 
                       help='Size of text chunks for summarization (default: 16000)')
    parser.add_argument('--overlap', type=int, default=200, 
                       help='Overlap between chunks (default: 200)')
    parser.add_argument('--max-books', type=int, default=None, 
                       help='Maximum number of books to process (default: all)')
    parser.add_argument('--max-workers', type=int, default=16, 
                       help='Maximum number of parallel workers (default: 16)')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--opensearch-endpoint', 
                       help='OpenSearch endpoint for bulk indexing')
    parser.add_argument('--no-checkpoint', action='store_true', 
                       help='Disable checkpointing')
    
    args = parser.parse_args()
    
    generator = BookSummaryGenerator(
        args.bucket, 
        args.profile, 
        args.embedding_model, 
        args.summary_model,
        args.max_workers
    )
    
    success = generator.process_all_books_scalable(
        args.chunk_size,
        args.overlap,
        args.max_books,
        args.batch_size,
        args.opensearch_endpoint,
        not args.no_checkpoint
    )
    
    if success:
        logger.info("Scalable book processing completed successfully!")
    else:
        logger.error("Scalable book processing failed!")
        exit(1)

if __name__ == "__main__":
    main() 