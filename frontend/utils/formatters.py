import streamlit as st

def format_response(response_data):
    """Format response data into detailed markdown"""
    
    formatted = ""
    
    # Main response
    if response_data.get('response'):
        formatted += f"## 📋 Answer\n\n{response_data['response']}\n\n"
    
    # Key points
    # if response_data.get('key_points'):
    #     formatted += "## 🎯 Key Points\n\n"
    #     for point in response_data['key_points']:
    #         formatted += f"- {point}\n"
    #     formatted += "\n"
    
    # Detailed sections
    if response_data.get('detailed_sections'):
        formatted += "## 📚 Detailed Sections\n\n"
        for i, section in enumerate(response_data['detailed_sections'], 1):
            formatted += f"### {section['title']}\n"
            formatted += f"**Source:** {section['source_file']}\n"
            formatted += f"**Relevance:** {section['relevance']}\n\n"
            formatted += f"{section['content']}\n\n"
    
    # Sources
    if response_data.get('sources'):
        formatted += "## 📖 Sources\n\n"
        for i, source in enumerate(response_data['sources'][:3], 1):
            formatted += f"{i}. {source[:100]}...\n"
    
    return formatted

def create_metric_card(title, value, icon="📊"):
    """Create a metric card"""
    st.markdown(f"""
    <div class='metric-card'>
        <h3>{icon} {title}</h3>
        <p style='font-size: 2rem; font-weight: bold;'>{value}</p>
    </div>
    """, unsafe_allow_html=True)

def create_response_box(title, content):
    """Create a response box"""
    st.markdown(f"""
    <div class='response-box'>
        <h4>{title}</h4>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)