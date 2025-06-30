#!/usr/bin/env python3
"""
Demo script untuk menjalankan Smart Contribution Bot secara lokal
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
    
    bot = SmartContributionBot()
    
    # Check if API key is available
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  GEMINI_API_KEY tidak ditemukan!")
        print("   Set environment variable: export GEMINI_API_KEY='your-api-key'")
        print("   Atau jalankan: set GEMINI_API_KEY=your-api-key (Windows)")
        return False
    
    print("✅ GEMINI_API_KEY ditemukan")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Show available contribution types
    print("\n🎯 Available contribution types:")
    for i, contrib_type in enumerate(bot.contribution_types, 1):
        print(f"   {i:2d}. {contrib_type.replace('_', ' ').title()}")
    
    # Show Python files in project
    python_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                python_files.append(os.path.join(root, file))
    
    print(f"\n📝 Found {len(python_files)} Python files for analysis:")
    for file in python_files[:10]:  # Show first 10
        print(f"   - {file}")
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
                for file in improvements[-5:]:  # Show last 5
                    print(f"   - {file}")
            
            # Show activity log
            if Path("smart_bot_activity.json").exists():
                import json
                with open("smart_bot_activity.json", 'r') as f:
                    activity = json.load(f)
                print(f"\n📊 Total contributions so far: {activity['total_contributions']}")
                print(f"📅 Last run: {activity['last_run']}")
        else:
            print("\n❌ Demo failed")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
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
    
    print(f"\n📋 Recent Activities ({len(activity['activities'])} total):")
    for activity_item in activity['activities'][-5:]:
        timestamp = activity_item['timestamp'][:19].replace('T', ' ')
        print(f"   {timestamp} - {activity_item['description']}")

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
    
    for file in sorted(improvements, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        # Get file info
        stat = file.stat()
        size = stat.st_size
        modified = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
        
        print(f"📄 {file.name}")
        print(f"   Size: {size} bytes | Modified: {modified}")
        
        # Show first few lines
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:3]:
                    if line.strip():
                        print(f"   {line.strip()}")
                        break
        except:
            pass
        print()

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
            print("  python run_smart_bot.py run         - Run the smart bot")
            print("  python run_smart_bot.py stats       - Show activity statistics")
            print("  python run_smart_bot.py improvements - Show generated improvements")
            print("  python run_smart_bot.py help        - Show this help")
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
        print("4. Exit")
        
        while True:
            try:
                choice = input("\nEnter choice (1-4): ").strip()
                
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
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please enter 1-4.")
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break

if __name__ == "__main__":
    main() 