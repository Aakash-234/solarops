# dashboard.py

import streamlit as st
import requests
import pandas as pd

FASTAPI_URL = "http://127.0.0.1:8000"  # Adjust if running elsewhere

st.set_page_config(page_title="SolarOps Dashboard", layout="wide")
st.title("🌞 SolarOps Streamlit Dashboard")

# 1️⃣ Fetch results
with st.spinner("Fetching data..."):
    response = requests.get(f"{FASTAPI_URL}/results")
    if response.status_code == 200:
        data = response.json()["results"]
        df = pd.DataFrame(data)
    else:
        st.error("Failed to fetch data from FastAPI.")
        st.stop()

# 2️⃣ Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", len(df))
col2.metric("Valid", df["valid"].sum())
col3.metric("Invalid", len(df) - df["valid"].sum())
col4.metric("Avg Confidence", f"{df['confidence'].mean():.1f}%")


# 3️⃣ Data Table
st.subheader("📋 All Files")
st.dataframe(df)

# 4️⃣ Select and view audit trail
filename = st.selectbox("Select a file to view audit trail:", df["filename"].unique())

if st.button("Show Audit Trail"):
    audit_url = f"{FASTAPI_URL}/audit/{filename}"
    st.markdown(f"[🔍 View Audit Trail in Browser]({audit_url})")

    # If you want to display inside Streamlit:
    audit_html = requests.get(audit_url)
    if audit_html.status_code == 200:
        st.components.v1.html(audit_html.text, height=600, scrolling=True)
    else:
        st.error("Failed to fetch audit trail.")

# 5️⃣ Download report
report_url = f"{FASTAPI_URL}/report/{filename}"
st.markdown(f"[⬇️ Download Feedback Report]({report_url})")

