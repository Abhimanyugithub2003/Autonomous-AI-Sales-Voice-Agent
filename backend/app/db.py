import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pymongo
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from app.config import MONGO_URI, MONGO_DB_NAME, DATA_DIR

logger = logging.getLogger("sales_db")
logging.basicConfig(level=logging.INFO)

FALLBACK_DB_FILE = DATA_DIR / "local_store.json"

class DatabaseManager:
    def __init__(self):
        self.connected_to_mongo = False
        self.client: Optional[pymongo.MongoClient] = None
        self.db = None
        self._memory_store = {
            "calls": [],
            "leads": [],
            "appointments": [],
            "summaries": []
        }
        self._load_fallback()
        self._init_mongo()

    def _load_fallback(self):
        if FALLBACK_DB_FILE.exists():
            try:
                with open(FALLBACK_DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memory_store.update(data)
            except Exception as e:
                logger.warning(f"Could not load fallback store: {e}")

    def _persist_fallback(self):
        try:
            FALLBACK_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(FALLBACK_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self._memory_store, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist fallback store: {e}")

    def _init_mongo(self):
        try:
            self.client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            # Test connection
            self.client.server_info()
            self.db = self.client[MONGO_DB_NAME]
            self.connected_to_mongo = True
            logger.info(f"Connected to MongoDB database '{MONGO_DB_NAME}' successfully at {MONGO_URI}")
            
            # Create indexes
            self.db.leads.create_index([("email", pymongo.ASCENDING)], sparse=True)
            self.db.leads.create_index([("phone", pymongo.ASCENDING)], sparse=True)
            self.db.appointments.create_index([("date", pymongo.ASCENDING), ("time_slot", pymongo.ASCENDING)])
            self.db.calls.create_index([("timestamp", pymongo.DESCENDING)])
        except (ServerSelectionTimeoutError, PyMongoError) as e:
            self.connected_to_mongo = False
            logger.warning(f"MongoDB not reachable ({e}). Using persistent JSON fallback store.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": "mongodb" if self.connected_to_mongo else "json_fallback",
            "connected": self.connected_to_mongo,
            "database": MONGO_DB_NAME if self.connected_to_mongo else "local_store.json",
            "counts": {
                "leads": self.db.leads.count_documents({}) if self.connected_to_mongo else len(self._memory_store["leads"]),
                "appointments": self.db.appointments.count_documents({}) if self.connected_to_mongo else len(self._memory_store["appointments"]),
                "calls": self.db.calls.count_documents({}) if self.connected_to_mongo else len(self._memory_store["calls"])
            }
        }

    # Leads
    def save_or_update_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        lead_data["updated_at"] = datetime.utcnow().isoformat()
        if "created_at" not in lead_data:
            lead_data["created_at"] = datetime.utcnow().isoformat()
            
        identifier = lead_data.get("email") or lead_data.get("phone") or lead_data.get("customer_name")
        
        if self.connected_to_mongo:
            try:
                if identifier:
                    filter_query = {
                        "$or": [
                            {"email": lead_data.get("email")} if lead_data.get("email") else None,
                            {"phone": lead_data.get("phone")} if lead_data.get("phone") else None,
                            {"customer_name": lead_data.get("customer_name")} if lead_data.get("customer_name") else None
                        ]
                    }
                    filter_query["$or"] = [q for q in filter_query["$or"] if q is not None]
                    
                    if filter_query["$or"]:
                        result = self.db.leads.find_one_and_update(
                            filter_query,
                            {"$set": lead_data},
                            upsert=True,
                            return_document=pymongo.ReturnDocument.AFTER
                        )
                        result["_id"] = str(result["_id"])
                        return result

                res = self.db.leads.insert_one(lead_data)
                lead_data["_id"] = str(res.inserted_id)
                return lead_data
            except Exception as e:
                logger.error(f"Error saving lead in Mongo: {e}")

        # Fallback store
        for i, item in enumerate(self._memory_store["leads"]):
            if identifier and (item.get("email") == lead_data.get("email") or item.get("phone") == lead_data.get("phone") or item.get("customer_name") == lead_data.get("customer_name")):
                item.update(lead_data)
                self._persist_fallback()
                return item
        lead_data["_id"] = f"lead_{len(self._memory_store['leads']) + 1}"
        self._memory_store["leads"].append(lead_data)
        self._persist_fallback()
        return lead_data

    def get_leads(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.connected_to_mongo:
            try:
                cursor = self.db.leads.find().sort("updated_at", -1).limit(limit)
                leads = []
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    leads.append(doc)
                return leads
            except Exception as e:
                logger.error(f"Error fetching leads from Mongo: {e}")
        return sorted(self._memory_store["leads"], key=lambda x: x.get("updated_at", ""), reverse=True)[:limit]

    # Appointments
    def save_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        appointment_data["created_at"] = datetime.utcnow().isoformat()
        if "status" not in appointment_data:
            appointment_data["status"] = "confirmed"

        if self.connected_to_mongo:
            try:
                res = self.db.appointments.insert_one(appointment_data)
                appointment_data["_id"] = str(res.inserted_id)
                return appointment_data
            except Exception as e:
                logger.error(f"Error saving appointment in Mongo: {e}")

        appointment_data["_id"] = f"apt_{len(self._memory_store['appointments']) + 1}"
        self._memory_store["appointments"].append(appointment_data)
        self._persist_fallback()
        return appointment_data

    def get_appointments(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.connected_to_mongo:
            try:
                cursor = self.db.appointments.find().sort("date", -1).limit(limit)
                apts = []
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    apts.append(doc)
                return apts
            except Exception as e:
                logger.error(f"Error fetching appointments from Mongo: {e}")
        return sorted(self._memory_store["appointments"], key=lambda x: x.get("date", ""), reverse=True)[:limit]

    # Calls & Transcripts
    def log_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        call_data["timestamp"] = datetime.utcnow().isoformat()
        if self.connected_to_mongo:
            try:
                res = self.db.calls.insert_one(call_data)
                call_data["_id"] = str(res.inserted_id)
                return call_data
            except Exception as e:
                logger.error(f"Error logging call in Mongo: {e}")

        call_data["_id"] = f"call_{len(self._memory_store['calls']) + 1}"
        self._memory_store["calls"].append(call_data)
        self._persist_fallback()
        return call_data

    def get_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.connected_to_mongo:
            try:
                cursor = self.db.calls.find().sort("timestamp", -1).limit(limit)
                calls = []
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    calls.append(doc)
                return calls
            except Exception as e:
                logger.error(f"Error getting calls from Mongo: {e}")
        return sorted(self._memory_store["calls"], key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    # Summaries
    def save_summary(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        summary_data["created_at"] = datetime.utcnow().isoformat()
        if self.connected_to_mongo:
            try:
                res = self.db.summaries.insert_one(summary_data)
                summary_data["_id"] = str(res.inserted_id)
                return summary_data
            except Exception as e:
                logger.error(f"Error saving summary in Mongo: {e}")

        summary_data["_id"] = f"sum_{len(self._memory_store['summaries']) + 1}"
        self._memory_store["summaries"].append(summary_data)
        self._persist_fallback()
        return summary_data

db_manager = DatabaseManager()
