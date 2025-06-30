#!/usr/bin/env python3
"""
Contribution Bot - Script untuk membuat commits yang terhitung sebagai GitHub contributions
"""

import subprocess
import sys
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

class ContributionBot:
    def __init__(self):
        self.activity_file = Path("bot_activity.json")
        self.readme_file = Path("README.md")
        
    def setup_git_with_user_email(self, user_email: str, user_name: str = None):
        """Setup git dengan email user yang sebenarnya"""
        try:
            if not user_name:
                user_name = user_email.split("@")[0]
            
            subprocess.run(["git", "config", "user.name", user_name], check=True)
            subprocess.run(["git", "config", "user.email", user_email], check=True)
            
            print(f"Git configured:")
            print(f"   Name: {user_name}")
            print(f"   Email: {user_email}")
            
            return True
        except Exception as e:
            print(f"Error setting up git: {e}")
            return False
    
    def update_activity_log(self):
        """Update activity log dengan timestamp dan stats"""
        try:
            # Load existing activity or create new
            if self.activity_file.exists():
                with open(self.activity_file, 'r', encoding='utf-8') as f:
                    activity = json.load(f)
            else:
                activity = {
                    "first_run": datetime.now().isoformat(),
                    "total_commits": 0,
                    "activities": []
                }
            
            # Add new activity
            new_activity = {
                "timestamp": datetime.now().isoformat(),
                "action": "automated_test_generation",
                "description": f"Bot generated tests and updated coverage",
                "commit_count": activity["total_commits"] + 1
            }
            
            activity["activities"].append(new_activity)
            activity["total_commits"] += 1
            activity["last_run"] = datetime.now().isoformat()
            
            # Keep only last 100 activities
            if len(activity["activities"]) > 100:
                activity["activities"] = activity["activities"][-100:]
            
            # Save updated activity
            with open(self.activity_file, 'w', encoding='utf-8') as f:
                json.dump(activity, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error updating activity log: {e}")
            return False
    
    def update_readme_stats(self):
        """Update README dengan bot stats"""
        try:
            if not self.activity_file.exists():
                return False
            
            with open(self.activity_file, 'r', encoding='utf-8') as f:
                activity = json.load(f)
            
            # Create/update stats section in README
            stats_section = f"""
## Bot Activity Stats

- **Total Auto-Commits**: {activity["total_commits"]}
- **Last Activity**: {activity["last_run"][:19].replace('T', ' ')}
- **Bot Started**: {activity["first_run"][:19].replace('T', ' ')}

*This repository uses automated test generation to continuously improve code coverage.*
"""
            
            # Read existing README or create new
            if self.readme_file.exists():
                try:
                    with open(self.readme_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Try different encodings
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                    content = ""
                    for encoding in encodings:
                        try:
                            with open(self.readme_file, 'r', encoding=encoding) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                
                # Replace existing stats section or append
                if "## Bot Activity Stats" in content:
                    # Find and replace existing section
                    lines = content.split('\n')
                    start_idx = None
                    end_idx = None
                    
                    for i, line in enumerate(lines):
                        if "## Bot Activity Stats" in line:
                            start_idx = i
                        elif start_idx is not None and line.startswith("## ") and i > start_idx:
                            end_idx = i
                            break
                    
                    if start_idx is not None:
                        if end_idx is not None:
                            # Replace section
                            new_lines = lines[:start_idx] + stats_section.strip().split('\n') + lines[end_idx:]
                        else:
                            # Replace to end
                            new_lines = lines[:start_idx] + stats_section.strip().split('\n')
                        
                        content = '\n'.join(new_lines)
                    else:
                        # Append at end
                        content += "\n" + stats_section
                else:
                    # Append stats section
                    content += "\n" + stats_section
            else:
                # Create new README
                content = f"""# AI Product QA

Auto-generated test coverage improvement system.
{stats_section}
"""
            
            # Write updated README with UTF-8 encoding
            with open(self.readme_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error updating README: {e}")
            return False
    
    def create_meaningful_commit(self):
        """Create a meaningful commit dengan actual changes"""
        try:
            # Update activity log
            if not self.update_activity_log():
                return False
            
            # Skip README update (disabled to keep it private)
            # if not self.update_readme_stats():
            #     return False
            
            # Stage files (only bot_activity.json, not README)
            subprocess.run(["git", "add", str(self.activity_file)], check=True)
            
            # Create commit message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            commit_msg = f"Auto-update: Test coverage improvement - {timestamp}"
            
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            print(f"Committed: {commit_msg}")
            
            # Push to remote
            subprocess.run(["git", "push"], check=True)
            print("Pushed to remote successfully!")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            return False
        except Exception as e:
            print(f"Error creating commit: {e}")
            return False
    
    def run_with_user_config(self, email: str, name: str = None):
        """Run bot dengan konfigurasi user yang benar"""
        print("GitHub Contribution Bot Starting...")
        print(f"Using email: {email}")
        
        # Setup git
        if not self.setup_git_with_user_email(email, name):
            return False
        
        # Create meaningful commit
        if not self.create_meaningful_commit():
            return False
        
        print("\nSuccess! Contribution created.")
        print("Tips untuk contributions:")
        print("   1. Gunakan email yang sama dengan GitHub account")
        print("   2. Pastikan di default branch (main/master)")
        print("   3. Repository harus public atau anda collaborator")
        print("   4. Contributions mungkin butuh beberapa jam untuk muncul")
        
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python contribution_bot.py <your-github-email> [your-name]")
        print("Example: python contribution_bot.py user@example.com 'Your Name'")
        sys.exit(1)
    
    email = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    
    bot = ContributionBot()
    success = bot.run_with_user_config(email, name)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 