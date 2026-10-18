# Database Architecture
## AI Research & Intelligence Platform

## 1. Overview

The AI Research & Intelligence Platform uses PostgreSQL as its primary relational database and the pgvector extension for vector storage and similarity search.

The database layer is responsible for maintaining application data, research records, uploaded document metadata, document chunks, agent execution records, generated reports, evaluations, and user feedback.

The database architecture is designed to provide data consistency, reliable relationships, efficient retrieval, and support for the platform's RAG pipeline.

## 2. Database Technology Stack

| Component | Technology | Responsibility |
|---|---|---|
| Primary Database | PostgreSQL | Persistent application data |
| Vector Extension | pgvector | Embedding storage and similarity search |
| ORM | SQLAlchemy | Python database interaction |
| Database Migrations | Alembic | Schema versioning and migrations |
| Message Broker | Redis | Celery task communication |
| Background Processing | Celery | Asynchronous task execution |

*Note: SQLAlchemy and Alembic are proposed implementation choices and will be confirmed during development.*

## 3. Database Selection

PostgreSQL is selected because the platform requires:

- Relational data management.
- Foreign key constraints and referential integrity.
- Transaction support.
- Complex queries and joins.
- JSONB support for flexible structured data.
- Compatibility with pgvector.
- Support for indexing and query optimization.

## 4. Database Responsibilities

The database layer is responsible for:

- Storing user and research information.
- Maintaining research job records and statuses.
- Storing uploaded document metadata.
- Maintaining extracted document chunks.
- Storing vector embeddings through pgvector.
- Recording research sources.
- Maintaining agent execution records.
- Storing generated research reports.
- Maintaining evaluation and feedback records.

## 5. Proposed Database Entities

| Entity | Responsibility |
|---|---|
| User | User account information |
| Research | Research requests and associated report information |
| ResearchTask | Background research job records |
| Document | Uploaded document metadata |
| DocumentChunk | Extracted text chunks and associated embeddings |
| Source | Web research source information |
| AgentRun | Individual agent execution records |
| Evaluation | Research and AI evaluation results |
| Feedback | User feedback on generated reports |

These entities represent the initial domain model. Their final attributes, constraints, and relationships will be established during detailed database design.

## 6. Database Relationships

The database will use relational associations to connect users, research requests, documents, sources, and execution records.

The relationship design will specify:

- One-to-One relationships.
- One-to-Many relationships.
- Many-to-Many relationships where required.
- Primary key constraints.
- Foreign key constraints.
- Referential integrity rules.

The final Entity Relationship Diagram will document the confirmed table structure and relationships.

## 7. Entity Relationship Diagram

The project-specific ER diagram will be added after entity attributes, primary keys, foreign keys, and relationship cardinalities have been finalized.

![Database ER Diagram](diagrams/Database_ER_Diagram.png)

## 8. Database Relationship Diagram

The relationship diagram will provide a focused view of how the main application entities are connected.

![Database Relationship Diagram](diagrams/Database_Relationship_Diagram.png)

## 9. RAG Data Storage Architecture

The RAG subsystem uses the following document processing pipeline:

1. User uploads a document.
2. Backend validates the uploaded file.
3. Document text is extracted.
4. Extracted text is divided into chunks.
5. An embedding model generates vector embeddings.
6. Document chunks and their embeddings are stored.
7. pgvector supports similarity-based retrieval.
8. Retrieved chunks are provided to the RAG Agent as context.

![RAG Data Flow](diagrams/RAG_Data_Flow.png)

## 10. Vector Storage Design

The platform will use the pgvector extension to store document embeddings.

Each document chunk can be associated with a vector embedding representing its semantic content.

The retrieval process will:

- Convert the research query into an embedding.
- Perform vector similarity search.
- Retrieve relevant document chunks.
- Provide retrieved context to the RAG Agent.

The embedding model, vector dimensions, distance metric, and index strategy will be finalized during implementation design.

## 11. Database Storage Architecture

The storage architecture separates persistent relational records from background message delivery.

### PostgreSQL

Responsible for:

- Users and research records.
- Research task status.
- Document metadata.
- Document chunks.
- Sources and agent runs.
- Research reports.
- Evaluation and feedback records.

### pgvector

Responsible for:

- Document chunk embeddings.
- Vector similarity search.

### Redis

Responsible for:

- Celery message broker functionality.
- Background task message delivery.

Redis is not the primary persistent application database.

![Database Storage Architecture](diagrams/Database_Storage_Architecture.png)

## 12. Indexing Strategy

Indexes will be designed around actual query patterns.

Potential indexing areas include:

- Primary keys.
- Foreign keys where appropriate.
- Frequently queried status fields.
- Research ownership and creation dates.
- Document ownership and metadata.
- Vector similarity search.

The final index types and definitions will be selected after query patterns and data volume are understood.

## 13. Data Integrity

The database will enforce data integrity through:

- Primary key constraints.
- Foreign key constraints.
- Unique constraints.
- NOT NULL constraints.
- Appropriate data types.
- Transaction management.
- Referential integrity rules.

## 14. Database Architecture Decisions

| Decision | Selected Approach |
|---|---|
| Primary Database | PostgreSQL |
| Vector Search | pgvector |
| Application Data Storage | Relational Tables |
| Embedding Storage | PostgreSQL with pgvector |
| Background Message Broker | Redis |
| Background Task Framework | Celery |
| ORM | SQLAlchemy — Proposed |
| Database Migrations | Alembic — Proposed |

## 15. Future Implementation Considerations

The following details will be finalized before database implementation:

- Complete table definitions.
- Column names and data types.
- Primary and foreign keys.
- Relationship cardinalities.
- Cascading behavior.
- Vector dimensions and distance metric.
- Index definitions.
- Database migration strategy.
- Backup and recovery approach.

## 16. References

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Alembic Documentation: https://alembic.sqlalchemy.org/