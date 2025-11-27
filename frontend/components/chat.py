# frontend/components/chat.py - COMPLETE WORKING VERSION

import streamlit as st
import requests

from utils.api_client import send_message, API_URL


# ============================================================
# QUICK FAQs - PREDEFINED
# ============================================================
QUICK_FAQS = [
    "What is the prerequisite for ___FNCE class___?",
    "What are the classes I need to take for the FNCE major?",
    "What are the popular pathways for FNCE students?",
    "Can I add a minor to my 4-year plan?",
    "Is my 4-year plan correct?",
    "What classes should I take if I am interested in ___specific branch of Finance___?",
    "How do I petition to graduate?",
    "How many units can I take in one quarter?",
    "How can I overload?",
    "Can I graduate early?",
    "What classes double dip for the FNCE major?",
    "How do I get on a waitlist?",
    "When can I add/drop a class?",
    "How do I create a workday schedule?",
]


def _generate_enhanced_next_steps(user_question: str, answer_text: str, key_points: list):
    """Generate enhanced next step suggestions"""
    suggestions = []
    
    answer_lower = answer_text.lower()
    answer_length = len(answer_text.split())
    has_numbers = any(char.isdigit() for char in answer_text)
    
    # Always include these
    suggestions.append({
        "label": "⚡ Can you summarize this?",
        "emoji": "⚡",
        "reason": "Get a quick, concise summary",
        "icon_color": "#F59E0B"
    })
    
    suggestions.append({
        "label": "❓ Ask a related question",
        "emoji": "❓",
        "reason": "Dive deeper into related topics",
        "icon_color": "#06B6D4"
    })
    
    if len(user_question.strip()) < 40:
        suggestions.append({
            "label": "🔍 Make question more specific",
            "emoji": "🔍",
            "reason": "Get more accurate answers",
            "icon_color": "#3B82F6"
        })
    
    if has_numbers or '%' in answer_text:
        suggestions.append({
            "label": "📊 Explain the numbers",
            "emoji": "📊",
            "reason": "Understand the data points",
            "icon_color": "#F59E0B"
        })
    
    suggestions.append({
        "label": "💡 Give me examples",
        "emoji": "💡",
        "reason": "See real-world examples",
        "icon_color": "#FBBF24"
    })
    
    suggestions.append({
        "label": "🎯 Deep dive into details",
        "emoji": "🎯",
        "reason": "Explore in-depth",
        "icon_color": "#10B981"
    })
    
    return suggestions[:6]


def chat_interface() -> None:
    """Chat interface with FAQ dropdown and persistent next steps"""

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "processing" not in st.session_state:
        st.session_state.processing = False

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
    
    # ============================================================
    # FAQ DROPDOWN - ALWAYS VISIBLE AT TOP
    # ============================================================
    st.markdown("### 📚 Quick FAQ")
    
    faq_col1, faq_col2 = st.columns([4, 1])
    
    with faq_col1:
        selected_faq = st.selectbox(
            "Choose a frequently asked question:",
            options=["-- Select a question --"] + QUICK_FAQS,
            key="faq_selector",
            label_visibility="collapsed"
        )
    
    with faq_col2:
        if st.button("🚀 Ask", key="faq_ask_btn", use_container_width=True, type="primary"):
            if selected_faq != "-- Select a question --":
                st.session_state.messages.append({
                    "role": "user",
                    "content": selected_faq
                })
                st.session_state.processing = True
                st.rerun()
    
    st.markdown("---")

    # ============================================================
    # CHAT HISTORY WITH NEXT STEPS
    # ============================================================
    for msg_idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show next steps for assistant messages (except the one being processed)
            if message["role"] == "assistant" and not st.session_state.processing:
                # Generate next steps for this message
                prev_user_msg = ""
                if msg_idx > 0 and st.session_state.messages[msg_idx - 1]["role"] == "user":
                    prev_user_msg = st.session_state.messages[msg_idx - 1]["content"]
                
                next_steps = _generate_enhanced_next_steps(
                    user_question=prev_user_msg,
                    answer_text=message["content"],
                    key_points=[]
                )
                
                if next_steps:
                    st.markdown("---")
                    st.markdown("### 🚀 Next Steps")
                    
                    # Show in a 2-column layout for better readability
                    step_cols = st.columns(2)
                    
                    for idx, step in enumerate(next_steps[:6]):
                        col = step_cols[idx % 2]
                        
                        with col:
                            label = step["label"]
                            emoji = step["emoji"]
                            reason = step["reason"]
                            icon_color = step["icon_color"]
                            
                            # Beautiful styled card
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {icon_color}10 0%, {icon_color}05 100%);
                                border-left: 4px solid {icon_color};
                                border-radius: 8px;
                                padding: 0.75rem;
                                margin: 0.5rem 0;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            ">
                                <div style="
                                    font-size: 0.95rem;
                                    font-weight: 600;
                                    color: {icon_color};
                                    margin-bottom: 0.25rem;
                                ">
                                    {emoji} {label.replace(emoji, '').strip()}
                                </div>
                                <div style="
                                    font-size: 0.8rem;
                                    color: #6b7280;
                                    line-height: 1.4;
                                ">
                                    {reason}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(
                                "✨ Ask This",
                                key=f"history_step_{msg_idx}_{idx}",
                                use_container_width=True,
                                type="secondary"
                            ):
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": label,
                                })
                                st.session_state.processing = True
                                st.rerun()

    # ============================================================
    # CHAT INPUT
    # ============================================================
    user_input = st.chat_input(
        "Ask a question about your documents...",
        key="chat_input",
    )

    # Process new input
    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
        })
        st.session_state.processing = True
        st.rerun()

    # ============================================================
    # PROCESS LAST MESSAGE IF NEEDED
    # ============================================================
    if st.session_state.processing and len(st.session_state.messages) > 0:
        last_msg = st.session_state.messages[-1]
        
        # Only process if last message is from user
        if last_msg["role"] == "user":
            user_query = last_msg["content"]
            
            with st.chat_message("user"):
                st.markdown(user_query)
            
            # Get AI response
            with st.chat_message("assistant"):
                placeholder = st.empty()
                
                with placeholder.container():
                    st.write("🤖 Analyzing documents...")
                
                try:
                    response_data = send_message(user_query)

                    # Error handling
                    if not response_data or "error" in response_data:
                        error_msg = response_data.get("error", "Unknown error") if response_data else "No response"
                        with placeholder.container():
                            st.error(f"❌ Error: {error_msg}")
                        st.session_state.processing = False
                        return

                    # Get main response
                    main_response = response_data.get("response") or response_data.get("main_response") or ""
                    
                    if not main_response.strip():
                        with placeholder.container():
                            st.warning("⚠️ No response generated")
                        st.session_state.processing = False
                        return

                    # Clear placeholder
                    placeholder.empty()

                    # ============================================================
                    # DISPLAY ANSWER
                    # ============================================================
                    st.markdown("### 📖 Answer")
                    st.markdown(main_response)

                    # Model info
                    model_used = response_data.get("model_used", "unknown")
                    selected_model = response_data.get("selected_model", "unknown")
                    
                    st.markdown("---")
                    st.markdown("### 🤖 Model Information")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Selected:** {selected_model}")
                    with col2:
                        if model_used == "google":
                            st.success("**Used:** 🔵 Google Gemini")
                        elif model_used == "ollama":
                            st.success("**Used:** 🟢 Ollama")
                        elif model_used == "deepseek":
                            st.success("**Used:** 🔷 DeepSeek")
                        else:
                            st.warning(f"**Used:** {model_used}")

                    # Key points
                    key_points = response_data.get("key_points", [])
                    if key_points:
                        st.markdown("### 🎯 Key Points")
                        for i, point in enumerate(key_points, 1):
                            st.markdown(f"**{i}.** {point}")
                        st.divider()

                    # URL Content
                    url_summaries = response_data.get("url_summaries", [])
                    if url_summaries:
                        st.divider()
                        st.markdown(f"### 🌐 Content from URLs ({len(url_summaries)} found)")
                        
                        for idx, url_data in enumerate(url_summaries, 1):
                            st.markdown(f"#### 🔗 {idx}. {url_data.get('title', 'URL')}")
                            st.markdown(f"**URL:** [{url_data['url']}]({url_data['url']})")
                            
                            if url_data.get('error'):
                                st.error(f"❌ Error: {url_data['error']}")
                            else:
                                content = url_data.get('text', '')
                                if content:
                                    preview = content[:500] + ("..." if len(content) > 500 else "")
                                    st.info(f"**Preview:** {preview}")
                                    
                                    show_full = st.checkbox(
                                        f"📄 Show Full Content",
                                        key=f"show_url_{idx}"
                                    )
                                    
                                    if show_full:
                                        st.text_area(
                                            "Full Content",
                                            value=content,
                                            height=300,
                                            key=f"url_content_{idx}",
                                            disabled=True
                                        )
                            st.markdown("---")

                    # Sources
                    passages = response_data.get("passages", []) or []
                    if passages:
                        with st.expander(f"📚 Sources ({len(passages)} passages)", expanded=False):
                            for idx, p in enumerate(passages[:8], start=1):
                                source = p.get("source", "Unknown")
                                distance = p.get("distance")
                                text = (p.get("text") or "").strip()

                                if isinstance(distance, (int, float)):
                                    if distance <= 0.6:
                                        relevance = "🔴 High"
                                    elif distance <= 1.0:
                                        relevance = "🟡 Medium"
                                    else:
                                        relevance = "🟢 Low"
                                else:
                                    relevance = "❓ Unknown"

                                st.markdown(f"**{idx}. {source}** – {relevance}")
                                snippet = text[:300] + "..." if len(text) > 300 else text
                                st.code(snippet, language="text")
                                st.divider()

                    # Save assistant response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": main_response,
                    })

                    st.success("✅ Response complete")
                    
                    # Mark processing as complete
                    st.session_state.processing = False
                    
                    # Rerun to show next steps in history
                    st.rerun()

                except Exception as e:
                    print(f"\n[ERROR] {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    with placeholder.container():
                        st.error(f"❌ Error: {str(e)}")
                    
                    st.session_state.processing = False
    
    # ============================================================
    # FOOTER - ALWAYS VISIBLE
    # ============================================================
    if len(st.session_state.messages) > 0:
        st.markdown("---")
        
        footer_cols = st.columns(3)
        
        with footer_cols[0]:
            if st.button("📋 Export Chat", key="export_chat_footer", use_container_width=True):
                chat_text = "Finance Chatbot - Chat History\n" + "="*60 + "\n\n"
                for i, msg in enumerate(st.session_state.messages, 1):
                    role = "👤 USER" if msg["role"] == "user" else "🤖 ASSISTANT"
                    chat_text += f"[{i}] {role}:\n{msg['content']}\n\n"
                
                st.download_button(
                    "⬇️ Download",
                    data=chat_text,
                    file_name="chat_history.txt",
                    mime="text/plain",
                    key="download_chat_footer_btn"
                )
        
        with footer_cols[1]:
            if st.button("🔄 Clear Chat", key="clear_chat_footer", use_container_width=True):
                st.session_state.messages = []
                st.session_state.processing = False
                st.rerun()
        
        with footer_cols[2]:
            st.metric("💬 Messages", len(st.session_state.messages))