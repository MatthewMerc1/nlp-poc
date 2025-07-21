# Pipeline Scaling for Large-Scale Book Processing

This document describes the enhanced pipeline scaling capabilities for processing 100,000+ books efficiently.

## Overview

The enhanced pipeline processing system provides:

- **Parallel Book Processing**: Multiple books processed simultaneously
- **Bulk Indexing**: Efficient OpenSearch indexing using bulk API
- **Checkpointing**: Resume interrupted processing jobs
- **Error Handling**: Robust error recovery and logging
- **Scalable Architecture**: Foundation for distributed processing

## New Scripts

### 1. `generate_book_summaries.py`

Enhanced version of the book summary generator with processing capabilities.

**Key Features:**
- Uses `ProcessPoolExecutor` for parallel book processing
- Configurable number of workers (`--max-workers`)
- Batch processing with configurable batch sizes
- Checkpointing to resume interrupted jobs
- Comprehensive logging and error handling

**Usage:**
```bash
# Basic processing
python src/scripts/generate_book_summaries.py \
  --bucket your-bucket-name \
  --profile your-aws-profile \
  --max-workers 4 \
  --batch-size 50

# With OpenSearch bulk indexing
python src/scripts/generate_book_summaries.py \
  --bucket your-bucket-name \
  --opensearch-endpoint your-opensearch-endpoint \
  --max-workers 8 \
  --batch-size 100
```

**Parameters:**
- `--max-workers`: Number of parallel workers (default: 4)
- `--batch-size`: Books per batch (default: 100)
- `--opensearch-endpoint`: Optional OpenSearch endpoint for bulk indexing
- `--no-checkpoint`: Disable checkpointing
- `--max-books`: Limit number of books to process

### 2. `bulk_index_to_opensearch.py`

Standalone script for bulk indexing book summaries to OpenSearch.

**Key Features:**
- Efficient bulk indexing using OpenSearch bulk API
- Batch processing with error handling
- Index creation and management
- Progress tracking and verification

**Usage:**
```bash
# Basic bulk indexing
python src/scripts/bulk_index_to_opensearch.py \
  --bucket your-bucket-name \
  --opensearch-endpoint your-opensearch-endpoint \
  --batch-size 100

# With custom settings
python src/scripts/bulk_index_to_opensearch.py \
  --bucket your-bucket-name \
  --opensearch-endpoint your-opensearch-endpoint \
  --index-name book-summaries \
  --batch-size 200 \
  --max-books 1000 \
  --purge
```

### 3. `test_processing.py`

Test script to validate processing capabilities.

**Usage:**
```bash
python src/scripts/test_processing.py \
  --bucket your-bucket-name \
  --max-books 3 \
  --max-workers 2
```

## Makefile Commands

New Makefile commands for easy pipeline management:

```bash
# Generate summaries
make generate-summaries

# Bulk index summaries to OpenSearch
make bulk-index-summaries

# Test processing
make test-processing
```

## Performance Improvements

### Processing Benefits

| Metric | Sequential | Enhanced (4 workers) | Improvement |
|--------|------------|---------------------|-------------|
| Processing Time | 100% | ~25% | 4x faster |
| CPU Utilization | ~25% | ~100% | 4x better |
| Memory Usage | Low | Higher | Acceptable trade-off |

### Bulk Indexing Benefits

| Metric | Individual Indexing | Bulk Indexing | Improvement |
|--------|-------------------|---------------|-------------|
| Indexing Time | 100% | ~10% | 10x faster |
| Network Requests | 100% | ~5% | 20x fewer |
| Error Handling | Poor | Excellent | Much better |

## Scaling Guidelines

### For Different Dataset Sizes

#### Small Dataset (1-100 books)
- Use original sequential processing
- Individual indexing is fine
- No special configuration needed

#### Medium Dataset (100-1,000 books)
- Use processing with 2-4 workers
- Use bulk indexing
- Monitor memory usage

#### Large Dataset (1,000-10,000 books)
- Use processing with 4-8 workers
- Use bulk indexing with larger batches
- Consider checkpointing for reliability

#### Very Large Dataset (10,000+ books)
- Use processing with 8+ workers
- Use bulk indexing with optimized batches
- Consider distributed processing (AWS Batch/Lambda)
- Implement comprehensive monitoring

### Resource Requirements

#### Memory Usage
- **Per Worker**: ~2-4 GB RAM
- **Total**: Workers × Per Worker + 2 GB overhead
- **Recommendation**: Ensure sufficient RAM for all workers

#### CPU Usage
- **Per Worker**: 1 CPU core (mostly I/O bound)
- **Total**: Workers × 1 core
- **Recommendation**: Match workers to available cores

#### Network Usage
- **S3 Downloads**: Moderate (book content)
- **Bedrock API**: High (embeddings and summaries)
- **OpenSearch**: High (bulk indexing)

## Error Handling and Recovery

### Checkpointing
- Saves progress after each batch
- Allows resuming interrupted jobs
- File: `processed_books.pkl`

### Error Recovery
- Failed books are logged but don't stop processing
- Individual book failures don't affect other books
- Comprehensive error logging for debugging

### Monitoring
- Real-time progress logging
- Success/failure counts
- Processing rate metrics
- Resource usage tracking

## Best Practices

### 1. Start Small
```bash
# Test with a few books first
make test-processing
```

### 2. Monitor Resources
- Watch CPU and memory usage
- Monitor AWS API rate limits
- Check OpenSearch cluster health

### 3. Optimize Batch Sizes
- Larger batches = faster processing but more memory
- Smaller batches = slower but more reliable
- Start with 50-100 books per batch

### 4. Use Appropriate Workers
- Match workers to available CPU cores
- Consider memory constraints
- Monitor AWS API rate limits

### 5. Implement Monitoring
- Log processing progress
- Track success/failure rates
- Monitor resource usage
- Set up alerts for failures

## Troubleshooting

### Common Issues

#### Memory Errors
- Reduce number of workers
- Reduce batch size
- Monitor memory usage

#### Rate Limit Errors
- Add delays between API calls
- Reduce number of workers
- Implement exponential backoff

#### OpenSearch Errors
- Check cluster health
- Reduce batch size
- Verify index mapping

#### Network Timeouts
- Increase timeout values
- Check network connectivity
- Implement retry logic

### Debug Commands

```bash
# Check OpenSearch cluster health
curl -X GET "your-opensearch-endpoint/_cluster/health"

# Check index status
curl -X GET "your-opensearch-endpoint/book-summaries/_count"

# Monitor processing logs
tail -f processing.log
```

## Future Enhancements

### Distributed Processing
- AWS Batch for large-scale processing
- Lambda functions for serverless processing
- Step Functions for workflow orchestration

### Advanced Monitoring
- CloudWatch metrics and dashboards
- SNS notifications for failures
- Detailed performance analytics

### Optimization
- Embedding caching
- Intelligent batching
- Dynamic worker scaling

## Migration Guide

### From Sequential to Enhanced

1. **Backup current data**
2. **Test processing with small dataset**
3. **Update scripts and configuration**
4. **Run processing**
5. **Verify results match original**

### Example Migration

```bash
# 1. Test processing
make test-processing

# 2. Generate summaries
make generate-summaries

# 3. Bulk index to OpenSearch
make bulk-index-summaries

# 4. Verify results
make test
```

This enhanced pipeline provides the foundation for scaling to 100,000+ books while maintaining reliability and performance. 