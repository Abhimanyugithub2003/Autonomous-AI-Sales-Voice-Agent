import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import httpx
from app.main import app
from app.rag import rag_engine

async def run_pipeline_test():
    print("=" * 60)
    print("AUTONOMOUS AI SALES VOICE AGENT — REGRESSION TEST SUITE")
    print("=" * 60)

    # 1. RAG Index Check
    print(f"\n[1/5] RAG Knowledge Base Verification...")
    print(f"  Products Indexed: {len(rag_engine.products)}")
    search_test = rag_engine.search("laptop for deep learning and 3D modeling", top_k=1)
    assert len(search_test) > 0, "RAG search failed"
    top_p = search_test[0]["product"]["name"]
    print(f"  Search Query: 'laptop for deep learning and 3D modeling'")
    print(f"  Matched Product: {top_p} (Score: {search_test[0]['score']})")

    # 2. Async Client Tests
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Health
        print(f"\n[2/5] API Health & Database Check...")
        r_health = await client.get("/api/health")
        assert r_health.status_code == 200
        health_data = r_health.json()
        print(f"  Service: {health_data['service']}")
        print(f"  Database Mode: {health_data['database']['mode']} (Connected: {health_data['database']['connected']})")
        print(f"  LLM Engine: {health_data['llm_engine']}")

        # Chat Turn
        print(f"\n[3/5] Conversational Sales Agent & BANT Lead Qualification...")
        r_chat = await client.post("/api/chat", json={
            "message": "Hello, my name is Samantha Wright. We need ultraportable laptops for 10 traveling executives. Budget is $2000 per laptop. Email samantha@wrightconsulting.com",
            "history": [],
            "current_lead": None
        })
        assert r_chat.status_code == 200
        chat_data = r_chat.json()
        print(f"  Customer Utterance: '...Samantha Wright... Budget is $2000 per laptop...'")
        print(f"  AI Voice Agent Reply: \"{chat_data['reply']}\"")
        lead = chat_data["lead"]
        print(f"  Extracted Name: {lead.get('customer_name')}")
        print(f"  Extracted Email: {lead.get('email')}")
        print(f"  Extracted Budget: {lead.get('budget')}")
        print(f"  BANT Score: {lead.get('score')} / 100 ({lead.get('status')})")

        # Booking & ICS
        print(f"\n[4/5] Appointment Booking & Google Calendar Synchronization...")
        r_book = await client.post("/api/appointments/book", json={
            "customer_name": lead.get("customer_name") or "Samantha Wright",
            "contact_info": lead.get("email") or "samantha@wrightconsulting.com",
            "date": "2026-11-28",
            "time_slot": "02:00 PM",
            "topic": "ThinkEnterprise Carbon X1 Volume Consultation"
        })
        assert r_book.status_code == 200
        booking = r_book.json()
        print(f"  Booking Created: {booking['booking_id']} on {booking['date']} at {booking['time_slot']}")
        print(f"  Meeting Link: {booking['meeting_link']}")

        # ICS Check
        r_ics = await client.get(f"/api/appointments/{booking['booking_id']}/ics")
        assert r_ics.status_code == 200
        assert "BEGIN:VCALENDAR" in r_ics.text
        print(f"  iCalendar (.ics) Invitee Stream: Verified OK ({len(r_ics.text)} bytes)")

        # Summary & Analytics
        print(f"\n[5/5] Post-Call Executive Summary & CRM Pipeline Analytics...")
        r_summary = await client.post("/api/call-summary", json={
            "call_id": chat_data["call_id"],
            "history": [
                {"sender": "agent", "text": "Hello, welcome to Fortive AI."},
                {"sender": "user", "text": "We need ultraportable laptops for 10 traveling executives with $2000 budget."},
                {"sender": "agent", "text": chat_data["reply"]}
            ],
            "lead": lead,
            "appointment": booking
        })
        assert r_summary.status_code == 200
        summary = r_summary.json()
        print(f"  Executive Summary: \"{summary['executive_summary'][:140]}...\"")
        print(f"  Recommended Next Action: \"{summary['recommended_next_action']}\"")

        r_analytics = await client.get("/api/analytics")
        assert r_analytics.status_code == 200
        m = r_analytics.json()
        print(f"  Total Pipeline Calls: {m['total_calls']}")
        print(f"  Qualified Leads in MongoDB: {m['total_leads']}")
        print(f"  Appointments Booked: {m['appointments_booked']}")
        print(f"  Conversion Rate: {m['conversion_rate_percent']}%")

    print("\n" + "=" * 60)
    print("ALL 5 SYSTEM TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
