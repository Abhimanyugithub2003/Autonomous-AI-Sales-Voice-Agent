import os
import io
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Response, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from app.config import PORT, HOST, DEFAULT_VOICE, GEMINI_API_KEY
from app.db import db_manager
from app.rag import rag_engine
from app.agent import sales_agent
from app.lead_qualifier import lead_qualifier
from app.calendar_service import calendar_service
from app.tts_service import tts_service
from app.analytics_service import analytics_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_server")

app = FastAPI(
    title="Autonomous AI Sales Voice Agent",
    description="Enterprise Virtual Sales Representative with RAG, Lead Qualification & Calendar Booking",
    version="1.0.0"
)

# Enable CORS for Vite frontend & browser mic audio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    sender: str
    text: str
    timestamp: Optional[str] = None

class ChatTurnRequest(BaseModel):
    call_id: Optional[str] = None
    message: str
    history: Optional[List[ChatMessage]] = []
    current_lead: Optional[Dict[str, Any]] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None

class AppointmentBookingRequest(BaseModel):
    customer_name: str
    contact_info: str
    date: str
    time_slot: str
    topic: Optional[str] = "Product Demo & Technical Discovery"
    notes: Optional[str] = ""

class CallSummaryRequest(BaseModel):
    call_id: str
    history: List[ChatMessage]
    lead: Dict[str, Any]
    appointment: Optional[Dict[str, Any]] = None

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    voice: Optional[str] = None

# Endpoints
@app.get("/api/health")
def health_check():
    db_stat = db_manager.get_status()
    return {
        "status": "healthy",
        "service": "Autonomous AI Sales Voice Agent",
        "database": db_stat,
        "rag_products_indexed": len(rag_engine.products),
        "tts_engine": "Edge Neural TTS (Available)",
        "llm_engine": "Gemini 1.5 Flash" if sales_agent.gemini_model else "Native Enterprise Consultative Brain"
    }

@app.post("/api/chat")
async def chat_turn(req: ChatTurnRequest):
    start_time = time.time()
    call_id = req.call_id or f"CALL-{uuid.uuid4().hex[:8].upper()}"
    
    # Format history
    hist = [{"sender": m.sender, "text": m.text} for m in req.history or []]
    
    # Process turn with Sales Agent Brain
    result = sales_agent.process_turn(
        user_message=req.message,
        conversation_history=hist,
        current_lead=req.current_lead
    )
    
    # Save/update lead in MongoDB
    saved_lead = db_manager.save_or_update_lead(result["lead"])
    
    # Save appointment if created
    saved_booking = None
    if result.get("booking"):
        saved_booking = db_manager.save_appointment(result["booking"])

    # Log turn to calls database
    latency_ms = round((time.time() - start_time) * 1000, 2)
    db_manager.log_call({
        "call_id": call_id,
        "user_message": req.message,
        "agent_reply": result["reply"],
        "latency_ms": latency_ms,
        "lead_id": saved_lead.get("_id"),
        "booking_id": saved_booking.get("booking_id") if saved_booking else None
    })

    return {
        "call_id": call_id,
        "reply": result["reply"],
        "lead": saved_lead,
        "retrieved_products": result["retrieved_products"],
        "booking": saved_booking,
        "latency_ms": latency_ms,
        "llm_engine": result["llm_engine"]
    }

@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """
    Streams neural TTS audio in MP3 format.
    """
    try:
        audio_bytes = await tts_service.generate_speech_audio(req.text, req.voice)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
def get_products():
    return {
        "count": len(rag_engine.products),
        "products": rag_engine.products
    }

@app.post("/api/products/search")
def search_products(query: str, top_k: int = 2):
    results = rag_engine.search(query, top_k=top_k)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

@app.get("/api/leads")
def get_leads(limit: int = 50):
    return {
        "leads": db_manager.get_leads(limit=limit)
    }

@app.get("/api/appointments")
def get_appointments(limit: int = 50):
    return {
        "appointments": db_manager.get_appointments(limit=limit)
    }

@app.get("/api/appointments/slots")
def get_appointment_slots():
    return {
        "slots": calendar_service.get_available_slots()
    }

@app.post("/api/appointments/book")
def book_appointment(req: AppointmentBookingRequest):
    booking = calendar_service.book_appointment(
        customer_name=req.customer_name,
        contact_info=req.contact_info,
        date=req.date,
        time_slot=req.time_slot,
        topic=req.topic or "Enterprise Solution Discovery",
        notes=req.notes or ""
    )
    saved = db_manager.save_appointment(booking)
    return saved

@app.get("/api/appointments/{booking_id}/ics")
def download_ics(booking_id: str):
    apts = db_manager.get_appointments(limit=200)
    target = next((a for a in apts if a.get("booking_id") == booking_id), None)
    if not target:
        target = {
            "booking_id": booking_id,
            "customer_name": "Valued Client",
            "contact_info": "Sales Lead",
            "date": "2026-11-28",
            "time_slot": "10:00 AM",
            "topic": "Fortive AI Enterprise Solution Demo",
            "meeting_link": "https://meet.google.com/ftv-sales-demo"
        }
    ics_text = calendar_service.generate_ics(target)
    return Response(
        content=ics_text,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=meeting_{booking_id}.ics"}
    )

@app.post("/api/call-summary")
def generate_call_summary(req: CallSummaryRequest):
    hist = [{"sender": m.sender, "text": m.text} for m in req.history]
    summary = analytics_service.generate_call_summary(
        call_id=req.call_id,
        conversation_history=hist,
        lead_data=req.lead,
        appointment_data=req.appointment
    )
    return summary

@app.get("/api/analytics")
def get_analytics():
    return analytics_service.get_dashboard_metrics()

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    if req.gemini_api_key is not None:
        sales_agent.update_api_key(req.gemini_api_key)
    if req.voice:
        tts_service.voice = req.voice
    return {
        "message": "Settings updated successfully",
        "llm_engine": "Gemini 1.5 Flash" if sales_agent.gemini_model else "Native Enterprise Consultative Brain",
        "active_voice": tts_service.voice
    }

# Mount static frontend build if it exists
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
