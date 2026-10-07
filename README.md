# Privacy-Aware User Journey Intelligence System for E-Commerce

A full-stack e-commerce intelligence platform that combines **privacy-aware user journey analytics** with an **AI-powered consumer product decision interpreter**.

The system analyzes how users browse, navigate, abandon, and purchase while also helping consumers understand what product specifications actually mean through **✦ Know Before You Buy**.

## Tech Stack

- **Frontend:** React, Vite, JavaScript, CSS
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic
- **Database:** SQLite
- **Analytics Dashboard:** Streamlit, Pandas, Plotly
- **AI:** Ollama, Llama 3.2 (`llama3.2:latest`)
- **Privacy:** Anonymous session tracking, data minimization, HMAC-SHA256 pseudonymization

## Key Features

- 🛍️ Responsive e-commerce storefront with search, products, cart, checkout and purchase flow
- 🔐 Privacy-aware anonymous user journey tracking
- 📊 Real-time event collection and journey reconstruction
- 📈 Conversion, abandonment, behavioral segmentation and journey analytics
- 🔎 Causal analysis and explainable recommendations
- 🔮 What-If simulation for hypothetical journey improvements
- ✦ **Know Before You Buy** AI product interpretation
- 🤖 Local AI inference using **Ollama + Llama 3.2**
- 🧠 AI-generated explanations, implications, trade-offs, considerations and missing information
- 🛡️ Hallucination-aware, evidence-grounded product interpretation

## Architecture

```text
React/Vite Storefront
        ↓
FastAPI Backend
   ↙           ↘
Events       Product AI
   ↓             ↓
SQLite       Ollama
   ↓        Llama 3.2
   ↓
Journey Analytics
        ↓
Streamlit Dashboard

Project Goal
An e-commerce intelligence platform that understands both sides of the shopping experience — how customers behave and what customers are buying.

# RUN:
cd path\to\privacy-aware-user-journey
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python scripts\seed_data.py


# T1:
.\venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload

# T2:
cd frontend
npm run dev
http://localhost:5173

# T3:
cd ..
privacy-aware-user-journey
.\venv\Scripts\Activate.ps1
streamlit run dashboard\app.py
Local URL: http://localhost:8501