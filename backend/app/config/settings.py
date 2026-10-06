import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./journey.db")
PSEUDONYMIZATION_SECRET=os.getenv("PSEUDONYMIZATION_SECRET","dev-secret")
SESSION_TIMEOUT_MINUTES=int(os.getenv("SESSION_TIMEOUT_MINUTES","30"))
RETENTION_DAYS=int(os.getenv("RETENTION_DAYS","90"))
MIN_AGGREGATION_THRESHOLD=int(os.getenv("MIN_AGGREGATION_THRESHOLD","3"))
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","")
AI_MODEL=os.getenv("AI_MODEL","gpt-4o-mini")
