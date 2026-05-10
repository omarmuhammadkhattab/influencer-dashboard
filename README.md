# Influencer Analytics Dashboard

A prototype dashboard that tracks influencer performance for a Shopify e-commerce store.

## 🚀 Live Demo

> https://influencer-dashboard-demo.streamlit.app/

---

## 📦 Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/influencer-dashboard
cd influencer-dashboard
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Create a `.env` file in the root:
```
SHOPIFY_STORE=influencer-analytics-demo.myshopify.com
SHOPIFY_TOKEN=your_admin_api_token
```

### 4. Seed the store with test data
```bash
python seed_data.py
```
This creates:
- 1 test product with a variant
- 30 influencer price rules + discount codes
- ~800 realistic orders across 3 months, tagged with channel and return information

### 5. Run the dashboard
```bash
streamlit run app.py
```

---

## 🏗️ Architecture

```
Shopify Dev Store
      │
      │  Admin REST API (paginated)
      ▼
  app.py (Streamlit)
      │
      ├── fetch_orders()     → pulls all orders with pagination
      ├── parse_orders()     → normalizes into a flat DataFrame
      ├── compute_metrics()  → aggregates per influencer:
      │       revenue, return rate, net revenue, worth-it score
      │
      └── Plotly charts + Streamlit UI
```

### Why this stack?

| Choice | Reason |
|---|---|
| **Python** | Best ecosystem for data manipulation (Pandas) |
| **Streamlit** | Fastest path from data → interactive dashboard; free deployment |
| **Plotly** | Interactive, professional charts with minimal boilerplate |
| **Shopify Admin REST API** | Direct access to orders, discounts; well-documented; no webhook complexity needed for a prototype |
| **python-dotenv** | Keeps credentials out of source code |

### Why not a heavier stack?

A React + FastAPI setup would be appropriate for a production app with user authentication, multi-store support, and real-time webhooks. For a prototype that needs to be readable, deployable, and demonstrable in one day — Streamlit is the right call.

### Data flow

1. `seed_data.py` creates test data directly via Shopify Admin API — no CSV imports, no mocking
2. `app.py` fetches live data on each load (cached for 5 minutes)
3. All metric computation happens in-memory with Pandas — no intermediate database needed at this scale

### Meta Ads attribution

The scenario describes influencer codes being reused in Meta Ads. In the seeded data, orders are tagged `meta_ad` or `influencer` to simulate UTM-based attribution. In production, this would use Shopify's `landing_site` field (which captures UTM parameters) to automatically classify traffic sources — no manual tagging needed.

---

## 📊 Dashboard Features

- **Revenue per influencer** — gross revenue, sorted and color-coded by tier
- **Return rate per influencer** — who's driving costly returns
- **"Worth It?" quadrant** — scatter plot of net revenue vs return rate with a composite score
- **Meta Ads attribution** — how many orders per code came from ads vs organic influencer traffic
- **Date range + tier filters** — slice the data as needed
- **Full ranking table** — sortable, exportable

---

## 🤖 AI Tools Used

| Tool | How it was used |
|---|---|
| **Claude (Anthropic)** | Architecture design, code generation, debugging, README drafting |
| **GitHub Copilot** | Inline code completion during development |

Using Claude significantly accelerated development — particularly for designing the data model, writing the Shopify API pagination logic, and structuring the Plotly charts. Every generated output was reviewed, tested, and adapted to fit the actual scenario requirements.

This is consistent with how I work professionally: AI tools handle boilerplate and first drafts; judgment, architecture decisions, and debugging remain human-driven.

---

## 📁 File Structure

```
influencer-dashboard/
├── app.py              # Streamlit dashboard
├── seed_data.py        # Shopify store seeder
├── requirements.txt    # Python dependencies
├── .env                # API credentials (not committed)
├── .gitignore
└── README.md
```
