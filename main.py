import streamlit as st
from llm_service import IncidentAnalyzer

st.set_page_config(
    page_title="Cross-Stack Incident Analyzer",
    page_icon="🔍",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .root-cause-box {
        background: #fff3cd !important;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
        color: #000000 !important;
    }
    .root-cause-box * {
        color: #000000 !important;
    }
    .solution-box {
        background: #d4edda !important;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        color: #000000 !important;
    }
    .solution-box * {
        color: #000000 !important;
    }
    .similar-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        margin: 0.8rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    .similar-card * {
        color: #000000 !important;
    }
    .similar-card h4 {
        color: #1a1a1a !important;
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# Initialize analyzer
@st.cache_resource
def get_analyzer():
    return IncidentAnalyzer()


# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.5rem;">🔍 Cross-Stack Incident Analyzer</h1>
    <p style="margin:0.5rem 0 0 0; font-size: 1.1rem;">AI-Powered Root Cause Analysis & Solutions</p>
</div>
""", unsafe_allow_html=True)

# Initialize form values ONCE
if 'form_description' not in st.session_state:
    st.session_state.form_description = ""
if 'form_tech_stack' not in st.session_state:
    st.session_state.form_tech_stack = "java"
if 'form_error_message' not in st.session_state:
    st.session_state.form_error_message = ""

# Sidebar with examples
with st.sidebar:
    st.markdown("### 📚 Quick Examples")

    if st.button("🔴 Database Timeout"):
        st.session_state.form_description = "Payment API timing out after 30 seconds when connecting to PostgreSQL database during checkout. Customers unable to complete purchases."
        st.session_state.form_tech_stack = "java"
        st.session_state.form_error_message = "SocketTimeoutException: Read timed out after 30000ms"

    if st.button("🟡 Null Reference"):
        st.session_state.form_description = "Getting NullPointerException when accessing user object after user deletes their account. Profile update API crashes."
        st.session_state.form_tech_stack = "java"
        st.session_state.form_error_message = "NullPointerException at UserService.java:156"

    if st.button("🟠 Memory Leak"):
        st.session_state.form_description = "Node.js service memory growing from 200MB to 4GB over 6 hours and crashing. WebSocket connections involved."
        st.session_state.form_tech_stack = "nodejs"
        st.session_state.form_error_message = "JavaScript heap out of memory"

    st.markdown("---")
    st.info(
        "💡 **How it works:**\n\n1. Describe incident\n2. AI searches 45 real cases\n3. Get root cause + solution\n4. See similar incidents")

    st.markdown("---")
    st.caption("🤖 Groq Llama-3.3-70B\n🗄️ PostgreSQL + Qdrant")

# Input form
st.markdown("### 📝 Describe Your Incident")

col1, col2 = st.columns([3, 1])

with col1:
    description = st.text_area(
        "Incident Description",
        value=st.session_state.form_description,
        placeholder="Describe what's happening in detail...",
        height=120,
        help="The more detail, the better the analysis"
    )

with col2:
    tech_stack = st.selectbox(
        "Tech Stack",
        ["java", "python", "nodejs"],
        index=["java", "python", "nodejs"].index(st.session_state.form_tech_stack)
    )

    error_message = st.text_input(
        "Error (optional)",
        value=st.session_state.form_error_message,
        placeholder="Paste error message"
    )

# Update session state when user types
st.session_state.form_description = description
st.session_state.form_tech_stack = tech_stack
st.session_state.form_error_message = error_message

# Analyze button
if st.button("🔍 Analyze Incident", type="primary", use_container_width=True):
    if not description:
        st.error("⚠️ Please describe the incident")
    else:
        with st.spinner("🤖 Analyzing with AI... Please wait 10-15 seconds"):
            try:
                analyzer = get_analyzer()
                result = analyzer.analyze_incident(description, tech_stack, error_message)

                st.success("✅ Analysis Complete!")

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        '<div class="metric-card"><h3 style="margin:0;">🎯 Root Cause</h3><p style="margin:0;">Identified</p></div>',
                        unsafe_allow_html=True)
                with col2:
                    if result["most_similar"]:
                        similarity = result["most_similar"]["similarity_score"]
                        st.markdown(
                            f'<div class="metric-card"><h3 style="margin:0;">📊 Similarity</h3><p style="margin:0;">{similarity:.0%} Match</p></div>',
                            unsafe_allow_html=True)
                with col3:
                    total_similar = len(result["same_stack"]) + len(result["cross_stack"])
                    st.markdown(
                        f'<div class="metric-card"><h3 style="margin:0;">🔍 Found</h3><p style="margin:0;">{total_similar} Similar</p></div>',
                        unsafe_allow_html=True)

                st.markdown("---")

                # Root Cause
                st.markdown("### 🎯 Most Likely Root Cause")
                st.markdown(f'<div class="root-cause-box">{result["root_cause"]}</div>', unsafe_allow_html=True)

                # Solution
                st.markdown("### ✅ Recommended Solution")
                solution_html = result["solution"].replace('\n', '<br>')
                st.markdown(f'<div class="solution-box">{solution_html}</div>', unsafe_allow_html=True)

                # Most Similar Incident
                if result["most_similar"]:
                    st.markdown("### 🔗 Most Similar Incident")
                    inc = result["most_similar"]
                    similarity_pct = inc['similarity_score'] * 100
                    st.markdown(f"""
                    <div class="similar-card">
                        <h4 style="margin-top:0;">{inc['id']}: {inc['title']}</h4>
                        <p><strong>Tech Stack:</strong> {inc['tech_stack']} | <strong>Error Type:</strong> {inc['error_type']} | <strong>Service:</strong> {inc['service']}</p>
                        <p><strong>Similarity:</strong> {similarity_pct:.1f}%</p>
                        <p><strong>Root Cause:</strong> {inc['root_cause']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📋 View Full Solution Steps"):
                        for i, step in enumerate(inc['solution'], 1):
                            st.markdown(f"**{i}.** {step}")

                # Reasoning
                with st.expander("💡 Why This Solution Works (Cross-Stack Reasoning)"):
                    st.write(result["reasoning"])

                # Additional Similar Incidents
                st.markdown("---")
                st.markdown("### 📚 Additional Similar Incidents")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🟢 Same Stack**")
                    if result["same_stack"]:
                        for inc in result["same_stack"][:3]:
                            title_short = inc['title'][:40] + "..." if len(inc['title']) > 40 else inc['title']
                            with st.expander(f"{inc['id']}: {title_short}"):
                                similarity_pct = inc['similarity_score'] * 100
                                st.write(f"**Similarity:** {similarity_pct:.1f}%")
                                st.write(f"**Error:** {inc['error_type']}")
                                root_short = inc['root_cause'][:120] + "..." if len(inc['root_cause']) > 120 else inc[
                                    'root_cause']
                                st.write(f"**Root Cause:** {root_short}")
                    else:
                        st.info("No same-stack incidents found")

                with col2:
                    st.markdown("**🟡 Cross-Stack**")
                    if result["cross_stack"]:
                        for inc in result["cross_stack"][:3]:
                            title_short = inc['title'][:40] + "..." if len(inc['title']) > 40 else inc['title']
                            with st.expander(f"{inc['id']}: {title_short} [{inc['tech_stack']}]"):
                                similarity_pct = inc['similarity_score'] * 100
                                st.write(f"**Similarity:** {similarity_pct:.1f}%")
                                st.write(f"**Error:** {inc['error_type']}")
                                root_short = inc['root_cause'][:120] + "..." if len(inc['root_cause']) > 120 else inc[
                                    'root_cause']
                                st.write(f"**Root Cause:** {root_short}")
                    else:
                        st.info("No cross-stack matches found")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                with st.expander("🔧 Troubleshooting"):
                    st.markdown("**Check these:**")
                    st.markdown("1. PostgreSQL is running")
                    st.markdown("2. Qdrant data exists")
                    st.markdown("3. Groq API key valid")
                    st.markdown("4. Run: `python setup_database_simple.py`")

# Footer
st.markdown("---")
st.caption("Built with ❤️ | Groq + PostgreSQL + Qdrant + Sentence-Transformers")
