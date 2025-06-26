#!/usr/bin/env python3
"""
Main orchestrator script untuk menjalankan seluruh workflow auto commit
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
import subprocess
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    def __init__(self):
        self.scripts_dir = Path(".github/scripts")
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": False,
            "steps": [],
            "errors": []
        }
        
    def run_script(self, script_path: str, description: str, timeout: int = 300) -> Dict:
        """Run a Python script and return results"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"[SUCCESS] {description} completed successfully in {duration:.2f}s")
                return {
                    "script": script_path,
                    "description": description,
                    "success": True,
                    "duration": duration,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                logger.error(f"[FAILED] {description} failed: {result.stderr}")
                return {
                    "script": script_path,
                    "description": description,
                    "success": False,
                    "duration": duration,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"[TIMEOUT] {description} timed out after {timeout}s")
            return {
                "script": script_path,
                "description": description,
                "success": False,
                "duration": duration,
                "error": f"Timeout after {timeout}s"
            }
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[ERROR] {description} failed with exception: {e}")
            return {
                "script": script_path,
                "description": description,
                "success": False,
                "duration": duration,
                "error": str(e)
            }
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        try:
            # Check if we're in a git repository
            result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Not in a git repository")
                return False
            
            # Check if Gemini API key is set (optional but recommended)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                logger.warning("GEMINI_API_KEY not set - test generation may fail")
            else:
                logger.info("GEMINI_API_KEY is set")
            
            # Check if required Python packages are available
            required_packages = ["pytest", "coverage", "google.generativeai"]
            missing_packages = []
            
            for package in required_packages:
                try:
                    if package == "google.generativeai":
                        import google.generativeai
                    elif package == "pytest":
                        import pytest
                    elif package == "coverage":
                        import coverage
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                logger.error(f"Missing required packages: {missing_packages}")
                return False
            
            logger.info("Prerequisites check passed")
            return True
            
        except Exception as e:
            logger.error(f"Error checking prerequisites: {e}")
            return False
    
    def cleanup_previous_runs(self):
        """Cleanup files dari previous runs"""
        cleanup_files = [
            "coverage_report.json",
            "test_generation_results.json", 
            "auto_commit_result.json",
            "coverage.xml",
            ".coverage"
        ]
        
        for file_path in cleanup_files:
            if Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                    logger.info(f"Cleaned up: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file_path}: {e}")
    
    def run_coverage_analysis(self) -> Dict:
        """Run coverage analysis"""
        return self.run_script(
            str(self.scripts_dir / "coverage_analyzer.py"),
            "Coverage Analysis",
            timeout=300
        )
    
    def run_test_generation(self) -> Dict:
        """Run test generation with Gemini"""
        return self.run_script(
            str(self.scripts_dir / "test_generator.py"),
            "Test Generation with Gemini",
            timeout=600  # 10 minutes for AI generation
        )
    
    def run_auto_commit(self) -> Dict:
        """Run auto commit"""
        return self.run_script(
            str(self.scripts_dir / "auto_commit.py"),
            "Auto Commit",
            timeout=120
        )
    
    def validate_results(self) -> Dict:
        """Validate results dari setiap step"""
        validation_result = {
            "success": True,
            "issues": []
        }
        
        # Check coverage report
        if Path("coverage_report.json").exists():
            try:
                with open("coverage_report.json", "r") as f:
                    coverage_data = json.load(f)
                
                if "error" in coverage_data:
                    validation_result["issues"].append(f"Coverage analysis error: {coverage_data['error']}")
                    validation_result["success"] = False
                elif not coverage_data.get("lowest_coverage_files"):
                    validation_result["issues"].append("No files with low coverage found")
            except Exception as e:
                validation_result["issues"].append(f"Error reading coverage report: {e}")
                validation_result["success"] = False
        
        # Check test generation results
        if Path("test_generation_results.json").exists():
            try:
                with open("test_generation_results.json", "r") as f:
                    test_data = json.load(f)
                
                if "error" in test_data:
                    validation_result["issues"].append(f"Test generation error: {test_data['error']}")
                    validation_result["success"] = False
                elif test_data.get("error_count", 0) > 0:
                    validation_result["issues"].append(f"Test generation had {test_data['error_count']} errors")
            except Exception as e:
                validation_result["issues"].append(f"Error reading test results: {e}")
                validation_result["success"] = False
        
        return validation_result
    
    def generate_summary_report(self) -> str:
        """Generate summary report"""
        summary = []
        summary.append("=" * 60)
        summary.append("AUTO COMMIT WORKFLOW SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Timestamp: {self.results['timestamp']}")
        summary.append(f"Overall Success: {'SUCCESS' if self.results['overall_success'] else 'FAILED'}")
        
        # Count steps
        successful_steps = sum(1 for step in self.results["steps"] if step.get("success", False))
        skipped_steps = sum(1 for step in self.results["steps"] if step.get("skipped", False))
        failed_steps = len(self.results["steps"]) - successful_steps - skipped_steps
        
        summary.append(f"Steps: {successful_steps} successful, {skipped_steps} skipped, {failed_steps} failed")
        summary.append("")
        
        # Step details
        for step in self.results["steps"]:
            status = "[SKIPPED]"
            if step.get("success", False):
                status = "[SUCCESS]"
            elif step.get("skipped", False):
                status = "[SKIPPED]"
            else:
                status = "[FAILED]"
            
            duration = step.get("duration", 0)
            summary.append(f"{status} {step['description']} ({duration:.2f}s)")
            
            if step.get("skipped") and step.get("reason"):
                summary.append(f"  Reason: {step['reason']}")
            elif step.get("error"):
                summary.append(f"  Error: {step['error']}")
        
        # Errors section
        if self.results["errors"]:
            summary.append("")
            summary.append("ERRORS:")
            for error in self.results["errors"]:
                summary.append(f"  - {error}")
        
        summary.append("=" * 60)
        return "\n".join(summary)
    
    def run_workflow(self) -> Dict:
        """Main workflow execution"""
        start_time = time.time()
        
        logger.info("Starting Auto Commit Workflow")
        logger.info("Checking prerequisites...")
        
        if not self.check_prerequisites():
            logger.error("Prerequisites check failed")
            return self._create_error_result("Prerequisites check failed")
        
        logger.info("Prerequisites check passed")
        
        # Clean up previous files
        self._cleanup_previous_files()
        
        # Step 1: Coverage Analysis
        logger.info("Running Coverage Analysis...")
        step1_result = self.run_coverage_analysis()
        
        # Step 2: Test Generation (only if coverage data available)
        step2_result = None
        if self._has_coverage_data():
            logger.info("Running Test Generation with Gemini...")
            step2_result = self.run_test_generation()
        else:
            logger.warning("Skipping test generation - no coverage data available")
        
        # Step 3: Auto Commit
        logger.info("Running Auto Commit...")
        step3_result = self.run_auto_commit()
        
        # Compile results
        results = self._compile_results(step1_result, step2_result, step3_result, start_time)
        
        # Save results
        self._save_results(results)
        
        # Print summary
        self._print_summary(results)
        
        return results

    def _cleanup_previous_files(self):
        """Clean up files from previous runs"""
        files_to_clean = [
            "coverage_report.json",
            "coverage.xml", 
            ".coverage",
            "test_generation_results.json",
            "auto_commit_result.json"
        ]
        
        for file_path in files_to_clean:
            if Path(file_path).exists():
                Path(file_path).unlink()
                logger.info(f"Cleaned up: {file_path}")
    
    def _has_coverage_data(self) -> bool:
        """Check if coverage data is available and usable"""
        if not Path("coverage_report.json").exists():
            return False
            
        try:
            with open("coverage_report.json", "r") as f:
                coverage_report = json.load(f)
            
            if "error" in coverage_report:
                return False
                
            lowest_files = coverage_report.get("lowest_coverage_files", [])
            return len(lowest_files) > 0
            
        except Exception as e:
            logger.error(f"Error reading coverage report: {e}")
            return False
    
    def _create_error_result(self, error_msg: str) -> Dict:
        """Create error result"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_success": False,
            "steps": [],
            "errors": [error_msg]
        }
    
    def _compile_results(self, step1_result: Dict, step2_result: Dict, step3_result: Dict, start_time: float) -> Dict:
        """Compile all step results into final result"""
        steps = [step1_result]
        if step2_result:
            steps.append(step2_result)
        steps.append(step3_result)
        
        # Count successful steps
        successful_steps = sum(1 for step in steps if step.get("success", False))
        total_steps = len(steps)
        
        # Determine overall success
        overall_success = successful_steps >= max(1, total_steps // 2)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_success": overall_success,
            "steps": steps,
            "errors": [step.get("error") for step in steps if step.get("error")],
            "duration": time.time() - start_time
        }
    
    def _save_results(self, results: Dict):
        """Save results to files"""
        with open("workflow_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("Workflow completed. Results saved to workflow_results.json")
    
    def _print_summary(self, results: Dict):
        """Print workflow summary"""
        print("\n" + "=" * 60)
        print("AUTO COMMIT WORKFLOW SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Success: {'SUCCESS' if results['overall_success'] else 'FAILED'}")
        
        successful_steps = sum(1 for step in results["steps"] if step.get("success", False))
        print(f"Steps: {successful_steps}/{len(results['steps'])} successful")
        
        for step in results["steps"]:
            status = "[SUCCESS]" if step.get("success", False) else "[FAILED]"
            print(f"{status} {step['description']} ({step.get('duration', 0):.2f}s)")
            if step.get("error"):
                print(f"  Error: {step['error']}")
        
        if results.get("errors"):
            print("\nERRORS:")
            for error in results["errors"]:
                if error:
                    print(f"  - {error}")
        
        print("=" * 60)

def main():
    """Main function"""
    orchestrator = WorkflowOrchestrator()
    
    try:
        results = orchestrator.run_workflow()
        
        if results.get("overall_success", False):
            logger.info("Workflow completed successfully!")
        else:
            logger.error("Workflow completed with errors")
            
    except Exception as e:
        logger.error(f"Workflow failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 