# 🔬 HealthLens

HealthLens is an AI-powered health analytics app that lets you ask questions about 299,000 Americans' behavioral health data in plain English — no SQL knowledge required.

## Data
CDC BRFSS 2024 survey — 299,022 respondents across all 50 US states, covering diabetes, smoking, heart disease, mental health, BMI, and more.

## How it works
- User types a health question in plain English
- LLM (Llama 3.3 via Groq) converts the question to a DuckDB SQL query
- Query runs on cleaned CDC BRFSS 2024 data stored as parquet
- Results display as an interactive table and bar chart

## How to run
```bash
source venv/bin/activate
python -m streamlit run app.py
```

## Known limitations
- Questions must relate to BRFSS 2024 survey columns
- LLM occasionally generates invalid SQL for complex queries
- Puerto Rico mental health values contain outliers above the 30-day monthly maximum — filtered out automatically