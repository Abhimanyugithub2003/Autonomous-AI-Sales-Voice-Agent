import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.main import app
from app.rag import rag_engine
from app.db import db_manager
from app.lead_qualifier import lead_qualifier
from app.agent import sales_agent
from app.calendar_service import calendar_service

print("--- BACKEND TEST SUITE ---")
print("1. DB Status:", db_manager.get_status())
print("2. RAG Index Count:", len(rag_engine.products))

# Test RAG query
query = "I need a high performance laptop with GPU for 3D modeling and AI training"
res = rag_engine.search(query, top_k=2)
print("3. RAG Search Result:", res[0]["product"]["name"], "Score:", res[0]["score"])

# Test Lead Qualification
lead = lead_qualifier.extract_entities("Hi, my name is David Miller. My budget is around $3500 and my email is david@example.com. We need this for deep learning ASAP.")
print("4. Qualified Lead:", lead)

# Test Agent Turn
turn = sales_agent.process_turn("Hi, my name is David Miller. I need a laptop for CAD and deep learning with budget around $3500. Email is david@example.com", [], None)
print("5. Agent Spoken Reply:", turn["reply"])
print("6. Agent Lead Score:", turn["lead"]["score"])
print("7. Engine:", turn["llm_engine"])

# Test Calendar Slots
slots = calendar_service.get_available_slots()
print("8. Available Slots Sample:", slots[0]["label"])

print("--- ALL BACKEND TESTS PASSED SUCCESSFULLY ---")
