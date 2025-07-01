#!/usr/bin/env python3
"""
Smart Contribution Bot - AI-powered bot untuk membuat berbagai jenis contributions
Optimized for high-frequency runs (target: 50 per day)
"""

import subprocess
import sys
import os
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import google.generativeai as genai

class SmartContributionBot:
    def __init__(self):
        self.activity_file = Path("smart_bot_activity.json")
        self.contribution_types = [
            "code_optimization",
            "documentation_improvement", 
            "code_comments",
            "refactoring_suggestions",
            "performance_analysis",
            "security_review",
            "type_hints_addition",
            "error_handling_improvement",
            "logging_enhancement",
            "configuration_update"
        ]
        
        # Time-based biases for natural patterns
        self.time_biases = {
            "night": ["security_review", "error_handling_improvement", "logging_enhancement"],
            "morning": ["documentation_improvement", "code_optimization", "type_hints_addition"],
            "afternoon": ["refactoring_suggestions", "performance_analysis", "code_comments"],
            "evening": ["project_analysis", "configuration_update", "code_optimization"]
        }
        
    def get_time_period(self):
        """Get current time period for bias selection"""
        hour = datetime.now().hour
        if 0 <= hour < 6:
            return "night"
        elif 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        else:
            return "evening"
    
    def select_contribution_type(self):
        """Select contribution type with time-based bias"""
        # Check for environment variable biases
        time_period = self.get_time_period()
        bias_key = f"{time_period.upper()}_BIAS"
        
        if bias_key in os.environ:
            biased_types = os.environ[bias_key].split(',')
            # 70% chance to use biased type, 30% random
            if random.random() < 0.7:
                return random.choice(biased_types)
        
        # Use time-based bias from class
        if time_period in self.time_biases and random.random() < 0.6:
            return random.choice(self.time_biases[time_period])
        
        # Random selection
        return random.choice(self.contribution_types)
        
    def setup_gemini_api(self):
        """Setup Gemini AI API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set")
            return False
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return True
        except Exception as e:
            print(f"Error setting up Gemini API: {e}")
            return False
    
    def get_random_python_file(self):
        """Get random Python file from the project"""
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'node_modules']]
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    # Skip very large files for faster processing
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) < 50000:  # Skip files > 50KB
                            python_files.append(file_path)
                    except:
                        pass
        
        return random.choice(python_files) if python_files else None
    
    def analyze_code_with_ai(self, file_path, contribution_type):
        """Analyze code and generate improvements using AI - optimized for speed"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Limit code size for faster processing
            if len(code_content) > 3000:
                lines = code_content.split('\n')
                # Take first 50 lines for analysis
                code_content = '\n'.join(lines[:50]) + '\n... (truncated for analysis)'
            
            # Shorter, more focused prompts for faster response
            short_prompts = {
                "code_optimization": f"Suggest ONE quick optimization for this Python code:\n\n{code_content}\n\nProvide a brief improvement with explanation.",
                
                "documentation_improvement": f"Add a docstring to ONE function in this code:\n\n{code_content}\n\nReturn the function with improved docstring.",
                
                "code_comments": f"Add helpful comments to ONE section:\n\n{code_content}\n\nReturn the code with explanatory comments.",
                
                "type_hints_addition": f"Add type hints to ONE function:\n\n{code_content}\n\nReturn the function with type hints.",
                
                "error_handling_improvement": f"Improve error handling in ONE part:\n\n{code_content}\n\nReturn improved code with better error handling.",
                
                "logging_enhancement": f"Add logging to ONE function:\n\n{code_content}\n\nReturn the function with logging statements.",
                
                "refactoring_suggestions": f"Suggest ONE refactoring improvement:\n\n{code_content}\n\nReturn refactored code with explanation.",
                
                "performance_analysis": f"Suggest ONE performance improvement:\n\n{code_content}\n\nReturn optimized code with justification.",
                
                "security_review": f"Suggest ONE security improvement:\n\n{code_content}\n\nReturn secured code with explanation.",
                
                "configuration_update": f"Extract ONE configuration value:\n\n{code_content}\n\nReturn improved code with extracted config."
            }
            
            prompt = short_prompts.get(contribution_type, short_prompts["code_optimization"])
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error analyzing code with AI: {e}")
            return None
    
    def create_improvement_file(self, file_path, improvement, contribution_type):
        """Create a file with AI-generated improvement"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        improvement_dir = Path("ai_improvements")
        improvement_dir.mkdir(exist_ok=True)
        
        improvement_file = improvement_dir / f"{contribution_type}_{timestamp}.md"
        
        # Shorter, more concise format for high-frequency runs
        content = f"""# {contribution_type.replace('_', ' ').title()}

**File**: `{file_path}`  
**Time**: {datetime.now().strftime('%H:%M:%S')}  
**Type**: {contribution_type}

## Improvement

{improvement}

---
*Generated by Smart AI Bot*
"""
        
        with open(improvement_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return improvement_file
    
    def create_quick_project_analysis(self):
        """Create a quick project analysis for high-frequency runs"""
        try:
            # Quick stats collection
            stats = {"python_files": 0, "total_lines": 0, "test_files": 0}
            
            # Sample only a few files for quick analysis
            sample_files = []
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
                for file in files:
                    if file.endswith('.py'):
                        stats["python_files"] += 1
                        if 'test' in file.lower():
                            stats["test_files"] += 1
                        if len(sample_files) < 3:  # Sample only 3 files
                            sample_files.append(os.path.join(root, file))
            
            # Quick AI analysis with shorter prompt
            prompt = f"""Quick analysis of Python project:
- {stats["python_files"]} Python files
- {stats["test_files"]} test files

Sample files: {', '.join(sample_files)}

Give 2 quick improvement suggestions in 100 words or less."""
            
            analysis = self.model.generate_content(prompt)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = Path("ai_improvements") / f"quick_analysis_{timestamp}.md"
            analysis_file.parent.mkdir(exist_ok=True)
            
            content = f"""# Quick Project Analysis

**Time**: {datetime.now().strftime('%H:%M:%S')}  
**Files**: {stats["python_files"]} Python, {stats["test_files"]} Tests

## Quick Insights

{analysis.text}

---
*Quick analysis by Smart AI Bot*
"""
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return analysis_file
            
        except Exception as e:
            print(f"Error creating quick analysis: {e}")
            return None
    
    def update_activity_log(self, contribution_type, file_created):
        """Update activity log with hourly stats for tracking"""
        try:
            if self.activity_file.exists():
                with open(self.activity_file, 'r', encoding='utf-8') as f:
                    activity = json.load(f)
            else:
                activity = {
                    "first_run": datetime.now().isoformat(),
                    "total_contributions": 0,
                    "contribution_types": {},
                    "hourly_stats": {},
                    "activities": []
                }
            
            # Update counters
            activity["total_contributions"] += 1
            activity["contribution_types"][contribution_type] = activity["contribution_types"].get(contribution_type, 0) + 1
            activity["last_run"] = datetime.now().isoformat()
            
            # Track hourly distribution for high-frequency monitoring
            hour_key = datetime.now().strftime("%Y-%m-%d_%H")
            activity["hourly_stats"][hour_key] = activity["hourly_stats"].get(hour_key, 0) + 1
            
            # Add new activity
            new_activity = {
                "timestamp": datetime.now().isoformat(),
                "type": contribution_type,
                "file_created": str(file_created).replace('\\', '/'),  # Normalize path
                "hour": datetime.now().hour
            }
            
            activity["activities"].append(new_activity)
            
            # Keep only last 100 activities for performance
            if len(activity["activities"]) > 100:
                activity["activities"] = activity["activities"][-100:]
            
            # Clean old hourly stats (keep only last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            activity["hourly_stats"] = {
                k: v for k, v in activity["hourly_stats"].items() 
                if datetime.strptime(k.split('_')[0], "%Y-%m-%d") > week_ago
            }
            
            with open(self.activity_file, 'w', encoding='utf-8') as f:
                json.dump(activity, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error updating activity log: {e}")
            return False
    
    def commit_improvements(self, files_to_commit, contribution_type):
        """Commit the generated improvements - workflow will handle push"""
        try:
            # Stage files
            for file_path in files_to_commit:
                subprocess.run(["git", "add", str(file_path)], check=True)
            
            # Check if there are any changes to commit
            result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
            if result.returncode == 0:
                print("No changes to commit")
                return True
            
            # Shorter commit messages for high-frequency runs
            hour = datetime.now().hour
            time_emoji = "🌙" if 0 <= hour < 6 else "🌅" if 6 <= hour < 12 else "☀️" if 12 <= hour < 18 else "🌆"
            
            commit_msg = f"{time_emoji} AI: {contribution_type.replace('_', ' ').title()} - {datetime.now().strftime('%H:%M')}"
            
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            print(f"Committed: {commit_msg}")
            
            # Don't push here - let the workflow handle it with retry logic
            print("Commit successful, workflow will handle push")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            return False
        except Exception as e:
            print(f"Error committing improvements: {e}")
            return False
    
    def run_smart_contribution(self):
        """Run one cycle of smart contribution - optimized for high frequency"""
        print(f"🤖 Smart Bot - {datetime.now().strftime('%H:%M:%S')}")
        
        # Setup AI
        if not self.setup_gemini_api():
            return False
        
        # Select contribution type with time bias
        contribution_type = self.select_contribution_type()
        time_period = self.get_time_period()
        print(f"📝 {time_period.title()} contribution: {contribution_type.replace('_', ' ').title()}")
        
        files_to_commit = []
        
        # 80% chance for quick file analysis, 20% for quick project analysis
        if random.random() < 0.8:
            # Analyze specific file
            target_file = self.get_random_python_file()
            if not target_file:
                print("No suitable Python files found")
                return False
            
            print(f"🔍 Analyzing: {target_file}")
            
            improvement = self.analyze_code_with_ai(target_file, contribution_type)
            if not improvement:
                print("Failed to generate improvement")
                return False
            
            improvement_file = self.create_improvement_file(target_file, improvement, contribution_type)
            files_to_commit.append(improvement_file)
            
        else:
            # Create quick project analysis
            print("🏗️ Quick project analysis...")
            analysis_file = self.create_quick_project_analysis()
            if analysis_file:
                files_to_commit.append(analysis_file)
                contribution_type = "quick_analysis"
        
        # Update activity log
        if files_to_commit:
            if self.update_activity_log(contribution_type, files_to_commit[0]):
                files_to_commit.append(self.activity_file)
        
        # Commit everything
        if files_to_commit:
            if self.commit_improvements(files_to_commit, contribution_type):
                print(f"✅ {contribution_type.replace('_', ' ').title()} contribution complete!")
                return True
        
        return False

def main():
    bot = SmartContributionBot()
    
    # Shorter randomization for high-frequency runs
    delay = random.randint(1, 10)
    print(f"⏳ Brief delay: {delay}s...")
    time.sleep(delay)
    
    success = bot.run_smart_contribution()
    
    if success:
        # Show daily progress
        try:
            if bot.activity_file.exists():
                with open(bot.activity_file, 'r') as f:
                    activity = json.load(f)
                
                today = datetime.now().strftime("%Y-%m-%d")
                today_count = sum(1 for a in activity.get('activities', []) 
                                if a['timestamp'].startswith(today))
                
                print(f"📊 Today's count: {today_count}/50")
        except:
            pass
        
        print("🎉 Contribution complete!")
    else:
        print("❌ Contribution failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
