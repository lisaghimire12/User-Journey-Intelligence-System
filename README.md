# Privacy-Aware User Journey Intelligence System for E-Commerce

A complete final-year project that combines **privacy-aware e-commerce analytics** with an **AI-based consumer product decision interpreter**.

The system understands both sides of an e-commerce experience:

- **Business side:** understand how users browse, compare, abandon, and purchase.
- **Consumer side:** help users understand what product specifications actually mean before buying.

The project includes a premium React/Vite dummy e-commerce storefront, a FastAPI analytics backend, privacy-aware event tracking, journey reconstruction, behavioral analytics, causal analysis, simulation, explainable recommendations, a Streamlit intelligence dashboard, and a local AI-powered **✦ Know Before You Buy** product interpreter.

---

## Features

### E-Commerce Storefront

- Premium React/Vite e-commerce interface
- Product listing and product detail pages
- Product search
- Product categories
- Product options such as size
- Shopping cart
- Checkout flow
- Purchase flow
- Responsive desktop, tablet, and mobile UI

### Privacy-Aware User Journey Tracking

The storefront records user interactions without collecting unnecessary personal information.

Tracked events include:

- `page_view`
- `search`
- `view_item`
- `select_size`
- `add_to_cart`
- `view_cart`
- `begin_checkout`
- `purchase`
- `product_insight_opened`
- `product_insight_section_viewed`
- `product_source_expanded`
- `product_insight_closed`

Anonymous user and session identifiers are used for journey reconstruction.

Sensitive personal information such as:

- passwords
- payment information
- email addresses
- phone numbers
- physical addresses

is not required for the analytics system.

User identifiers are designed to be privacy-aware and can be pseudonymized using **HMAC-SHA256**.

---

## AI: ✦ Know Before You Buy

The project includes an AI-powered consumer product decision interpreter.

The feature is accessed from the product page through:

> **✦ KNOW BEFORE YOU BUY**

The AI receives the supplied product information and explains it in simple language.

It can identify:

- important product facts
- what technical specifications mean
- practical implications
- meaningful relationships between attributes
- meaningful trade-offs
- considerations for the consumer
- information that has not been provided
- a concise evidence-grounded bottom line

The system is designed to avoid simply repeating the product description.

For example, if a product provides multiple related specifications, the AI can reason about their relationship rather than displaying unrelated explanations for each field.

The AI does **not** use a fixed set of hard-coded rules such as:

```text
IF category == clothing:
    explain fabric

IF category == electronics:
    explain RAM

IF category == food:
    explain protein

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