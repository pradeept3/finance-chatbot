import html
import requests
import streamlit as st

from utils.api_client import send_message, API_URL
from utils.formatters import format_response


def chat_interface() -> None:
    """Clean Chat UI — NO email, NO next-steps, only RAG + raw outputs."""

    # -------------------------------
    # 1. INIT CHAT HISTORY
    # -------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # -------------------------------
    # 2. VERIFY DOCUMENTS EXIST
    # -------------------------------
    try:
        resp = requests.get(f"{API_URL}/api/documents", timeout=5)
        doc_count = resp.json().get("total_documents", 0)
    except Exception:
        doc_count = 0

    if doc_count == 0:
        st.warning(
            "📋 No documents uploaded yet!\n\n"
            "Please go to the **📤 Upload** tab to upload documents first."
        )
        return

    st.info(f"📚 **{doc_count}** document chunks in knowledge base")
    st.markdown("---")

    # -------------------------------
    # 3. DISPLAY CHAT HISTORY
    # -------------------------------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # -------------------------------
    # 4. WAIT FOR USER INPUT
    # -------------------------------
    user_input = st.chat_input("Ask a question about your documents...", key="chat_input")

    if not user_input:
        return

    # Save user msg
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # -------------------------------
    # 5. CALL BACKEND
    # -------------------------------
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing documents with AI..."):
            try:
                response_data = send_message(user_input)
                if not response_data:
                    st.error("❌ Failed to get response.")
                    return

                # -------------------------------
                # MODEL LABEL
                # -------------------------------
                model_used = response_data.get("model_used", "")
                if model_used == "google":
                    model_label = "🔵 **Model used:** Google Gemini"
                elif model_used == "ollama":
                    model_label = "🟢 **Model used:** Ollama (local LLM)"
                elif model_used == "google+ollama":
                    model_label = "🟣 **Model used:** Google + Ollama (combined)"
                else:
                    model_label = ""

                # -------------------------------
                # MAIN ANSWER
                # -------------------------------
                main_body = format_response(response_data)
                assistant_full = f"{model_label}\n\n{main_body}"

                # Save to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_full}
                )

                st.markdown(assistant_full)

                # -------------------------------
                # RAW MODEL OUTPUTS
                # -------------------------------
                ollama_raw = response_data.get("ollama_raw") or ""
                google_raw = response_data.get("google_raw") or ""

                if ollama_raw or google_raw:
                    with st.expander("🧪 Raw model outputs"):

                        if google_raw:
                            safe_google = html.escape(google_raw)
                            st.markdown(
                                '<div class="raw-output-title gemini">GOOGLE GEMINI (raw)</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="raw-output-box">{safe_google}</div>',
                                unsafe_allow_html=True,
                            )

                        if ollama_raw:
                            safe_ollama = html.escape(ollama_raw)
                            st.markdown(
                                '<div class="raw-output-title">OLLAMA (raw)</div>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="raw-output-box">{safe_ollama}</div>',
                                unsafe_allow_html=True,
                            )

                # -------------------------------
                # PASSAGES USED
                # -------------------------------
                passages = response_data.get("passages", [])
                summaries = response_data.get("url_summaries", [])

                # Map URL → summary markdown
                url_map = {x["url"]: x["summary_markdown"] for x in summaries if x.get("url")}

                if passages:
                    with st.expander("📚 Passages used for answer"):
                        answer_lower = assistant_full.lower()

                        for idx, p in enumerate(passages[:5], start=1):
                            raw = (p.get("text") or "").replace("\n", " ").strip()
                            snippet = raw[:600] + "..." if len(raw) > 600 else raw

                            # highlight line
                            highlight = ""
                            for sentence in raw.split(". "):
                                if sentence.strip().lower() in answer_lower:
                                    highlight = sentence.strip()
                                    break

                            if highlight:
                                highlight_html = (
                                    f"<span style='background-color:#fff3cd;"
                                    f"padding:2px 4px;border-radius:4px;'>{highlight}</span>"
                                )
                            else:
                                highlight_html = "_No exact line found in answer._"

                            # relevance
                            dist = p.get("distance")
                            if isinstance(dist, (int, float)):
                                rel = (
                                    "high" if dist <= 0.6 else
                                    "medium" if dist <= 1.0 else
                                    "low"
                                )
                            else:
                                rel = "unknown"

                            st.markdown(
                                f"""
**🧩 Passage {idx} — {p.get("id")}**

- 📄 **Source:** `{p.get("source")}`
- 🌐 **URL:** {p.get("url") or '_none_'}
- 🎯 **Relevance:** `{rel}` (distance={dist})

**🔺 Highlighted line:**  
{highlight_html}

<details><summary><strong>Show passage text</strong></summary>

{snippet}

</details>
""",
                                unsafe_allow_html=True,
                            )

                            # show URL summary if exists
                            url = p.get("url")
                            if url and url in url_map:
                                st.markdown("**🌐 URL Summary:**")
                                st.markdown(url_map[url])

                            st.markdown("---")

                st.success("✅ Response generated successfully")

            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("💡 Make sure the backend is running and documents are uploaded.")
