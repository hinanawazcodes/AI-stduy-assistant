import json
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import APIError
from ai_client import create_history, get_study_response



# 1. Page configuration


st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="centered",
)


# 1.1 Custom styling 


st.markdown(
    """
    <style>
    /* Gradient title, centered */
    h1 {
        background: linear-gradient(90deg, #6C63FF, #3FA9F5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 800;
        padding-bottom: 0.2rem;
    }

    /* Centered caption */
    [data-testid="stCaptionContainer"] {
        text-align: center;
    }

    /* Base button style */
    .stButton > button {
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }

    /* Primary buttons (New chat + the currently open chat): gradient */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #6C63FF, #3FA9F5);
        color: white;
        border: none;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(108, 99, 255, 0.35);
        color: white;
        border: none;
    }

    /* Secondary buttons (other saved chats): soft, transparent look */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background: rgba(255, 255, 255, 0.08);
        color: #F1F0FF;
        border: 1px solid rgba(255, 255, 255, 0.18);
        font-weight: 500;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(108, 99, 255, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: white;
    }

    /* Sidebar background and text color */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E1B3A, #2A2650);
    }
    [data-testid="stSidebar"] * {
        color: #F1F0FF;
    }

    /* Chat messages as rounded cards */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        background-color: rgba(108, 99, 255, 0.08);
        border: 1px solid rgba(108, 99, 255, 0.15);
    }

    /* Chat input box */
    [data-testid="stChatInput"] textarea {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📚 AI Study Assistant")
st.caption(
    "Your learning companion for explanations, summaries, "
    "and practice questions."
)



# 2. Chat history helpers (saved in a JSON file)


# The history file is stored next to app.py, so it works no matter
# which folder the terminal is opened in.
HISTORY_FILE = Path(__file__).parent / "chat_history.json"


def load_chats():
    """Read all saved chats from disk. Returns {} if nothing is saved yet."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            # If the file is damaged, start fresh instead of crashing.
            return {}
    return {}


def save_chats(chats):
    """Write all chats to disk so they survive a browser refresh or restart."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(chats, file, ensure_ascii=False, indent=2)


def new_chat_id():
    """Create a unique id from the current time (also sorts chats by date)."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def make_title(messages):
    """Use the first user question as the chat title (shortened)."""
    for message in messages:
        if message["role"] == "user":
            text = message["content"].strip().replace("\n", " ")
            return text[:30] + ("..." if len(text) > 30 else "")
    return "New chat"


def start_new_chat():
    """Switch to a fresh, empty conversation."""
    st.session_state.current_chat_id = new_chat_id()
    st.session_state.messages = create_history()



# 3. Initialize conversation state


# All saved chats: {chat_id: {"title": ..., "messages": [...]}}
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

# The conversation that is currently open.
if "messages" not in st.session_state:
    start_new_chat()



# 4. Sidebar
# 

with st.sidebar:
    st.header("🎓 Study Assistant")
    st.write("What would you like to learn today?")

    st.divider()

    st.subheader("Available features")
    st.write("💡 Explain concepts")
    st.write("📝 Summarize text")
    st.write("❓ Generate practice questions")

    st.divider()

    if st.button("➕ New conversation", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    
    #Chat history list #
    st.subheader("Chat history")

    if not st.session_state.chats:
        st.caption("No saved chats yet. Ask a question to start one!")

    # Newest chats first (ids are timestamps, so reverse order = newest first).
    for chat_id in sorted(st.session_state.chats, reverse=True):
        chat = st.session_state.chats[chat_id]
        is_current = chat_id == st.session_state.current_chat_id

        # The open chat is highlighted with the gradient (primary) style.
        if st.button(
            f"💬 {chat['title']}",
            key=f"chat_{chat_id}",
            use_container_width=True,
            type="primary" if is_current else "secondary",
        ):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = chat["messages"]
            st.rerun()

    #  Delete the currently open chat (only if it is saved)
    if st.session_state.current_chat_id in st.session_state.chats:
        st.divider()
        if st.button("🗑️ Delete this chat", use_container_width=True):
            del st.session_state.chats[st.session_state.current_chat_id]
            save_chats(st.session_state.chats)
            start_new_chat()
            st.rerun()



# 5. Display previous chat messages


for message in st.session_state.messages:
    # The system message is only instructions for the AI, so we hide it.
    if message["role"] == "system":
        continue

    # Avatars are cosmetic only.
    avatar = "🧑‍🎓" if message["role"] == "user" else "🤖"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])



# 6. Accept a new question


prompt = st.chat_input("Ask a study question...")

if prompt:
    # Display the user's question immediately.
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    # Prepare conversation history for the API.
    next_messages = st.session_state.messages + [
        {"role": "user", "content": prompt}
    ]

    try:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                answer = get_study_response(next_messages)

            st.markdown(answer)

        # Save history only after a successful response.
        st.session_state.messages = next_messages + [
            {"role": "assistant", "content": answer}
        ]

        # Store this conversation in the chat list and write it to disk.
        st.session_state.chats[st.session_state.current_chat_id] = {
            "title": make_title(st.session_state.messages),
            "messages": st.session_state.messages,
        }
        save_chats(st.session_state.chats)

        # Refresh so the sidebar shows the new/updated chat title right away.
        st.rerun()

    except (APIError, ValueError) as error:
        st.error(
            "Could not get an answer. Check your API configuration "
            "and connection, then try again."
        )
        print(f"AI API error: {error}")
