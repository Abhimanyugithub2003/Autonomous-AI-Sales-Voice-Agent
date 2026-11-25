# REST API Specification
## Autonomous AI Sales Voice Agent — Fortive AI

Base URL: `http://localhost:8000` (or `http://<host>:<port>`)
Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

---

### 1. Health & Status

#### `GET /api/health`
Returns system operational status, active database mode (MongoDB vs Fallback), indexed RAG products, and active AI engine.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Autonomous AI Sales Voice Agent",
  "database": {
    "mode": "mongodb",
    "connected": true,
    "database": "fortive_sales_ai",
    "counts": {
      "leads": 12,
      "appointments": 5,
      "calls": 18
    }
  },
  "rag_products_indexed": 5,
  "tts_engine": "Edge Neural TTS (Available)",
  "llm_engine": "Native Enterprise Consultative Brain"
}
```

---

### 2. Conversational Agent & Voice Turns

#### `POST /api/chat`
Processes one conversational turn. Performs lead entity extraction, RAG product retrieval, LLM reasoning, appointment intent detection, and logs conversation turns to MongoDB.

**Request Body**:
```json
{
  "call_id": "CALL-A1B2C3D4",
  "message": "Hi, I am David Miller. I need a heavy duty laptop for 3D CAD modeling. My budget is around $3500 and email is david@techfirm.com.",
  "history": [
    {
      "sender": "agent",
      "text": "Hello! Welcome to Fortive AI Solutions. My name is Alex Carter."
    }
  ],
  "current_lead": null
}
```

**Response `200 OK`**:
```json
{
  "call_id": "CALL-A1B2C3D4",
  "reply": "Given your requirements and budget around $3500, the Precision Workstation 7780 Studio is the optimal match. I can schedule a quick 15-minute live demonstration with our systems engineer to review deployment and volume discounts. Would tomorrow morning or afternoon work best for you?",
  "lead": {
    "customer_name": "David Miller",
    "email": "david@techfirm.com",
    "phone": null,
    "budget": "$3500",
    "requirements": [
      "3D CAD / Modeling / Engineering Work",
      "Local AI / Deep Learning Acceleration"
    ],
    "timeline": null,
    "interest_level": "High",
    "sentiment": "Positive",
    "score": 90,
    "status": "Hot (High Intent)",
    "_id": "674501a2..."
  },
  "retrieved_products": [
    {
      "product": {
        "id": "PROD-002",
        "name": "Precision Workstation 7780 Studio",
        "price": 3299,
        "specs": { "processor": "Intel Core i9-14900HX", "gpu": "NVIDIA RTX 4000 Ada" }
      },
      "score": 0.496,
      "matched_snippet": "Precision Workstation 7780 Studio ($3299) - Unmatched computational power..."
    }
  ],
  "booking": null,
  "latency_ms": 142.5,
  "llm_engine": "Native Enterprise Consultative Brain"
}
```

---

### 3. Voice Synthesis (TTS)

#### `POST /api/tts`
Streams synthesized speech in MP3 format using Microsoft Edge Neural TTS.

**Request Body**:
```json
{
  "text": "The Precision Workstation 7780 Studio is an outstanding choice for engineering.",
  "voice": "en-US-JennyNeural"
}
```

**Response `200 OK`**:
- Content-Type: `audio/mpeg`
- Body: Binary MP3 audio stream

---

### 4. Appointment Booking & Google Calendar

#### `GET /api/appointments/slots`
Returns real-world upcoming business day time slots.

**Response `200 OK`**:
```json
{
  "slots": [
    {
      "slot_id": "2026-11-28_10:00_am",
      "date": "2026-11-28",
      "day_name": "Friday, Nov 28",
      "time": "10:00 AM",
      "label": "Friday, Nov 28 at 10:00 AM EST",
      "available": true
    }
  ]
}
```

#### `POST /api/appointments/book`
Books an appointment slot and saves the record in MongoDB.

**Request Body**:
```json
{
  "customer_name": "David Miller",
  "contact_info": "david@techfirm.com",
  "date": "2026-11-28",
  "time_slot": "10:00 AM",
  "topic": "Precision Workstation 7780 Custom Configuration Demo",
  "notes": "Interested in 5 units for CAD engineering team."
}
```

**Response `200 OK`**:
```json
{
  "booking_id": "APPT-01485CE5",
  "customer_name": "David Miller",
  "contact_info": "david@techfirm.com",
  "date": "2026-11-28",
  "time_slot": "10:00 AM",
  "topic": "Precision Workstation 7780 Custom Configuration Demo",
  "status": "Confirmed",
  "meeting_link": "https://meet.google.com/ftv-df4-9dc2",
  "calendar_provider": "Google Calendar (Synchronized)",
  "_id": "674502f1..."
}
```

#### `GET /api/appointments/{booking_id}/ics`
Generates and downloads standard iCalendar `.ics` file for Google Calendar, Outlook, and Apple Calendar.

**Response `200 OK`**:
- Content-Type: `text/calendar`
- Content-Disposition: `attachment; filename=meeting_APPT-01485CE5.ics`

---

### 5. Call Summary & CRM Analytics

#### `POST /api/call-summary`
Produces post-call executive summary, sentiment analysis, key topics, and saves summary to MongoDB.

**Request Body**:
```json
{
  "call_id": "CALL-A1B2C3D4",
  "history": [
    { "sender": "user", "text": "I need a CAD laptop with $3500 budget." },
    { "sender": "agent", "text": "The Precision Workstation 7780 fits your needs." }
  ],
  "lead": { "customer_name": "David Miller", "budget": "$3500", "score": 90 },
  "appointment": { "booking_id": "APPT-01485CE5", "date": "2026-11-28", "time_slot": "10:00 AM" }
}
```

**Response `200 OK`**:
```json
{
  "call_id": "CALL-A1B2C3D4",
  "customer_name": "David Miller",
  "contact": "david@techfirm.com",
  "duration_turns": 2,
  "key_topics": ["Hardware Procurement", "Pricing & Budgetary Alignment"],
  "executive_summary": "Customer 'David Miller' engaged with sales agent Alex Carter to explore enterprise solutions. Stated requirements include CAD hardware with a target budget of $3500. Successfully scheduled a 30-minute technical demonstration for 2026-11-28 at 10:00 AM.",
  "lead_qualification_score": 90,
  "lead_status": "Hot (High Intent)",
  "sentiment": "Positive",
  "appointment_booked": true,
  "recommended_next_action": "Assigned to Enterprise Account Executive for scheduled live demonstration."
}
```

#### `GET /api/analytics`
Returns aggregated pipeline metrics from MongoDB (total calls, qualified leads, appointments, conversion rate).

---

### 6. Settings & Configuration

#### `POST /api/settings`
Updates API keys or active voice profile on the fly without server restart.

**Request Body**:
```json
{
  "gemini_api_key": "AIzaSy...",
  "voice": "en-US-GuyNeural"
}
```
