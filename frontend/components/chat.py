# frontend/components/chat.py

import streamlit as st
import requests

from utils.api_client import send_message, API_URL


def _generate_next_steps(user_question: str, answer_text: str, key_points: list):
    """Generate local next step suggestions"""
    suggestions = []

    suggestions.append(
        {
            "label": "Ask a follow-up question",
            "category": "followup",
            "reason": "Dive deeper into related topics or aspects.",
        }
    )

    if key_points and len(key_points) >= 3:
        suggestions.append(
            {
                "label": "Request detailed analysis",
                "category": "deep_dive",
                "reason": "Get a more comprehensive breakdown of the key points.",
            }
        )

    if len(user_question.strip()) < 40:
        suggestions.append(
            {
                "label": "Clarify your question",
                "category": "clarification",
                "reason": "More specific questions lead to more accurate answers.",
            }
        )

    if "http" in answer_text.lower():
        suggestions.append(
            {
                "label": "Review source documents",
                "category": "action",
                "reason": "Check the referenced sources for additional context.",
            }
        )

    suggestions.append(
        {
            "label": "Export this conversation",
            "category": "action",
            "reason": "Save this answer for future reference.",
        }
    )

    return suggestions[:5]


def chat_interface() -> None:
    """Chat interface - displays LLM responses clearly"""

    # Ensure chat history exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Check document count
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

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input(
        "Ask a question about your documents...",
        key="chat_input",
    )

    if not user_input:
        return

    # Add user message to history
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get AI response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        with placeholder.container():
            st.write("🤔 Analyzing documents...")
        
        try:
            response_data = send_message(user_input)

            # Debug logging
            print("\n" + "="*60)
            print("[DEBUG] Response received from backend")
            print(f"  Keys: {list(response_data.keys()) if response_data else 'None'}")
            if response_data and "response" in response_data:
                print(f"  Response length: {len(response_data.get('response', ''))}")
            print("="*60 + "\n")

            # Error handling
            if not response_data or "error" in response_data:
                error_msg = response_data.get("error", "Unknown error") if response_data else "No response"
                with placeholder.container():
                    st.error(f"❌ Error: {error_msg}")
                return

            # Get the main response - try both possible field names
            main_response = response_data.get("response") or response_data.get("main_response") or ""
            
            if not main_response or main_response.strip() == "":
                with placeholder.container():
                    st.warning("⚠️ No response generated from LLM")
                    st.info("Make sure the backend is running and documents are uploaded.")
                return

            # Clear placeholder and start rendering
            placeholder.empty()

            # ============================================================
            # MAIN ANSWER - MOST IMPORTANT
            # ============================================================
            st.markdown("### 📝 Answer")
            st.markdown(main_response)

            # Model indicator
            model_used = response_data.get("model_used", "unknown")
            
            if model_used == "google":
                st.info("🔵 **Model Used:** Google Gemini")
            elif model_used == "ollama":
                st.info("🟢 **Model Used:** Ollama (Local LLM)")
            elif model_used == "google+ollama":
                st.info("🟣 **Model Used:** Google + Ollama (Combined)")
            elif model_used == "context-only":
                st.info("⚪ **Model Used:** Context-Only (No LLM)")
            else:
                st.info(f"❓ **Model Used:** {model_used}")

            # ============================================================
            # KEY POINTS
            # ============================================================
            key_points = response_data.get("key_points", [])
            if key_points:
                st.markdown("### 🎯 Key Points")
                for i, point in enumerate(key_points, 1):
                    st.markdown(f"**{i}.** {point}")
                st.divider()

            # ============================================================
            # SOURCES & PASSAGES - COLLAPSIBLE
            # ============================================================
            passages = response_data.get("passages", []) or []

            if passages:
                with st.expander(f"📚 Sources Used ({len(passages)} passages)", expanded=False):
                    for idx, p in enumerate(passages[:8], start=1):
                        source = p.get("source", "Unknown")
                        url = p.get("url")
                        distance = p.get("distance")
                        text = (p.get("text") or "").replace("\n", " ").strip()

                        # Relevance score
                        if isinstance(distance, (int, float)):
                            if distance <= 0.6:
                                relevance = "🔴 High Match"
                            elif distance <= 1.0:
                                relevance = "🟡 Medium Match"
                            else:
                                relevance = "🟢 Low Match"
                        else:
                            relevance = "❓ Unknown"

                        st.markdown(f"**Passage {idx}** — {relevance}")
                        st.markdown(f"📄 **Source:** `{source}`")
                        
                        if url:
                            st.markdown(f"🌐 **URL:** [{url}]({url})")

                        snippet = text[:400] + ("..." if len(text) > 400 else "")
                        st.code(snippet, language="text")
                        st.divider()

            # ============================================================
            # RAW MODEL OUTPUTS - ADVANCED COLLAPSIBLE
            # ============================================================
            ollama_raw = response_data.get("ollama_raw") or ""
            google_raw = response_data.get("google_raw") or ""

            if ollama_raw or google_raw:
                st.divider()
                with st.expander("🔧 Raw Model Outputs (Advanced)", expanded=False):
                    if google_raw:
                        st.markdown("#### 🔵 Google Gemini (Raw Output)")
                        st.markdown("---")
                        # Display raw output in code block for better formatting
                        st.code(google_raw, language="text")
                        st.markdown("")

                    if ollama_raw:
                        if google_raw:  # Only add divider if we already showed Google
                            st.markdown("---")
                        st.markdown("#### 🟢 Ollama (Raw Output)")
                        st.markdown("---")
                        # Display raw output in code block for better formatting
                        st.code(ollama_raw, language="text")

            # ============================================================
            # NEXT STEPS - AT THE BOTTOM
            # ============================================================
            next_steps = _generate_next_steps(
                user_question=user_input,
                answer_text=main_response,
                key_points=key_points,
            )

            if next_steps:
                st.divider()
                st.markdown("### 🔮 Recommended Next Steps")
                
                for i, step in enumerate(next_steps, 1):
                    label = step.get("label", "Next step")
                    reason = step.get("reason", "")
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{i}. {label}**")
                        st.caption(reason)
                    with col2:
                        if st.button("→", key=f"next_step_{i}", help=f"Ask: {label}"):
                            st.session_state.messages.append(
                                {
                                    "role": "user",
                                    "content": label,
                                }
                            )
                            st.rerun()

            # Save to history (after successful display)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": main_response,
                }
            )

            st.success("✅ Response complete")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
            with placeholder.container():
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Check backend console for more details.")