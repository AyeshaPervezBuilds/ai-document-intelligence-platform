# Decisions

**Status:** Draft v0.1, Milestone 1 (2026-10-01)

Each entry records what was chosen, what was rejected, and why. Add a new entry whenever a major choice changes. This log feeds the design chapters of the FYP report, and it is the answer sheet for "why did you build it this way?" questions.

## D-01: Free-only stack, with swappable model providers

- **Chosen:** The LLM and the embedding model sit behind interfaces. Defaults are a free LLM tier (Gemini or Groq) or Ollama, and a local embedding model (`nomic-embed-text`).
- **Rejected:** OpenAI's API and embeddings as defaults. They cost money, and the project has a zero-spend rule.
- **Why:** Providers and their free tiers change often. An interface turns a provider change into a config change. Check each provider's rate limits and data-use terms when integrating (Milestone 9), and prefer local mode for private documents.

## D-02: PostgreSQL + pgvector as the single data store

- **Chosen:** One Postgres database holds relational data, vectors, the keyword index, and the job queue.
- **Rejected:** Chroma or another separate vector database next to a relational one.
- **Why:** Metadata filtering becomes a normal SQL `WHERE`. There is no syncing between stores, one backup, and fewer services to run and explain. The vector store still sits behind an interface, so it can be replaced later (NFR-05).

## D-03: Hybrid retrieval with reciprocal rank fusion

- **Chosen:** Vector search and Postgres full-text search run separately, and their rankings are merged with reciprocal rank fusion (RRF).
- **Rejected:** Vector-only retrieval, and merging raw scores.
- **Why:** Embeddings blur names, IDs, and exact numbers, and keyword search catches them. RRF merges by rank, so the two scoring scales never need normalizing.
- **Note:** Postgres full-text ranking is not BM25. Say so in the report, and let the evaluation (FR-41) show how much it matters.

## D-04: Rerank after fusion, configurable

- **Chosen:** A local cross-encoder rescores the fused candidates and keeps the best few. Starting values: 30 candidates in, 5 kept. The evaluation tunes them.
- **Rejected:** Sending every retrieved chunk to the LLM.
- **Why:** Less noise in the prompt gives better answers, stronger grounding, and lower cost.

## D-05: Own the pipeline, borrow the parsers

- **Chosen:** Chunking, retrieval, fusion, reranking, and prompting are written in this repository. Libraries are used for reading files and calling models.
- **Rejected:** LangChain or LlamaIndex as the core of the pipeline.
- **Why:** Frameworks hide the exact steps an examiner or interviewer will ask about. Writing them makes each step explainable and testable.

## D-06: Background jobs on Postgres, no Redis

- **Chosen:** An upload inserts a job row. A separate worker claims jobs with row-level locking and updates the status the UI displays.
- **Rejected:** Celery + Redis.
- **Why:** One fewer service to run and explain, and plenty for this workload. Jobs stay retryable (NFR-04). Revisit only if throughput ever demands a real queue.

## D-07: Every chunk records its embedding model

- **Chosen:** `embedding_model` is stored with each chunk.
- **Rejected:** One global "current model" setting.
- **Why:** Vectors from different models cannot be compared, and each model has its own vector size. Recording the model makes "swap the model later" (spec section 14) real: change the setting, re-embed, and the old data stays identifiable in the meantime.

## D-08: Schema and auth in Milestone 3, evaluation before Should-features

- **Chosen:** The database schema, auth, and per-user isolation move from Milestone 12 to Milestone 3. The evaluation harness moves from Milestone 14 to Milestone 12, ahead of chat follow-ups, summaries, and comparison.
- **Rejected:** The original order.
- **Why:** Isolation (FR-05) is simple to build in from the first query and painful to retrofit. And a finished, measured core matters more than extra features.

## D-09: Golden questions start in Milestone 7

- **Chosen:** Begin the golden question set when hybrid retrieval first works, and extend it every milestone.
- **Rejected:** Writing all evaluation data at the end.
- **Why:** Without it, "hybrid beats vector-only" and "reranking helps" are opinions. With it they are measurements, and they become the results table in the README and the FYP report.

## D-10: Local-first delivery, hosting last

- **Chosen:** `docker compose up` on a laptop is the primary, fully free way to run and demo the project. A public live demo is a bonus decided in Milestone 16.
- **Rejected:** Designing around a specific host from day one.
- **Why:** Free hosts come with limits that shape the design (idle sleep, filesystems that reset, no free background workers, small databases), and those limits change. Keeping the core host-independent means none of them