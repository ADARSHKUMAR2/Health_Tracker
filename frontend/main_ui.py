import streamlit as st
import requests
import pandas as pd
import sqlite3
from pathlib import Path

# --- Configuration ---
# Ensure this matches the route you verified in your FastAPI backend
BACKEND_URL = "http://localhost:8000/api/health-chat"

st.set_page_config(page_title="Health AI Coach", page_icon="🩺", layout="wide")
st.title("🩺 Personal Health AI")

# --- Data Loading Logic ---
@st.cache_data(ttl=3600)
def load_health_data():
    """Fetches the last 30 days of data for the dashboard charts."""
    db_path = Path(__file__).resolve().parent.parent / "data" / "health_data.db"
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM daily_metrics ORDER BY date DESC LIMIT 30", conn)
        conn.close()
        
        if df.empty:
            return df
            
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True) 
        df['resting_hr'] = df['resting_hr'].replace(0, pd.NA)
        
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame()

# --- UI Layout: Tabs ---
tab_chat, tab_dashboard = st.tabs(["💬 AI Coach", "📊 30-Day Dashboard"])

# -----------------------------------------
# TAB 1: Chat Interface
# -----------------------------------------
with tab_chat:
    st.subheader("Chat with your Data")
    
    # 1. Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # 2. Display existing chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg["content"], dict):
                # Format the structured Pydantic response
                data = msg["content"]
                st.write(data.get("summary_message", ""))
                
                # Show key metrics in columns
                col1, col2 = st.columns(2)
                col1.metric("Average Steps", data.get("average_steps", "N/A"))
                col2.markdown(f"**HR Trend:** {data.get('heart_rate_trend', 'N/A')}")
                
                # Show insights in an expander
                with st.expander("View Key Insights"):
                    for insight in data.get("key_insights", []):
                        st.markdown(f"- {insight}")
            else:
                st.write(msg["content"])

    # 3. Handle new user input
    if prompt := st.chat_input("Ask about your health trends..."):
        # Append and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Fetch and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your biometric data..."):
                try:
                    # Send request to FastAPI
                    res = requests.post(BACKEND_URL, json={"message": prompt})
                    
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("status") == "success":
                            ai_response = data.get("response", {})
                            
                            # Render the structured response
                            st.write(ai_response.get("summary_message", ""))
                            
                            m_col1, m_col2 = st.columns(2)
                            m_col1.metric("Average Steps", ai_response.get("average_steps", "N/A"))
                            m_col2.markdown(f"**HR Trend:** {ai_response.get('heart_rate_trend', 'N/A')}")
                            
                            with st.expander("View Key Insights"):
                                for insight in ai_response.get("key_insights", []):
                                    st.markdown(f"- {insight}")
                                    
                            # Save response to history
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        else:
                            st.error(f"API Error: {data.get('message')}")
                    else:
                        st.error(f"Server error: {res.status_code}")
                except Exception as e:
                    st.error(f"Connection failed: Ensure your FastAPI server is running on port 8000. Details: {e}")

# -----------------------------------------
# TAB 2: Dashboard Section
# -----------------------------------------
with tab_dashboard:
    df = load_health_data()

    if not df.empty:
        st.subheader("🚶‍♂️ Daily Step Count")
        st.bar_chart(df['step_count'], color="#1f77b4")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("❤️ Resting Heart Rate (bpm)")
            st.line_chart(df['resting_hr'].dropna(), color="#d62728")
            
        with col2:
            st.subheader("💤 Sleep Duration (Hours)")
            st.area_chart(df['sleep_hours'], color="#2ca02c")
    else:
        st.info("No health data found in the database. Please run the ingestion script!")