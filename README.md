# 🎙️ Autonomous AI Sales Voice Agent (Fortive AI)

An enterprise-grade, conversational virtual sales representative that communicates with customers through voice, analyzes technical requirements, retrieves verified product knowledge via RAG, qualifies leads using the **BANT** framework, and schedules sales demonstrations with calendar synchronization.

---

## 🌟 Executive Summary & Core MVP Features

This repository implements a functional, production-ready MVP engineered for technical evaluation:

1. **🎙️ Dual-Pipeline Real-Time Voice Conversation**:
   - **Speech-to-Text (STT)**: Real-time browser speech recognition (Web Speech API) with continuous listening and live voice activity detection.
   - **Text-to-Speech (TTS)**: High-fidelity **Microsoft Edge Neural TTS** (`en-US-JennyNeural`) streaming natural MP3 audio, plus instant fallback to client-side speech synthesis.
   - **Reactive Audio Visualizer**: Animated soundwave HUD reacting dynamically to customer speech, AI reasoning, and vocal output.
2. **🧠 LLM Conversational Brain & Consultative Selling Persona**:
   - Sales representative persona: *Alex Carter*, Senior Enterprise Solutions Specialist.
   - Powered by **Google Gemini 1.5 Flash** with an automatic failover to the native **Enterprise Consultative Engine**, guaranteeing 100% testability out of the box with zero external API key requirements.
3. **📚 RAG (Retrieval-Augmented Generation) Knowledge Base**:
   - Indexes enterprise hardware products (e.g. *Precision Workstation 7780 Studio*, *ThinkEnterprise Carbon X1 Gen 12*, *ApexBook Developer Pro 16*, *Fortive Fluke Industrial Connect 850*).
   - Instant sub-millisecond vector similarity ranking based on TF-IDF term weighting and cosine similarity.
   - Dynamically injects verified product specs, pricing, warranty terms, and SLAs into LLM context.
4. **🎯 Automated Lead Qualification (BANT Framework)**:
   - Real-time entity extraction: Customer Name, Email, Phone, Budget, Purchase Timeline, and Workload Requirements.
   - Computes dynamic **BANT Qualification Score (0–100%)** and classifies leads as **Hot (High Intent)**, **Warm (Active Evaluation)**, or **Cold (Early Inquirer)**.
   - Conversational sentiment analysis (Positive, Analytical, Hesitant).
5. **📅 Appointment Booking & Google Calendar Synchronization**:
   - Detects customer appointment intent; dynamically fetches upcoming open business day slots.
   - Confirms booking, generates Google Meet links, and streams standard **iCalendar (.ics)** calendar invite files.
6. **📊 Call Summarization & CRM Pipeline Analytics (MongoDB)**:
   - Generates executive post-call summaries, key discussion topics, and recommended next actions.
   - Real-time MongoDB persistence with live CRM metrics: total calls, qualified leads, bookings, and pipeline conversion rates.

---

## 🏗️ System Architecture

```
Customer Microphone ──► Web Speech STT ──► FastAPI Backend (Port 8000)
                                                    │
                   ┌────────────────────────────────┴────────────────────────────────┐
                   ▼                                                                 ▼
           [RAG Vector Engine]                                            [Lead Qualification]
       - Product Catalog Search                                        - Name / Email / Phone
       - Hardware Specs & Pricing                                      - Budget & Timeline
       - Warranty & SLA Grounding                                      - BANT Score (0-100)
                   │                                                                 │
                   └────────────────────────────────┬────────────────────────────────┘
                                                    ▼
                                         [LLM Conversational Brain]
                                    - Gemini 1.5 Flash / Native Engine
                                    - Consultative Sales Persona
                                    - Appointment Intent Detection
                                                    │
                   ┌────────────────────────────────┼────────────────────────────────┐
                   ▼                                ▼                                ▼
           [Neural TTS Service]             [Google Calendar]               [MongoDB Database]
         - Microsoft Edge-TTS            - Slot Scheduling               - calls collection
         - Natural Speech MP3            - .ICS Calendar Invite          - leads collection
                   │                                                     - appointments collection
                   ▼                                                     - summaries collection
             Customer Ear
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind/Modern CSS | Glassmorphism cockpit, live visualizer, audio player, BANT card |
| **Backend** | Python 3.12, FastAPI, Uvicorn | High-throughput asynchronous REST & streaming audio services |
| **Speech-to-Text (STT)** | Web Speech API / OpenAI Whisper | Real-time voice capture with zero client latency |
| **Text-to-Speech (TTS)** | Microsoft Edge Neural TTS | High-fidelity natural voice generation (`en-US-JennyNeural`) |
| **AI Brain (LLM)** | Gemini 1.5 Flash / Consultative Brain | Multi-turn reasoning, consultative selling, intent detection |
| **RAG Retrieval** | Vector Indexing + Cosine Similarity | Enterprise hardware catalog grounding and spec matching |
| **Database** | MongoDB Server (with JSON fallback) | Persistent calls, leads, appointments, and summary storage |
| **Calendar Service** | Google Calendar API + iCal (.ics) | Automated slot reservation & downloadable meeting invites |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** & npm (Tested on Node v22.14)
- **MongoDB** (Local `mongodb://localhost:27017` or MongoDB Atlas; automatic JSON fallback if offline)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd "fortive ai"
   ```

2. **Install Python backend dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **(Optional) Configure environment variables**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY if desired (agent includes native consultative brain if omitted)
   ```

4. **Seed database with sample sales records**:
   ```bash
   python scripts/seed_data.py
   ```

5. **Start the Unified Server**:
   ```bash
   python backend/run.py
   ```
   *The application will launch at **http://localhost:8000** serving both the FastAPI REST endpoints and the React frontend!*

> **Windows One-Click Launch**: Double-click `scripts\run_demo.bat` to seed the database, launch the server, and open the cockpit in your browser automatically!

---

## 🧪 Automated Regression Test Suite

Run the end-to-end integration test suite verifying RAG retrieval, lead qualification, appointment booking, .ICS invite generation, and MongoDB metrics:

```bash
python scripts/test_pipeline.py
```

Expected output:
```
============================================================
ALL 5 SYSTEM TESTS PASSED WITH 100% SUCCESS!
============================================================
```

---

## 🎭 Step-by-Step Demonstration Walkthrough

Open the web cockpit at **http://localhost:8000** and test the following business scenarios:

### Scenario 1: Customer Inquiring About Engineering/CAD Laptops
1. Click **"Start Live Voice Call"** (or click test scenario button 1).
2. The AI agent greets: *"Hello! Welcome to Fortive AI Solutions. My name is Alex Carter..."*
3. **Customer speaks**: *"Hi, my name is David Miller. I need a heavy-duty laptop for 3D CAD modeling and deep learning. My budget is around $3500 and email is david@techfirm.com."*
4. **AI responds with RAG**: Identifies the **Precision Workstation 7780 Studio** ($3,299), highlights its Intel i9-14900HX, RTX 4000 Ada GPU, and 3-Year ProSupport warranty.
5. **Lead Qualification updates live**:
   - Customer Name: *David Miller*
   - Stated Budget: *$3,500*
   - Email: *david@techfirm.com*
   - Requirements: *3D CAD, Local AI Acceleration*
   - BANT Score: **90 / 100 (Hot - High Intent)**

### Scenario 2: Scheduling the Technical Demonstration
1. **Customer speaks**: *"Yes, that sounds perfect. Can we schedule a live demonstration with your engineering specialist?"*
2. **AI Action**: Detects appointment booking intent, reserves an upcoming slot (e.g. *Friday at 10:00 AM EST*), assigns booking ID `APPT-XXXXXX`, and generates a Google Meet link.
3. Switch to the **"Schedule"** tab to view the confirmed meeting and click **"Download .ICS Calendar Invite"**.

### Scenario 3: Executive Call Summary & CRM Analytics
1. Click **"End Call & Generate Summary"**.
2. Switch to the **"Analytics"** tab to view:
   - Structured Executive Summary
   - Identified Key Topics (*Hardware Procurement, Pricing, Demo Scheduling*)
   - Recommended Next Action (*"Assigned to Enterprise Account Executive..."*)
   - Real-time MongoDB pipeline metrics (Total calls, conversion rate %).

---

## 📂 Documentation & Evaluation Deliverables

Comprehensive technical evaluation documents are available in the `docs/` folder:

- **[System Architecture & Data Flows](docs/ARCHITECTURE.md)**: Sequence diagrams, component interactions, and data schemas.
- **[Scalability Strategy for 100,000 Users](docs/SCALABILITY_100K_USERS.md)**: Stateless microservices, WebRTC/SIP gateways, Kafka/Redis queues, Milvus/Pinecone sharding, and Kubernetes HPA.
- **[Security, Compliance & Cost Analysis](docs/SECURITY_AND_COST_ANALYSIS.md)**: TLS 1.3, PII redaction, GDPR/HIPAA compliance, unit economics (7.4¢/call), and 100k-user cost modeling.
- **[REST API Specification](docs/API_SPECIFICATION.md)**: Detailed OpenAPI endpoints, request schemas, and responses.

---

## 🛡️ License

MIT License. Engineered for technical evaluation at Fortive AI.
