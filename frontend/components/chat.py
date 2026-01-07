def show_processing_animation():
    """Show an animated processing indicator"""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">
        <div style="font-size: 24px;">
            <span style="animation: spin 1s linear infinite; display: inline-block;">⚙️</span>
        </div>
        <div>
            <div style="font-weight: 600; font-size: 16px;">Processing Your Query...</div>
            <div style="font-size: 13px; opacity: 0.9; margin-top: 4px;">Analyzing documents and generating response</div>
        </div>
    </div>
    
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
    </style>
    """, unsafe_allow_html=True)


def show_thinking_indicator():
    """Show thinking/analyzing indicator"""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; padding: 12px 15px; background: #f0f4ff; border-left: 4px solid #667eea; border-radius: 6px;">
        <div style="font-size: 20px;">
            <span style="animation: bounce 1.4s infinite; display: inline-block;">🤔</span>
        </div>
        <div>
            <div style="font-size: 14px; color: #333;">
                <strong>Thinking...</strong> Searching through documents
            </div>
        </div>
    </div>
    
    <style>
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
    </style>
    """, unsafe_allow_html=True)


def show_search_indicator(passages_count: int = 0):
    """Show search progress indicator"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; padding: 12px 15px; background: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 6px; margin: 10px 0;">
        <div style="font-size: 20px;">
            <span style="animation: pulse 1.5s infinite; display: inline-block;">🔍</span>
        </div>
        <div>
            <div style="font-size: 14px; color: #333;">
                <strong>Searching...</strong> Found {passages_count} relevant passages
            </div>
        </div>
    </div>
    
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def show_generating_indicator():
    """Show response generation indicator"""
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; padding: 12px 15px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px; margin: 10px 0;">
        <div style="font-size: 20px;">
            <span style="animation: spin 2s linear infinite; display: inline-block;">✍️</span>
        </div>
        <div>
            <div style="font-size: 14px; color: #333;">
                <strong>Generating...</strong> Creating detailed response
            </div>
        </div>
    </div>
    
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)# Finance Chatbot - Chat Interface
# Check if user is admin BEFORE showing sensitive details

import streamlit as st
import requests
import json
import re
import math

from utils.api_client import send_message, API_URL





# ============================================================
# CONSTANTS & CONFIG
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

GREETING_KEYWORDS = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"}


# ============================================================
# SESSION STATE MANAGEMENT
# ============================================================
def get_user_messages_key() -> str:
    """Get user-specific messages key for session state"""
    if st.session_state.get("authenticated"):
        username = st.session_state.user.get("username", "guest")
        return f"messages_{username}"
    return "messages_guest"


def get_processing_key(messages_key: str) -> str:
    """Get processing flag key"""
    return f"processing_{messages_key}"


def get_context_key(messages_key: str, msg_idx: int) -> str:
    """Get context storage key for a specific message"""
    return f"context_{messages_key}_{msg_idx}"


def init_session_state() -> tuple:
    """Initialize session state and return keys"""
    messages_key = get_user_messages_key()
    processing_key = get_processing_key(messages_key)
    
    if messages_key not in st.session_state:
        st.session_state[messages_key] = []
    if processing_key not in st.session_state:
        st.session_state[processing_key] = False
    
    return messages_key, processing_key


# ============================================================
# RESPONSE GENERATION
# ============================================================
def generate_next_steps(user_question: str, answer_text: str) -> list:
    """Generate contextual next step suggestions based on QUESTION TOPIC, not all documents"""
    suggestions = []
    
    question_lower = user_question.lower()
    answer_lower = answer_text.lower()
    has_numbers = any(char.isdigit() for char in answer_text)
    answer_length = len(answer_text.split())
    
    # Extract key topic from question
    question_topic = extract_question_topic(user_question)
    
    # Suggestion 1: Summarize (if answer is long)
    if answer_length > 150:
        suggestions.append({
            "label": "⚡ Can you summarize this?",
            "emoji": "⚡",
            "reason": "Get a quick, concise summary",
            "icon_color": "#F59E0B",
            "hint": f"About {question_topic}"
        })
    
    # Suggestion 2: Related question (context-specific)
    if "prerequisite" in question_lower or "requirement" in question_lower:
        suggestions.append({
            "label": "🔍 What comes after?",
            "emoji": "🔍",
            "reason": "Explore next steps in the sequence",
            "icon_color": "#06B6D4"
        })
    elif "course" in question_lower or "class" in question_lower:
        suggestions.append({
            "label": "🔍 Related courses",
            "emoji": "🔍",
            "reason": "Discover connected courses",
            "icon_color": "#06B6D4"
        })
    else:
        suggestions.append({
            "label": "🔍 Ask a related question",
            "emoji": "🔍",
            "reason": f"Dive deeper into {question_topic}",
            "icon_color": "#06B6D4"
        })
    
    # Suggestion 3: Make specific (if question was vague)
    if len(user_question.strip()) < 40:
        suggestions.append({
            "label": "🎯 Be more specific",
            "emoji": "🎯",
            "reason": "Narrow down for precise answers",
            "icon_color": "#3B82F6"
        })
    
    # Suggestion 4: Explain numbers (if answer has data)
    if has_numbers or '%' in answer_text or any(keyword in answer_lower for keyword in ['units', 'credits', 'hours', 'required', 'maximum', 'minimum', 'number', 'count']):
        suggestions.append({
            "label": "📊 Explain the numbers",
            "emoji": "📊",
            "reason": "Understand specific metrics",
            "icon_color": "#F59E0B"
        })
    
    # Suggestion 5: Examples (if answer is conceptual)
    if any(keyword in answer_lower for keyword in ['can', 'may', 'should', 'recommend', 'suggest', 'option', 'pathway', 'include']):
        suggestions.append({
            "label": "💡 Show me examples",
            "emoji": "💡",
            "reason": f"Examples related to {question_topic}",
            "icon_color": "#FBBF24"
        })
    
    # Suggestion 6: Deep dive (context-aware)
    suggestions.append({
        "label": "🎯 Deep dive into details",
        "emoji": "🎯",
        "reason": f"Detailed information about {question_topic}",
        "icon_color": "#10B981"
    })
    
    return suggestions[:6]


def extract_question_topic(question: str) -> str:
    """Extract main topic from question"""
    question_lower = question.lower()
    
    # Finance-related topics
    if "fnce" in question_lower or "finance" in question_lower:
        return "Finance"
    elif "course" in question_lower or "class" in question_lower:
        if "fnce" in question_lower:
            return "Finance Courses"
        return "Courses"
    elif "prerequisite" in question_lower:
        return "Prerequisites"
    elif "requirement" in question_lower:
        return "Requirements"
    elif "major" in question_lower:
        return "Major Requirements"
    elif "pathway" in question_lower:
        return "Career Pathways"
    elif "internship" in question_lower:
        return "Internships"
    elif "graduate" in question_lower:
        return "Graduation"
    else:
        # Extract first key noun
        words = question.split()
        for word in words:
            if len(word) > 4 and word not in ["what", "when", "where", "which", "would", "could"]:
                return word.capitalize()
        return "this topic"


# ============================================================
# VISUALIZATION
# ============================================================
def create_hierarchy_graph(passages: list) -> str | None:
    """Create an Entity-Relationship (EER) graph visualization"""
    if not passages:
        return None
    
    entities = {}
    relationships = []
    
    # Extract entities and relationships
    for idx, passage in enumerate(passages, 1):
        source = passage.get("source", "Unknown")
        text = passage.get("text", "")
        
        if source not in entities:
            entities[source] = {"type": "document", "count": 0, "passages": []}
        entities[source]["count"] += 1
        entities[source]["passages"].append(idx)
        
        # Extract key terms (capitalized words)
        terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text[:200])
        for term in set(terms[:2]):
            if term not in entities and len(term) > 3:
                entities[term] = {"type": "concept", "count": 1, "passages": [idx]}
            if term in entities and entities[term]["type"] == "concept":
                if idx not in entities[term]["passages"]:
                    entities[term]["passages"].append(idx)
                    relationships.append((source, term, "mentions"))
    
    # Calculate entity positions
    entity_list = list(entities.items())
    num_entities = len(entity_list)
    positions = {}
    
    for i, (name, entity) in enumerate(entity_list):
        angle = (2 * math.pi * i) / num_entities if num_entities > 1 else 0
        x = 150 + 120 * math.cos(angle)
        y = 150 + 120 * math.sin(angle)
        positions[name] = (x, y)
    
    # Build HTML
    html = """
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #f8f9fa; border-radius: 10px;">
        <h3 style="color: #333; margin-bottom: 20px;">📊 Entity-Relationship Graph</h3>
        <div style="background: white; padding: 20px; border-radius: 8px; border: 2px solid #667eea;">
            <svg width="100%" height="300" style="background: #fafafa; border-radius: 5px;">
    """
    
    # Draw relationships
    for entity_a, entity_b, _ in relationships[:10]:
        if entity_a in positions and entity_b in positions:
            x1, y1 = positions[entity_a]
            x2, y2 = positions[entity_b]
            html += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#ccc" stroke-width="2" marker-end="url(#arrowhead)" />'
    
    # Arrow marker definition
    html += """
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#999" />
            </marker>
        </defs>
    """
    
    # Draw entities
    for name, entity in entity_list:
        if name in positions:
            x, y = positions[name]
            color = "#667eea" if entity["type"] == "document" else "#22c55e"
            icon = "📄" if entity["type"] == "document" else "🏷️"
            
            html += f"""
            <circle cx="{x}" cy="{y}" r="35" fill="{color}" opacity="0.2" stroke="{color}" stroke-width="2"/>
            <text x="{x}" y="{y-8}" text-anchor="middle" font-size="12" font-weight="bold" fill="{color}">{icon}</text>
            <text x="{x}" y="{y+15}" text-anchor="middle" font-size="10" fill="#333" font-weight="600">
                {name[:15]}{'...' if len(name) > 15 else ''}
            </text>
            """
    
    html += """
            </svg>
        </div>
        <div style="margin-top: 15px; padding: 10px; background: #f0f4ff; border-radius: 5px;">
            <h4 style="color: #667eea; margin-top: 0;">📈 Entities Summary:</h4>
    """
    
    doc_count = sum(1 for e in entities.values() if e["type"] == "document")
    concept_count = sum(1 for e in entities.values() if e["type"] == "concept")
    
    html += f"""
            <div style="font-size: 0.9em; color: #666;">
                <div>📄 <strong>Documents:</strong> {doc_count}</div>
                <div>🏷️ <strong>Concepts:</strong> {concept_count}</div>
                <div>📊 <strong>Relationships:</strong> {len(relationships)}</div>
            </div>
        </div>
    </div>
    """
    
    return html


# ============================================================
# RESPONSE DISPLAY
# ============================================================
def display_answer(response_data: dict) -> None:
    """Display the main answer section"""
    st.markdown("### 📖 Answer")
    st.markdown(response_data.get("response", "No response generated"))


def display_model_info(response_data: dict) -> None:
    """Display model information"""
    st.markdown("---")
    st.markdown("### 🤖 Model Information")
    
    col1, col2 = st.columns(2)
    selected_model = response_data.get("selected_model", "unknown")
    model_used = response_data.get("model_used", "unknown")
    
    with col1:
        st.info(f"**Selected:** {selected_model}")
    
    with col2:
        model_display = {
            "google": "**Used:** 🔵 Google Gemini",
            "ollama": "**Used:** 🟢 Ollama",
            "deepseek": "**Used:** 🔷 DeepSeek"
        }
        st.success(model_display.get(model_used, f"**Used:** {model_used}"))


def display_key_points(response_data: dict) -> None:
    """Display key points from response"""
    key_points = response_data.get("key_points", [])
    if key_points:
        st.markdown("### 🎯 Key Points")
        for i, point in enumerate(key_points, 1):
            st.markdown(f"**{i}.** {point}")
        st.divider()


def filter_relevant_passages(passages: list, threshold: float = 0.3) -> list:
    """Filter passages by relevance score (distance <= threshold) - Very strict filtering"""
    return [p for p in passages if isinstance(p.get("distance"), (int, float)) and p.get("distance") <= threshold]


def display_hierarchy_graph(response_data: dict) -> None:
    """Display entity-relationship graph"""
    passages = response_data.get("passages", []) or []
    relevant_passages = filter_relevant_passages(passages)
    
    if relevant_passages:
        hierarchy_html = create_hierarchy_graph(relevant_passages)
        if hierarchy_html:
            st.markdown(hierarchy_html, unsafe_allow_html=True)
            st.divider()


def display_admin_sources(response_data: dict) -> None:
    """Display source details (admin only) - Very strict filtering"""
    passages = response_data.get("passages", []) or []
    relevant_passages = filter_relevant_passages(passages, threshold=0.3)
    
    if relevant_passages:
        with st.expander(f"📚 Excellent Sources ({len(relevant_passages)} passages)", expanded=False):
            for idx, passage in enumerate(relevant_passages[:8], start=1):
                source = passage.get("source", "Unknown")
                distance = passage.get("distance")
                text = (passage.get("text") or "").strip()
                
                # Determine relevance (very strict scale)
                if isinstance(distance, (int, float)):
                    if distance <= 0.2:
                        relevance = "🔴 Perfect Match"
                    elif distance <= 0.3:
                        relevance = "🟠 Excellent"
                    else:
                        relevance = "🟡 Good"
                else:
                    relevance = "⚪ Unknown"
                
                st.markdown(f"**{idx}. {source}** — {relevance} (Score: {distance:.3f})")
                snippet = text[:300] + "..." if len(text) > 300 else text
                st.code(snippet, language="text")
                st.divider()
    else:
        st.info("No passages meet the strict relevance threshold (< 0.3)")


def display_admin_urls(response_data: dict) -> None:
    """Display URL content (admin only)"""
    passages = response_data.get("passages", []) or []
    document_urls = {p.get("url") for p in passages if p.get("url") and p.get("url") != "None"}
    
    url_summaries = response_data.get("url_summaries", [])
    document_url_summaries = [u for u in url_summaries if u.get("url") in document_urls]
    
    if document_url_summaries:
        st.divider()
        st.markdown(f"### 🌐 Content from Document URLs ({len(document_url_summaries)} found)")
        
        for idx, url_data in enumerate(document_url_summaries, 1):
            st.markdown(f"#### 📎 {idx}. {url_data.get('title', 'URL')}")
            st.markdown(f"**URL:** [{url_data['url']}]({url_data['url']})")
            
            if url_data.get('error'):
                st.error(f"❌ Error: {url_data['error']}")
            else:
                content = url_data.get('text', '')
                if content:
                    preview = content[:500] + ("..." if len(content) > 500 else "")
                    st.info(f"**Preview:** {preview}")
                    
                    if st.checkbox(f"📄 Show Full Content", key=f"show_url_{idx}"):
                        st.text_area("Full Content", value=content, height=300, 
                                   key=f"url_content_{idx}", disabled=True)
            st.markdown("---")


def is_user_admin() -> bool:
    """Check if current user is admin"""
    return (st.session_state.get("authenticated") and 
            st.session_state.get("user") and 
            st.session_state.user.get("role") == "admin")


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def is_greeting(query: str) -> bool:
    """Check if query is a greeting"""
    return query.lower().strip() in GREETING_KEYWORDS


def check_documents_exist() -> int:
    """Check if documents are available"""
    try:
        resp = requests.get(f"{API_URL}/api/documents", timeout=5)
        return resp.json().get("total_documents", 0)
    except Exception:
        return 0


# ============================================================
# CHAT DISPLAY COMPONENTS
# ============================================================
def render_faq_section() -> None:
    """Render FAQ dropdown section"""
    st.markdown("### 📚 Quick FAQ")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        selected_faq = st.selectbox(
            "Choose a frequently asked question:",
            options=["-- Select a question --"] + QUICK_FAQS,
            key="faq_selector",
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("🚀 Ask", key="faq_ask_btn", use_container_width=True, type="primary"):
            if selected_faq != "-- Select a question --":
                messages_key, processing_key = init_session_state()
                st.session_state[messages_key].append({"role": "user", "content": selected_faq})
                st.session_state[processing_key] = True
                st.rerun()
    
    st.markdown("---")


def render_chat_history(messages_key: str, processing_key: str) -> None:
    """Render chat message history with context-aware next steps on all assistant messages"""
    # Check if user is admin
    is_admin = is_user_admin()
    
    for msg_idx, message in enumerate(st.session_state[messages_key]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show next steps ONLY for ADMIN users and only for assistant messages
            if message["role"] == "assistant" and not st.session_state[processing_key] and is_admin:
                # Get the user question that preceded this answer
                prev_user_msg = ""
                if msg_idx > 0 and st.session_state[messages_key][msg_idx - 1]["role"] == "user":
                    prev_user_msg = st.session_state[messages_key][msg_idx - 1]["content"]
                
                next_steps = generate_next_steps(prev_user_msg, message["content"])
                
                if next_steps:
                    st.markdown("---")
                    st.markdown("### 🚀 Next Steps (Admin Only)")
                    
                    cols = st.columns(2)
                    for step_idx, step in enumerate(next_steps[:6]):
                        col = cols[step_idx % 2]
                        
                        with col:
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, {step['icon_color']}10 0%, {step['icon_color']}05 100%);
                                border-left: 4px solid {step['icon_color']};
                                border-radius: 8px;
                                padding: 0.75rem;
                                margin: 0.5rem 0;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            ">
                                <div style="font-size: 0.95rem; font-weight: 600; color: {step['icon_color']}; margin-bottom: 0.25rem;">
                                    {step['emoji']} {step['label'].replace(step['emoji'], '').strip()}
                                </div>
                                <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.4;">
                                    {step['reason']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Unique key includes message index to ensure each next step is independent
                            if st.button("✨ Ask This", key=f"next_step_{msg_idx}_{step_idx}", 
                                       use_container_width=True, type="secondary"):
                                
                                # Get passages from parent answer
                                parent_msg = st.session_state[messages_key][msg_idx]
                                context_passages = parent_msg.get("_passages", [])
                                
                                # Add new user message with context tracking
                                st.session_state[messages_key].append({
                                    "role": "user",
                                    "content": step["label"],
                                    "_parent_idx": msg_idx  # Track which answer this came from
                                })
                                
                                # Mark that this is a constrained follow-up
                                st.session_state[f"constrain_to_{len(st.session_state[messages_key])-1}"] = context_passages
                                st.session_state[processing_key] = True
                                st.rerun()


def render_chat_input(messages_key: str, processing_key: str) -> None:
    """Render chat input and handle submission"""
    user_input = st.chat_input("Ask a question about your documents...")
    
    if user_input:
        st.session_state[messages_key].append({"role": "user", "content": user_input})
        st.session_state[processing_key] = True
        st.rerun()


def render_footer(messages_key: str, processing_key: str) -> None:
    """Render footer with action buttons"""
    if len(st.session_state[messages_key]) == 0:
        return
    
    st.markdown("---")
    cols = st.columns(3)
    
    with cols[0]:
        if st.button("📋 Export Chat", key="export_chat", use_container_width=True):
            chat_text = "Finance Chatbot - Chat History\n" + "="*60 + "\n\n"
            for i, msg in enumerate(st.session_state[messages_key], 1):
                role = "👤 USER" if msg["role"] == "user" else "🤖 ASSISTANT"
                chat_text += f"[{i}] {role}:\n{msg['content']}\n\n"
            
            st.download_button("⬇️ Download", data=chat_text, file_name="chat_history.txt", 
                             mime="text/plain", key="download_btn")
    
    with cols[1]:
        if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
            st.session_state[messages_key] = []
            st.session_state[processing_key] = False
            st.rerun()
    
    with cols[2]:
        st.metric("💬 Messages", len(st.session_state[messages_key]))


# ============================================================
# MAIN CHAT INTERFACE
# ============================================================
def chat_interface() -> None:
    """Main chat interface function"""
    
    # Initialize session state
    messages_key, processing_key = init_session_state()
    
    # Check for documents
    doc_count = check_documents_exist()
    if doc_count == 0:
        st.warning("📋 No documents uploaded yet!\n\nPlease go to the **📤 Upload** tab to upload documents first.")
        return
    
    st.info(f"📚 **{doc_count}** document chunks in knowledge base")
    
    # Render FAQ section
    render_faq_section()
    
    # Render chat history
    render_chat_history(messages_key, processing_key)
    
    # Render chat input
    render_chat_input(messages_key, processing_key)
    
    # ============================================================
    # PROCESS LAST MESSAGE IF NEEDED
    # ============================================================
    if st.session_state[processing_key] and len(st.session_state[messages_key]) > 0:
        last_msg = st.session_state[messages_key][-1]
        
        if last_msg["role"] == "user":
            user_query = last_msg["content"]
            
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
                        st.session_state[processing_key] = False
                        return
                    
                    main_response = response_data.get("response") or response_data.get("main_response") or ""
                    
                    if not main_response.strip():
                        with placeholder.container():
                            st.warning("⚠️ No response generated")
                        st.session_state[processing_key] = False
                        return
                    
                    placeholder.empty()
                    
                    # Display response components
                    display_answer(response_data)
                    display_model_info(response_data)
                    display_key_points(response_data)
                    
                    # Check passage relevance
                    all_passages = response_data.get("passages", []) or []
                    relevant_passages = filter_relevant_passages(all_passages, threshold=0.3)
                    
                    if len(relevant_passages) == 0:
                        st.warning("⚠️ No highly relevant passages found for this query. Try rephrasing your question.")
                    elif len(all_passages) > len(relevant_passages):
                        filtered_count = len(all_passages) - len(relevant_passages)
                        st.info(f"✅ Showing {len(relevant_passages)} highly relevant passages (filtered {filtered_count} low-quality matches)")
                    
                    display_hierarchy_graph(response_data)
                    
                    # Admin-only sections
                    if is_user_admin():
                        display_admin_urls(response_data)
                        display_admin_sources(response_data)
                    
                    # Save and finalize
                    st.session_state[messages_key].append({"role": "assistant", "content": main_response})
                    st.success("✅ Response complete")
                    st.session_state[processing_key] = False
                    st.rerun()
                
                except Exception as e:
                    print(f"\n[ERROR] {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    with placeholder.container():
                        st.error(f"❌ Error: {str(e)}")
                    
                    st.session_state[processing_key] = False
    
    # Render footer
    render_footer(messages_key, processing_key)