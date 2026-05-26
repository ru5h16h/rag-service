# Chunking Strategy

This ADR records the chunking alternatives we are evaluating for the ingestion pipeline.
Phase 1 establishes the implementations and test coverage; Phase 2 will fill in retrieval metrics
once the retrieval path and gold Q&A set are available.

| Strategy | Chunk size | Overlap | Recall@5 (20 gold Q&A) | Avg chunk tokens | Notes |
|---|---:|---:|---|---|---|
| Fixed | 512 | 10% | TBD | TBD | Baseline |
| Fixed | 512 | 20% | TBD | TBD | Higher redundancy |
| Fixed | 1024 | 15% | TBD | TBD | Larger context window |
| Semantic | 512 | 15% | TBD | TBD | Slower, better boundaries |

## Decision Status

Pending. We will compare fixed-size and sentence-aware chunking after retrieval evaluation is wired
into the service.
