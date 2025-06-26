#!/usr/bin/env python3
"""
Script untuk melakukan auto commit dengan git
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoCommitter:
    def __init__(self):
        self.repo_path = Path.cwd()
        self.commit_message_template = "🤖 Auto-commit: {action} - {details}"
        
    def run_git_command(self, command: List[str], capture_output: bool = True) -> Dict:
        """Run git command dan return result"""
        try:
            logger.info(f"Running git command: {' '.join(command)}")
            result = subprocess.run(
                command, 
                capture_output=capture_output, 
                text=True, 
                cwd=self.repo_path
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "returncode": 1
            }
    
    def check_git_status(self) -> Dict:
        """Check git status dan return list of changes"""
        result = self.run_git_command(["git", "status", "--porcelain"])
        
        if not result["success"]:
            return {"error": "Failed to check git status"}
        
        changes = []
        for line in result["stdout"].strip().split('\n'):
            if line.strip():
                status = line[:2]
                filename = line[3:]
                changes.append({
                    "status": status,
                    "filename": filename
                })
        
        return {
            "success": True,
            "changes": changes,
            "total_changes": len(changes)
        }
    
    def add_files(self, files: Optional[List[str]] = None) -> Dict:
        """Add files to git staging"""
        if files:
            # Add specific files
            command = ["git", "add"] + files
        else:
            # Add all changes
            command = ["git", "add", "."]
        
        return self.run_git_command(command)
    
    def create_commit(self, message: str) -> Dict:
        """Create git commit"""
        command = ["git", "commit", "-m", message]
        return self.run_git_command(command)
    
    def push_changes(self, branch: str = "main") -> Dict:
        """Push changes to remote repository"""
        command = ["git", "push", "origin", branch]
        return self.run_git_command(command)
    
    def get_current_branch(self) -> str:
        """Get current git branch"""
        result = self.run_git_command(["git", "branch", "--show-current"])
        if result["success"] and result["stdout"].strip():
            return result["stdout"].strip()
        
        # Fallback: try to get branch from git symbolic-ref
        result = self.run_git_command(["git", "symbolic-ref", "--short", "HEAD"])
        if result["success"] and result["stdout"].strip():
            return result["stdout"].strip()
        
        # Final fallback
        logger.warning("Unable to determine current branch, using 'main'")
        return "main"
    
    def generate_commit_message(self, action: str, details: str) -> str:
        """Generate commit message dengan timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.commit_message_template.format(
            action=action,
            details=f"{details} - {timestamp}"
        )
    
    def analyze_changes(self, changes: List[Dict]) -> Dict:
        """Analyze changes untuk generate meaningful commit message"""
        test_files = []
        source_files = []
        config_files = []
        other_files = []
        
        for change in changes:
            filename = change["filename"]
            if filename.startswith("tests/"):
                test_files.append(filename)
            elif filename.startswith("app/"):
                source_files.append(filename)
            elif filename.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
                config_files.append(filename)
            else:
                other_files.append(filename)
        
        return {
            "test_files": test_files,
            "source_files": source_files,
            "config_files": config_files,
            "other_files": other_files
        }
    
    def create_meaningful_commit_message(self, changes_analysis: Dict) -> str:
        """Create meaningful commit message berdasarkan jenis perubahan"""
        parts = []
        
        if changes_analysis["test_files"]:
            parts.append(f"Add {len(changes_analysis['test_files'])} test files")
        
        if changes_analysis["source_files"]:
            parts.append(f"Update {len(changes_analysis['source_files'])} source files")
        
        if changes_analysis["config_files"]:
            parts.append(f"Update {len(changes_analysis['config_files'])} config files")
        
        if changes_analysis["other_files"]:
            parts.append(f"Update {len(changes_analysis['other_files'])} other files")
        
        if not parts:
            parts.append("Update files")
        
        return " | ".join(parts)
    
    def auto_commit(self, force: bool = False) -> Dict:
        """Main function untuk auto commit"""
        logger.info("Starting auto commit process...")
        
        # Check git status
        status_result = self.check_git_status()
        if "error" in status_result:
            return status_result
        
        changes = status_result["changes"]
        total_changes = status_result["total_changes"]
        
        if total_changes == 0:
            logger.info("No changes to commit")
            return {
                "success": True,
                "message": "No changes to commit",
                "changes_count": 0
            }
        
        logger.info(f"Found {total_changes} changes to commit")
        
        # Analyze changes
        changes_analysis = self.analyze_changes(changes)
        
        # Add files
        add_result = self.add_files()
        if not add_result["success"]:
            return {
                "success": False,
                "error": "Failed to add files",
                "details": add_result
            }
        
        # Generate commit message
        action = "Update test coverage"
        details = self.create_meaningful_commit_message(changes_analysis)
        commit_message = self.generate_commit_message(action, details)
        
        # Create commit
        commit_result = self.create_commit(commit_message)
        if not commit_result["success"]:
            return {
                "success": False,
                "error": "Failed to create commit",
                "details": commit_result
            }
        
        # Push changes (optional, based on force parameter)
        push_result = None
        if force:
            current_branch = self.get_current_branch()
            push_result = self.push_changes(current_branch)
            
            if not push_result["success"]:
                logger.warning(f"Failed to push changes: {push_result['stderr']}")
        
        return {
            "success": True,
            "message": f"Successfully committed {total_changes} changes",
            "commit_message": commit_message,
            "changes_count": total_changes,
            "changes_analysis": changes_analysis,
            "push_result": push_result
        }
    
    def load_test_results(self, results_file: str = "test_generation_results.json") -> Optional[Dict]:
        """Load test generation results"""
        if not Path(results_file).exists():
            return None
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading test results: {e}")
            return None
    
    def create_detailed_commit_message(self, test_results: Dict) -> str:
        """Create detailed commit message berdasarkan test results"""
        if "error" in test_results:
            return f"Test generation failed: {test_results['error']}"
        
        success_count = test_results.get("success_count", 0)
        error_count = test_results.get("error_count", 0)
        total_processed = len(test_results.get("processed_files", []))
        
        if total_processed == 0:
            return "No files processed for test generation"
        
        details = f"Generated tests for {total_processed} files"
        if success_count > 0:
            details += f" ({success_count} successful)"
        if error_count > 0:
            details += f" ({error_count} errors)"
        
        return details

def main():
    """Main function"""
    try:
        committer = AutoCommitter()
        
        # Load test results if available
        test_results = committer.load_test_results()
        
        # Perform auto commit
        result = committer.auto_commit(force=True)  # Force push for automation
        
        # Save commit result
        with open("auto_commit_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info("Auto commit result saved to auto_commit_result.json")
        
        if result["success"]:
            print(f"\n✅ Auto commit successful!")
            print(f"Message: {result['message']}")
            print(f"Changes: {result['changes_count']}")
            
            if test_results:
                details = committer.create_detailed_commit_message(test_results)
                print(f"Test generation: {details}")
        else:
            print(f"\n❌ Auto commit failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Auto commit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 