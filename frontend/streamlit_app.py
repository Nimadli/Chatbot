import requests
import streamlit as st

st.set_page_config(page_title="💬 RAG Chatbot", layout="wide")
st.title("💬 RAG Chatbot")

# ----------------- Sidebar -----------------
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Choose mode:", ["Stream LLM", "Stream Knowledge Base"])
creativity = st.sidebar.slider(
    "Creativeness / Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05
)
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []

# ----------------- Initialize Messages -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------- CSS for Chat Bubbles -----------------
st.markdown(
    """
    <style>
    .user-bubble {
        background-color: #2E7D32; 
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        display: inline-block;
        max-width: 70%;
        font-size: 16px;
    }
    .bot-bubble {
        background-color: #424242; 
        color: #fff;
        padding: 10px 15px;
        border-radius: 20px;
        display: inline-block;
        max-width: 70%;
        font-size: 16px;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------- Helper Function -----------------
def format_messages_for_backend(messages):
    return [
        {"role": "user" if sender == "You" else "assistant", "content": msg}
        for sender, msg in messages
    ]


# ----------------- Chat Display -----------------
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        for sender, msg in st.session_state.messages:
            align = "right" if sender == "You" else "left"
            bubble_class = "user-bubble" if sender == "You" else "bot-bubble"
            st.markdown(
                f"<div style='text-align:{align};'><span class='{bubble_class}'>{msg}</span></div>",
                unsafe_allow_html=True,
            )

# ----------------- Input Form -----------------
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask something:", key="input", label_visibility="collapsed")
    submitted = st.form_submit_button("Send")

# ----------------- Send Message -----------------
if submitted and user_input:
    st.session_state.messages.append(("You", user_input))
    history = format_messages_for_backend(st.session_state.messages)

    if mode == "Stream LLM":
        url = "http://backend:8000/llm/stream"
        with st.spinner("🤖 Bot is thinking..."):
            placeholder = st.empty()
            answer = ""
            try:
                with requests.post(
                    url, json={"messages": history, "temperature": creativity}, stream=True
                ) as r:
                    for chunk in r.iter_content(chunk_size=1):
                        if chunk:
                            answer += chunk.decode("utf-8")
                            placeholder.markdown(
                                f"<div style='text-align:left;'><span class='bot-bubble'>{answer}</span></div>",
                                unsafe_allow_html=True,
                            )
                st.session_state.messages.append(("Bot", answer))
            except Exception as e:
                st.session_state.messages.append(("Bot", f"❌ Error: {str(e)}"))

    elif mode == "Stream Knowledge Base":
        url = "http://backend:8000/kb/stream"
        with st.spinner("📚 Searching knowledge base..."):
            placeholder = st.empty()
            answer = ""
            try:
                with requests.post(url, json={"messages": history}, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=1):
                        if chunk:
                            answer += chunk.decode("utf-8")
                            placeholder.markdown(
                                f"<div style='text-align:left;'><span class='bot-bubble'>{answer}</span></div>",
                                unsafe_allow_html=True,
                            )
                st.session_state.messages.append(("Bot", answer))
            except Exception as e:
                st.session_state.messages.append(("Bot", f"❌ Error: {str(e)}"))

# ----------------- Optional: Bottom Emoji Panel -----------------
st.markdown(
    """
    <div style='text-align:center; margin-top:10px;'>
    <span style='font-size:20px;'>💡 Try asking creative questions! 🎨🤖📚</span>
    </div>
    """,
    unsafe_allow_html=True,
)
