"""
Streamlit web interface for meeting transcript chatbot with guardrails
"""
import streamlit as st
from datetime import datetime, timedelta
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag.chat_engine import MeetingChatEngine
from src.guardrails.user_manager import UserManager, Department, AccessLevel
from src.transcript_sources.google_drive import GoogleDriveSource
from src.transcript_sources.email import EmailSource
from src.transcript_sources.slack import SlackSource

# Page config
st.set_page_config(
    page_title="Meeting Assistant",
    page_icon="",
    layout="wide"
)

# Initialize session state
if 'chat_engine' not in st.session_state:
    st.session_state.chat_engine = MeetingChatEngine()

if 'user_manager' not in st.session_state:
    st.session_state.user_manager = UserManager()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'indexed' not in st.session_state:
    st.session_state.indexed = False

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Login section
if not st.session_state.current_user:
    st.title("Login to Meeting Assistant")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Enter your credentials")
        user_id = st.text_input("User ID", key="login_user_id")
        
        if st.button("Login", type="primary"):
            user = st.session_state.user_manager.get_user(user_id)
            if user:
                st.session_state.current_user = user
                st.rerun()
            else:
                st.error("❌ User not found")
    
    with col2:
        st.info("""
        ### Test Users
        
        **Admin Access:**
        - User ID: `admin`
        - Access: Full system access
        
        **Engineering Manager:**
        - User ID: `eng_manager`
        - Access: Engineering department + cross-dept
        
        **Sales Member:**
        - User ID: `sales_member`
        - Access: Sales department only
        
        **HR Manager:**
        - User ID: `hr_manager`
        - Access: HR department + cross-dept
        """)
    
    st.stop()

# User is logged in
user = st.session_state.current_user

# Sidebar
with st.sidebar:
    st.title(f"{user.name}")
    st.caption(f"**{user.department.value.title()}** | {user.access_level.value.title()}")
    
    if st.button("Logout"):
        st.session_state.current_user = None
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Index Management
    st.header("Index Transcripts")
    
    hours = st.number_input("Hours to look back", min_value=1, max_value=720, value=168)
    
    if st.button("Index New Transcripts", type="primary"):
        with st.spinner("Indexing transcripts..."):
            try:
                # Load config
                with open('config.yml') as f:
                    config = yaml.safe_load(f)
                
                # Get transcript source
                source_type = config['transcript_source']['type']
                
                if source_type == 'google_drive':
                    source = GoogleDriveSource(config['transcript_source'])
                elif source_type == 'email':
                    source = EmailSource(config['transcript_source'])
                elif source_type == 'slack':
                    source = SlackSource(config['transcript_source'])
                else:
                    st.error(f"Unsupported source: {source_type}")
                    source = None
                
                if source:
                    # Fetch transcripts
                    transcript_objects = source.get_recent_transcripts(hours=hours)
                    
                    # Convert Transcript objects to dicts for chat engine
                    transcripts = []
                    for t in transcript_objects:
                        transcripts.append({
                            'title': t.name,
                            'content': t.text,
                            'timestamp': t.modified_time or datetime.now().isoformat(),
                            'source': t.source
                        })
                    
                    # Index them
                    stats = st.session_state.chat_engine.index_multiple_transcripts(transcripts)
                    
                    st.success(f"Indexed {stats['added']} new transcripts")
                    if stats['skipped'] > 0:
                        st.info(f"Skipped {stats['skipped']} duplicates")
                    if stats['errors'] > 0:
                        st.warning(f"{stats['errors']} errors")
                    
                    st.session_state.indexed = True
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Stats
    st.header("Statistics")
    stats = st.session_state.chat_engine.get_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Meetings", stats['unique_meetings'])
    with col2:
        st.metric("Chunks", stats['total_chunks'])
    
    st.metric("Your Questions", user.query_count)
    
    # Task Creation
    st.divider()
    st.header("✅ Create Task")
    
    with st.form("create_task_form"):
        task_name = st.text_input("Task Description*", placeholder="e.g., Follow up with client about proposal")
        assignee = st.text_input("Assign To", placeholder="e.g., John Doe")
        due_date = st.date_input("Due Date", value=None)
        notes = st.text_area("Notes", placeholder="Additional details...")
        
        submit_task = st.form_submit_button("Create Task", type="primary")
        
        if submit_task:
            if not task_name:
                st.error("Please enter a task description")
            else:
                with st.spinner("Creating task..."):
                    result = st.session_state.chat_engine.create_task(
                        task_name=task_name,
                        assignee=assignee if assignee else None,
                        due_date=due_date.strftime("%Y-%m-%d") if due_date else None,
                        notes=notes if notes else None
                    )
                    
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['message'])
    
    # Admin features
    if user.access_level == AccessLevel.ADMIN:
        st.divider()
        st.header("🔧 Admin")
        
        if st.button(" View Audit Logs"):
            st.session_state.show_audit = True
        
        user_stats = st.session_state.user_manager.get_stats()
        st.metric("Total Users", user_stats['total_users'])
        st.metric("Total Queries", user_stats['total_queries'])
    
    # Clear chat
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_engine.clear_history()
        st.rerun()

# Main area
st.title("Meeting Assistant")
st.caption(f"Ask questions about your meeting transcripts | {user.access_level.value.title()} Access")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show metadata for assistant messages
        if message["role"] == "assistant":
            # Warnings
            if message.get("warnings"):
                for warning in message["warnings"]:
                    st.warning(warning)
            
            # Redactions
            if message.get("redactions"):
                st.info(f" {len(message['redactions'])} item(s) redacted for your access level")
            
            # Sources
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['title']}** - {source['timestamp']}")

# Chat input
if prompt := st.chat_input("Ask about your meetings..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.ask(prompt, user.user_id)
            
            # Check if blocked
            if response.get('blocked'):
                st.error(response['answer'])
                for warning in response.get('warnings', []):
                    st.warning(warning)
            else:
                # Display answer
                st.markdown(response['answer'])
                
                # Display warnings
                for warning in response.get('warnings', []):
                    st.warning(warning)
                
                # Display redactions
                if response.get('redactions'):
                    st.info(f"{len(response['redactions'])} item(s) redacted for your access level")
                
                # Display metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    confidence_emoji = {
                        'high': '🟢',
                        'medium': '🟡',
                        'low': '🔴',
                        'none': '⚫'
                    }
                    confidence_score = response.get('confidence_score', 0)
                    st.caption(f"Confidence: {confidence_emoji.get(response['confidence'], '⚫')} {response['confidence'].upper()} ({confidence_score}%)")
                with col2:
                    st.caption(f"Sources: {len(response.get('sources', []))}")
                with col3:
                    risk_score = response.get('risk_score', 0.0)
                    if risk_score >= 0.7:
                        risk_color = "🔴"
                        risk_label = "HIGH"
                    elif risk_score >= 0.4:
                        risk_color = "🟡"
                        risk_label = "MEDIUM"
                    elif risk_score > 0:
                        risk_color = "🟢"
                        risk_label = "LOW"
                    else:
                        risk_color = "⚪"
                        risk_label = "NONE"
                    st.caption(f"Risk: {risk_color} {risk_label} ({risk_score:.2f})")
                
                # Show risk warning if applicable
                if risk_score >= 0.7:
                    st.error(f"🔴 **HIGH RISK** - This response contains highly sensitive information. Verify access permissions before sharing.")
                elif risk_score >= 0.4:
                    st.warning(f"🟡 **MEDIUM RISK** - This response may contain sensitive information. Use discretion when sharing.")
                
                # Show confidence warning if applicable
                confidence_level = response.get('confidence', 'none')
                confidence_score = response.get('confidence_score', 0)
                if confidence_level == 'low':
                    st.info(f"ℹ️ **Low Confidence ({confidence_score}%)** - The answer may not be fully accurate. Consider rephrasing your question or checking source documents.")
                elif confidence_level == 'none':
                    st.warning(f"⚠️ **Very Low Confidence ({confidence_score}%)** - Could not find relevant information. Try asking differently or check if the data exists.")
                
                # Display sources
                if response['sources']:
                    with st.expander("📄 Sources"):
                        for source in response['sources']:
                            st.markdown(f"**{source['title']}** - {source['timestamp']}")
            
            # Add to messages
            st.session_state.messages.append({
                "role": "assistant",
                "content": response['answer'],
                "sources": response.get('sources', []),
                "warnings": response.get('warnings', []),
                "redactions": response.get('redactions', []),
                "confidence": response.get('confidence'),
                "blocked": response.get('blocked', False)
            })

# Example questions
if not st.session_state.messages and st.session_state.indexed:
    st.info("**Example questions:**")
    
    examples = [
        "What were the main action items from last week's meetings?",
        "Who is responsible for the Q4 deliverables?",
        "What deadlines were mentioned in recent meetings?",
        "Summarize the decisions made about the new feature",
        "What concerns were raised about the timeline?"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            if st.button(example, key=f"example_{i}"):
                st.session_state.messages.append({"role": "user", "content": example})
                st.rerun()

# First time user
if not st.session_state.indexed:
    st.warning("Please index your transcripts first using the sidebar")

# Show audit logs (admin only)
if user.access_level == AccessLevel.ADMIN and st.session_state.get('show_audit'):
    st.divider()
    st.header("Audit Logs")
    
    logs = st.session_state.chat_engine.get_audit_logs(limit=50)
    
    for log in reversed(logs):
        with st.expander(f"{log['timestamp']} - {log['event_type']} - {log['user_name']}"):
            st.json(log)
