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
            "steps": [],
            "overall_success": False,
            "errors": []
        }
        
    def run_script(self, script_name: str, description: str) -> Dict:
        """Run Python script dan return result"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            error_msg = f"Script not found: {script_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "script": script_name,
                "description": description
            }
        
        try:
            logger.info(f"Running {description}...")
            start_time = time.time()
            
            # Run script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            step_result = {
                "script": script_name,
                "description": description,
                "success": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully in {duration:.2f}s")
            else:
                logger.error(f"❌ {description} failed: {result.stderr}")
                step_result["error"] = result.stderr
            
            return step_result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Script timeout: {script_name}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "script": script_name,
                "description": description
            }
        except Exception as e:
            error_msg = f"Error running script {script_name}: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "script": script_name,
                "description": description
            }
    
    def check_prerequisites(self) -> bool:
        """Check prerequisites sebelum menjalankan workflow"""
        logger.info("Checking prerequisites...")
        
        # Check if we're in a git repository
        if not Path(".git").exists():
            logger.error("Not in a git repository")
            return False
        
        # Check if required files exist
        required_files = [
            "requirements.txt",
            "app/",
            "tests/"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"Required file/directory not found: {file_path}")
                return False
        
        # Check if Gemini API key is set
        if not os.getenv("GEMINI_API_KEY"):
            logger.warning("GEMINI_API_KEY not set - test generation may fail")
        
        logger.info("✅ Prerequisites check passed")
        return True
    
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
        """Step 1: Run coverage analysis"""
        return self.run_script(
            "coverage_analyzer.py",
            "Coverage Analysis"
        )
    
    def run_test_generation(self) -> Dict:
        """Step 2: Generate tests using Gemini"""
        return self.run_script(
            "test_generator.py", 
            "Test Generation with Gemini"
        )
    
    def run_auto_commit(self) -> Dict:
        """Step 3: Auto commit changes"""
        return self.run_script(
            "auto_commit.py",
            "Auto Commit"
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
        """Generate enhanced summary report"""
        summary = []
        summary.append("=" * 60)
        summary.append("🤖 AUTO COMMIT WORKFLOW SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Timestamp: {self.results['timestamp']}")
        summary.append(f"Overall Success: {'✅' if self.results['overall_success'] else '❌'}")
        
        # Calculate statistics
        successful_steps = sum(1 for step in self.results["steps"] if step.get("success", False))
        skipped_steps = sum(1 for step in self.results["steps"] if step.get("skipped", False))
        failed_steps = len(self.results["steps"]) - successful_steps - skipped_steps
        
        summary.append(f"Steps: {successful_steps} successful, {skipped_steps} skipped, {failed_steps} failed")
        summary.append("")
        
        for step in self.results["steps"]:
            if step.get("skipped", False):
                status = "⏭️"
                reason = f" (skipped: {step.get('reason', 'unknown reason')})"
            elif step.get("success", False):
                status = "✅"
                reason = ""
            else:
                status = "❌"
                reason = ""
            
            duration = step.get("duration", 0)
            summary.append(f"{status} {step['description']} ({duration:.2f}s){reason}")
            
            if not step.get("success", False) and not step.get("skipped", False) and step.get("error"):
                summary.append(f"   Error: {step['error']}")
        
        if self.results["errors"]:
            summary.append("")
            summary.append("❌ ERRORS:")
            for error in self.results["errors"]:
                summary.append(f"  - {error}")
        
        summary.append("=" * 60)
        return "\n".join(summary)
    
    def run_workflow(self) -> Dict:
        """Main workflow execution"""
        logger.info("🚀 Starting Auto Commit Workflow")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.results["errors"].append("Prerequisites check failed")
            return self.results
        
        # Cleanup previous runs
        self.cleanup_previous_runs()
        
        # Step 1: Coverage Analysis
        step1_result = self.run_coverage_analysis()
        self.results["steps"].append(step1_result)
        
        coverage_data_available = False
        if step1_result["success"]:
            # Check if coverage data actually exists and is usable
            if Path("coverage_report.json").exists():
                try:
                    with open("coverage_report.json", "r") as f:
                        coverage_report = json.load(f)
                    
                    if "error" not in coverage_report and coverage_report.get("lowest_coverage_files"):
                        coverage_data_available = True
                        logger.info(f"✅ Coverage data available for {len(coverage_report['lowest_coverage_files'])} files")
                    else:
                        logger.warning("Coverage report exists but has no usable data")
                except Exception as e:
                    logger.error(f"Error reading coverage report: {e}")
        
        if not step1_result["success"]:
            self.results["errors"].append(f"Coverage analysis failed: {step1_result.get('error', 'Unknown error')}")
            logger.warning("Coverage analysis failed, but continuing with remaining steps...")
        
        # Step 2: Test Generation (only if we have coverage data)
        if coverage_data_available:
            step2_result = self.run_test_generation()
            self.results["steps"].append(step2_result)
            
            if not step2_result["success"]:
                self.results["errors"].append(f"Test generation failed: {step2_result.get('error', 'Unknown error')}")
        else:
            logger.warning("⏭️ Skipping test generation - no coverage data available")
            step2_result = {
                "script": "test_generator.py",
                "description": "Test Generation with Gemini",
                "success": False,
                "skipped": True,
                "reason": "No coverage data available",
                "duration": 0
            }
            self.results["steps"].append(step2_result)
            self.results["errors"].append("Test generation skipped: No coverage data available")
        
        # Step 3: Auto Commit (only if there are changes to commit)
        git_status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        has_changes = bool(git_status_result.stdout.strip())
        
        if has_changes:
            step3_result = self.run_auto_commit()
            self.results["steps"].append(step3_result)
            
            if not step3_result["success"]:
                self.results["errors"].append(f"Auto commit failed: {step3_result.get('error', 'Unknown error')}")
        else:
            logger.info("⏭️ No changes to commit")
            step3_result = {
                "script": "auto_commit.py", 
                "description": "Auto Commit",
                "success": True,
                "skipped": True,
                "reason": "No changes to commit",
                "duration": 0
            }
            self.results["steps"].append(step3_result)
        
        # Validate results
        validation = self.validate_results()
        if not validation["success"]:
            self.results["errors"].extend(validation["issues"])
        
        # Determine overall success - improved logic
        successful_steps = sum(1 for step in self.results["steps"] if step.get("success", False))
        skipped_steps = sum(1 for step in self.results["steps"] if step.get("skipped", False))
        total_steps = len(self.results["steps"])
        actual_executed_steps = total_steps - skipped_steps
        
        # Success criteria:
        # - If all steps are skipped (no work needed) = success
        # - If at least 1 step executed successfully = partial success
        # - If coverage analysis works + (test gen OR commit works) = success
        if skipped_steps == total_steps:
            self.results["overall_success"] = True
            logger.info("🎉 All steps skipped - no work needed, considering successful")
        elif successful_steps >= max(1, actual_executed_steps // 2):
            self.results["overall_success"] = True
            logger.info(f"🎉 {successful_steps}/{actual_executed_steps} executed steps successful")
        else:
            self.results["overall_success"] = False
            logger.warning(f"⚠️ Only {successful_steps}/{actual_executed_steps} executed steps successful")
        
        # Save results
        with open("workflow_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        summary = self.generate_summary_report()
        print(summary)
        
        # Save summary to file
        with open("workflow_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
        
        logger.info("Workflow completed. Results saved to workflow_results.json")
        
        return self.results

def main():
    """Main function"""
    try:
        orchestrator = WorkflowOrchestrator()
        results = orchestrator.run_workflow()
        
        if results["overall_success"]:
            logger.info("🎉 Workflow completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Workflow completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 