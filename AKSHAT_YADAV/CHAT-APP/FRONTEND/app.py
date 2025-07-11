import streamlit as st
import requests
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"  # Change if backend is hosted elsewhere

# --- Model Dropdown ---
MODELS = [
    ("Mistral 7B Instruct", "mistralai/mistral-7b-instruct"),
    ("OpenChat 3.5", "openchat/openchat-3.5"),
    ("NeuralBeagle 7B", "nousresearch/nous-hermes-2-mixtral"),
    ("Meta LLaMA 3 8B Instruct", "meta-llama/llama-3-8b-instruct"),
    ("HuggingFace Zephyr 7B Beta", "huggingfaceh4/zephyr-7b-beta"),
]

st.title("LLM Chat App")



# --- Session State ---
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "history" not in st.session_state:
    st.session_state.history = []
if "model" not in st.session_state:
    st.session_state.model = MODELS[0][1]
if "user_id" not in st.session_state:
    st.session_state.user_id = None


# --- Model Selection ---
model_name = st.selectbox("Choose a model", [m[0] for m in MODELS])
model_id = dict(MODELS)[model_name]
st.session_state.model = model_id





# --- Always use a dummy user/session for instant chat (no login required) ---
if st.session_state.session_id is None:
    # Use a fixed dummy user_id for all users (or generate a random UUID if you want per-user isolation)
    dummy_user_id = "00000000-0000-0000-0000-000000000000"
    st.session_state.user_id = dummy_user_id
    resp = requests.post(f"{API_URL}/chat/session", json={"user_id": dummy_user_id})
    if resp.status_code == 200:
        st.session_state.session_id = resp.json()["session_id"]
    else:
        st.error("Failed to create session. Backend error or not running.")


# --- Start/Resume Session ---
# (No-op: handled above for instant chat)

# --- Load History ---
if st.session_state.session_id:
    resp = requests.get(f"{API_URL}/chat/history", params={"session_id": st.session_state.session_id})
    if resp.status_code == 200:
        st.session_state.history = resp.json()["history"]

# --- Chat Window ---
st.subheader("Chat")
for msg in st.session_state.history:
    st.markdown(f"**{msg['role'].capitalize()}:** {msg['content']}")

# --- Input Box ---
if st.session_state.session_id:
    user_input = st.text_input("Your message:", key="user_input")
    if st.button("Send") and user_input:
        # Send message to backend
        payload = {
            "session_id": st.session_state.session_id,
            "model": st.session_state.model,
            "message": user_input
        }
        resp = requests.post(f"{API_URL}/chat", json=payload)
        if resp.status_code == 200:
            # Refresh history
            resp_hist = requests.get(f"{API_URL}/chat/history", params={"session_id": st.session_state.session_id})
            if resp_hist.status_code == 200:
                st.session_state.history = resp_hist.json()["history"]
            st.experimental_rerun()
        else:
            st.error("Error sending message.")

else:
    st.warning("Please log in and start a session to chat.")


# --- Logout Button removed for now ---
