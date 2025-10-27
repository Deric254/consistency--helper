import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Green theme configuration
GREEN_PRIMARY = "#2e7d32"
GREEN_LIGHT = "#66bb6a"
GREEN_DARK = "#1b5e20"

st.set_page_config(
    page_title="Deric Consistency Plan",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for green theme
st.markdown(f"""

    .main {{
        background-color: #f1f8f4;
    }}
    .stButton>button {{
        background-color: {GREEN_PRIMARY};
        color: white;
        border-radius: 8px;
    }}
    .stProgress > div > div {{
        background-color: {GREEN_PRIMARY};
    }}
    h1, h2, h3 {{
        color: {GREEN_DARK};
    }}

""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_db_connection():
    return sqlite3.connect('tracker.db', check_same_thread=False)

conn = get_db_connection()

# Header
st.title("🌿 Deric Consistency Plan Dashboard")
st.markdown(f"**Legacy Engine** | *Building discipline, one day at a time*")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    
    if st.button("▶️ Run Daily Flow", use_container_width=True):
        st.info("Execute from terminal: `python core.py`")
    
    if st.button("📧 Generate Outreach", use_container_width=True):
        st.info("Use option 1 in core.py menu")
    
    if st.button("📅 View Schedule", use_container_width=True):
        st.info("Checking scheduled items...")
    
    st.markdown("---")
    st.header("⚙️ Settings")
    
    date_range = st.selectbox(
        "View Range",
        ["Last 7 Days", "Last 30 Days", "All Time"]
    )

# Main metrics
col1, col2, col3, col4 = st.columns(4)

# Fetch today's progress
today = datetime.now().date().isoformat()
cursor = conn.cursor()

cursor.execute("SELECT tasks_completed FROM daily_progress WHERE date = ?", (today,))
result = cursor.fetchone()
tasks_today = result[0] if result else 0

cursor.execute("SELECT COUNT(*) FROM logs")
total_tasks = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM logs WHERE intent IS NOT NULL")
total_posts = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM schedule WHERE status = 'pending'")
pending_items = cursor.fetchone()[0]

with col1:
    st.metric(
        label="✅ Tasks Today",
        value=tasks_today,
        delta=f"{tasks_today}/5 complete"
    )

with col2:
    st.metric(
        label="📝 Total Tasks",
        value=total_tasks,
        delta="All time"
    )

with col3:
    st.metric(
        label="📱 Posts Generated",
        value=total_posts,
        delta="Multi-platform"
    )

with col4:
    st.metric(
        label="⏰ Pending Items",
        value=pending_items,
        delta="Scheduled"
    )

st.markdown("---")

# Progress visualization
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 7-Day Consistency Streak")
    
    # Fetch last 7 days
    cursor.execute("""
        SELECT date, tasks_completed 
        FROM daily_progress 
        ORDER BY date DESC 
        LIMIT 7
    """)
    progress_data = cursor.fetchall()
    
    if progress_data:
        df = pd.DataFrame(progress_data, columns=['Date', 'Tasks'])
        df = df.sort_values('Date')
        
        fig = px.bar(
            df,
            x='Date',
            y='Tasks',
            color_discrete_sequence=[GREEN_PRIMARY],
            title="Daily Task Completion"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=GREEN_DARK),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet. Start completing tasks!")

with col2:
    st.subheader("🎯 Today's Progress")
    
    progress_pct = (tasks_today / 5) * 100
    st.progress(progress_pct / 100)
    st.markdown(f"**{progress_pct:.0f}%** Complete")
    
    st.markdown("#### Task Checklist")
    tasks = [
        "Post outreach message",
        "DM 10 leads",
        "Offer audit to SMEs",
        "Update WhatsApp group",
        "Post recap with proof"
    ]
    
    for i, task in enumerate(tasks):
        if i < tasks_today:
            st.markdown(f"✅ ~~{task}~~")
        else:
            st.markdown(f"⬜ {task}")

st.markdown("---")

# Recent activity
st.subheader("📜 Recent Activity")

cursor.execute("""
    SELECT task, timestamp, intent 
    FROM logs 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
recent_logs = cursor.fetchall()

if recent_logs:
    df_logs = pd.DataFrame(recent_logs, columns=['Task', 'Timestamp', 'Intent'])
    df_logs['Timestamp'] = pd.to_datetime(df_logs['Timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    st.info("No activity logged yet")

# Scheduled items
st.markdown("---")
st.subheader("📅 Upcoming Schedule")

cursor.execute("""
    SELECT type, date, description, status 
    FROM schedule 
    WHERE status = 'pending'
    ORDER BY date ASC
""")
schedule_items = cursor.fetchall()

if schedule_items:
    df_schedule = pd.DataFrame(
        schedule_items,
        columns=['Type', 'Date', 'Description', 'Status']
    )
    st.dataframe(df_schedule, use_container_width=True, hide_index=True)
else:
    st.success("✅ No pending items. Schedule ahead!")

# Footer
st.markdown("---")
st.markdown(
    f""
    "🌿 Built for impact. Powered by discipline. | Deric Marangu"
    "",
    unsafe_allow_html=True
)