import os
import sys
from pathlib import Path

def setup_cron_job():
    """Set up cron job for automatic daily execution"""
    
    script_dir = Path(__file__).parent.absolute()
    python_path = sys.executable
    core_script = script_dir / "core.py"
    
    # Cron job entry for 13:00 EAT (10:00 UTC, adjust for your timezone)
    cron_entry = f"0 10 * * * {python_path} {core_script} >> {script_dir}/cron.log 2>&1"
    
    print("\n🕐 Setting up automatic daily execution...")
    print(f"   Time: 13:00 EAT (10:00 UTC)")
    print(f"   Script: {core_script}")
    print(f"\nAdd this line to your crontab:\n")
    print(f"   {cron_entry}\n")
    
    response = input("Would you like to add this automatically? (y/n): ").strip().lower()
    
    if response == 'y':
        os.system(f'(crontab -l 2>/dev/null; echo "{cron_entry}") | crontab -')
        print("✅ Cron job added successfully!")
        print("   The system will now run automatically at 13:00 EAT daily.")
    else:
        print("\nManual setup:")
        print("1. Run: crontab -e")
        print(f"2. Add: {cron_entry}")
        print("3. Save and exit")

def create_systemd_service():
    """Alternative: Create systemd service for Linux"""
    
    service_content = """[Unit]
Description=Deric Consistency Plan Daily Execution
After=network.target

[Service]
Type=oneshot
User={user}
WorkingDirectory={workdir}
ExecStart={python} {script}

[Install]
WantedBy=multi-user.target
"""
    
    timer_content = """[Unit]
Description=Deric Consistency Plan Timer
Requires=deric-consistency.service

[Timer]
OnCalendar=*-*-* 10:00:00
Persistent=true

[Install]
WantedBy=timers.target
"""
    
    script_dir = Path(__file__).parent.absolute()
    user = os.getenv("USER")
    
    service_file = f"/etc/systemd/system/deric-consistency.service"
    timer_file = f"/etc/systemd/system/deric-consistency.timer"
    
    print("\n🔧 Systemd Service Setup (Linux only)\n")
    print("Service file content:")
    print(service_content.format(
        user=user,
        workdir=script_dir,
        python=sys.executable,
        script=script_dir / "core.py"
    ))
    print("\nTo install:")
    print(f"1. sudo nano {service_file}")
    print("2. Paste the service content")
    print(f"3. sudo nano {timer_file}")
    print("4. Paste the timer content")
    print("5. sudo systemctl enable deric-consistency.timer")
    print("6. sudo systemctl start deric-consistency.timer")

if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════")
    print("  🌿 DERIC CONSISTENCY PLAN - AUTO SCHEDULER")
    print("═══════════════════════════════════════════════════════\n")
    
    print("Choose setup method:")
    print("  1. Cron job (macOS, Linux)")
    print("  2. Systemd service (Linux only)")
    print("  3. Task Scheduler (Windows - manual instructions)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        setup_cron_job()
    elif choice == "2":
        create_systemd_service()
    elif choice == "3":
        print("\nWindows Task Scheduler Setup:")
        print("1. Open Task Scheduler")
        print("2. Create Basic Task")
        print("3. Set trigger: Daily at 13:00")
        print(f"4. Action: Start Program")
        print(f"5. Program: {sys.executable}")
        print(f"6. Arguments: {Path(__file__).parent / 'core.py'}")
        print("7. Finish")
    else:
        print("Invalid choice")