#!/usr/bin/env python3
"""
Test script to validate book processing capabilities.
This script tests the book processing with a small sample.
"""

import argparse
import time
from generate_book_summaries import BookSummaryGenerator

def test_book_processing(bucket_name: str, aws_profile: str = None, 
                        max_books: int = 3, max_workers: int = 2):
    """Test book processing with a small number of books."""
    print(f"Testing book processing with {max_workers} workers")
    print(f"Processing up to {max_books} books")
    print("=" * 60)
    
    # Initialize generator
    generator = BookSummaryGenerator(
        bucket_name, 
        aws_profile, 
        max_workers=max_workers
    )
    
    # Get list of books
    book_keys = generator.list_books_in_s3()
    if not book_keys:
        print("No books found to process")
        return
    
    print(f"Found {len(book_keys)} books in S3")
    
    # Limit to test books
    test_books = book_keys[:max_books]
    print(f"Testing with {len(test_books)} books:")
    for book_key in test_books:
        print(f"  - {book_key}")
    
    # Time the processing
    start_time = time.time()
    
    # Process books
    successful_books = generator.process_books_parallel(
        test_books, 
        chunk_size=8000, 
        overlap=500, 
        batch_size=10
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print("\n" + "=" * 60)
    print("BOOK PROCESSING RESULTS")
    print("=" * 60)
    print(f"Total time: {processing_time:.2f} seconds")
    print(f"Books processed: {len(successful_books)}")
    print(f"Average time per book: {processing_time / len(successful_books):.2f} seconds")
    print(f"Processing rate: {len(successful_books) / processing_time:.2f} books/second")
    
    if successful_books:
        print(f"\nSuccessfully processed books:")
        for book_data in successful_books:
            print(f"  ✓ {book_data['book_title']} by {book_data['author']}")
    
    return successful_books

def main():
    """Main function to run the book processing test."""
    parser = argparse.ArgumentParser(description='Test book processing')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--max-books', type=int, default=3, help='Maximum number of books to test')
    parser.add_argument('--max-workers', type=int, default=2, help='Number of workers')
    
    args = parser.parse_args()
    
    print("BOOK PROCESSING TEST")
    print("=" * 60)
    
    successful_books = test_book_processing(
        args.bucket,
        args.profile,
        args.max_books,
        args.max_workers
    )
    
    if successful_books:
        print(f"\n✅ Test completed successfully! Processed {len(successful_books)} books.")
    else:
        print(f"\n❌ Test failed! No books were processed successfully.")
        exit(1)

if __name__ == "__main__":
    main() 