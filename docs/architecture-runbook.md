Architecture Runbook



Scope: How to build, run, and deploy the system locally and on a minimal/free AWS (Amazon Web Services) setup.

Services: api/ (API — Application Programming Interface), graph/ (LangGraph pipeline), ingestor/ (CLI — Command-Line Interface workers), web/ (React/Next.js), infra/cdk/ (CDK — Cloud Development Kit), docker/ (images for local + cloud).



0\) TL;DR (first run)



Local dev: run graph, then api, then test with curl or the docs UI (User Interface).



Data flow: User → api → graph ⇒ PHI (Protected Health Information) guard → retrieve (vector DB) → answer (with citations) → verify → optional escalation.



Minimal cloud: package api + graph into containers (or Lambda functions), store docs in S3 (Simple Storage Service), vectors in Qdrant (self-hosted via Docker), configs/secrets in SSM (Systems Manager Parameter Store)/Secrets Manager, users in Cognito.



1\) Repository layout (authoritative)

.

├── api/                  # FastAPI (Fast Application Programming Interface) adapter with SSE (Server-Sent Events)

│  ├── app.py

│  └── requirements.txt

├── graph/                # LangGraph app (phi\_guard → retrieve → answer → verify → decide/escalate)

│  ├── app.py

│  └── requirements.txt

├── ingestor/             # CLI (Command-Line Interface): parse PDFs/HTML, chunk, embed, upsert to Qdrant

│  └── run.py

├── docker/               # Dockerfiles

│  ├── Dockerfile.lambda  # base for Lambda container

│  └── Dockerfile.dev     # local dev (compose)

├── infra/

│  └── cdk/               # CDK (Cloud Development Kit) stacks: s3, dynamodb, cognito, gateway, lambda

├── web/                  # Next.js (React) static export or simple widget

└── README.md





Note: We use requirements.txt here for the “minimal setup.” If you also maintain a uv (fast Python package / virtual environment manager) workspace, export from uv to keep these files in sync (see §3).



2\) Environments and prerequisites

Local (developer machine)



Python 3.11+, Node.js 18+, Docker Desktop.



AWS CLI (Command Line Interface) v2 and CDK (Cloud Development Kit) v2.



Accounts/keys for: Cognito (User Pool), Qdrant (local Docker or hosted), LLM (Large Language Model) provider.



Cloud (minimal/free)



Lambda + API Gateway for api and graph (cheaper than ECS Fargate — Elastic Container Service for small usage).



S3 (raw docs + processed chunks), DynamoDB (conversations/escalations/config), Cognito (auth), CloudWatch (logs/metrics).



Qdrant for vectors (self-host in EC2 or local lab for demos). If you need fully managed AWS vector search later, switch to OpenSearch Serverless (not free).



3\) Dependencies and packaging



Choose one routine and stick with it:



Simple/minimal: manually manage requirements.txt in each service.



Structured (recommended for teams): keep a uv workspace and export pinned requirements to each service:



uv export --package mce-api --frozen -o api/requirements.txt



uv export --package graph --frozen -o graph/requirements.txt



uv export --package mce-ingestor --frozen -o ingestor/requirements.txt



Why export? Single lock for everything, but your minimal layout still gets plain requirements.txt for Docker/Lambda.



4\) Configuration (env vars and secrets)



Define once, use everywhere. Keep a README table and a .env.example in each service.



Auth: COGNITO\_USER\_POOL\_ID, COGNITO\_CLIENT\_ID, COGNITO\_JWKS\_URL



Data: S3\_BUCKET\_RAW, S3\_BUCKET\_CHUNKS, QDRANT\_URL, QDRANT\_API\_KEY



Embeddings: EMBED\_MODEL, EMBED\_BATCH\_SIZE, EMBED\_MAX\_QPS (Queries Per Second)



LLM: LLM\_PROVIDER, LLM\_MODEL, LLM\_API\_KEY



Runtime: REGION, LOG\_LEVEL, CONFIDENCE\_THRESHOLD, ENABLE\_PHI\_GUARD



Stores: DDB\_TABLE\_CONVOS, DDB\_TABLE\_ESCALATIONS, DDB\_TABLE\_ADMIN



Escalations: SLACK\_WEBHOOK\_URL or SES (Simple Email Service) settings



Local: use .env files (never commit).

Cloud: use Parameter Store/Secrets Manager; inject via Lambda/Task definitions.



5\) Local development workflow

5.1 Ingest a few documents



Place test PDFs/HTML in a local folder.



Run ingestor/run.py to parse → chunk → embed → upsert to Qdrant.



Verify chunks exist in Qdrant (use its dashboard or API).



Checklist



&nbsp;Qdrant is reachable (Docker container running).



&nbsp;Embedding model key present.



&nbsp;Chunks show non-zero vector counts.



5.2 Start the graph service



Launch graph/app.py.



Ensure it can query Qdrant and read S3 (for local: point to a local storage folder or a dev bucket).



Confirm /healthz returns healthy.



Checklist



&nbsp;PHI-guard toggles and redaction policy loaded.



&nbsp;Retrieval returns k-NN (k-Nearest Neighbors) hits for known prompts.



&nbsp;Verifier returns confidence values; escalation threshold set.



5.3 Start the API service



Launch api/app.py (serves SSE — Server-Sent Events).



JWT verification (Cognito) enabled in middleware.



Confirm docs UI (Swagger) at /docs.



Test chat route; see streamed tokens.



Checklist



&nbsp;/docs reachable; GET /healthz returns 200.



&nbsp;Requests forward to graph with timeout/retry.



&nbsp;Logs are redacted and structured (no PHI).



5.4 Run the web app (optional early)



Start web/ (Next.js dev server or static export).



Configure it to call the api with a valid Cognito JWT.



6\) Data flow (contract)



User → API → Graph:

PHI-Guard (detect/redact/block) → Retrieve (Qdrant) → Answer (LLM with citations) → Verify (confidence) → Escalate (DynamoDB + Slack/Email) if below threshold or PHI risk.



Artifacts to standardize



Request/response schema (conversation id, user id, message, top-k, filters).



Chunk schema (id, doc id, text, vector, metadata).



Citation rendering (source, page/section, confidence).



Escalation payload (question, answer, confidence, retrieved snippets, timestamps).



7\) Security and compliance



PII/PHI (Personally Identifiable Information / Protected Health Information): redact on ingress, never log raw text when flagged.



IAM (Identity and Access Management) least privilege: separate roles for api, graph, ingestor.



Secrets: only from Secrets Manager/Parameter Store; rotate keys.



Networking (cloud): private subnets, strict security groups, HTTPS everywhere.



Audit: enable CloudTrail; tag resources with system name and data classification.



8\) Observability



Logs: JSON (JavaScript Object Notation) logs with request id, user id (pseudonymized), latency, model usage; no PHI.



Metrics: request counts, p95 latency, retrieval hit rate, tokens per response, ingestion throughput, confidence histogram.



Tracing: optional X-Ray/OTel (OpenTelemetry); propagate trace ids from api → graph.



Alarms: 5xx spikes, rising latency, verifier failures, ingestion errors.



9\) Testing strategy



Unit: chunkers, retriever adapters, PHI-guard rules, verifiers.



Integration: api ↔ graph contracts, Qdrant queries, S3 reads.



E2E (End to End): ingest a doc, ask a question, confirm citations + confidence, force escalation path.



Data quality: validate chunk counts, vector norms, index freshness.



10\) Minimal cloud deployment (free-leaning)



Target: Lambda + API Gateway for api and graph; EventBridge + Lambda for ingestor; S3, DynamoDB, Cognito, CloudWatch. Use self-hosted Qdrant for vectors (or temporarily local during demo).



Steps



Build images or Lambda zips using docker/Dockerfile.lambda.



Infra with CDK:



Stacks for S3, DynamoDB, Cognito, API Gateway + Lambda integrations.



Parameters/Secrets for LLM keys, Qdrant creds.



Deploy order: data stores → auth → functions/APIs → web.



Post-deploy: update web .env with API base URL and Cognito config; smoke test /healthz and /docs.



Checklist



&nbsp;Cognito pool + client created; JWKS (JSON Web Key Set) URL reachable.



&nbsp;API Gateway routes 200 for /healthz, streams /chat.



&nbsp;Graph Lambda can reach Qdrant endpoint.



&nbsp;DynamoDB tables contain new conversations/escalations.



&nbsp;CloudWatch shows logs/metrics; alarms configured.



11\) Production path (when ready)



Migrate compute to ECS Fargate behind ALB (Application Load Balancer) if you need long-running containers and steady traffic.



Replace Qdrant with OpenSearch Serverless if you want managed vectors (cost trade-off).



Add CI/CD (Continuous Integration / Continuous Delivery) pipelines (lint, test, build, deploy).



Add WAF (Web Application Firewall) on the edge.



12\) Common failure runbooks



Qdrant unavailable: return “temporarily degraded,” log metric, backoff, trigger alert; keep API up so chat degrades gracefully.



LLM rate-limit: apply retries with jitter, reduce streaming chunk size, surface “please retry” UX.



Cognito JWT verification fails: rotate keys, verify clock skew, confirm audience/issuer.



S3/DynamoDB throttling: increase capacity or add exponential backoff; check hot partitions (conversations by user).



Escalation delivery fails (Slack/Email): queue and retry; send fallback email to on-call.



13\) Roles and ownership



Service owners: api (auth/routes), graph (policies/pipeline), ingestor (parsers/chunkers).



Data owner: documents/chunks, retention, access control.



Cloud owner: CDK stacks, IAM, Networking, Observability.



On-call: alarm runbooks, escalations, incident postmortems.



14\) Milestone checklists



M1 – Local E2E working



&nbsp;Ingest 1–2 docs, vectors present.



&nbsp;Graph returns citations, confidence.



&nbsp;API streams responses, docs page works.



&nbsp;Web chat renders citations.



M2 – Minimal cloud



&nbsp;Infra deployed (S3/DynamoDB/Cognito/API Gateway/Lambda).



&nbsp;Qdrant reachable (self-host/EC2 or demo).



&nbsp;End-to-end chat via public URL.



M3 – Harden



&nbsp;Secrets rotated; PHI-guard validated.



&nbsp;Alarms green for 24h; error budget set.



&nbsp;Backups/snapshots in place (S3 lifecycle, DynamoDB PITR — Point In Time Recovery).



Appendix: Local commands you’ll use often



Run API locally: start api/app.py and open http://127.0.0.1:8000/docs.



Run Graph locally: start graph/app.py, hit /healthz.



Run Ingestor locally: execute ingestor/run.py with a folder of PDFs/HTML.



Docker dev: use docker/Dockerfile.dev (compose) to spin up Qdrant + services for team demos.

