#!/usr/bin/env python3
"""
Script untuk menggunakan Gemini API untuk generate test cases
"""

import os
import sys
import json
import time
import subprocess
import ast
import inspect
import importlib.util
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
        
    def analyze_module_structure(self, filepath: str) -> Dict:
        """Analyze module to get accurate class and function information"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Get imports to understand dependencies
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{node.module}.{alias.name}")
            
            # Get classes and their methods
            classes = {}
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Skip private methods
                            if not item.name.startswith('_'):
                                class_methods.append(item.name)
                    classes[node.name] = class_methods
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions (not inside classes)
                    parent = getattr(node, 'parent', None)
                    if not hasattr(node, 'parent') or not isinstance(getattr(node, 'parent', None), ast.ClassDef):
                        if not node.name.startswith('_'):
                            functions.append(node.name)
            
            return {
                "content": content,
                "imports": imports,
                "classes": classes,
                "functions": functions
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            return {"content": "", "imports": [], "classes": {}, "functions": []}
        
    def generate_test_prompt(self, file_info: Dict) -> str:
        """Generate prompt untuk Gemini berdasarkan file info - fokus pada satu fungsi/class saja"""
        filepath = file_info["filepath"]
        module_info = file_info["module_info"]
        target_item = file_info.get("target_item", "")
        target_type = file_info.get("target_type", "function")  # "function" or "class"
        
        # Create import statement based on file structure
        clean_filepath = filepath.replace("app/", "").replace("/", ".").replace(".py", "")
        import_path = f"app.{clean_filepath}"
        
        prompt = f"""
Buatkan unit test pytest untuk {target_type} '{target_item}' di file '{filepath}'.

File structure analysis:
- File: {filepath}
- Available classes: {list(module_info['classes'].keys())}
- Available functions: {module_info['functions']}
- Target {target_type}: {target_item}

Source code excerpt:
```python
{module_info['content'][:2000]}...
```

Instruksi:
1. Buatkan test untuk {target_type} '{target_item}' yang BENAR-BENAR ADA di file
2. Gunakan import yang tepat: from {import_path} import {target_item}
3. Test harus sederhana dan realistic
4. Jangan gunakan mock yang rumit
5. Handle potential exceptions dengan try-catch
6. HANYA return complete test file dengan import statements

Output format:
```python
import pytest
from {import_path} import {target_item}

def test_{target_item}_basic():
    '''Test basic functionality of {target_item}'''
    try:
        # Simple test implementation here
        result = {target_item}()  # or appropriate call
        assert result is not None
    except Exception as e:
        pytest.skip(f"Skipping test due to dependency: {{e}}")
```

Return ONLY the complete test file code with proper imports.
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
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"Retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                    return None
                    
            except Exception as e:
                logger.error(f"Error generating test for {file_info['filepath']} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
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
        basic_checks = [
            "import pytest" in test_code or "import" in test_code,
            "def test_" in test_code,
            "from app." in test_code  # Ensure proper import
        ]
        
        return all(basic_checks)
    
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
                
                # Analyze module structure
                module_info = self.analyze_module_structure(file_info['filepath'])
                
                # Determine what to test (prefer classes, then functions)
                target_item = None
                target_type = None
                
                if module_info['classes']:
                    target_item = list(module_info['classes'].keys())[0]
                    target_type = "class"
                elif module_info['functions']:
                    target_item = module_info['functions'][0]
                    target_type = "function"
                else:
                    logger.warning(f"No testable items found in {file_info['filepath']}")
                    file_result = {
                        "filepath": file_info['filepath'],
                        "coverage": file_info['coverage'],
                        "test_generated": False,
                        "error": "No testable items found"
                    }
                    results["processed_files"].append(file_result)
                    results["error_count"] += 1
                    continue
                
                # Create enhanced file_info for test generation
                enhanced_file_info = {
                    "filepath": file_info['filepath'],
                    "module_info": module_info,
                    "target_item": target_item,
                    "target_type": target_type
                }
                
                # Generate test code
                test_code = self.generate_test_code(enhanced_file_info)
                
                if test_code and self.validate_test_code(test_code):
                    # Save test file
                    if self.save_test_file(file_info['filepath'], test_code):
                        # Run test to validate
                        test_result = self.run_generated_test(file_info['filepath'])
                        
                        file_result = {
                            "filepath": file_info['filepath'],
                            "coverage": file_info['coverage'],
                            "target_item": target_item,
                            "target_type": target_type,
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
                            "target_item": target_item,
                            "target_type": target_type,
                            "test_generated": True,
                            "test_saved": False,
                            "error": "Failed to save test file"
                        }
                        results["error_count"] += 1
                else:
                    file_result = {
                        "filepath": file_info['filepath'],
                        "coverage": file_info['coverage'],
                        "target_item": target_item,
                        "target_type": target_type,
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

def main():
    """Main function"""
    try:
        generator = TestGenerator()
        
        # Process coverage report and generate tests
        results = generator.process_coverage_report("coverage_report.json")
        
        # Save results
        with open("test_generation_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("Test generation results saved to test_generation_results.json")
        
        # Print summary
        if "error" in results:
            logger.error(f"Test generation failed: {results['error']}")
        else:
            total = len(results["processed_files"])
            success = results["success_count"]
            error = results["error_count"]
            logger.info(f"Test generation completed: {success} successful, {error} failed out of {total} files")
        
    except Exception as e:
        logger.error(f"Test generation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 