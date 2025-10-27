import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# Ensure DB schema and image checks run when the GUI starts so users
# don't need to run terminal helpers manually.
from core import Database, ImageManager, ConsistencyEngine
from scripts.normalize_images import normalize_images, pretty_print
from social_poster import post, load_secrets

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
<style>
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
</style>
""", unsafe_allow_html=True)

# Ensure database schema exists before dashboard queries run
# This uses the existing Database initializer which creates tables if needed.
db_init = Database('tracker.db')
db_init.close()

# Database connection (cached resource for Streamlit)
@st.cache_resource
def get_db_connection():
    return sqlite3.connect('tracker.db', check_same_thread=False)

conn = get_db_connection()

# Image sanity check: warns and prints instructions in the GUI instead of
# requiring the user to run a terminal script.
img_manager = ImageManager('.')
missing_images = img_manager.get_missing_images()
if missing_images:
    st.warning(f"Missing outreach images: {len(missing_images)} files. The app will be more reliable if these are added.")
    st.write("Missing files (expected pattern: day1.png ... day7.png):")
    for m in missing_images:
        st.write(f"- {m}")
    st.info(img_manager.get_setup_instructions())
    if st.button("Auto-fix images (non-destructive)"):
        result = normalize_images('.')
        st.code(pretty_print(result))
        if result.get('errors'):
            st.error('Some errors occurred during normalization. See details above.')
        else:
            st.success('Normalization complete — missing files were copied where possible.')

# Header
st.title("🌿 Deric Consistency Plan Dashboard")
st.markdown(f"**Legacy Engine** | *Building discipline, one day at a time*")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    
    if st.button("▶️ Run Daily Flow", use_container_width=True):
        # Open a small form to run the daily flow via GUI
        engine = ConsistencyEngine()
        progress = engine.db.get_today_progress()
        idx = progress['tasks_completed']
        current_task = engine.tasks[idx] if idx < len(engine.tasks) else None

        with st.form(key='daily_flow_form'):
            st.write(f"Current task: {current_task}")
            if current_task and "Post outreach message" in current_task:
                intent_choice = st.selectbox("Intent", ("teachingleads", "analyticsleads"), format_func=lambda x: "Teaching Leads" if x=="teachingleads" else "Analytics Leads")
                platforms = ["whatsapp","linkedin","facebook","twitter","instagram"]
                platform_choice = st.selectbox("Enhance platform (optional)", [None] + platforms)
                use_ai = st.checkbox("Use AI enhancement (if available)")
                submit = st.form_submit_button("Run Outreach")
            else:
                confirm = st.checkbox("Mark this task as complete")
                submit = st.form_submit_button("Run Task")

        if submit:
            if current_task and "Post outreach message" in current_task:
                res = engine.run_daily_flow_gui(intent_choice=intent_choice, enhance_platform=platform_choice, use_enhanced=use_ai)
                if res['status'] == 'ok':
                    st.success(res['message'])
                    if res.get('posts'):
                        st.subheader("Generated Posts")
                        for p, text in res['posts'].items():
                            st.markdown(f"**{p.title()}**")
                            st.text_area(f"{p}", value=text, height=120)
                else:
                    st.error(res['message'])
            else:
                res = engine.run_daily_flow_gui(confirm_standard=confirm)
                if res['logged']:
                    st.success(res['message'])
                else:
                    st.info(res['message'])
    
    if st.button("📧 Generate Outreach", use_container_width=True):
        # Ensure a single engine instance per Streamlit session
        if 'engine' not in st.session_state:
            st.session_state.engine = ConsistencyEngine()
        engine = st.session_state.engine

        with st.form(key='generate_outreach'):
            intent_choice = st.selectbox('Intent', ("teachingleads", "analyticsleads"), format_func=lambda x: "Teaching Leads" if x=="teachingleads" else "Analytics Leads")
            day_number = st.number_input('Day number (1-7, leave 0 for auto)', min_value=0, max_value=7, value=0)
            # allow explicit selection of platforms to generate
            platforms = engine.outreach_gen.PLATFORMS
            chosen = st.multiselect('Platforms to generate', options=platforms, default=platforms)
            use_ai = st.checkbox('Use AI enhancement (may take longer)')
            auto_log = st.checkbox('Automatically log generated posts to DB', value=False)
            ai_platform = None
            if use_ai:
                ai_platform = st.selectbox('Which platform to enhance (optional)', [None] + platforms)
            submit_gen = st.form_submit_button('Generate')

        if submit_gen:
            # determine day
            if day_number == 0:
                day_number = (datetime.now().timetuple().tm_yday % 7) + 1

            audience = 'learners' if intent_choice == 'teachingleads' else 'SMEs'
            img_ok = engine.image_manager.validate_image(day_number, intent_choice)
            if not img_ok:
                st.error(f"Missing image for {intent_choice}/day{day_number}.png. Use Auto-fix or add the image.")
            else:
                image_path = engine.image_manager.get_image_path(day_number, intent_choice)
                # generate full set and filter by chosen
                with st.spinner('Generating posts...'):
                    posts = engine.outreach_gen.generate_post(intent_choice, audience, day_number, image_path)

                # filter posts to only chosen platforms
                posts = {p: posts[p] for p in posts.keys() if p in chosen}

                if not posts:
                    st.info('No platforms selected.')
                else:
                    st.success('Posts generated')
                    for p, text in posts.items():
                        st.subheader(p.title())
                        st.text_area(p, value=text, height=140, key=f"post_{p}")

                    # Auto-log generated posts if requested. Log one task completion for the outreach task.
                    if auto_log:
                        try:
                            for p, text in posts.items():
                                engine.db.log_task("Post outreach message", text, intent_choice, str(image_path))
                            # mark task complete once
                            engine.db.update_daily_progress()
                            st.success('All generated posts logged to DB and progress updated')
                            # Refresh the app so metrics update
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f'Failed to auto-log posts: {e}')

                # AI enhancement (run with timeout to avoid hanging)
                if use_ai and ai_platform:
                    if ai_platform not in posts:
                        st.warning(f"AI platform {ai_platform} not in generated set; skipping enhancement.")
                    else:
                        import concurrent.futures
                        with st.spinner('Enhancing post with AI...'):
                            try:
                                def enhance():
                                    return engine.ai_enhancer.enhance_post(posts[ai_platform], ai_platform, tone=engine.config.get('branding', {}).get('tone','empowering'))

                                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                                    fut = ex.submit(enhance)
                                    enhanced = fut.result(timeout=20)
                                st.success('AI enhancement complete')
                                st.subheader(f'{ai_platform.title()} (Enhanced)')
                                st.text_area(f"{ai_platform}_enhanced", value=enhanced, height=140)
                                # offer to log the enhanced version
                                if st.button(f"Log {ai_platform} (enhanced) to DB"):
                                    engine.db.log_task("Post outreach message", enhanced, intent_choice, str(image_path))
                                    engine.db.update_daily_progress()
                                    st.success('Logged enhanced post to DB')
                            except concurrent.futures.TimeoutError:
                                st.error('AI enhancement timed out (took too long). Try again or disable AI).')
                            except Exception as e:
                                st.error(f'AI enhancement failed: {e}')

                # allow logging original generated posts per-platform
                for p in posts.keys():
                    if st.button(f"Log {p} to DB"):
                        engine.db.log_task("Post outreach message", posts[p], intent_choice, str(image_path))
                        engine.db.update_daily_progress()
                        st.success(f'Logged {p} post to DB')
    
    if st.button("📅 View Schedule", use_container_width=True):
        st.info("Checking scheduled items...")
    
    st.markdown("---")
    st.header("⚙️ Settings")
    
    date_range = st.selectbox(
        "View Range",
        ["Last 7 Days", "Last 30 Days", "All Time"]
    )

    # Social credentials settings
    st.subheader('🔐 Social Accounts (optional)')
    secrets = load_secrets()
    linkedin = st.text_input('LinkedIn Access Token', value=secrets.get('linkedin_token',''))
    twitter = st.text_input('Twitter Bearer Token', value=secrets.get('twitter_bearer',''))
    facebook = st.text_input('Facebook Page Token', value=secrets.get('facebook_page_token',''))
    whatsapp_url = st.text_input('WhatsApp API URL', value=secrets.get('whatsapp_url',''))
    whatsapp_token = st.text_input('WhatsApp API Token', value=secrets.get('whatsapp_token',''))

    if st.button('Save Social Credentials'):
        # Write secrets.json locally and ensure it's gitignored
        data = {
            'linkedin_token': linkedin.strip(),
            'twitter_bearer': twitter.strip(),
            'facebook_page_token': facebook.strip(),
            'whatsapp_url': whatsapp_url.strip(),
            'whatsapp_token': whatsapp_token.strip()
        }
        try:
            Path('secrets.json').write_text(json.dumps(data, indent=2))
            # ensure .gitignore contains secrets.json
            gi = Path('.gitignore')
            if gi.exists():
                content = gi.read_text()
                if 'secrets.json' not in content:
                    gi.write_text(content + '\nsecrets.json\n')
            else:
                Path('.gitignore').write_text('secrets.json\n')
            st.success('Credentials saved locally to secrets.json (not committed).')
        except Exception as e:
            st.error(f'Failed to save credentials: {e}')

    if st.button('Test Social Credentials'):
        s = load_secrets()
        for p in ('linkedin','twitter','facebook','whatsapp'):
            ok, msg = post(p, 'Test message')
            if ok:
                st.success(f'{p.title()}: OK — {msg}')
            else:
                st.warning(f'{p.title()}: {msg}')

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
    f"""
    "🌿 Built for impact. Powered by discipline. | Deric Marangu"
    """,
    unsafe_allow_html=True
)
