import os
import streamlit as st
import duckdb
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

FIPS_TO_STATE = {
    1:'Alabama', 2:'Alaska', 4:'Arizona', 5:'Arkansas', 6:'California',
    8:'Colorado', 9:'Connecticut', 10:'Delaware', 11:'DC', 12:'Florida',
    13:'Georgia', 15:'Hawaii', 16:'Idaho', 17:'Illinois', 18:'Indiana',
    19:'Iowa', 20:'Kansas', 21:'Kentucky', 22:'Louisiana', 23:'Maine',
    24:'Maryland', 25:'Massachusetts', 26:'Michigan', 27:'Minnesota',
    28:'Mississippi', 29:'Missouri', 30:'Montana', 31:'Nebraska', 32:'Nevada',
    33:'New Hampshire', 34:'New Jersey', 35:'New Mexico', 36:'New York',
    37:'North Carolina', 38:'North Dakota', 39:'Ohio', 40:'Oklahoma',
    41:'Oregon', 42:'Pennsylvania', 44:'Rhode Island', 45:'South Carolina',
    46:'South Dakota', 47:'Tennessee', 48:'Texas', 49:'Utah', 50:'Vermont',
    51:'Virginia', 53:'Washington', 54:'West Virginia', 55:'Wisconsin',
    56:'Wyoming', 66:'Guam', 72:'Puerto Rico', 78:'Virgin Islands'
}

st.set_page_config(page_title="HealthLens", page_icon="🔬", layout="wide")

@st.cache_data
def load_data():
    return pd.read_parquet('data/processed/brfss_clean.parquet')

df = load_data()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SCHEMA = """
You are a SQL expert. Convert the user's question to a DuckDB SQL query.
The table is called 'df' and has these columns:
- diabetes: 'Yes', 'No', 'Yes - pregnancy', 'Pre-diabetes'
- smoking: 'Yes', 'No'
- heart_attack: 'Yes', 'No'
- health_insurance: 'Yes', 'No'
- exercise: 'Yes', 'No'
- alcohol: 'Yes', 'No'
- general_health: 'Excellent', 'Very good', 'Good', 'Fair', 'Poor'
- sex: 'Male', 'Female'
- _STATE: FIPS state code (number)
- _BMI5: BMI multiplied by 100
- MENTHLTH: number of bad mental health days (0-30)
Note: All refused and don't know values have been removed. Data is clean.
Return ONLY the SQL query, nothing else.
Always use LIMIT 100 unless the user asks for all data. Never return more than 100 rows.
Always aggregate data - never SELECT raw rows without GROUP BY.
MENTHLTH values are 0-30 (days per month). Ignore values above 30 as outliers.
Always include GROUP BY when using COUNT, AVG, SUM or any aggregate function.
If the question is not about health data, respond with: SELECT 'Please ask a health-related question' as message
"""

def ask(question):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SCHEMA},
            {"role": "user", "content": question}
        ]
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    result = duckdb.query(sql).df()
    if '_STATE' in result.columns:
        result['_STATE'] = result['_STATE'].map(FIPS_TO_STATE)
    return sql, result
st.title("🔬 HealthLens")
st.markdown("**Ask questions about 299,000 Americans' health data in plain English.**")
with st.sidebar:
    st.header("🐶 Try asking...")
    st.markdown("""
    - Which states have the highest diabetes rate?
    - What percentage of smokers have heart attacks?
    - Which sex has better mental health?
    - What is the average BMI by general health category?
    - Which states have the lowest health insurance coverage?
    - Do people who exercise have lower diabetes rates?
    """)

question = st.text_input("Ask a health question:", placeholder="e.g. Which states have the highest diabetes rate?")

if question:
    with st.spinner("Thinking..."):
        try:
            sql, result = ask(question)
            st.subheader("Generated SQL")
            st.code(sql, language="sql")
            st.subheader("Results")
            st.dataframe(result)
            if len(result.columns) == 2 and result.shape[0] > 1:
                st.subheader("Chart")
                st.bar_chart(result.set_index(result.columns[0]))
        except Exception as e:
            st.error("I couldn't answer that question. Try asking something more specific, like 'Which states have the highest diabetes rate?' or                          'What percentage of smokers have heart attacks?'")
