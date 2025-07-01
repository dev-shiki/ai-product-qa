#!/usr/bin/env python3
"""
Demo script untuk menjalankan Smart Contribution Bot secara lokal
Run this from the ai-product-qa directory root
"""

import os
import sys
import time
from pathlib import Path

# Add the scripts directory to the path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from smart_contribution_bot import SmartContributionBot

def demo_smart_bot():
    """Demonstrasi Smart Contribution Bot dengan berbagai fitur"""
    print("🚀 Smart Contribution Bot Demo")
    print("=" * 50)
    
    # Check working directory
    expected_files = ['app', 'tests', 'requirements.txt', '.github']
    current_dir = Path.cwd()
    
    if not all(Path(f).exists() for f in expected_files[:2]):  # Check app and tests
        print("⚠️  Warning: Please run this script from the ai-product-qa directory")
        print(f"   Current directory: {current_dir}")
        print("   Expected to find: app/, tests/, requirements.txt")
        print()
        print("   Try: cd ai-product-qa && python .github/scripts/run_smart_bot.py")
        return False
    
    bot = SmartContributionBot()
    
    # Check if API key is available
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  GEMINI_API_KEY tidak ditemukan!")
        print("   Set environment variable:")
        print("   • Linux/Mac: export GEMINI_API_KEY='your-api-key'")
        print("   • Windows: set GEMINI_API_KEY=your-api-key")
        print("   • PowerShell: $env:GEMINI_API_KEY='your-api-key'")
        return False
    
    print("✅ GEMINI_API_KEY ditemukan")
    print(f"📁 Working directory: {current_dir}")
    
    # Show available contribution types
    print("\n🎯 Available contribution types:")
    for i, contrib_type in enumerate(bot.contribution_types, 1):
        print(f"   {i:2d}. {contrib_type.replace('_', ' ').title()}")
    
    # Show current time period and bias
    time_period = bot.get_time_period()
    biased_types = bot.time_biases.get(time_period, [])
    print(f"\n⏰ Current time period: {time_period.title()}")
    if biased_types:
        print(f"🎯 Time-biased types: {', '.join(t.replace('_', ' ').title() for t in biased_types)}")
    
    # Show Python files in project
    python_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) < 50000:  # Same filter as bot
                        python_files.append(file_path)
                except:
                    pass
    
    print(f"\n📝 Found {len(python_files)} suitable Python files for analysis:")
    for file in python_files[:10]:  # Show first 10
        size = os.path.getsize(file) if os.path.exists(file) else 0
        print(f"   - {file} ({size:,} bytes)")
    if len(python_files) > 10:
        print(f"   ... and {len(python_files) - 10} more files")
    
    # Run the bot
    print("\n🤖 Running Smart Contribution Bot...")
    print("-" * 30)
    
    try:
        success = bot.run_smart_contribution()
        
        if success:
            print("\n🎉 Demo completed successfully!")
            
            # Show generated files
            if Path("ai_improvements").exists():
                improvements = list(Path("ai_improvements").glob("*.md"))
                print(f"\n📄 Generated {len(improvements)} improvement files:")
                for file in sorted(improvements, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    mtime = time.strftime('%H:%M:%S', time.localtime(file.stat().st_mtime))
                    print(f"   - {file.name} (created at {mtime})")
            
            # Show activity log
            if Path("smart_bot_activity.json").exists():
                import json
                with open("smart_bot_activity.json", 'r') as f:
                    activity = json.load(f)
                print(f"\n📊 Total contributions so far: {activity['total_contributions']}")
                print(f"📅 Last run: {activity['last_run'][:19].replace('T', ' ')}")
                
                # Show today's count
                today = time.strftime("%Y-%m-%d")
                today_count = sum(1 for a in activity.get('activities', []) 
                                if a['timestamp'].startswith(today))
                print(f"🎯 Today's contributions: {today_count}/50")
        else:
            print("\n❌ Demo failed")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def show_activity_stats():
    """Show smart bot activity statistics"""
    if not Path("smart_bot_activity.json").exists():
        print("No activity data found. Run the bot first!")
        return
    
    import json
    with open("smart_bot_activity.json", 'r') as f:
        activity = json.load(f)
    
    print("📊 Smart Bot Activity Statistics")
    print("=" * 40)
    print(f"Total Contributions: {activity['total_contributions']}")
    print(f"First Run: {activity['first_run'][:19].replace('T', ' ')}")
    print(f"Last Run: {activity['last_run'][:19].replace('T', ' ')}")
    
    print("\n📈 Contribution Types:")
    for contrib_type, count in activity.get('contribution_types', {}).items():
        print(f"   {contrib_type.replace('_', ' ').title()}: {count}")
    
    # Show hourly distribution
    if 'hourly_stats' in activity:
        print("\n🕐 Hourly Distribution (last 24 hours):")
        from datetime import datetime, timedelta
        now = datetime.now()
        for hour in range(24):
            check_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_key = check_time.strftime("%Y-%m-%d_%H")
            count = activity['hourly_stats'].get(hour_key, 0)
            if count > 0:
                print(f"   {hour:02d}:00 - {count} contributions")
    
    print(f"\n📋 Recent Activities ({len(activity['activities'])} total):")
    for activity_item in activity['activities'][-10:]:
        timestamp = activity_item['timestamp'][:19].replace('T', ' ')
        hour = activity_item.get('hour', 'N/A')
        print(f"   {timestamp} ({hour:02d}h) - {activity_item['type'].replace('_', ' ').title()}")

def show_improvements():
    """Show generated AI improvements"""
    improvements_dir = Path("ai_improvements")
    if not improvements_dir.exists():
        print("No improvements directory found. Run the bot first!")
        return
    
    improvements = list(improvements_dir.glob("*.md"))
    if not improvements:
        print("No improvement files found.")
        return
    
    print(f"📁 Found {len(improvements)} AI Improvement Files")
    print("=" * 45)
    
    # Group by type
    by_type = {}
    for file in improvements:
        type_name = file.name.split('_')[0]
        by_type.setdefault(type_name, []).append(file)
    
    print("\n📊 By Type:")
    for type_name, files in sorted(by_type.items()):
        print(f"   {type_name.replace('_', ' ').title()}: {len(files)} files")
    
    print(f"\n📄 Latest Files:")
    for file in sorted(improvements, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        # Get file info
        stat = file.stat()
        size = stat.st_size
        modified = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
        
        print(f"\n📄 {file.name}")
        print(f"   Size: {size} bytes | Modified: {modified}")
        
        # Show first few lines
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:2]:
                    if line.strip() and line.startswith('#'):
                        print(f"   {line.strip()}")
                        break
        except:
            pass

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "run":
            demo_smart_bot()
        elif command == "stats":
            show_activity_stats()
        elif command == "improvements":
            show_improvements()
        elif command == "help":
            print("Smart Contribution Bot Demo Commands:")
            print()
            print("Usage: python .github/scripts/run_smart_bot.py [command]")
            print()
            print("Commands:")
            print("  run          - Run the smart bot demo")
            print("  stats        - Show detailed activity statistics")
            print("  improvements - Show generated AI improvements")
            print("  help         - Show this help message")
            print()
            print("Note: Run this script from the ai-product-qa directory root")
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' to see available commands")
    else:
        # Interactive mode
        print("🤖 Smart Contribution Bot Demo")
        print("Choose an option:")
        print("1. Run smart bot")
        print("2. Show statistics")
        print("3. Show improvements")
        print("4. Help")
        print("5. Exit")
        
        while True:
            try:
                choice = input("\nEnter choice (1-5): ").strip()
                
                if choice == "1":
                    demo_smart_bot()
                    break
                elif choice == "2":
                    show_activity_stats()
                    break
                elif choice == "3":
                    show_improvements()
                    break
                elif choice == "4":
                    main()  # Show help
                    break
                elif choice == "5":
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please enter 1-5.")
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break

if __name__ == "__main__":
    main() 