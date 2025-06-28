#!/usr/bin/env python3
"""
Test script untuk simulate auto workflow secara lokal
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🧪 Testing Auto Workflow Locally")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app").exists() or not Path(".github/scripts").exists():
        print("❌ Error: Please run this from the ai-product-qa root directory")
        sys.exit(1)
    
    # Test 1: Coverage Analysis
    print("\n1️⃣ Testing Coverage Analysis...")
    try:
        result = subprocess.run(
            ["python", ".github/scripts/coverage_analyzer.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Coverage analysis completed successfully")
            if Path("coverage_report.json").exists():
                print("📄 coverage_report.json created")
        else:
            print(f"⚠️ Coverage analysis failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Coverage analysis error: {e}")
    
    # Test 2: Test Generation (if API key available)
    print("\n2️⃣ Testing Test Generation...")
    if os.getenv("GEMINI_API_KEY"):
        try:
            result = subprocess.run(
                ["python", ".github/scripts/test_generator.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Test generation completed successfully")
                if Path("test_generation_results.json").exists():
                    print("📄 test_generation_results.json created")
            else:
                print(f"⚠️ Test generation failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Test generation error: {e}")
    else:
        print("⏭️ Skipping test generation (no GEMINI_API_KEY)")
    
    # Test 3: Contribution Bot
    print("\n3️⃣ Testing Contribution Bot...")
    try:
        # Get current git user
        email_result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True
        )
        
        name_result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True
        )
        
        if email_result.returncode == 0 and name_result.returncode == 0:
            user_email = email_result.stdout.strip()
            user_name = name_result.stdout.strip()
            
            print(f"📧 Using git config: {user_name} <{user_email}>")
            
            result = subprocess.run(
                ["python", ".github/scripts/contribution_bot.py", user_email, user_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Contribution bot completed successfully")
                if Path("bot_activity.json").exists():
                    print("📄 bot_activity.json created/updated")
            else:
                print(f"⚠️ Contribution bot failed: {result.stderr}")
        else:
            print("❌ No git user configured. Run:")
            print("   git config user.name 'Your Name'")
            print("   git config user.email 'your-email@example.com'")
    except Exception as e:
        print(f"❌ Contribution bot error: {e}")
    
    # Test 4: Check for changes
    print("\n4️⃣ Checking for Changes...")
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("📝 Changes detected:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
            
            # Ask if user wants to commit
            response = input("\n❓ Commit these changes? (y/N): ").lower()
            if response == 'y':
                subprocess.run(["git", "add", "-A"])
                subprocess.run(["git", "commit", "-m", "🧪 Test run: Auto workflow simulation"])
                print("✅ Changes committed")
        else:
            print("ℹ️ No changes detected")
    except Exception as e:
        print(f"❌ Git status error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\n💡 To enable automatic runs:")
    print("   1. Add GEMINI_API_KEY to GitHub secrets")
    print("   2. Workflow runs every 30 minutes automatically")
    print("   3. Check GitHub Actions tab for results")

if __name__ == "__main__":
    main() 