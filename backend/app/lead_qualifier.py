import re
from typing import Dict, Any, List

class LeadQualifier:
    """
    Lead Qualification & Extraction Engine.
    Uses BANT (Budget, Authority, Need, Timeline) framework and conversational sentiment analysis.
    """
    
    # Common name patterns (e.g. "My name is John Doe", "I am Alice", "This is Robert")
    NAME_PATTERNS = [
        r"(?:my name is|i am|this is|i'm|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"(?:name:\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    ]

    # Email pattern
    EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    # Phone pattern
    PHONE_PATTERNS = [
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\b\d{10}\b"
    ]

    # Budget pattern
    BUDGET_PATTERNS = [
        r"\$(\d+(?:,\d{3})*|\d+)(?:\s*(?:k|thousand|usd|dollars))?\b",
        r"(?:budget(?:\s*is)?(?:\s*around)?(?:\s*of)?)\s*(?:under|around|approx|up to)?\s*\$?(\d+[\d,]*\s*(?:k|thousand)?)\b",
        r"(?:under|around|approx|up to|about)\s*\$?(\d+[\d,]*)\s*(?:dollars|usd)?\b"
    ]

    # Timeline patterns
    TIMELINE_PATTERNS = [
        r"(immediately|asap|this week|next week|within a month|this month|in (\d+) weeks?|q[1-4]|next quarter)",
        r"(urgent|soon|by (?:end of )?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|month|year))"
    ]

    # Positive sentiment keywords
    POSITIVE_WORDS = {"great", "perfect", "interested", "sounds good", "love", "excellent", "awesome", "impressive", "ready", "need this", "book", "schedule", "yes"}
    # Hesitant / objection keywords
    HESITANT_WORDS = {"expensive", "too much", "not sure", "maybe", "doubt", "competitor", "cheaper", "hesitant", "think about it", "pricey"}

    def extract_entities(self, text: str, existing_lead: Dict[str, Any] = None) -> Dict[str, Any]:
        lead = existing_lead.copy() if existing_lead else {
            "customer_name": None,
            "email": None,
            "phone": None,
            "budget": None,
            "requirements": [],
            "timeline": None,
            "interest_level": "Medium",
            "sentiment": "Neutral",
            "score": 40,
            "status": "Warm"
        }

        # 1. Extract Name
        if not lead.get("customer_name"):
            for pat in self.NAME_PATTERNS:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    lead["customer_name"] = match.group(1).strip()
                    break

        # 2. Extract Email
        email_match = re.search(self.EMAIL_PATTERN, text)
        if email_match:
            lead["email"] = email_match.group(0).lower().rstrip(".,;:!?'\"")

        # 3. Extract Phone
        for pat in self.PHONE_PATTERNS:
            phone_match = re.search(pat, text)
            if phone_match and not lead.get("phone"):
                # Clean up
                cleaned_phone = phone_match.group(0).strip()
                if len(re.sub(r"\D", "", cleaned_phone)) >= 10:
                    lead["phone"] = cleaned_phone
                    break

        # 4. Extract Budget
        for pat in self.BUDGET_PATTERNS:
            budget_match = re.search(pat, text, re.IGNORECASE)
            if budget_match:
                raw_b = budget_match.group(0).strip().rstrip(".,;:!?'\"")
                lead["budget"] = raw_b
                break

        # 5. Extract Timeline
        for pat in self.TIMELINE_PATTERNS:
            time_match = re.search(pat, text, re.IGNORECASE)
            if time_match:
                lead["timeline"] = time_match.group(0).strip()
                break

        # 6. Extract Technical Requirements
        req_triggers = [
            ("cad", "3D CAD / Modeling / Engineering Work"),
            ("ai", "Local AI / Deep Learning Acceleration"),
            ("docker", "DevOps / Docker / Kubernetes"),
            ("battery", "Long Battery Life (15+ Hours)"),
            ("lightweight", "Ultra-lightweight / Portability (< 1.2kg)"),
            ("rugged", "Ruggedized / Industrial Grade / IP65"),
            ("oled", "High-Resolution OLED / Color Accuracy"),
            ("mac", "macOS Developer Ecosystem"),
            ("budget", "Cost-effective Corporate Fleet")
        ]
        text_lower = text.lower()
        current_reqs = set(lead.get("requirements", []))
        for trigger, label in req_triggers:
            if trigger in text_lower:
                current_reqs.add(label)
        lead["requirements"] = list(current_reqs)

        # 7. Sentiment
        pos_hits = sum(1 for w in self.POSITIVE_WORDS if w in text_lower)
        neg_hits = sum(1 for w in self.HESITANT_WORDS if w in text_lower)
        if pos_hits > neg_hits:
            lead["sentiment"] = "Positive"
        elif neg_hits > pos_hits:
            lead["sentiment"] = "Hesitant / Price Sensitive"
        else:
            lead["sentiment"] = "Neutral / Analytical"

        # 8. Compute BANT Qualification Score (0-100)
        score = 20  # Base for initiating conversation
        if lead.get("customer_name"):
            score += 15
        if lead.get("email") or lead.get("phone"):
            score += 25
        if lead.get("budget"):
            score += 15
        if lead.get("requirements"):
            score += 15
        if lead.get("timeline"):
            score += 10
        if lead.get("sentiment") == "Positive":
            score += 10

        lead["score"] = min(score, 100)

        # Status categorization
        if lead["score"] >= 75:
            lead["status"] = "Hot (High Intent)"
            lead["interest_level"] = "High"
        elif lead["score"] >= 50:
            lead["status"] = "Warm (Active Evaluation)"
            lead["interest_level"] = "Medium"
        else:
            lead["status"] = "Cold (Early Inquirer)"
            lead["interest_level"] = "Low"

        return lead

lead_qualifier = LeadQualifier()
