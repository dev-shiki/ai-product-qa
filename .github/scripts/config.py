#!/usr/bin/env python3
"""
Configuration file untuk Auto Commit Workflow
"""

import os
from pathlib import Path

# Project paths - Updated for ai-product-qa structure
PROJECT_ROOT = Path.cwd()
SOURCE_DIR = PROJECT_ROOT / "app"
TEST_DIR = PROJECT_ROOT / "tests"
SCRIPTS_DIR = PROJECT_ROOT / ".github" / "scripts"

# Coverage settings
COVERAGE_SETTINGS = {
    "source_dir": str(SOURCE_DIR),
    "test_dir": str(TEST_DIR),
    "target_coverage": 80.0,  # Target coverage percentage
    "min_files_to_process": 1,  # Minimum files to process
    "max_files_to_process": 5,  # Maximum files to process per run
    "coverage_threshold": 50.0,  # Only process files below this coverage
}

# Test generation settings
TEST_GENERATION_SETTINGS = {
    "model": "gemini-2.5-flash",  # Updated to latest model
    "target_test_coverage": 90.0,  # Target coverage for generated tests
    "max_retries": 3,  # Maximum retries for API calls
    "delay_between_calls": 2,  # Delay between API calls (seconds)
    "timeout": 60,  # Timeout for test execution (seconds)
    "required_elements": [
        "import pytest",
        "def test_",
        "assert"
    ]
}

# Auto commit settings
AUTO_COMMIT_SETTINGS = {
    "commit_message_template": "🤖 Auto-commit: {action} - {details} - {timestamp}",
    "auto_push": True,  # Automatically push changes
    "force_push": False,  # Force push if needed
    "branch": "main",  # Default branch
    "git_user": {
        "name": "GitHub Action",
        "email": "action@github.com"
    }
}

# Workflow settings
WORKFLOW_SETTINGS = {
    "max_execution_time": 300,  # Maximum execution time per step (seconds)
    "continue_on_error": True,  # Continue workflow even if some steps fail
    "min_success_rate": 0.67,  # Minimum success rate (2 out of 3 steps)
    "cleanup_previous_runs": True,  # Clean up files from previous runs
    "log_level": "INFO",  # Logging level
}

# File patterns
FILE_PATTERNS = {
    "python_files": "*.py",
    "test_files": "test_*.py",
    "coverage_files": [".coverage", "coverage.xml"],
    "result_files": [
        "coverage_report.json",
        "test_generation_results.json",
        "auto_commit_result.json",
        "workflow_results.json",
        "workflow_summary.txt",
        "orchestrator.log"
    ]
}

# Environment variables
ENV_VARS = {
    "GEMINI_API_KEY": os.getenv("GOOGLE_API_KEY"),
    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
    "GITHUB_REPOSITORY": os.getenv("GITHUB_REPOSITORY"),
    "GITHUB_SHA": os.getenv("GITHUB_SHA"),
    "GITHUB_REF": os.getenv("GITHUB_REF"),
}

# Validation functions
def validate_config():
    """Validate configuration"""
    errors = []
    
    # Check required directories
    if not SOURCE_DIR.exists():
        errors.append(f"Source directory not found: {SOURCE_DIR}")
    
    if not TEST_DIR.exists():
        errors.append(f"Test directory not found: {TEST_DIR}")
    
    # Check environment variables
    if not ENV_VARS["GEMINI_API_KEY"]:
        errors.append("GEMINI_API_KEY not set")
    
    # Check settings
    if COVERAGE_SETTINGS["target_coverage"] < 0 or COVERAGE_SETTINGS["target_coverage"] > 100:
        errors.append("Invalid target coverage percentage")
    
    if TEST_GENERATION_SETTINGS["target_test_coverage"] < 0 or TEST_GENERATION_SETTINGS["target_test_coverage"] > 100:
        errors.append("Invalid target test coverage percentage")
    
    return errors

def get_config_summary():
    """Get configuration summary"""
    return {
        "project_root": str(PROJECT_ROOT),
        "source_dir": str(SOURCE_DIR),
        "test_dir": str(TEST_DIR),
        "coverage_target": COVERAGE_SETTINGS["target_coverage"],
        "test_coverage_target": TEST_GENERATION_SETTINGS["target_test_coverage"],
        "max_files_per_run": COVERAGE_SETTINGS["max_files_to_process"],
        "auto_push": AUTO_COMMIT_SETTINGS["auto_push"],
        "gemini_api_key_set": bool(ENV_VARS["GEMINI_API_KEY"]),
        "github_token_set": bool(ENV_VARS["GITHUB_TOKEN"]),
    }

# Export all settings
__all__ = [
    "PROJECT_ROOT",
    "SOURCE_DIR", 
    "TEST_DIR",
    "SCRIPTS_DIR",
    "COVERAGE_SETTINGS",
    "TEST_GENERATION_SETTINGS",
    "AUTO_COMMIT_SETTINGS",
    "WORKFLOW_SETTINGS",
    "FILE_PATTERNS",
    "ENV_VARS",
    "validate_config",
    "get_config_summary"
] 