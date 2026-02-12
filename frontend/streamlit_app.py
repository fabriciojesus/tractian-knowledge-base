"""
Streamlit frontend for the Tractian Knowledge Base RAG system.
Provides a user-friendly interface for uploading PDFs and asking questions.
"""

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Tractian Knowledge Base",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    .reference-box {
        background-color: #F3F4F6;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    .stChatMessage {
        border-radius: 12px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "documents_uploaded" not in st.session_state:
    st.session_state.documents_uploaded = 0
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0


def check_api_health() -> dict | None:
    """Check if the API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.ConnectionError:
        return None
    return None


def upload_documents(files) -> dict | None:
    """Upload PDF files to the API."""
    try:
        upload_files = [
            ("files", (f.name, f.getvalue(), "application/pdf"))
            for f in files
        ]
        response = requests.post(
            f"{API_BASE_URL}/documents",
            files=upload_files,
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload error: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.ConnectionError:
        st.error("❌ Cannot connect to the API. Is the server running?")
        return None


def ask_question(question: str, provider: str = None) -> dict | None:
    """Send a question to the API."""
    try:
        payload = {"question": question}
        if provider:
            payload["provider"] = provider
            
        response = requests.post(
            f"{API_BASE_URL}/question",
            json=payload,
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.ConnectionError:
        st.error("❌ Cannot connect to the API. Is the server running?")
        return None


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔧 Tractian KB")
    st.markdown("---")

    # API Status
    health = check_api_health()
    if health:
        st.success("✅ API Connected")
        stats = health.get("collection_stats", {})
        if stats:
            st.metric(
                "Documents in Store",
                stats.get("total_documents", 0),
            )
    else:
        st.error("❌ API Disconnected")
        st.caption("Start the API with: `make run-api`")

    st.markdown("---")

    # Document Upload
    st.markdown("### 📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF documents to index.",
    )

    if uploaded_files and st.button(
        "📤 Upload & Index", type="primary", use_container_width=True
    ):
        with st.spinner("Processing documents..."):
            result = upload_documents(uploaded_files)
            if result:
                st.session_state.documents_uploaded += result[
                    "documents_indexed"
                ]
                st.session_state.total_chunks += result["total_chunks"]
                st.markdown(
                    f'<div class="success-box">'
                    f"✅ <strong>{result['documents_indexed']}</strong> document(s) indexed<br>"
                    f"📊 <strong>{result['total_chunks']}</strong> chunks created"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown("### ℹ️ Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Docs", st.session_state.documents_uploaded)
    with col2:
        st.metric("Chunks", st.session_state.total_chunks)

    st.markdown("---")
    st.markdown("### 🤖 LLM Settings")
    provider_option = st.selectbox(
        "Choose Model",
        options=["Gemini 2.0 Flash", "GPT-4"],
        index=0,
        help="Select which AI model to use for answering.",
    )
    provider_map = {
        "Gemini 2.0 Flash": "gemini",
        "GPT-4": "openai",
    }
    selected_provider = provider_map[provider_option]

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown(
    '<p class="main-header">🔧 Tractian Knowledge Base</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">'
    "Upload PDF documents and ask questions about their contents. "
    "Powered by RAG (Retrieval-Augmented Generation)."
    "</p>",
    unsafe_allow_html=True,
)

# Chat Interface
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("references"):
            with st.expander("📚 References", expanded=False):
                for i, ref in enumerate(msg["references"], 1):
                    st.markdown(
                        f'<div class="reference-box">'
                        f"<strong>Reference {i}:</strong><br>{ref}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

# Chat Input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.chat_history.append(
        {"role": "user", "content": prompt}
    )
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = ask_question(prompt, provider=selected_provider)
            if result:
                st.markdown(result["answer"])
                references = result.get("references", [])
                if references:
                    with st.expander("📚 References", expanded=False):
                        for i, ref in enumerate(references, 1):
                            st.markdown(
                                f'<div class="reference-box">'
                                f"<strong>Reference {i}:</strong><br>{ref}"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": result["answer"],
                        "references": references,
                    }
                )
            else:
                error_msg = "Sorry, I couldn't process your question. Please check the API connection."
                st.markdown(error_msg)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": error_msg}
                )
