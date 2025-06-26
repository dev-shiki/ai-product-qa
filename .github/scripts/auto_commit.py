#!/usr/bin/env python3
"""
Script untuk auto commit perubahan ke git repository
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoCommitter:
    def __init__(self):
        self.commit_message_template = "Auto-commit: {action} - {details}"
        
    def get_git_status(self) -> List[str]:
        """Get list of changed files"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git status failed: {result.stderr}")
                return []
            
            # Parse porcelain output
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Format: XY PATH
                    # X = status of index, Y = status of working tree
                    status = line[:2]
                    filepath = line[3:]
                    changed_files.append((status, filepath))
            
            return changed_files
            
        except subprocess.TimeoutExpired:
            logger.error("Git status timed out")
            return []
        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return []
    
    def categorize_changes(self, changed_files: List[tuple]) -> Dict[str, List[str]]:
        """Categorize changes by type"""
        categories = {
            "config_files": [],
            "test_files": [],
            "source_files": [],
            "other_files": []
        }
        
        for status, filepath in changed_files:
            if filepath.endswith(('.yml', '.yaml', '.json', '.toml', '.ini', '.cfg')):
                categories["config_files"].append(filepath)
            elif filepath.startswith('tests/') or 'test_' in filepath:
                categories["test_files"].append(filepath)
            elif filepath.startswith('app/') or filepath.endswith('.py'):
                categories["source_files"].append(filepath)
            else:
                categories["other_files"].append(filepath)
        
        return categories
    
    def generate_commit_message(self, categories: Dict[str, List[str]]) -> str:
        """Generate commit message based on changes"""
        action = "Update test coverage"
        details_parts = []
        
        if categories["config_files"]:
            details_parts.append(f"Update {len(categories['config_files'])} config files")
        if categories["test_files"]:
            details_parts.append(f"Update {len(categories['test_files'])} test files")
        if categories["source_files"]:
            details_parts.append(f"Update {len(categories['source_files'])} source files")
        if categories["other_files"]:
            details_parts.append(f"Update {len(categories['other_files'])} other files")
        
        details = " | ".join(details_parts) if details_parts else "General updates"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"{self.commit_message_template.format(action=action, details=details)} - {timestamp}"
    
    def stage_changes(self) -> bool:
        """Stage all changes"""
        try:
            result = subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git add failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Git add timed out")
            return False
        except Exception as e:
            logger.error(f"Error staging changes: {e}")
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit staged changes"""
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git commit failed: {result.stderr}")
                return False
            
            logger.info(f"Committed: {message}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Git commit timed out")
            return False
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False
    
    def push_changes(self) -> bool:
        """Push changes to remote"""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to get current branch: {result.stderr}")
                return False
            
            current_branch = result.stdout.strip()
            
            # Push to remote
            result = subprocess.run(
                ["git", "push", "origin", current_branch],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git push failed: {result.stderr}")
                return False
            
            logger.info(f"Pushed to origin/{current_branch}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Git push timed out")
            return False
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False
    
    def auto_commit(self) -> Dict:
        """Main auto commit process"""
        logger.info("Starting auto commit process...")
        
        try:
            # Get git status
            logger.info("Running git command: git status --porcelain")
            changed_files = self.get_git_status()
            
            if not changed_files:
                logger.info("No changes to commit")
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "files_changed": 0
                }
            
            logger.info(f"Found {len(changed_files)} changes to commit")
            
            # Categorize changes
            categories = self.categorize_changes(changed_files)
            
            # Generate commit message
            commit_message = self.generate_commit_message(categories)
            
            # Stage changes
            logger.info("Running git command: git add .")
            if not self.stage_changes():
                return {
                    "success": False,
                    "error": "Failed to stage changes"
                }
            
            # Commit changes
            logger.info(f"Running git command: git commit -m {commit_message}")
            if not self.commit_changes(commit_message):
                return {
                    "success": False,
                    "error": "Failed to commit changes"
                }
            
            # Push changes
            logger.info("Running git command: git branch --show-current")
            logger.info("Running git command: git push origin master")
            if not self.push_changes():
                return {
                    "success": False,
                    "error": "Failed to push changes"
                }
            
            # Success
            result = {
                "success": True,
                "message": commit_message,
                "files_changed": len(changed_files),
                "categories": categories
            }
            
            # Save result
            with open("auto_commit_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info("Auto commit result saved to auto_commit_result.json")
            return result
            
        except Exception as e:
            error_msg = f"Auto commit failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

def main():
    """Main function"""
    committer = AutoCommitter()
    result = committer.auto_commit()
    
    if result["success"]:
        print(f"\n[SUCCESS] Auto commit successful!")
        print(f"Message: {result['message']}")
        print(f"Files changed: {result['files_changed']}")
    else:
        print(f"\n[FAILED] Auto commit failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main() 