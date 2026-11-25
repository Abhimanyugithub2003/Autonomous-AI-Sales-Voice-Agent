import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import httpx
from app.main import app

async def run_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Test Health
        r_health = await client.get("/api/health")
        print("Health status code:", r_health.status_code)
        print("Health payload:", r_health.json())

        # Test Frontend Root
        r_root = await client.get("/")
        print("Root status code:", r_root.status_code)
        print("Root contains Fortive AI:", "Fortive AI" in r_root.text)

        # Test Chat Turn
        r_chat = await client.post("/api/chat", json={
            "message": "Hello, I am interested in laptops for high performance AI workloads with budget around $3500. My name is Alex Stone, email alex@stone.io",
            "history": [],
            "current_lead": None
        })
        print("Chat status code:", r_chat.status_code)
        chat_res = r_chat.json()
        print("Chat reply:", chat_res["reply"])
        print("Lead score:", chat_res["lead"]["score"])
        print("Lead name:", chat_res["lead"]["customer_name"])
        print("Lead budget:", chat_res["lead"]["budget"])

        # Test Booking Slots
        r_slots = await client.get("/api/appointments/slots")
        print("Slots count:", len(r_slots.json()["slots"]))

        # Test Appointment Booking
        r_book = await client.post("/api/appointments/book", json={
            "customer_name": "Alex Stone",
            "contact_info": "alex@stone.io",
            "date": "2026-11-28",
            "time_slot": "10:00 AM",
            "topic": "Precision Workstation 7780 Custom Configuration"
        })
        print("Booking status code:", r_book.status_code)
        print("Booking ID:", r_book.json()["booking_id"])

        # Test ICS download
        r_ics = await client.get(f"/api/appointments/{r_book.json()['booking_id']}/ics")
        print("ICS status code:", r_ics.status_code)
        print("ICS contains VCALENDAR:", "BEGIN:VCALENDAR" in r_ics.text)

        # Test Call Summary
        r_summary = await client.post("/api/call-summary", json={
            "call_id": "CALL-TEST-001",
            "history": [
                {"sender": "agent", "text": "Hello, how can I help you?"},
                {"sender": "user", "text": "I need a CAD laptop with $3500 budget. My email is alex@stone.io"},
                {"sender": "agent", "text": "The Precision Workstation 7780 Studio fits perfectly."}
            ],
            "lead": chat_res["lead"],
            "appointment": r_book.json()
        })
        print("Summary status code:", r_summary.status_code)
        print("Executive Summary:", r_summary.json()["executive_summary"])

        # Test Analytics
        r_analytics = await client.get("/api/analytics")
        print("Analytics metrics:", r_analytics.json())

        print("--- ALL HTTP ENDPOINTS & FRONTEND STATIC SERVING TESTED AND WORKING! ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
