# Requirements

**Project:** Document Intelligence Platform (working title)
**Status:** Draft v0.1, Milestone 1 (2026-10-01)

An AI-powered platform where users upload, organize, search, summarize, compare, and question diverse documents. Every answer is grounded in retrieved evidence and backed by citations.

Priorities say what is essential. The milestone order in section 6 is the build order. If a hard deadline ever appears, drop Coulds first, then Shoulds.

| Priority | Meaning |
|---|---|
| M (Must) | The core product. Not done without it. |
| S (Should) | Strong features built on the core. |
| C (Could) | Extras, built last. |

## 1. Users

- **User:** registers, owns workspaces, uploads documents, asks questions.
- **Admin:** views system-wide metrics (Could).

## 2. Functional requirements

### Auth and users

| ID | Requirement | Pri |
|---|---|---|
| FR-01 | A visitor can register with an email and password. | M |
| FR-02 | A user can log in and log out. Sessions use JWT access tokens. | M |
| FR-03 | Passwords are stored only as salted hashes. | M |
| FR-04 | Every API route except register and login requires authentication. | M |
| FR-05 | A user can never read, search, or cite another user's workspaces, documents, conversations, or search history. | M |
| FR-06 | A user can view and edit their profile. | C |

### Workspaces

| ID | Requirement | Pri |
|---|---|---|
| FR-07 | A user can create, rename, and delete workspaces. | M |
| FR-08 | A workspace holds many documents, which are searchable together. | M |
| FR-09 | A question or search can be scoped to the whole workspace or to a chosen subset of its documents. | M |

### Documents and ingestion

| ID | Requirement | Pri |
|---|---|---|
| FR-10 | A user can upload PDF, DOCX, TXT, and Markdown files. | M |
| FR-11 | Uploads are validated for file type and size before any processing. | M |
| FR-12 | Processing runs as a background job and never blocks the API. | M |
| FR-13 | Each document shows its status: uploaded, processing, embedding, indexing, ready, or failed (with the reason). | M |
| FR-14 | The pipeline extracts text and detects structure (pages, headings, lists, tables where feasible). | M |
| FR-15 | The pipeline cleans and normalizes text, then splits it into chunks that respect document structure. | M |
| FR-16 | Each chunk stores document id, filename, file type, page number, section, heading, chunk position, and creation time. | M |
| FR-17 | Each chunk stores its embedding and the name of the model that produced it. | M |
| FR-18 | A failed document can be retried or deleted without affecting other documents. | S |
| FR-19 | Scanned or image-only PDFs go through an OCR path. | C |
| FR-20 | Additional formats (for example HTML and PPTX) are accepted. | C |

### Retrieval

| ID | Requirement | Pri |
|---|---|---|
| FR-21 | Retrieval combines semantic (vector) search and keyword (full-text) search, and fuses the two rankings. | M |
| FR-22 | Retrieval can filter by workspace and by document. | M |
| FR-23 | Retrieval can also filter by file type, page range, section, and date. | S |
| FR-24 | A reranking stage rescores the candidates and keeps only the strongest evidence. The number of candidates and the number kept are configurable. | M |
| FR-25 | When the best evidence is below a confidence threshold, the system says it could not find sufficient evidence instead of answering. | M |

### Answers and citations

| ID | Requirement | Pri |
|---|---|---|
| FR-26 | Answers are generated from retrieved evidence only. The LLM is instructed not to invent facts or citations. | M |
| FR-27 | Every answer carries citations (document, page, section, passage) that point to the chunks actually used. | M |
| FR-28 | Clicking a citation opens the source document at the cited page with the passage highlighted. | M |
| FR-29 | Answers separate what the sources state from what the model infers. | S |
| FR-30 | The LLM provider and the embedding model are switchable through configuration, without code changes elsewhere. | M |

### Chat and search

| ID | Requirement | Pri |
|---|---|---|
| FR-31 | A user can ask a natural-language question and receive a cited answer. | M |
| FR-32 | Follow-up questions are rewritten into standalone queries using recent history, so context carries over without sending the whole conversation to the LLM. | S |
| FR-33 | Conversations are saved and can be reopened. | S |
| FR-34 | A search page returns ranked passages (document, page, section, text, score) across all documents, a workspace, or one document. Clicking a result opens the source. | S |

### Summaries, comparison, insights

| ID | Requirement | Pri |
|---|---|---|
| FR-35 | A user can summarize a whole document, selected pages, or a section, in executive, key-points, or detailed mode, using hierarchical (chunk-aware) summarization. | S |
| FR-36 | A user can compare two or more documents on a question or topic and get a structured table with a citation for every important claim. | S |
| FR-37 | The system can extract topics, entities, key insights, and action items, clearly separating generated interpretation from what the source states. | C |
| FR-38 | The system can generate questions that a document can answer. | C |

### Evaluation and monitoring

| ID | Requirement | Pri |
|---|---|---|
| FR-39 | A versioned golden dataset of questions with expected evidence exists. | M |
| FR-40 | An evaluation harness reports retrieval recall (hit@k), citation accuracy, groundedness, answer relevance, and latency. | M |
| FR-41 | The harness can compare configurations (vector only, keyword only, hybrid, hybrid plus rerank) and save the results. | M |
| FR-42 | Every query is logged with per-stage latency, retrieved chunks, and outcome. | M |
| FR-43 | An admin dashboard shows totals (users, workspaces, documents, chunks, queries), average response time, failed queries, and processing errors. | C |

## 3. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Security: authentication on private routes, an authorization check on every data access, file type and size limits, input validation, secrets only in environment variables, and no API key ever reaching the frontend. |
| NFR-02 | Privacy: with a local LLM, document content never leaves the machine. Some free API tiers let the provider use submitted content to improve its products, so check each provider's terms and prefer local mode for private documents. |
| NFR-03 | Performance: slow work runs in background jobs, answers stream to the UI, and per-stage timings are recorded. Latency targets are set after the first benchmark in Milestone 7. |
| NFR-04 | Reliability: a failed job never corrupts the index, and jobs are safe to retry. |
| NFR-05 | Replaceability: the embedding model, LLM provider, and vector store are used through interfaces so each can change without rewriting the rest. Changing the embedding model triggers re-embedding. |
| NFR-06 | Cost: no paid services anywhere. Every component has a free or local option. |
| NFR-07 | Testability: unit tests for chunking, fusion, and permissions; integration tests for ingestion to retrieval to answer; CI runs on every push. |
| NFR-08 | Reproducibility: the whole stack starts with `docker compose up` and a documented `.env` file. |
| NFR-09 | Documentation: README, architecture, database schema, OpenAPI docs, and evaluation results are kept up to date in the repository. |

## 4. Out of scope (for now)

- Sharing workspaces between users, or real-time collaboration
- Model fine-tuning
- Mobile apps
- Payments and billing

## 5. Constraints and assumptions

- One developer, zero budget, no paid APIs.
- Development runs in GitHub Codespaces. Any hosted demo uses free tiers, which may sleep or rate-limit.
- English documents first. Multilingual support later means swapping the embedding model and re-embedding.

## 6. Build order

Milestones follow the 18-milestone plan, with schema and auth moved forward to Milestone 3 and the evaluation harness moved ahead of the Should features (see `decisions.md`, D-08).

| Milestone | Delivers |
|---|---|
| M1 | Requirements, architecture, decisions (this folder) |
| M2 | Repository, tooling, Docker Compose with Postgres + pgvector |
| M3 | FastAPI skeleton, database schema, auth, workspaces, isolation (FR-01 to FR-05, FR-07 to FR-09) |
| M4 | Upload, validation, parsing, job queue, status (FR-10 to FR-14) |
| M5 | Cleaning, chunking, metadata (FR-15, FR-16) |
| M6 | Embeddings and vector indexing (FR-17, FR-30 embedding side) |
| M7 | Hybrid retrieval and filters; first golden questions (FR-21, FR-22, FR-39 started) |
| M8 | Reranking (FR-24) |
| M9 | LLM answers, grounding, refusal (FR-25, FR-26, FR-30 LLM side, FR-31) |
| M10 | Citations and source API (FR-27, FR-28) |
| M11 | React frontend for everything above |
| M12 | Evaluation harness and query logging (FR-39 finished, FR-40 to FR-42) |
| M13 | Follow-up chat, saved conversations, search page, extra filters (FR-23, FR-29, FR-32 to FR-34) |
| M14 | Summaries, comparison, insights, question generation, admin dashboard (FR-35 to FR-38, FR-43) |
| M15 | Testing and security hardening (FR-18, NFR-01, NFR-07) |
| M16 | Docker polish and deployment (NFR-08) |
| M17 | GitHub documentation (NFR-09) |
| M18 | FYP report and presentation |

Stretch, after M16: profile (FR-06), OCR (FR-19), extra formats (FR-20).

## 7. FYP report mapping

This file is the starting point for Chapter 3 (Requirements Analysis). The functional requirements become the use cases, and the non-functional requirements become the quality attributes.