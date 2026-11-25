# System Architecture & Technical Specifications
## Autonomous AI Sales Voice Agent — Fortive AI

### 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React.js + Web Audio API)"]
        A1["Microphone / User Audio"] --> A2["Web Speech API (STT)"]
        A2 --> A3["Cockpit UI & Live Visualizer"]
        A4["Audio Output (Speakers)"] <-- A5["HTML5 Audio Player / Web Speech"]
    end

    subgraph Gateway["API & Communication Gateway"]
        B1["FastAPI ASGI Server (Port 8000)"]
        B2["CORS & Request Middleware"]
        B3["Static Files Mount (React Bundle)"]
    end

    subgraph AgentBrain["Agentic Brain & Pipeline (Python)"]
        C1["Sales Agent Orchestrator (Alex Carter)"]
        C2["Lead Qualifier & BANT Engine"]
        C3["RAG Vector Engine (TF-IDF / Cosine Sim)"]
        C4["Appointment Scheduler (.ICS Engine)"]
        C5["Neural TTS Service (Edge-TTS)"]
        C6["Post-Call Analytics & Summarizer"]
    end

    subgraph External["External AI & Cloud Integrations"]
        D1["Gemini 1.5 Flash / OpenAI API"]
        D2["Google Calendar API (Live Sync)"]
        D3["Microsoft Edge Neural Speech API"]
    end

    subgraph Storage["Persistent Data Tier"]
        E1[("MongoDB Database (Port 27017)")]
        E2["calls collection"]
        E3["leads collection"]
        E4["appointments collection"]
        E5["summaries collection"]
        E6["Fallback JSON Store"]
    end

    %% Connections
    A3 -->|HTTP POST /api/chat| B1
    B1 --> C1
    C1 --> C2
    C1 --> C3
    C3 -->|Retrieve Specs & Pricing| C1
    C1 -->|LLM Reasoning| D1
    C1 --> C4
    C4 -.->|OAuth2 Sync| D2
    C1 --> C5
    C5 -->|Generate MP3 Audio| D3
    D3 -->|Audio Stream| A5
    C2 -->|Upsert Lead Record| E3
    C4 -->|Store Confirmed Slot| E4
    C1 -->|Log Latency & Turns| E2
    C6 -->|Store Executive Summary| E5
    E1 -.->|Failover| E6
```

---

### 2. End-to-End Voice & Processing Pipeline

1. **Audio Capture (ASR / STT)**:
   - The browser captures microphone audio at 16kHz / 48kHz via the Web Audio API.
   - Converts customer speech to text using the browser's native **Web Speech Recognition** engine with continuous listening and zero server-side streaming latency.
   - Real-time animated audio visualizer reflects volume fluctuations and speaking state.

2. **Lead Qualification & Entity Extraction**:
   - The conversational utterance is processed by `LeadQualifier`.
   - Extracts customer name, contact details (email/phone), stated budget, purchase timeline, and technical requirements (e.g., 3D CAD, local AI, ruggedized, battery life).
   - Computes a dynamic **BANT Qualification Score (0-100)** and classifies the lead status into **Hot (High Intent)**, **Warm (Active Evaluation)**, or **Cold (Early Inquirer)**.
   - Detects customer sentiment (Positive, Neutral, Hesitant / Price-Sensitive).

3. **Knowledge Retrieval (RAG)**:
   - Customer query is tokenized and matched against the enterprise product catalog via the `RAGEngine`.
   - Vector similarity is computed using term weighting and cosine similarity across product specifications, target use cases, and enterprise pricing.
   - Top-ranked product specifications, warranties, and SLAs are dynamically injected into the LLM system prompt as grounding truth.

4. **Conversational Agent Brain & Decision Loop**:
   - Persona: *Alex Carter*, Senior Enterprise Solutions Specialist at Fortive AI.
   - Employs consultative selling methodology:
     - Greets warmly and explores pain points.
     - Recommends the exact matching hardware/solution with concise value props.
     - Asks qualifying BANT questions.
     - Confirms contact details.
     - Proactively closes by offering a live 20-minute product demonstration with a systems engineer.
   - Powered by **Google Gemini 1.5 Flash** (when API key is set) with automatic failover to the native **Enterprise Consultative Sales Engine**, ensuring 100% testability with zero external billing barriers.

5. **Appointment Booking & Calendar Synchronization**:
   - Detects appointment booking intent or customer confirmation.
   - Generates available upcoming business day time slots.
   - Books the appointment, assigns a unique `APPT-XXXXXX` confirmation ID, and generates a Google Meet link.
   - Generates a standard **iCalendar (.ics)** file for one-click import into Google Calendar, Outlook, or Apple Calendar.

6. **Voice Synthesis (TTS)**:
   - Agent reply text is cleaned of markdown formatting, asterisks, and code artifacts for smooth, human-like vocalization.
   - Synthesizes speech using **Microsoft Edge Neural TTS** (`en-US-JennyNeural` / `en-US-GuyNeural`) streaming high-fidelity MP3 audio to the browser, with instant fallback to browser Web Speech Synthesis.

7. **Database Persistence (MongoDB)**:
   - Stores all conversation records, lead profiles, appointment bookings, and executive summaries across dedicated collections:
     - `leads`: Full BANT qualification, contact details, score, and timestamps.
     - `appointments`: Booking IDs, scheduled slots, client details, meeting URLs.
     - `calls`: Turn-by-turn latency, dialogue history, and session metadata.
     - `summaries`: Executive summaries, key topics, sentiment, and recommended next actions.
   - Automatically falls back to an ACID-safe JSON file store if MongoDB is offline.

---

### 3. Data Models & Schemas

#### A. Lead Record (`leads` collection)
```json
{
  "_id": "6745...b241",
  "customer_name": "David Miller",
  "email": "david@techfirm.com",
  "phone": "+1 (555) 234-5678",
  "budget": "$3,500",
  "requirements": [
    "3D CAD / Modeling / Engineering Work",
    "Local AI / Deep Learning Acceleration"
  ],
  "timeline": "ASAP / Next Week",
  "interest_level": "High",
  "sentiment": "Positive",
  "score": 90,
  "status": "Hot (High Intent)",
  "created_at": "2026-11-25T18:00:00.000Z",
  "updated_at": "2026-11-25T18:02:15.000Z"
}
```

#### B. Appointment Booking Record (`appointments` collection)
```json
{
  "_id": "6745...c668",
  "booking_id": "APPT-01485CE5",
  "customer_name": "David Miller",
  "contact_info": "david@techfirm.com",
  "date": "2026-11-28",
  "time_slot": "10:00 AM",
  "topic": "Precision Workstation 7780 Custom Configuration Demo",
  "meeting_link": "https://meet.google.com/ftv-df4-9dc2",
  "calendar_provider": "Google Calendar (Synchronized)",
  "status": "Confirmed",
  "booked_at": "2026-11-25T18:02:15.000Z"
}
```

#### C. Executive Call Summary (`summaries` collection)
```json
{
  "call_id": "CALL-A82F19B",
  "customer_name": "David Miller",
  "contact": "david@techfirm.com",
  "duration_turns": 6,
  "key_topics": [
    "Hardware Procurement",
    "Pricing & Budgetary Alignment",
    "Technical Requirements & Workloads",
    "Product Demo Scheduling"
  ],
  "executive_summary": "Customer 'David Miller' engaged with sales agent Alex Carter to explore enterprise solutions. Stated requirements include 3D CAD modeling and deep learning acceleration with a target budget of $3,500. Successfully scheduled a 30-minute technical demonstration for 2026-11-28 at 10:00 AM. Invitation sent to david@techfirm.com.",
  "lead_qualification_score": 90,
  "lead_status": "Hot (High Intent)",
  "sentiment": "Positive",
  "appointment_booked": true,
  "recommended_next_action": "Assigned to Enterprise Account Executive for scheduled live demonstration."
}
```
