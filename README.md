# Privacy-Aware User Journey Intelligence System for E-Commerce

Complete final-year project:
- premium React/Vite dummy e-commerce storefront
- privacy-aware event collection and HMAC-SHA256 pseudonymization
- SQLAlchemy analytics data layer
- session and journey reconstruction
- behavioral segmentation
- cautious causal-analysis layer
- what-if simulator
- explainable recommendations
- Streamlit intelligence dashboard
- consumer-facing **✦ Know Before You Buy** interpreter
- synthetic demo data and automated tests

## Run

### Python
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/seed_data.py
uvicorn backend.app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Dashboard
From project root:
```bash
streamlit run dashboard/app.py
```

Store: http://localhost:5173
API docs: http://localhost:8000/docs
Dashboard: http://localhost:8501

SQLite is the zero-setup development default. Change DATABASE_URL to PostgreSQL when desired.

The AI feature has a deterministic evidence-grounded local fallback so the project works without an API key. An OpenAI key can be added later without exposing it to the browser.
