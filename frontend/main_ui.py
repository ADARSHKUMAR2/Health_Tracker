import streamlit as st
import requests
import datetime

CHAT_URL = "http://brain:8000/api/health-chat"

st.subheader("🩺 Autonomous Health Coach")
st.markdown("Ask questions about your biometric trends, workouts, and recovery.")

# 1. Initialize chat history in memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 2. Render previous messages so the conversation persists
for message in st.session_state.chat_history:
    role_icon = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=role_icon):
        st.markdown(message["content"])

# 3. The Chat Input Bar
if user_query := st.chat_input("Ask about your sleep, HRV, or calories..."):
    
    # Display user prompt immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_query)
        
    # Append to session state
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    # 4. Fetch the Agent's analysis
    with st.spinner("Agent is querying your database and analyzing biometrics..."):
        try:
            res = requests.post(CHAT_URL, json={"message": user_query})
            
            if res.status_code == 200:
                data = res.json()
                if data["status"] == "success":
                    agent_response = data["response"]
                    
                    # Display the Agent's response
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(agent_response)
                        
                    # Save to history
                    st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
                else:
                    st.error(f"Agent Error: {data['message']}")
            else:
                st.error("Failed to connect to the backend API.")
        except Exception as e:
            st.error(f"Network error: {e}")