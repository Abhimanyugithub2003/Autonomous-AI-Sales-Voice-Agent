import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db import db_manager
from datetime import datetime, timedelta

sample_leads = [
  {
    "customer_name": "Marcus Vance",
    "email": "m.vance@nexustech.io",
    "phone": "+1 (555) 432-8910",
    "budget": "$18,000 (Fleet of 8)",
    "requirements": ["Ultra-lightweight / Portability (< 1.2kg)", "Long Battery Life (15+ Hours)"],
    "timeline": "Within 2 weeks",
    "interest_level": "High",
    "sentiment": "Positive",
    "score": 95,
    "status": "Hot (High Intent)"
  },
  {
    "customer_name": "Sarah Jenkins",
    "email": "sjenkins@aerocore.com",
    "phone": "+1 (555) 891-2345",
    "budget": "$3,500",
    "requirements": ["3D CAD / Modeling / Engineering Work", "Local AI / Deep Learning Acceleration"],
    "timeline": "Next month",
    "interest_level": "High",
    "sentiment": "Positive",
    "score": 90,
    "status": "Hot (High Intent)"
  },
  {
    "customer_name": "Elena Rostova",
    "email": "elena.r@quantumdyn.org",
    "phone": "+1 (555) 345-6789",
    "budget": "$2,500",
    "requirements": ["macOS Developer Ecosystem", "DevOps / Docker / Kubernetes"],
    "timeline": "ASAP",
    "interest_level": "Medium",
    "sentiment": "Neutral / Analytical",
    "score": 75,
    "status": "Warm (Active Evaluation)"
  },
  {
    "customer_name": "Kevin Patel",
    "email": "kevin@patelfinancial.com",
    "phone": "+1 (555) 210-9876",
    "budget": "$1,100",
    "requirements": ["Cost-effective Corporate Fleet"],
    "timeline": "Q4",
    "interest_level": "Low",
    "sentiment": "Hesitant / Price Sensitive",
    "score": 45,
    "status": "Cold (Early Inquirer)"
  }
]

sample_appointments = [
  {
    "booking_id": "APPT-VANCE01",
    "customer_name": "Marcus Vance",
    "contact_info": "m.vance@nexustech.io",
    "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
    "time_slot": "10:00 AM",
    "topic": "ThinkEnterprise Carbon X1 Enterprise Fleet Consultation",
    "meeting_link": "https://meet.google.com/ftv-vnc-928",
    "calendar_provider": "Google Calendar (Synchronized)",
    "status": "Confirmed"
  },
  {
    "booking_id": "APPT-JENK02",
    "customer_name": "Sarah Jenkins",
    "contact_info": "sjenkins@aerocore.com",
    "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    "time_slot": "02:00 PM",
    "topic": "Precision Workstation 7780 CAD Simulation Demo",
    "meeting_link": "https://meet.google.com/ftv-jnx-481",
    "calendar_provider": "Google Calendar (Synchronized)",
    "status": "Confirmed"
  }
]

def seed():
    print("Seeding database with sample sales records...")
    for lead in sample_leads:
        res = db_manager.save_or_update_lead(lead)
        print(f"  + Seeded Lead: {res['customer_name']} [{res['status']}]")

    for apt in sample_appointments:
        res = db_manager.save_appointment(apt)
        print(f"  + Seeded Appointment: {res['booking_id']} for {res['customer_name']}")

    stat = db_manager.get_status()
    print("\nDatabase Status after seeding:", stat)
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
