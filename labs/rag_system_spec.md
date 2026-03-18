# Lab 01: RAG System Specification (Legal Documents)

## Context (Framing)
I am an AI Engineer & PM building a high-stakes RAG system for legal departments. The system must process complex contracts and legal proceedings where precision is non-negotiable and hallucinations can have severe legal consequences.

## Input Data Schema
- **Source:** Multi-page PDF documents (20-100 pages).
- **Complexity:** Legal jargon, nested clauses, tables, and cross-references.
- **Volume:** Low to medium volume but high information density per page.

## Constraints & Advanced Pipeline
- **Security:** Data sovereignty and PII masking are mandatory.
- **Latency:** Must be optimized for professional use (near real-time retrieval).
- **Retrieval Strategy:**
    - **Chunking:** Semantic Chunking (breaking based on meaning/structure, not character count).
    - **Search:** Hybrid Search (Vector + Keyword/BM25).
    - **Reranking:** Post-retrieval ranking using a Cross-Encoder (e.g., Cohere or BGE-Reranker).
- **Tools:** Comparing LangChain (LangGraph) vs. LlamaIndex for this specific orchestration.

## Output Expected
1. **Architecture Diagram:** Mermaid.js flowchart of the pipeline.
2. **Comparison Table:** LangChain vs. LlamaIndex on 3 criteria: Ease of implementation of Semantic Chunking, Reranking native support, and Production-readiness (traceability).
3. **Draft Prompt:** A system prompt template for the final answer generation phase.
