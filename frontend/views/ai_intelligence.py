import streamlit as st
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.theme.styles import apply_stitch_theme
from frontend.utils.api_client import APIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.alerts import render_alert

apply_stitch_theme()

if not st.session_state.get("authenticated"):
    st.warning("Authentication required. Redirecting to login...")
    if "login_page" in st.session_state:
        st.switch_page(st.session_state["login_page"])
    else:
        st.stop()

render_sidebar()

st.title("AI Intelligence")
st.markdown("Your Digital Twin, powered by your personal data.")

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! I can help you understand your Digital Twin. What would you like to know?"}
    ]

col1, col2 = st.columns([8, 2])
with col2:
    if st.button("New Conversation", use_container_width=True):
        st.session_state["conversation_id"] = None
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hi! I can help you understand your Digital Twin. What would you like to know?"}
        ]
        st.rerun()

st.markdown("---")

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask your Digital Twin..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            payload = {
                "message": prompt,
                "conversation_id": st.session_state["conversation_id"]
            }
            # Depending on actual API route
            response = APIClient.post("/ai/chat", data=payload, timeout=60)
            
            if response and "response" in response:
                ai_response = response["response"]
                if "conversation_id" in response:
                    st.session_state["conversation_id"] = response["conversation_id"]
                message_placeholder.markdown(ai_response)
                st.session_state["messages"].append({"role": "assistant", "content": ai_response})
            else:
                err = response.get("error", "Failed to connect to the AI service.") if isinstance(response, dict) else "Failed to connect."
                message_placeholder.markdown(f"❌ **Error:** {err}")
                st.session_state["messages"].append({"role": "assistant", "content": f"❌ **Error:** {err}"})
