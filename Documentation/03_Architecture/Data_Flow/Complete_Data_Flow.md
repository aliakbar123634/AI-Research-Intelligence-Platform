# Complete Data Flow
## AI Research & Intelligence Platform

## 1. Overview

This document describes the end-to-end data flow of the AI Research & Intelligence Platform, from research question submission to final research report generation.

The system uses asynchronous background processing to handle research tasks without keeping the user waiting for the entire workflow to finish.

The main technologies involved are:

- React (Vite) — Frontend
- FastAPI — Backend API
- PostgreSQL — Application database
- Celery — Background task processing
- Redis — Message broker
- LangGraph — AI workflow orchestration
- RAG — Document-based retrieval
- External Services — LLM, Web Search and Embedding Model

## 2. Main Research Workflow

### Step 1 — User Submits Research Request

The user enters a research question through the React frontend.

The user may also select previously uploaded documents or provide documents for research.

Example:

"Analyze the latest AI agent frameworks and compare their architecture, features and limitations."

### Step 2 — Frontend Sends API Request

React sends an HTTP POST request to FastAPI.

**Endpoint:**

`POST /api/v1/research`

The request contains:

- Research question
- Optional document IDs
- Research configuration (if applicable)

### Step 3 — FastAPI Creates Research Job

FastAPI performs input validation and creates a research job in PostgreSQL.

Initial job status:

`pending`

The database generates a unique research job ID.

FastAPI then dispatches the background task to Celery.

The API returns:

- HTTP Status: `202 Accepted`
- Research Job ID
- Current Job Status

The frontend does not wait for the complete AI workflow.

### Step 4 — Celery and Redis Background Processing

FastAPI dispatches the task to Celery.

Redis acts as the message broker and temporarily holds queued task messages.

The Celery worker consumes the task and starts executing the research workflow.

Responsibilities:

- Task queuing
- Background execution
- Task retries
- Error handling
- Job status updates

### Step 5 — LangGraph Research Workflow

The background worker invokes the LangGraph workflow.

LangGraph manages the execution and coordination of the AI agents.

The workflow consists of the following agents:

**Planner Agent**
- Understands the research question.
- Breaks the question into subtasks.
- Creates a research plan.
- Determines which tools are required.

**Research Agent**
- Searches external web sources.
- Collects relevant information.
- Extracts useful research findings.
- Records source references.

**RAG Agent**
- Retrieves relevant document chunks.
- Uses vector similarity search.
- Provides document context to the research workflow.

**Analyst Agent**
- Analyzes collected information.
- Combines web research and document context.
- Identifies important findings.
- Organizes research insights.

**Critic Agent**
- Reviews the research output.
- Checks evidence and source relevance.
- Identifies missing information.
- Evaluates completeness and quality.
- Can request additional research when necessary.

**Writer Agent**
- Generates the final structured research report.
- Organizes findings into sections.
- Includes relevant citations and references.
- Produces Markdown or HTML output.

### Step 6 — External Services Interaction

During workflow execution, agents interact with external services.

**LLM Provider**
- Agent reasoning
- Research analysis
- Critic review
- Report generation

**Web Search Service**
- Searches the internet.
- Finds relevant sources.
- Returns search results and URLs.

**Embedding Model**
- Converts research queries into vectors.
- Supports semantic retrieval from document chunks.

**Observability Service**
- Records traces and workflow execution information.
- Helps investigate errors and performance.

### Step 7 — Database Updates and Report Storage

After successful workflow execution, the system saves the final results in PostgreSQL.

Stored information includes:

- Research job information
- Final research report
- Source references
- Agent execution records
- Evaluation results (when enabled)
- Relevant workflow metadata

The research job status is updated to:

`completed`

### Step 8 — Frontend Retrieves Research Status

React periodically checks the research job status through FastAPI.

**Endpoint:**

`GET /api/v1/research/{research_id}`

The API retrieves the latest job status and available research results from PostgreSQL.

Possible statuses:

- `pending`
- `running`
- `completed`
- `failed`

### Step 9 — Final Research Report Display

When the job is completed, FastAPI returns the research report to the frontend.

React displays:

- Research summary
- Key findings
- Detailed analysis
- Sources and references
- Final structured report

The user can view the completed research report.

## 3. Document Upload and RAG Integration

The document upload and RAG ingestion process is designed as a separate workflow.

Documents are processed before they are used for research retrieval.

The ingestion pipeline consists of:

1. User uploads a document.
2. FastAPI validates the uploaded file.
3. Document parser extracts text.
4. Extracted text is divided into smaller chunks.
5. Embedding model generates vector embeddings.
6. Document chunks and embeddings are stored in PostgreSQL using pgvector.
7. During research, the RAG service retrieves relevant chunks.
8. Retrieved context is passed to the RAG Agent.

The main research workflow can use the retrieved document context together with external web research.

For the complete ingestion design, refer to:

`RAG_Ingestion_Flow.png`

## 4. Communication Between Components

| From | To | Communication |
|---|---|---|
| React | FastAPI | HTTP API Request |
| FastAPI | PostgreSQL | Database Operations |
| FastAPI | Celery | Task Dispatch |
| Celery | Redis | Queue Message |
| Redis | Celery Worker | Task Consumption |
| Celery Worker | LangGraph | Workflow Invocation |
| LangGraph | LLM Provider | Model Requests |
| Research Agent | Web Search | External API |
| RAG Agent | RAG Service | Retrieval Request |
| RAG Service | PostgreSQL + pgvector | Vector Search |
| LangGraph | PostgreSQL | Save Results |
| React | FastAPI | Job Status Polling |

## 5. Research Job Status Lifecycle

The research job follows a status lifecycle.

### Pending

The research job has been created and is waiting for background execution.

### Running

The Celery worker has started executing the research workflow.

### Completed

The workflow has successfully generated and saved the final research report.

### Failed

The workflow has encountered an unrecoverable error and the job has been marked as failed.

## 6. Error Handling and Recovery

The system should handle failures at different stages.

Examples:

- Invalid research request
- Background task execution failure
- External API timeout
- LLM provider error
- Document retrieval failure
- Agent execution failure
- Database operation failure

Expected behaviour:

- Validate user input before task dispatch.
- Record meaningful error information.
- Use controlled retries for retryable failures.
- Update job status when execution fails.
- Preserve useful execution logs and traces.
- Avoid silently marking unsuccessful jobs as completed.

## 7. Data Flow Summary

The complete main research flow:

**User → React → FastAPI → PostgreSQL → Celery → Redis → Background Worker → LangGraph → AI Agents → External Services / RAG → PostgreSQL → FastAPI → React → Final Research Report**

The document ingestion flow:

**Document Upload → Validation → Text Extraction → Chunking → Embeddings → PostgreSQL + pgvector → Vector Retrieval → RAG Agent**

Both workflows are connected through the RAG retrieval service.

## 8. Related Architecture Visuals

| Visual | Filename |
|---|---|
| Complete Research Workflow | `Complete_Data_Flow.png` |
| RAG Ingestion and Retrieval | `RAG_Ingestion_Flow.png` |

## 9. Architecture Principle

The system uses asynchronous processing for long-running research tasks.

FastAPI handles user requests and API communication, while Celery workers execute background tasks.

LangGraph coordinates AI agents, and PostgreSQL stores application data, research results and vector embeddings through pgvector.

The separate document ingestion workflow provides relevant document context to the main research workflow through RAG.

This separation improves modularity and makes the system easier to maintain, test and extend.