# ============================================================================
# DERIC CONSISTENCY PLAN - MAIN SYSTEM
# A modular discipline and outreach automation engine
# Author: Built for Deric Marangu
# Color Theme: #2e7d32 (Material Green 800)
# ============================================================================

import os
import json
import sqlite3
from datetime import datetime, time
from pathlib import Path
import hashlib

# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class Config:
    """Manages system configuration and branding"""
    
    DEFAULT_CONFIG = {
        "name": "Deric Marangu",
        "phone": "+254791360805",
        "email": "dericmarangu@gmail.com",
        "links": {
            "DericBI": "https://dericBi.netlify.app",
            "Tujengane": "https://tujengane.netlify.app"
        },
        "branding": {
            "tone": "empowering",
            "style": "minimal",
            "primary_color": "#2e7d32",
            "language": "English"
        },
        "si_time": "13:00"
    }
    
    DEFAULT_TASKS = [
        "Post outreach message",
        "DM 10 leads",
        "Offer audit to SMEs",
        "Update WhatsApp group",
        "Post recap with proof"
    ]
    
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.config_file = self.base_path / "config.json"
        self.tasks_file = self.base_path / "tasks.json"
        self._ensure_files()
    
    def _ensure_files(self):
        """Create default config files if they don't exist"""
        if not self.config_file.exists():
            with open(self.config_file, 'w') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
        
        if not self.tasks_file.exists():
            with open(self.tasks_file, 'w') as f:
                json.dump(self.DEFAULT_TASKS, f, indent=2)
    
    def load_config(self):
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def load_tasks(self):
        with open(self.tasks_file, 'r') as f:
            return json.load(f)

# ============================================================================
# DATABASE MANAGER
# ============================================================================

class Database:
    """Manages SQLite database for tracking tasks, posts, and schedules"""
    
    def __init__(self, db_path="tracker.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize()
    
    def _initialize(self):
        """Create database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Task logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                enhanced_post TEXT,
                intent TEXT,
                image_path TEXT
            )
        """)
        
        # Schedule table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                description TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Daily progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                tasks_completed INTEGER DEFAULT 0,
                posts_generated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'in_progress'
            )
        """)
        
        self.conn.commit()
    
    def log_task(self, task, enhanced_post=None, intent=None, image_path=None):
        """Log a completed task"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO logs (task, timestamp, enhanced_post, intent, image_path)
            VALUES (?, ?, ?, ?, ?)
        """, (task, timestamp, enhanced_post, intent, image_path))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_today_progress(self):
        """Get today's task completion status"""
        today = datetime.now().date().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_progress WHERE date = ?
        """, (today,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("""
                INSERT INTO daily_progress (date, tasks_completed, posts_generated)
                VALUES (?, 0, 0)
            """, (today,))
            self.conn.commit()
            return {'date': today, 'tasks_completed': 0, 'posts_generated': 0, 'status': 'in_progress'}
        
        return {
            'id': result[0],
            'date': result[1],
            'tasks_completed': result[2],
            'posts_generated': result[3],
            'status': result[4]
        }
    
    def update_daily_progress(self):
        """Increment today's task count"""
        today = datetime.now().date().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE daily_progress 
            SET tasks_completed = tasks_completed + 1
            WHERE date = ?
        """, (today,))
        self.conn.commit()
    
    def add_schedule_item(self, item_type, date, description=""):
        """Add a scheduled item"""
        cursor = self.conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO schedule (type, date, description, created_at)
            VALUES (?, ?, ?, ?)
        """, (item_type, date, description, created_at))
        self.conn.commit()
    
    def get_pending_schedules(self):
        """Get pending scheduled items for today or past"""
        today = datetime.now().date().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM schedule 
            WHERE status = 'pending' AND date <= ?
            ORDER BY date ASC
        """, (today,))
        return cursor.fetchall()
    
    def close(self):
        if self.conn:
            self.conn.close()

# ============================================================================
# IMAGE MANAGER
# ============================================================================

class ImageManager:
    """Manages outreach screenshots and validates their presence"""
    
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.images_dir = self.base_path / "images"
        self.teaching_dir = self.images_dir / "teaching_leads"
        self.analytics_dir = self.images_dir / "analytics_leads"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create image directories if they don't exist"""
        self.teaching_dir.mkdir(parents=True, exist_ok=True)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
    
    def get_image_path(self, day_number, intent):
        """Get the path for a specific day's image based on intent"""
        if intent == "teachingleads":
            directory = self.teaching_dir
        elif intent == "analyticsleads":
            directory = self.analytics_dir
        else:
            raise ValueError(f"Invalid intent: {intent}. Use 'teachingleads' or 'analyticsleads'")
        
        image_path = directory / f"day{day_number}.png"
        return image_path
    
    def validate_image(self, day_number, intent):
        """Check if required image exists"""
        image_path = self.get_image_path(day_number, intent)
        return image_path.exists()
    
    def get_missing_images(self):
        """Return list of missing images"""
        missing = []
        for day in range(1, 8):
            for intent in ["teachingleads", "analyticsleads"]:
                if not self.validate_image(day, intent):
                    missing.append(f"{intent}/day{day}.png")
        return missing
    
    def get_setup_instructions(self):
        """Return instructions for image setup"""
        return f"""
┌────────────────────────────────────────────────┐
│  📸 IMAGE SETUP REQUIRED                       │
└────────────────────────────────────────────────┘

Please add your outreach screenshots to:

📁 {self.teaching_dir}/
   └─ day1.png to day7.png (Teaching leads)

📁 {self.analytics_dir}/
   └─ day1.png to day7.png (Analytics leads)

Missing images: {len(self.get_missing_images())}

The system will block post generation until all 
14 images are uploaded.
"""

# ============================================================================
# OUTREACH POST GENERATOR
# ============================================================================

class OutreachGenerator:
    """Generates platform-specific outreach posts"""
    
    PLATFORMS = ["whatsapp", "linkedin", "facebook", "twitter", "instagram"]
    
    def __init__(self, config):
        self.config = config
    
    def generate_post(self, intent, audience, day_number, image_path):
        """Generate posts for all platforms"""
        posts = {}
        
        base_content = self._create_base_content(intent, audience, day_number)
        
        for platform in self.PLATFORMS:
            posts[platform] = self._format_for_platform(base_content, platform)
        
        return posts
    
    def _create_base_content(self, intent, audience, day_number):
        """Create base content structure"""
        if intent == "teachingleads":
            topic = "Business Intelligence & Data Analytics"
            cta = "Ready to master BI tools and transform your career?"
        else:
            topic = "Dashboard Audit & Analytics Consulting"
            cta = "Need a professional dashboard audit for your business?"
        
        return {
            "topic": topic,
            "cta": cta,
            "day": day_number,
            "audience": audience,
            "name": self.config["name"],
            "phone": self.config["phone"],
            "email": self.config["email"],
            "links": self.config["links"]
        }
    
    def _format_for_platform(self, content, platform):
        """Format content for specific platform"""
        if platform == "whatsapp":
            return self._whatsapp_format(content)
        elif platform == "linkedin":
            return self._linkedin_format(content)
        elif platform == "facebook":
            return self._facebook_format(content)
        elif platform == "twitter":
            return self._twitter_format(content)
        elif platform == "instagram":
            return self._instagram_format(content)
    
    def _whatsapp_format(self, c):
        return f"""✨ Day {c['day']} - {c['topic']}

{c['cta']}

📞 {c['phone']}
📧 {c['email']}
🔗 {c['links']['DericBI']}

#DataAnalytics #BusinessIntelligence #DericBI"""
    
    def _linkedin_format(self, c):
        return f"""Day {c['day']}: {c['topic']}

{c['cta']}

I help {c['audience']} unlock insights from their data and make better decisions.

Let's connect:
📧 {c['email']}
🌐 {c['links']['DericBI']}

#DataAnalytics #BusinessIntelligence #BI #DataVisualization #CareerGrowth"""
    
    def _facebook_format(self, c):
        return f"""🚀 {c['topic']} - Day {c['day']}

{c['cta']}

Reach out today:
📞 {c['phone']}
🌐 {c['links']['DericBI']}

#DataDriven #Analytics #BusinessGrowth"""
    
    def _twitter_format(self, c):
        return f"""Day {c['day']}: {c['topic']}

{c['cta']}

DM me or visit: {c['links']['DericBI']}

#DataAnalytics #BI"""
    
    def _instagram_format(self, c):
        return f"""✨ Day {c['day']} ✨

{c['topic']}

{c['cta']}

Link in bio or DM me!

#DataAnalytics #BusinessIntelligence #DericBI #DataScience #TechCareer"""

# ============================================================================
# AI API ENHANCER (Placeholder for integration)
# ============================================================================

class AIEnhancer:
    """Enhances posts using AI API (integrate with OpenAI, Cohere, etc.)"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def enhance_post(self, post_text, platform):
        """
        Placeholder for AI enhancement
        In production: Call OpenAI/Cohere/HuggingFace API
        """
        # For now, return with basic enhancements
        enhanced = f"{post_text}\n\n[AI Enhanced - Ready for {platform}]"
        return enhanced
    
    def add_hashtags(self, post_text, count=5):
        """Add relevant hashtags"""
        # Placeholder - AI would generate contextual hashtags
        return post_text
    
    def translate(self, post_text, target_language):
        """Translate post to target language"""
        # Placeholder for translation API
        return post_text

# ============================================================================
# SCHEDULER
# ============================================================================

class Scheduler:
    """Manages scheduled classes, audits, and campaigns"""
    
    def __init__(self, database):
        self.db = database
    
    def add_class(self, date, description):
        """Schedule a class"""
        self.db.add_schedule_item("class", date, description)
    
    def add_audit(self, date, description):
        """Schedule an audit"""
        self.db.add_schedule_item("audit", date, description)
    
    def add_campaign(self, date, description):
        """Schedule an outreach campaign"""
        self.db.add_schedule_item("post", date, description)
    
    def get_today_schedule(self):
        """Get today's scheduled items"""
        return self.db.get_pending_schedules()
    
    def check_and_notify(self):
        """Check for pending scheduled items"""
        pending = self.get_today_schedule()
        if pending:
            print("\n⏰ SCHEDULED ITEMS DUE:\n")
            for item in pending:
                print(f"  [{item[1]}] {item[2]} - {item[4]}")
            print()

# ============================================================================
# CORE ENGINE
# ============================================================================

class ConsistencyEngine:
    """Main engine that enforces discipline and task flow"""
    
    def __init__(self):
        self.config_manager = Config()
        self.config = self.config_manager.load_config()
        self.tasks = self.config_manager.load_tasks()
        self.db = Database()
        self.image_manager = ImageManager()
        self.outreach_gen = OutreachGenerator(self.config)
        
        # UPDATED: Load AI integration with config
        try:
            from ai_integration import AIIntegration
            
            api_config = self.config.get("ai_api", {})
            api_key = api_config.get("api_key") or None
            provider = api_config.get("provider", "cohere")
            model = api_config.get("model", "command")
            
            self.ai_enhancer = AIIntegration(provider=provider, api_key=api_key, model=model)
            
            if self.ai_enhancer.enabled:
                print(f"✅ AI Enhancement Active: {provider.upper()}")
            else:
                print("⚠️  AI Enhancement Disabled: Using basic mode")
        except ImportError:
            # Fallback if ai_integration.py not present
            self.ai_enhancer = AIEnhancer()
            print("⚠️  Using basic AI enhancer (ai_integration.py not found)")
        
        self.scheduler = Scheduler(self.db)
    
    def check_si_time(self):
        """Check if it's the scheduled execution time (13:00 EAT)"""
        now = datetime.now().time()
        si_time = time.fromisoformat(self.config["si_time"])
        return now.hour == si_time.hour and now.minute == si_time.minute
    
    def run_daily_flow(self):
        """Execute the daily task flow"""
        self._print_header()
        
        # Check for missing images
        missing_images = self.image_manager.get_missing_images()
        if missing_images:
            print(self.image_manager.get_setup_instructions())
            return
        
        # Check scheduled items
        self.scheduler.check_and_notify()
        
        # Get today's progress
        progress = self.db.get_today_progress()
        current_task_index = progress['tasks_completed']
        
        if current_task_index >= len(self.tasks):
            print("✅ All tasks completed for today!\n")
            self._print_summary()
            return
        
        # Execute current task
        current_task = self.tasks[current_task_index]
        print(f"\n📋 Current Task: {current_task}\n")
        
        if "Post outreach message" in current_task:
            self._execute_outreach_task()
        else:
            self._execute_standard_task(current_task)
        
        # Update progress
        self.db.update_daily_progress()
        
        print(f"\n✓ Task completed: {current_task}")
        print(f"📊 Progress: {current_task_index + 1}/{len(self.tasks)} tasks\n")
    
    def _execute_outreach_task(self):
        """Generate and log outreach posts with AI enhancement"""
        day_number = (datetime.now().timetuple().tm_yday % 7) + 1
        
        print("Select intent:")
        print("  1. Teaching Leads")
        print("  2. Analytics Leads")
        choice = input("\nEnter choice (1-2): ").strip()
        
        intent = "teachingleads" if choice == "1" else "analyticsleads"
        audience = "learners" if choice == "1" else "SMEs"
        
        # Validate image
        if not self.image_manager.validate_image(day_number, intent):
            print(f"\n❌ Missing image: {intent}/day{day_number}.png")
            return
        
        image_path = self.image_manager.get_image_path(day_number, intent)
        
        # Generate posts
        print("\n⏳ Generating posts for all platforms...\n")
        posts = self.outreach_gen.generate_post(intent, audience, day_number, image_path)
        
        print("📱 GENERATED POSTS:\n")
        print("="*60)
        
        for platform, post in posts.items():
            print(f"\n━━━ {platform.upper()} ━━━")
            print(post)
        
        print("\n" + "="*60)
        
        # Ask which platform to enhance
        print("\n🤖 AI Enhancement Available")
        print("Select platform to enhance:")
        platforms_list = list(posts.keys())
        for i, platform in enumerate(platforms_list, 1):
            print(f"  {i}. {platform.title()}")
        print(f"  {len(platforms_list) + 1}. Skip AI enhancement")
        
        enhance_choice = input(f"\nEnter choice (1-{len(platforms_list) + 1}): ").strip()
        
        enhanced = None
        selected_platform = None
        
        try:
            choice_num = int(enhance_choice)
            if 1 <= choice_num <= len(platforms_list):
                selected_platform = platforms_list[choice_num - 1]
                
                print(f"\n⏳ Enhancing {selected_platform} post with AI...\n")
                
                # Enhance with AI
                tone = self.config['branding']['tone']
                enhanced = self.ai_enhancer.enhance_post(
                    posts[selected_platform], 
                    selected_platform, 
                    tone=tone
                )
                
                print("✨ AI-ENHANCED VERSION:\n")
                print("="*60)
                print(enhanced)
                print("="*60)
                
                # Ask if they want to use enhanced version
                use_enhanced = input("\nUse this enhanced version? (y/n): ").strip().lower()
                if use_enhanced != 'y':
                    enhanced = posts[selected_platform]
                    print("Using original version")
            else:
                print("\n✓ Skipping AI enhancement")
                enhanced = posts['linkedin']  # Default to LinkedIn original
                
        except (ValueError, IndexError):
            print("\n⚠️  Invalid choice, using original LinkedIn post")
            enhanced = posts['linkedin']
        
        # Log to database
        self.db.log_task(
            "Post outreach message", 
            enhanced, 
            intent, 
            str(image_path)
        )
        
        print(f"\n✅ Posts generated and logged successfully!")
    
    def _execute_standard_task(self, task):
        """Execute a standard non-outreach task"""
        print(f"\n📝 Task: {task}")
        print("Complete this task, then return here.")
        confirm = input("\nMark as complete? (y/n): ").strip().lower()
        
        if confirm == 'y':
            self.db.log_task(task)
            print("✅ Task logged")
        else:
            print("❌ Task not completed - staying on current task")
    
    def _print_header(self):
        """Print system header with green theme"""
        print("\n" + "="*60)
        print("  🌿 DERIC CONSISTENCY PLAN")
        print("  Your discipline engine for impact and legacy")
        print("  Color Theme: #2e7d32 (Green)")
        print("="*60)
    
    def _print_summary(self):
        """Print daily summary"""
        progress = self.db.get_today_progress()
        print("\n" + "="*60)
        print("📊 DAILY SUMMARY")
        print("="*60)
        print(f"   ✅ Tasks Completed: {progress['tasks_completed']}")
        print(f"   📱 Posts Generated: {progress['posts_generated']}")
        print(f"   🎯 Status: {progress['status']}")
        print("="*60 + "\n")
# ============================================================================
# REPORTER
# ============================================================================

class Reporter:
    """Generates discipline and outreach reports"""
    
    def __init__(self, database):
        self.db = database
    
    def generate_weekly_report(self):
        """Generate weekly performance report"""
        cursor = self.db.conn.cursor()
        
        # Get last 7 days of progress
        cursor.execute("""
            SELECT * FROM daily_progress 
            ORDER BY date DESC 
            LIMIT 7
        """)
        days = cursor.fetchall()
        
        print("\n" + "="*60)
        print("  📈 WEEKLY CONSISTENCY REPORT")
        print("="*60 + "\n")
        
        total_tasks = sum(day[2] for day in days)
        total_posts = sum(day[3] for day in days)
        
        print(f"Total Tasks Completed: {total_tasks}")
        print(f"Total Posts Generated: {total_posts}")
        print(f"Days Tracked: {len(days)}")
        print(f"Average Tasks/Day: {total_tasks/len(days) if days else 0:.1f}")
        print()
    
    def export_to_csv(self, filename="deric_report.csv"):
        """Export logs to CSV"""
        import csv
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
        logs = cursor.fetchall()
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Task', 'Timestamp', 'Enhanced Post', 'Intent', 'Image Path'])
            writer.writerows(logs)
        
        print(f"✅ Report exported to {filename}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point"""
    engine = ConsistencyEngine()
    
    print("\n🌿 DERIC CONSISTENCY PLAN - INITIALIZED")
    print("Choose an option:")
    print("  1. Run Daily Flow")
    print("  2. View Weekly Report")
    print("  3. Check Schedule")
    print("  4. Add Scheduled Item")
    print("  5. Export Report to CSV")
    print("  6. Exit")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        engine.run_daily_flow()
    elif choice == "2":
        reporter = Reporter(engine.db)
        reporter.generate_weekly_report()
    elif choice == "3":
        engine.scheduler.check_and_notify()
    elif choice == "4":
        item_type = input("Type (class/audit/post): ").strip()
        date = input("Date (YYYY-MM-DD): ").strip()
        desc = input("Description: ").strip()
        engine.scheduler.db.add_schedule_item(item_type, date, desc)
        print("✅ Scheduled item added")
    elif choice == "5":
        reporter = Reporter(engine.db)
        reporter.export_to_csv()
    elif choice == "6":
        print("Exiting... Stay consistent! 🌿")
        engine.db.close()
        return
    
    engine.db.close()

if __name__ == "__main__":
    main()