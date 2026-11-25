# Scalability Strategy for 100,000+ Users & Enterprise Production
## Autonomous AI Sales Voice Agent — Fortive AI

This document details the complete production architecture, concurrency modeling, infrastructure topology, and cost optimization required to scale the Autonomous AI Sales Voice Agent from an MVP to **100,000 daily active users (DAU)** and up to **5,000 peak concurrent voice sessions**.

---

### 1. Concurrency & Throughput Modeling

| Metric | Target Dimension |
| :--- | :--- |
| **Total Daily Active Users (DAU)** | 100,000 users / day |
| **Average Call Duration** | 3.5 minutes (210 seconds) |
| **Total Daily Audio Minutes** | 350,000 minutes / day |
| **Average Turns per Call** | 8 – 12 dialogue turns |
| **Peak Concurrency Window** | 4-hour peak (10:00 AM – 2:00 PM EST) handling ~45% of daily volume |
| **Peak Concurrent Voice Sessions** | **3,500 – 5,000 simultaneous calls** |
| **Inbound Requests per Second (RPS)** | ~1,200 – 1,800 turn RPS during peak bursts |

---

### 2. High-Level Scalable Production Topology

```mermaid
flowchart TD
    subgraph Edge["Global Ingress & Edge Layer"]
        A1["Cloudflare CDN & DDoS Shield"]
        A2["AWS Route 53 (Latency-based Geo DNS)"]
        A3["NLB / ALB (Network & Application Load Balancers)"]
    end

    subgraph VoiceGateways["Independently Scalable Voice Gateway Cluster"]
        B1["LiveKit / FreeSWITCH / WebRTC Gateway Pod 1"]
        B2["LiveKit / FreeSWITCH / WebRTC Gateway Pod N"]
        B3["Auto-Scaled SIP & RTP Media Workers"]
    end

    subgraph AppTier["Stateless Application Microservices (EKS / GKE)"]
        C1["FastAPI Conversational Orchestrator (HPA Autoscaled)"]
        C2["RAG Embedding & Retrieval Microservice"]
        C3["Lead Qualification & BANT Engine"]
        C4["Calendar & Booking Microservice"]
    end

    subgraph AsyncTier["Asynchronous Messaging & Queue Tier"]
        D1["Apache Kafka / RabbitMQ Event Bus"]
        D2["Redis Cluster 7.x (Session State, Caching, Pub/Sub)"]
        D3["Celery / Temporal Workers (Post-call Summaries & CRM Sync)"]
    end

    subgraph AIInference["AI Inference & Voice Processing Tier"]
        E1["GPU Cluster: Whisper Large-v3 (Triton Inference Server)"]
        E2["LLM Inference: Gemini 1.5 Flash / vLLM Llama-3.3-70B Cluster"]
        E3["TTS Cluster: Kokoro / XTTS / Azure Neural Speech"]
        E4["Pinecone / Milvus Vector Database (Sharded HNSW)"]
    end

    subgraph Persistence["Distributed Data Persistence"]
        F1[("MongoDB Atlas Sharded Cluster (3 Shards, 3x Replicas)")]
        F2[("PostgreSQL / Snowflake (Read-Replica Data Warehouse)")]
        F3["AWS S3 / GCS (Encrypted Audio Archive & Call Recordings)"]
    end

    %% Routing
    A1 --> A2 --> A3
    A3 --> B1 & B2
    B1 & B2 --> B3
    B3 -->|WebSocket / gRPC Audio Stream| C1
    C1 <--> D2
    C1 --> C2
    C2 <--> E4
    C1 --> E2
    B3 <--> E1
    C1 --> E3
    C1 -->|Publish Call End Event| D1
    D1 --> D3
    D3 --> F1 & F2 & F3
    C3 & C4 --> F1
```

---

### 3. Core Architectural Pillars for 100,000 Users

#### Pillar 1: Stateless Backend Services & Horizontal Pod Autoscaling (HPA)
- **Zero In-Memory Session Locking**: All conversational state, turn counts, and extracted entities are keyed by `session_id` and stored in a high-speed **Redis 7.0 Cluster** with sub-2ms read/write latency.
- **FastAPI with Uvicorn Workers**: Each backend container runs lightweight ASGI event loops managed by Gunicorn with 4 worker processes per pod.
- **Kubernetes HPA Rules**:
  - Scale up when CPU utilization exceeds 65% or Memory exceeds 75%.
  - Custom metrics: Scale based on active WebSocket / gRPC voice stream connections.
  - Baseline: 20 pods; Peak Scale: 120 pods across multiple availability zones (AZs).

#### Pillar 2: Asynchronous Event Processing & Decoupled Architecture
- **Critical Path vs. Background Tasks**:
  - *Synchronous Critical Path (< 400ms target)*: Audio Stream $\rightarrow$ VAD $\rightarrow$ STT $\rightarrow$ RAG lookup $\rightarrow$ LLM turn generation $\rightarrow$ First-chunk TTS audio streaming.
  - *Asynchronous Path (Offloaded to Kafka/Celery)*:
    1. Long-form post-call executive summary generation.
    2. Deep sentiment and customer objection analysis.
    3. Salesforce / HubSpot CRM lead synchronization.
    4. Audio file FLAC transcoding and S3 long-term storage archiving.
- **Circuit Breakers**: Implemented via Netflix Hystrix / Tenacity patterns. If an external service (e.g. Google Calendar API or third-party CRM) experiences latency spikes or rate limits, requests are queued in RabbitMQ without delaying the live voice call.

#### Pillar 3: Distributed Database Indexing & Sharding (MongoDB)
For 100,000 daily users generating ~350,000 calls per week, the database stores millions of records:
- **Sharding Strategy**:
  - Shard key: `{"account_id": 1, "created_at": 1}` or hashed `{"call_id": "hashed"}` to prevent write hotspots.
  - Primary collections: `leads`, `calls`, `appointments`, `summaries`.
- **Compound & Sparse Indexing**:
  ```javascript
  // Fast email/phone upsert lookups during live calls (< 1ms)
  db.leads.createIndex({ "email": 1 }, { sparse: true });
  db.leads.createIndex({ "phone": 1 }, { sparse: true });
  
  // Real-time BANT analytics queries
  db.leads.createIndex({ "status": 1, "score": -1, "updated_at": -1 });
  
  // High-performance appointment scheduling collision detection
  db.appointments.createIndex({ "date": 1, "time_slot": 1, "status": 1 });
  
  // TTL index for automatic ephemeral session cleanup
  db.sessions.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 86400 });
  ```
- **Read/Write Splitting**: Read queries for analytics dashboards query secondary replica members (`secondaryPreferred`), keeping primary nodes 100% dedicated to live call transactions.

#### Pillar 4: Multi-Tier Caching & Low-Latency RAG Retrieval
- **L1 In-Memory Semantic Cache**:
  - Redis vector cache using cosine distance. Common inquiries (e.g. *"What is the warranty on the Carbon X1?"*, *"Do you have laptops under $1500?"*) are cached with semantic embeddings. If semantic similarity is $\ge 0.94$, the pre-computed verified answer is returned immediately ($\approx 12\text{ ms}$).
- **Vector Index Sharding**:
  - For enterprise knowledge bases expanding to tens of thousands of SKUs and technical PDFs, FAISS / Milvus HNSW indexes are sharded with IVF-PQ (Inverted File with Product Quantization) compression, delivering 99.8% recall under 5ms.

#### Pillar 5: Independently Scalable Voice Processing Services
- **Speech-to-Text (STT)**:
  - Deployed on an auto-scaled cluster of NVIDIA L4 / T4 GPUs using **Triton Inference Server** running `faster-whisper` (CTranslate2 INT8 quantized).
  - WebRTC audio chunks streamed over gRPC with streaming VAD (Voice Activity Detection) using Silero VAD, cutting silence frames before running Whisper.
- **Text-to-Speech (TTS) Streaming**:
  - Uses chunked sentence-level streaming. The agent does not wait for the entire response to finish generating before speaking; the first sentence (e.g. *"The Precision Workstation 7780 is an ideal match."*) is sent to TTS immediately, achieving a Time-To-First-Audio (TTFA) of **< 350ms**!

---

### 4. High-Availability & Disaster Recovery (DR)

| Failure Scenario | Mitigation & Redundancy Protocol |
| :--- | :--- |
| **Primary Region Outage (e.g. us-east-1)** | Multi-Region Active-Passive deployment in `us-west-2` with Route 53 health-checked automated failover within 30 seconds. |
| **MongoDB Primary Node Failure** | Automated replica set election (< 3 seconds) with zero data loss using `w: "majority"` write concern. |
| **Primary LLM Provider Outage** | Automated multi-provider fallback router (Gemini 1.5 Flash $\rightarrow$ Claude 3.5 Sonnet $\rightarrow$ Local self-hosted vLLM Mistral/Llama-3). |
| **Redis Node Eviction** | Redis Sentinel / Multi-AZ cluster with automated in-memory failover and disk persistence (AOF + RDB). |

---

### 5. Summary Architecture Checklist

- [x] **Stateless microservices** containerized on Docker & Kubernetes.
- [x] **Asynchronous message bus** (Kafka/RabbitMQ) for non-blocking post-call tasks.
- [x] **MongoDB sharding & indexing** for million-record scale.
- [x] **Semantic Redis caching** reducing LLM token consumption by 35%.
- [x] **Sub-400ms voice round-trip latency** through sentence-level TTS chunking and GPU streaming.
