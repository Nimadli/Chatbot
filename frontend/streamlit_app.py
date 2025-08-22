import requests
import streamlit as st
import json
import time

st.set_page_config(page_title="💬 RAG Chatbot", layout="wide")
st.title("💬 RAG Chatbot")

# ----------------- Sidebar -----------------
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Choose mode:", ["Direct Chat", "Knowledge Base RAG", "Weather"])
creativity = st.sidebar.slider(
    "Creativeness / Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05
)
max_tokens = st.sidebar.slider(
    "Max Tokens", min_value=100, max_value=2048, value=1024, step=50
)

# Backend URL configuration (hardcoded)
backend_url = "http://localhost:8000"

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
        margin: 5px 0;
    }
    .bot-bubble {
        background-color: #424242; 
        color: #fff;
        padding: 10px 15px;
        border-radius: 20px;
        display: inline-block;
        max-width: 70%;
        font-size: 16px;
        margin: 5px 0;
    }
    .weather-bubble {
        background-color: #1565C0; 
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        display: inline-block;
        max-width: 70%;
        font-size: 16px;
        margin: 5px 0;
    }
    .sources-container {
        background-color: #f5f5f5;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        font-size: 12px;
        color: #666;
    }
    .error-bubble {
        background-color: #d32f2f;
        color: white;
        padding: 10px 15px;
        border-radius: 20px;
        display: inline-block;
        max-width: 70%;
        font-size: 16px;
        margin: 5px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- Helper Functions -----------------
def format_messages_for_backend(messages):
    """Convert streamlit message history into backend expected format."""
    backend_messages = []
    for sender, msg_data in messages:
        if sender == "You":
            backend_messages.append({"role": "user", "content": msg_data})
        elif sender == "Bot" and isinstance(msg_data, str):
            backend_messages.append({"role": "assistant", "content": msg_data})
    return backend_messages

def simulate_typing(text, placeholder):
    """Simulate typing effect by gradually revealing text."""
    words = text.split(' ')
    current_text = ""
    for i, word in enumerate(words):
        current_text += word + " "
        placeholder.markdown(
            f"<div style='text-align:left;'><span class='bot-bubble'>{current_text}●</span></div>",
            unsafe_allow_html=True,
        )
        time.sleep(0.05)  # Adjust speed as needed
    
    # Final display without cursor
    placeholder.markdown(
        f"<div style='text-align:left;'><span class='bot-bubble'>{text}</span></div>",
        unsafe_allow_html=True,
    )

def call_chat_endpoint(messages, temperature, max_tokens, placeholder):
    """Call the /chat endpoint and return response."""
    try:
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(f"{backend_url}/chat", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "No response received")
            simulate_typing(answer, placeholder)
            return answer
        else:
            error_msg = f"❌ Error: {response.status_code} - {response.text}"
            placeholder.markdown(
                f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
                unsafe_allow_html=True,
            )
            return error_msg
            
    except Exception as e:
        error_msg = f"❌ Connection Error: {str(e)}"
        placeholder.markdown(
            f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
            unsafe_allow_html=True,
        )
        return error_msg

def call_rag_endpoint(query, placeholder):
    """Call the /kb-rag-query endpoint and return response with sources."""
    try:
        payload = {"query": query}
        
        response = requests.post(f"{backend_url}/kb-rag-query", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer received")
            sources = result.get("sources", [])
            
            # Simulate typing for the main answer
            simulate_typing(answer, placeholder)
            
            # Format sources information
            if sources:
                sources_text = "\n\n📚 **Sources:**\n"
                for i, source in enumerate(sources[:3], 1):  # Show max 3 sources
                    score = source.get('score', 0)
                    content_preview = source.get('content', '')[:100] + "..." if len(source.get('content', '')) > 100 else source.get('content', '')
                    sources_text += f"{i}. Score: {score:.3f} | {content_preview}\n"
                
                # Update placeholder with answer + sources
                placeholder.markdown(
                    f"<div style='text-align:left;'><span class='bot-bubble'>{answer}</span></div>" +
                    f"<div class='sources-container'>{sources_text}</div>",
                    unsafe_allow_html=True,
                )
            
            return {"answer": answer, "sources": sources}
        else:
            error_msg = f"❌ RAG Error: {response.status_code} - {response.text}"
            placeholder.markdown(
                f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
                unsafe_allow_html=True,
            )
            return {"answer": error_msg, "sources": []}
            
    except Exception as e:
        error_msg = f"❌ RAG Connection Error: {str(e)}"
        placeholder.markdown(
            f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
            unsafe_allow_html=True,
        )
        return {"answer": error_msg, "sources": []}

def call_weather_endpoint(location, placeholder):
    """Call the /weather endpoint and return response."""
    try:
        payload = {"location": location}
        
        response = requests.post(f"{backend_url}/weather", json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            weather_data = result.get("weather", {})
            location = result.get("location", "Unknown")
            
            if isinstance(weather_data, dict) and "temperature" in weather_data:
                weather_text = f"🌤️ **Weather in {location}:**\n"
                weather_text += f"🌡️ Temperature: {weather_data['temperature']}°C\n"
                weather_text += f"📝 Description: {weather_data['description']}\n"
                weather_text += f"💧 Humidity: {weather_data['humidity']}%\n"
                weather_text += f"💨 Wind Speed: {weather_data['wind_speed']} km/h"
            else:
                weather_text = f"Weather data for {location}: {weather_data}"
            
            placeholder.markdown(
                f"<div style='text-align:left;'><span class='weather-bubble'>{weather_text}</span></div>",
                unsafe_allow_html=True,
            )
            return weather_text
        else:
            error_msg = f"❌ Weather Error: {response.status_code} - {response.text}"
            placeholder.markdown(
                f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
                unsafe_allow_html=True,
            )
            return error_msg
            
    except Exception as e:
        error_msg = f"❌ Weather Connection Error: {str(e)}"
        placeholder.markdown(
            f"<div style='text-align:left;'><span class='error-bubble'>{error_msg}</span></div>",
            unsafe_allow_html=True,
        )
        return error_msg

# ----------------- Chat Display -----------------
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        for sender, msg_data in st.session_state.messages:
            align = "right" if sender == "You" else "left"
            bubble_class = "user-bubble" if sender == "You" else "bot-bubble"
            
            if sender == "You":
                st.markdown(
                    f"<div style='text-align:{align};'><span class='{bubble_class}'>{msg_data}</span></div>",
                    unsafe_allow_html=True,
                )
            else:
                # Handle different types of bot responses
                if isinstance(msg_data, dict) and "answer" in msg_data:
                    # RAG response with sources
                    answer = msg_data["answer"]
                    sources = msg_data.get("sources", [])
                    st.markdown(
                        f"<div style='text-align:{align};'><span class='{bubble_class}'>{answer}</span></div>",
                        unsafe_allow_html=True,
                    )
                    if sources:
                        sources_text = "📚 **Sources:**\n"
                        for i, source in enumerate(sources[:3], 1):
                            score = source.get('score', 0)
                            content_preview = source.get('content', '')[:100] + "..." if len(source.get('content', '')) > 100 else source.get('content', '')
                            sources_text += f"{i}. Score: {score:.3f} | {content_preview}\n"
                        st.markdown(
                            f"<div class='sources-container'>{sources_text}</div>",
                            unsafe_allow_html=True,
                        )
                elif "🌤️" in str(msg_data):
                    # Weather response
                    st.markdown(
                        f"<div style='text-align:{align};'><span class='weather-bubble'>{msg_data}</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    # Regular text response
                    bubble_class = "error-bubble" if "❌" in str(msg_data) else "bot-bubble"
                    st.markdown(
                        f"<div style='text-align:{align};'><span class='{bubble_class}'>{msg_data}</span></div>",
                        unsafe_allow_html=True,
                    )

# ----------------- Input Form -----------------
with st.form(key="chat_form", clear_on_submit=True):
    if mode == "Weather":
        user_input = st.text_input("Enter a location for weather:", key="input", label_visibility="collapsed", placeholder="e.g., Baku, Paris, New York")
    else:
        user_input = st.text_input("Ask something:", key="input", label_visibility="collapsed", placeholder="Type your message here...")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        submitted = st.form_submit_button("Send 📤")

# ----------------- Process User Input -----------------
if submitted and user_input:
    # Add user message to chat
    st.session_state.messages.append(("You", user_input))
    
    # Create placeholder for bot response
    placeholder = st.empty()
    
    if mode == "Direct Chat":
        with st.spinner("🤖 Bot is thinking..."):
            history = format_messages_for_backend(st.session_state.messages)
            answer = call_chat_endpoint(history, creativity, max_tokens, placeholder)
            st.session_state.messages.append(("Bot", answer))
    
    elif mode == "Knowledge Base RAG":
        with st.spinner("📚 Searching knowledge base..."):
            result = call_rag_endpoint(user_input, placeholder)
            st.session_state.messages.append(("Bot", result))
    
    elif mode == "Weather":
        with st.spinner("🌤️ Getting weather information..."):
            weather_result = call_weather_endpoint(user_input, placeholder)
            st.session_state.messages.append(("Bot", weather_result))

# ----------------- Footer Information -----------------
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("💬 **Direct Chat**: Chat directly with Claude")
    
with col2:
    st.info("📚 **Knowledge Base RAG**: Query your knowledge base with context-aware responses")
    
with col3:
    st.info("🌤️ **Weather**: Get current weather information for any location")

# ----------------- Optional: Bottom Emoji Panel -----------------
st.markdown(
    """
    <div style='text-align:center; margin-top:20px; padding:10px; background-color:#f0f0f0; border-radius:10px;'>
    <span style='font-size:16px;'>💡 Try different modes to explore various capabilities! 🎨🤖📚🌤️</span>
    </div>
    """,
    unsafe_allow_html=True,
)