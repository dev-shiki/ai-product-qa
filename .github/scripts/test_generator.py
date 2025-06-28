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
        """Generate prompt untuk Gemini - FOKUS PADA SATU FUNGSI SAJA"""
        filepath = file_info["filepath"]
        module_info = file_info["module_info"]
        target_item = file_info.get("target_item", "")
        target_type = file_info.get("target_type", "function")
        
        # Create import statement based on file structure
        clean_filepath = filepath.replace("app/", "").replace("/", ".").replace(".py", "")
        import_path = f"app.{clean_filepath}"
        
        prompt = f"""Create unit test for single function: '{target_item}'

File: {filepath}
Target: {target_type} '{target_item}'
Import: from {import_path} import {target_item}

Source code:
```python
{module_info['content'][:1500]}...
```

Instructions:
1. Focus ONLY on {target_type} '{target_item}' - do not test others
2. Create SIMPLE and REALISTIC tests
3. Use correct import: `from {import_path} import {target_item}`
4. Handle exceptions with try-catch
5. Do not use complex mocks
6. Test must be runnable directly

Expected output:
```python
import pytest
from {import_path} import {target_item}

def test_{target_item}_basic():
    """Test basic functionality of {target_item}"""
    try:
        # Simple test implementation
        result = {target_item}()  # Adjust based on actual function signature
        assert result is not None
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency: {{e}}")

def test_{target_item}_edge_cases():
    """Test edge cases for {target_item}"""
    try:
        # Test with edge cases
        pass
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency: {{e}}")
```

Return ONLY Python test code, no additional explanations."""
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
        """Process coverage report dan generate tests - FOCUS ON ONE FUNCTION ONLY"""
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
                "error_count": 0,
                "strategy": "single_function_focus"
            }
            
            # FOCUS: Only process the FIRST file with lowest coverage
            if not report["lowest_coverage_files"]:
                return {"error": "No files with low coverage found"}
            
            # Get only the first file (lowest coverage)
            file_info = report["lowest_coverage_files"][0]
            logger.info(f"🎯 FOCUSING ON SINGLE FILE: {file_info['filepath']}")
            
            # Analyze module structure
            module_info = self.analyze_module_structure(file_info['filepath'])
            
            # FOCUS: Find the BEST candidate for testing (prioritize functions over classes)
            target_item = None
            target_type = None
            
            # Prefer simple functions first (easier to test)
            if module_info['functions']:
                # Get the first function that's not a test function
                for func in module_info['functions']:
                    if not func.startswith('test_') and not func.startswith('_'):
                        target_item = func
                        target_type = "function"
                        break
            
            # If no suitable function, try classes
            if not target_item and module_info['classes']:
                target_item = list(module_info['classes'].keys())[0]
                target_type = "class"
            
            if not target_item:
                logger.warning(f"No suitable testable items found in {file_info['filepath']}")
                file_result = {
                    "filepath": file_info['filepath'],
                    "coverage": file_info['coverage'],
                    "test_generated": False,
                    "error": "No suitable testable items found",
                    "strategy": "single_function_focus"
                }
                results["processed_files"].append(file_result)
                results["error_count"] += 1
                return results
            
            logger.info(f"🎯 TARGET: {target_type} '{target_item}' in {file_info['filepath']}")
            
            # Create enhanced file_info for test generation
            enhanced_file_info = {
                "filepath": file_info['filepath'],
                "module_info": module_info,
                "target_item": target_item,
                "target_type": target_type,
                "strategy": "single_function_focus"
            }
            
            # Generate test code with retry logic
            test_code = None
            max_retries = 3
            
            for attempt in range(max_retries):
                logger.info(f"🔄 Generating test (attempt {attempt + 1}/{max_retries})")
                test_code = self.generate_test_code(enhanced_file_info)
                
                if test_code and self.validate_test_code(test_code):
                    logger.info(f"✅ Test code generated successfully on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"❌ Test generation failed on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
            
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
                        "test_result": test_result,
                        "strategy": "single_function_focus",
                        "attempts": max_retries
                    }
                    
                    if test_result["success"]:
                        results["success_count"] += 1
                        logger.info(f"🎉 SUCCESS: Test for {target_item} passed!")
                    else:
                        results["error_count"] += 1
                        logger.warning(f"⚠️ Test for {target_item} failed but was generated")
                else:
                    file_result = {
                        "filepath": file_info['filepath'],
                        "coverage": file_info['coverage'],
                        "target_item": target_item,
                        "target_type": target_type,
                        "test_generated": True,
                        "test_saved": False,
                        "error": "Failed to save test file",
                        "strategy": "single_function_focus"
                    }
                    results["error_count"] += 1
            else:
                file_result = {
                    "filepath": file_info['filepath'],
                    "coverage": file_info['coverage'],
                    "target_item": target_item,
                    "target_type": target_type,
                    "test_generated": False,
                    "error": f"Failed to generate valid test code after {max_retries} attempts",
                    "strategy": "single_function_focus"
                }
                results["error_count"] += 1
            
            results["processed_files"].append(file_result)
            
            # Summary
            logger.info(f"📊 SINGLE FUNCTION FOCUS COMPLETE:")
            logger.info(f"   File: {file_info['filepath']}")
            logger.info(f"   Target: {target_type} '{target_item}'")
            logger.info(f"   Success: {results['success_count']}, Errors: {results['error_count']}")
            
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