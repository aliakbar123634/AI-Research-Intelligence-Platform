# External Services Architecture
## AI Research & Intelligence Platform

## 1. Overview

The External Services Architecture defines how the platform integrates with external APIs, AI model providers, document processing libraries, and observability services.

These integrations support research generation, document understanding, semantic retrieval, and AI workflow monitoring.

## 2. Confirmed Technology Stack

| Component | Selected Technology | Responsibility |
|---|---|---|
| LLM Provider | Groq API | AI model inference |
| Embedding Model | Local Sentence Transformers | Generate vector embeddings |
| Web Search | Tavily API | Retrieve web research results |
| Document Parsing | PyMuPDF + python-docx | Extract text from PDF and DOCX files |
| Observability | LangSmith | Trace and debug AI workflows |

## 3. Integration Responsibilities

### 3.1 LLM Provider — Groq API

- Provides access to supported language models.
- Used by LangGraph agents for reasoning and response generation.
- Supports research analysis, criticism, and report generation.

### 3.2 Embedding Model — Sentence Transformers

- Generates embeddings for document chunks.
- Generates embeddings for user research queries.
- Supports semantic similarity search through pgvector.
- Runs locally rather than requiring a hosted embedding API.

### 3.3 Web Search — Tavily API

- Performs web searches for research questions.
- Returns relevant search results and source URLs.
- Supplies external research information to the Research Agent.

### 3.4 Document Parsing — PyMuPDF and python-docx

- PyMuPDF extracts text from PDF documents.
- python-docx extracts text from DOCX documents.
- Extracted text is passed to the RAG ingestion pipeline.
- TXT files can be handled through standard Python file processing.

### 3.5 Observability — LangSmith

- Traces LangGraph execution.
- Helps inspect agent execution steps.
- Supports debugging of LLM and workflow operations.
- Helps identify errors and performance bottlenecks.

## 4. Integration Architecture

The integrations connect to the platform through their respective internal services:

- LangGraph communicates with the LLM provider.
- RAG Service communicates with the local embedding model and PostgreSQL + pgvector.
- Research Agent communicates with Tavily.
- Document Processing Service uses the document parsing libraries.
- LangGraph execution is traced through LangSmith.

## 5. Security Considerations

- API credentials are stored in backend environment variables.
- External API keys are never exposed to the frontend.
- API requests use appropriate timeout and error handling.
- External search results are treated as untrusted content.
- LLM responses are validated before being used by downstream components.
- External integrations follow the principle of least privilege.

## 6. Reliability Considerations

- Handle external API failures gracefully.
- Implement timeouts for network requests.
- Log integration errors.
- Consider retry policies for temporary failures.
- Avoid unnecessary repeated API calls.

## 7. Architecture Decisions

| Decision | Status |
|---|---|
| Groq API for LLM inference | Confirmed |
| Local Sentence Transformers for embeddings | Confirmed |
| Tavily API for web search | Confirmed |
| PyMuPDF + python-docx for document parsing | Confirmed |
| LangSmith for observability | Confirmed |

## 8. Future Implementation Considerations

- Select the exact Groq model.
- Select the Sentence Transformers model and embedding dimensions.
- Configure Tavily API credentials.
- Implement document validation and extraction error handling.
- Configure LangSmith tracing and project settings.
- Verify API quotas, service limits, and deployment compatibility.