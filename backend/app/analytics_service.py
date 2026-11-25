import logging
from typing import List, Dict, Any
from app.db import db_manager

logger = logging.getLogger("analytics_service")

class AnalyticsService:
    """
    Call Summarization, Sentiment Evaluation & B2B Sales Pipeline Analytics.
    """
    
    def generate_call_summary(
        self,
        call_id: str,
        conversation_history: List[Dict[str, str]],
        lead_data: Dict[str, Any],
        appointment_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Produces a structured post-call executive summary.
        """
        user_utterances = [msg["text"] for msg in conversation_history if msg.get("sender") == "user"]
        agent_utterances = [msg["text"] for msg in conversation_history if msg.get("sender") == "agent"]
        full_dialogue = " ".join(user_utterances)

        # 1. Key topics identified
        topics = []
        if any(w in full_dialogue.lower() for w in ["laptop", "carbon", "x1", "workstation", "probook", "hardware"]):
            topics.append("Hardware Procurement")
        if any(w in full_dialogue.lower() for w in ["price", "cost", "budget", "$"]):
            topics.append("Pricing & Budgetary Alignment")
        if any(w in full_dialogue.lower() for w in ["cad", "engineering", "ai", "docker", "battery"]):
            topics.append("Technical Requirements & Workloads")
        if appointment_data or any(w in full_dialogue.lower() for w in ["meeting", "demo", "schedule", "book"]):
            topics.append("Product Demo Scheduling")

        if not topics:
            topics.append("General Solution Discovery")

        # 2. Executive Summary
        customer_name = lead_data.get("customer_name") or "Prospective Client"
        budget = lead_data.get("budget") or "Not specified"
        reqs = ", ".join(lead_data.get("requirements", [])) or "Standard business workloads"
        
        summary_text = (
            f"Customer '{customer_name}' engaged with sales agent Alex Carter to explore enterprise solutions. "
            f"Stated requirements include {reqs} with a target budget of {budget}. "
        )
        if appointment_data:
            summary_text += (
                f"Successfully scheduled a 30-minute technical demonstration for {appointment_data.get('date')} "
                f"at {appointment_data.get('time_slot')}. Invitation sent to {appointment_data.get('contact_info')}."
            )
        else:
            summary_text += "Lead expressed active interest; recommended follow-up via email with detailed product catalog sheet."

        # 3. Recommended Next Actions
        if appointment_data:
            next_action = "Assigned to Enterprise Account Executive for scheduled live demonstration."
        elif lead_data.get("score", 0) >= 60:
            next_action = "Send customized proposal and schedule follow-up call within 24 hours."
        else:
            next_action = "Nurture with product spec sheets and case studies via marketing automation."

        summary_payload = {
            "call_id": call_id,
            "customer_name": customer_name,
            "contact": lead_data.get("email") or lead_data.get("phone") or "Pending",
            "duration_turns": len(conversation_history),
            "key_topics": topics,
            "executive_summary": summary_text,
            "lead_qualification_score": lead_data.get("score", 40),
            "lead_status": lead_data.get("status", "Warm"),
            "sentiment": lead_data.get("sentiment", "Positive"),
            "appointment_booked": bool(appointment_data),
            "appointment_details": appointment_data,
            "recommended_next_action": next_action
        }

        # Save to database
        db_manager.save_summary(summary_payload)
        return summary_payload

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Aggregates live sales metrics from MongoDB.
        """
        leads = db_manager.get_leads(limit=200)
        appointments = db_manager.get_appointments(limit=200)
        calls = db_manager.get_calls(limit=200)

        total_leads = len(leads)
        total_apts = len(appointments)
        total_calls = max(len(calls), total_leads)

        hot_leads = sum(1 for l in leads if "Hot" in l.get("status", ""))
        warm_leads = sum(1 for l in leads if "Warm" in l.get("status", ""))
        cold_leads = sum(1 for l in leads if "Cold" in l.get("status", ""))

        conversion_rate = round((total_apts / max(total_calls, 1)) * 100, 1)

        return {
            "total_calls": total_calls,
            "total_leads": total_leads,
            "appointments_booked": total_apts,
            "conversion_rate_percent": conversion_rate,
            "lead_distribution": {
                "hot": hot_leads,
                "warm": warm_leads,
                "cold": cold_leads
            },
            "recent_leads": leads[:10],
            "recent_appointments": appointments[:10]
        }

analytics_service = AnalyticsService()
