#!/usr/bin/env python3
"""
Script untuk menggunakan Gemini API untuk generate test cases
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Import config
sys.path.append(str(Path(__file__).parent))
from config import TEST_GENERATION_SETTINGS

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini - Use model from config
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(TEST_GENERATION_SETTINGS["model"])
        logger.info(f"Using Gemini model: {TEST_GENERATION_SETTINGS['model']}")
        
    def generate_test_prompt(self, file_info: Dict) -> str:
        """Generate prompt untuk Gemini berdasarkan file info"""
        filepath = file_info["filepath"]
        content = file_info["content"]
        existing_test = file_info.get("existing_test", "")
        coverage = file_info["coverage"]
        
        prompt = f"""
You are an expert Python developer and testing specialist. I need you to generate comprehensive test cases for a Python file with low test coverage.

File: {filepath}
Current Coverage: {coverage}%

Here's the source code:
```python
{content}
"""

        if existing_test:
            prompt += f"""
Here's the existing test file (if any):
```python
{existing_test}
```
"""
        else:
            prompt += "No existing test file found."

        prompt += """
Please generate a complete, production-ready test file that:
1. Uses pytest framework
2. Has comprehensive test coverage (aim for 90%+ coverage)
3. Tests all functions, methods, and edge cases
4. Includes proper mocking where needed
5. Has clear test names and documentation
6. Follows Python testing best practices
7. Handles both success and error scenarios
8. Uses appropriate fixtures and setup/teardown

The test file should be named: test_""" + filepath.replace('app/', '') + """

Return ONLY the complete test code without any explanations or markdown formatting.
"""
        return prompt
    
    def generate_test_code(self, file_info: Dict) -> Optional[str]:
        """Generate test code menggunakan Gemini API dengan retry logic"""
        max_retries = TEST_GENERATION_SETTINGS["max_retries"]
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                prompt = self.generate_test_prompt(file_info)
                
                logger.info(f"Generating test for {file_info['filepath']} (attempt {attempt + 1}/{max_retries})")
                
                # Generate response from Gemini
                response = self.model.generate_content(prompt)
                
                if response.text:
                    # Clean up the response
                    test_code = response.text.strip()
                    
                    # Remove markdown code blocks if present
                    if test_code.startswith("```python"):
                        test_code = test_code[9:]
                    if test_code.endswith("```"):
                        test_code = test_code[:-3]
                    
                    logger.info(f"Successfully generated test code for {file_info['filepath']}")
                    return test_code.strip()
                else:
                    logger.error(f"No response from Gemini for {file_info['filepath']}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    return None
                    
            except Exception as e:
                logger.error(f"Error generating test for {file_info['filepath']} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                return None
        
        return None
    
    def save_test_file(self, filepath: str, test_code: str) -> bool:
        """Save test code ke file (selalu di root tests/, penamaan unik, tidak overwrite)"""
        try:
            # Ambil nama file python asli tanpa path
            base_name = Path(filepath).name  # e.g. ai_service.py
            test_base = f"test_{base_name}"
            test_file_path = Path("tests") / test_base

            # Jika sudah ada, tambahkan versi _v2, _v3, dst
            version = 2
            while test_file_path.exists():
                stem = Path(test_base).stem  # test_ai_service
                suffix = Path(test_base).suffix  # .py
                test_file_path = Path("tests") / f"{stem}_v{version}{suffix}"
                version += 1

            # Write test file
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            logger.info(f"Test file saved: {test_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving test file: {e}")
            return False
    
    def validate_test_code(self, test_code: str) -> bool:
        """Basic validation untuk test code"""
        if not test_code:
            return False
        
        # Check for basic pytest elements
        required_elements = [
            "import pytest",
            "def test_",
            "assert"
        ]
        
        for element in required_elements:
            if element not in test_code:
                logger.warning(f"Test code missing required element: {element}")
                return False
        
        return True
    
    def run_generated_test(self, filepath: str) -> Dict:
        """Run generated test dan return result"""
        try:
            # Ambil nama file python asli tanpa path
            base_name = Path(filepath).name  # e.g. ai_service.py
            test_base = f"test_{base_name}"
            test_file_path = Path("tests") / test_base

            # Cari file test yang sudah dibuat (termasuk versi)
            version = 2
            while not test_file_path.exists():
                stem = Path(test_base).stem  # test_ai_service
                suffix = Path(test_base).suffix  # .py
                test_file_path = Path("tests") / f"{stem}_v{version}{suffix}"
                version += 1
                
                # Jika sudah cek sampai v10 dan tidak ketemu, berarti file tidak ada
                if version > 10:
                    return {"success": False, "error": "Test file not found"}

            # Run the specific test file
            cmd = ["python", "-m", "pytest", str(test_file_path), "-v", "--tb=short"]
            
            logger.info(f"Running test: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_coverage_report(self, report_file: str = "coverage_report.json") -> Dict:
        """Process coverage report dan generate tests"""
        if not Path(report_file).exists():
            logger.error(f"Coverage report not found: {report_file}")
            return {"error": "Coverage report not found"}
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            if "error" in report:
                return report
            
            results = {
                "processed_files": [],
                "success_count": 0,
                "error_count": 0
            }
            
            for file_info in report["lowest_coverage_files"]:
                current_file = len(results["processed_files"]) + 1
                total_files = len(report["lowest_coverage_files"])
                logger.info(f"Processing {file_info['filepath']} ({current_file}/{total_files})")
                
                # Generate test code
                test_code = self.generate_test_code(file_info)
                
                if test_code and self.validate_test_code(test_code):
                    # Save test file
                    if self.save_test_file(file_info['filepath'], test_code):
                        # Run test to validate
                        test_result = self.run_generated_test(file_info['filepath'])
                        
                        file_result = {
                            "filepath": file_info['filepath'],
                            "coverage": file_info['coverage'],
                            "test_generated": True,
                            "test_saved": True,
                            "test_result": test_result
                        }
                        
                        if test_result["success"]:
                            results["success_count"] += 1
                        else:
                            results["error_count"] += 1
                    else:
                        file_result = {
                            "filepath": file_info['filepath'],
                            "coverage": file_info['coverage'],
                            "test_generated": True,
                            "test_saved": False,
                            "error": "Failed to save test file"
                        }
                        results["error_count"] += 1
                else:
                    file_result = {
                        "filepath": file_info['filepath'],
                        "coverage": file_info['coverage'],
                        "test_generated": False,
                        "error": "Failed to generate valid test code"
                    }
                    results["error_count"] += 1
                
                results["processed_files"].append(file_result)
                
                # Add delay to avoid rate limiting (progressive backoff)
                delay = min(2 + (results["error_count"] * 0.5), 10)  # Max 10 seconds
                logger.info(f"Waiting {delay}s before next API call...")
                time.sleep(delay)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing coverage report: {e}")
            return {"error": str(e)}

    def generate_tests(self, files: List[str], coverage_data: Dict) -> List[Dict]:
        """Generate one focused test function for the first uncovered function in each file, save as flat test file."""
        results = []
        for filepath in files:
            module_name = Path(filepath).stem
            uncovered_funcs = self.get_uncovered_functions(filepath, coverage_data)
            if not uncovered_funcs:
                logger.info(f"No uncovered functions found in {filepath}, skipping.")
                continue
            target_func = uncovered_funcs[0]
            logger.info(f"Generating test for {filepath} function {target_func}")

            # Prompt: only one test function, focus, must be simple
            prompt = (
                f"Buatkan satu fungsi unit test pytest untuk fungsi '{target_func}' di file '{filepath}'. "
                f"Test harus sederhana, tidak perlu mock berlebihan, dan cukup satu test function saja. "
                f"Output hanya kode fungsi test-nya saja (tanpa import, tanpa class, tanpa file penuh)."
            )
            test_func_code = self.generate_test_with_gemini(prompt, filepath)
            if not test_func_code:
                logger.error(f"Failed to generate test for {filepath}::{target_func}")
                results.append({"file": filepath, "function": target_func, "success": False, "error": "No test generated"})
                continue

            # Save to flat test file with versioning
            test_file_path = self.get_next_test_file_path(module_name)
            with open(test_file_path, "w", encoding="utf-8") as f:
                # Add import pytest and import target module
                f.write(f"import pytest\n")
                import_path = filepath.replace("/", ".").replace(".py", "")
                f.write(f"from app.{import_path} import {target_func}\n\n")
                f.write(test_func_code.strip() + "\n")
            logger.info(f"Saved test for {filepath}::{target_func} to {test_file_path}")
            results.append({"file": filepath, "function": target_func, "success": True, "test_file": str(test_file_path)})
        return results

    def get_uncovered_functions(self, filepath: str, coverage_data: Dict) -> List[str]:
        """Return list of function names in the file that are not covered (dummy: return first function if any)."""
        # TODO: Replace with real coverage analysis per function if available
        # For now, just return all top-level function names
        import ast
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            return []

    def get_next_test_file_path(self, module_name: str) -> Path:
        """Get next available test file path in tests/ with versioning."""
        tests_dir = Path("tests")
        base = f"test_{module_name}.py"
        path = tests_dir / base
        version = 2
        while path.exists():
            path = tests_dir / f"test_{module_name}_v{version}.py"
            version += 1
        return path

def main():
    """Main function"""
    try:
        generator = TestGenerator()
        
        # Load coverage report
        if not Path("coverage_report.json").exists():
            logger.error("coverage_report.json not found")
            return
        
        with open("coverage_report.json", "r", encoding="utf-8") as f:
            coverage_data = json.load(f)
        
        # Get files with low coverage
        low_coverage_files = []
        for item in coverage_data.get("lowest_coverage_files", []):
            filepath = item.get("filepath", "")
            if filepath and Path(filepath).exists():
                low_coverage_files.append(filepath)
        
        if not low_coverage_files:
            logger.info("No files with low coverage found")
            return
        
        # Generate focused tests
        results = generator.generate_tests(low_coverage_files, coverage_data)

        # Save results
        with open("test_generation_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info("Test generation results saved to test_generation_results.json")

        # Print summary
        successful = sum(1 for r in results if r.get("success", False))
        total = len(results)
        logger.info(f"Generated {successful}/{total} focused tests successfully")

    except Exception as e:
        logger.error(f"Test generation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 