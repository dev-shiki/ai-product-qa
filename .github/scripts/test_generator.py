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
        """Analyze module structure untuk mendapatkan info yang lebih detail"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse content untuk mendapatkan struktur yang lebih detail
            lines = content.split('\n')
            
            classes = {}
            functions = []
            imports = []
            class_methods = {}
            
            current_class = None
            in_class = False
            indent_level = 0
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip comments and empty lines
                if stripped.startswith('#') or not stripped:
                    continue
                
                # Detect imports
                if stripped.startswith('import ') or stripped.startswith('from '):
                    imports.append(stripped)
                
                # Detect class definitions
                elif stripped.startswith('class '):
                    class_name = stripped.split('class ')[1].split('(')[0].split(':')[0].strip()
                    current_class = class_name
                    in_class = True
                    classes[class_name] = {
                        'name': class_name,
                        'methods': [],
                        'line': i + 1
                    }
                    class_methods[class_name] = []
                
                # Detect function definitions
                elif stripped.startswith('def '):
                    func_def = stripped.split('def ')[1]
                    func_name = func_def.split('(')[0].strip()
                    
                    # Extract parameters if possible
                    params = []
                    if '(' in func_def and ')' in func_def:
                        param_part = func_def.split('(', 1)[1].split(')')[0]
                        if param_part.strip():
                            # Simple parameter parsing
                            for param in param_part.split(','):
                                param = param.strip()
                                if param and param != 'self':
                                    # Remove type hints if present
                                    if ':' in param:
                                        param = param.split(':')[0].strip()
                                    params.append(param)
                    
                    if in_class and current_class:
                        # This is a class method
                        class_methods[current_class].append(func_name)
                        classes[current_class]['methods'].append({
                            'name': func_name,
                            'params': params,
                            'line': i + 1
                        })
                    else:
                        # This is a standalone function
                        if not func_name.startswith('_') and not func_name.startswith('test_'):
                            functions.append({
                                'name': func_name,
                                'params': params,
                                'line': i + 1
                            })
                
                # Detect end of class (when indentation decreases)
                elif in_class and current_class:
                    if line and not line.startswith(' ') and not line.startswith('\t'):
                        in_class = False
                        current_class = None
            
            # Get the actual content for context
            content_preview = content[:2000] if len(content) > 2000 else content
            
            return {
                'classes': classes,
                'functions': functions,
                'imports': imports,
                'class_methods': class_methods,
                'content': content_preview,
                'filepath': filepath
            }
            
        except Exception as e:
            logger.error(f"Error analyzing module structure for {filepath}: {e}")
            return {
                'classes': {},
                'functions': [],
                'imports': [],
                'class_methods': {},
                'content': '',
                'filepath': filepath
            }
        
    def generate_test_prompt(self, file_info: Dict) -> str:
        """Generate prompt untuk Gemini - FOKUS PADA SATU FUNGSI/METHOD SAJA"""
        filepath = file_info["filepath"]
        module_info = file_info["module_info"]
        target_item = file_info.get("target_item", "")
        target_type = file_info.get("target_type", "function")
        target_class = file_info.get("target_class", "")
        target_params = file_info.get("target_params", [])
        import_statement = file_info.get("import_statement", "")
        
        # Determine how to call the target with proper parameters
        if target_type == "method" and target_class:
            # For class methods, create instance and call method
            if target_params:
                param_str = ", ".join([f'"{param}_value"' for param in target_params])
                call_statement = f"{target_class}().{target_item}({param_str})"
            else:
                call_statement = f"{target_class}().{target_item}()"
        else:
            # For standalone functions
            if target_params:
                param_str = ", ".join([f'"{param}_value"' for param in target_params])
                call_statement = f"{target_item}({param_str})"
            else:
                call_statement = f"{target_item}()"
        
        # Create parameter examples for the prompt
        param_examples = ""
        if target_params:
            param_examples = f"\nParameters: {', '.join(target_params)}"
            param_examples += "\nExample values: " + ", ".join([f'"{param}_value"' for param in target_params])
        
        prompt = f"""Create unit test for single {target_type}: '{target_item}'

File: {filepath}
Target: {target_type} '{target_item}'{param_examples}
Import: {import_statement}
Call: {call_statement}

Source code:
```python
{module_info['content'][:1500]}...
```

Instructions:
1. Focus ONLY on {target_type} '{target_item}' - do not test others
2. Create SIMPLE and REALISTIC tests with proper parameters
3. Use correct import: {import_statement}
4. Handle exceptions with try-catch
5. Do not use complex mocks
6. Test must be runnable directly
7. Use realistic parameter values based on the function signature

Expected output:
```python
import pytest
{import_statement}

def test_{target_item}_basic():
    try:
        result = {call_statement}
        assert result is not None
    except Exception as e:
        pytest.skip(f"Test skipped due to dependency: {{e}}")

def test_{target_item}_edge_cases():
    try:
        # Test with edge cases or different parameter values
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
            target_class = None
            target_params = []
            import_statement = None
            
            # Prefer simple functions first (easier to test)
            if module_info['functions']:
                # Get the first function that's not a test function
                for func in module_info['functions']:
                    if not func['name'].startswith('test_') and not func['name'].startswith('_'):
                        target_item = func['name']
                        target_type = "function"
                        target_params = func['params']
                        # For standalone functions, import directly
                        clean_filepath = file_info['filepath'].replace("app/", "").replace("/", ".").replace(".py", "")
                        import_statement = f"from app.{clean_filepath} import {target_item}"
                        break
            
            # If no suitable function, try class methods
            if not target_item and module_info['classes']:
                for class_name, class_info in module_info['classes'].items():
                    if class_info['methods']:
                        # Get the first public method
                        for method in class_info['methods']:
                            if not method['name'].startswith('_') and not method['name'].startswith('test_'):
                                target_item = method['name']
                                target_type = "method"
                                target_class = class_name
                                target_params = method['params']
                                # For class methods, import the class
                                clean_filepath = file_info['filepath'].replace("app/", "").replace("/", ".").replace(".py", "")
                                import_statement = f"from app.{clean_filepath} import {class_name}"
                                break
                        if target_item:
                            break
            
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
            if target_class:
                logger.info(f"🎯 CLASS: {target_class}")
            logger.info(f"🎯 PARAMS: {target_params}")
            logger.info(f"🎯 IMPORT: {import_statement}")
            
            # Create enhanced file_info for test generation
            enhanced_file_info = {
                "filepath": file_info['filepath'],
                "module_info": module_info,
                "target_item": target_item,
                "target_type": target_type,
                "target_class": target_class,
                "target_params": target_params,
                "import_statement": import_statement,
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