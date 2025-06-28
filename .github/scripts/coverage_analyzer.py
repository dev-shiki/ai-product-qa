#!/usr/bin/env python3
"""
Script untuk menganalisis coverage dan mengidentifikasi modul dengan coverage terendah
"""

import os
import sys
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoverageAnalyzer:
    def __init__(self, source_dir: str = "app", test_dir: str = "tests"):
        self.source_dir = Path(source_dir)
        self.test_dir = Path(test_dir)
        self.coverage_file = Path(".coverage")
        self.xml_file = Path("coverage.xml")
        
    def run_coverage(self) -> bool:
        """Menjalankan coverage test menggunakan coverage CLI (seperti codecov workflow)"""
        try:
            # Step 1: Run tests with coverage
            logger.info("Running tests with coverage...")
            cmd_run = [
                "coverage", "run", 
                "--source=" + str(self.source_dir),
                "-m", "pytest", 
                str(self.test_dir),
                "-v"
            ]
            
            logger.info(f"Running coverage command: {' '.join(cmd_run)}")
            result_run = subprocess.run(cmd_run, capture_output=True, text=True, timeout=300)  # 5 minutes timeout
            
            if result_run.returncode != 0:
                logger.warning(f"Coverage run had issues: {result_run.stderr}")
                # Continue anyway to check if coverage data was generated
            
            # Step 2: Generate coverage report
            logger.info("Generating coverage report...")
            cmd_report = ["coverage", "report", "-m"]
            result_report = subprocess.run(cmd_report, capture_output=True, text=True, timeout=60)
            
            if result_report.returncode == 0:
                logger.info("Coverage report generated successfully")
                logger.info(f"Report output:\n{result_report.stdout}")
            else:
                logger.warning(f"Coverage report generation had issues: {result_report.stderr}")
            
            # Step 3: Generate XML report
            logger.info("Generating XML coverage report...")
            cmd_xml = ["coverage", "xml"]
            result_xml = subprocess.run(cmd_xml, capture_output=True, text=True, timeout=60)
            
            if result_xml.returncode == 0:
                logger.info("Coverage XML generated successfully")
                if self.xml_file.exists():
                    logger.info(f"XML file created: {self.xml_file}")
                    return True
                else:
                    logger.error("XML file not found after generation")
                    return False
            else:
                logger.error(f"XML generation failed: {result_xml.stderr}")
                    return False
            
        except subprocess.TimeoutExpired:
            logger.error("Coverage analysis timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Error running coverage: {e}")
            return False
    
    def parse_coverage_xml(self) -> Dict[str, float]:
        """Parse coverage XML dan return dict dengan file dan coverage percentage"""
        if not self.xml_file.exists():
            logger.error("Coverage XML file not found")
            return {}
            
        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
            
            coverage_data = {}
            
            # Parse coverage data from XML
            for package in root.findall(".//package"):
                package_name = package.get("name", "")
                if package_name:
                    # Convert absolute paths to relative paths
                    if package_name.startswith("/"):
                        package_name = package_name[1:]
                    
                    # Get line rate for the package
                    line_rate = package.get("line-rate", "0")
                    try:
                        lines_covered = float(line_rate) * 100
                        coverage_data[package_name] = lines_covered
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid line-rate for {package_name}: {line_rate}")
                        coverage_data[package_name] = 0.0
                
                # Also check individual classes within packages
                for class_elem in package.findall(".//class"):
                    filename = class_elem.get("filename", "")
                    if filename:
                        # Convert to relative path
                        if filename.startswith("/"):
                            filename = filename[1:]
                        
                        # Get coverage percentage
                        line_rate = class_elem.get("line-rate", "0")
                        try:
                            lines_covered = float(line_rate) * 100
                            coverage_data[filename] = lines_covered
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid line-rate for {filename}: {line_rate}")
                            coverage_data[filename] = 0.0
            
            # If no data found, try alternative parsing
            if not coverage_data:
                logger.warning("No coverage data found in XML, attempting alternative parsing")
                coverage_data = self._parse_coverage_alternative()
                        
            logger.info(f"Parsed coverage for {len(coverage_data)} files")
            return coverage_data
            
        except Exception as e:
            logger.error(f"Error parsing coverage XML: {e}")
            return self._parse_coverage_alternative()
    
    def _parse_coverage_alternative(self) -> Dict[str, float]:
        """Alternative parsing menggunakan coverage report terminal output"""
        try:
            # Get coverage from terminal output
            cmd = ["coverage", "report", "-m"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            coverage_data = {}
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    # Parse lines like "app/file.py                   10      8    20%   8-10"
                    if 'app/' in line and '%' in line:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            filename = parts[0]
                            try:
                                coverage_str = parts[-2].replace('%', '')  # Second to last part
                                coverage = float(coverage_str)
                                coverage_data[filename] = coverage
                            except (ValueError, IndexError):
                                continue
            
            return coverage_data
            
        except Exception as e:
            logger.error(f"Alternative parsing failed: {e}")
            return {}
    
    def find_lowest_coverage_files(self, coverage_data: Dict[str, float], limit: int = 5) -> List[Tuple[str, float]]:
        """Mencari file dengan coverage terendah"""
        if not coverage_data:
            return []
            
        # Filter hanya file Python dengan path yang benar dan coverage < 100%
        python_files = []
        for filepath, coverage in coverage_data.items():
            # Skip directories and non-Python files
            if not filepath.endswith('.py'):
                continue
                
            # Convert relative paths to app/ format
            if filepath.startswith('app/'):
                normalized_path = filepath
            elif '/' in filepath or '\\' in filepath:
                # Handle paths like "api/products.py" -> "app/api/products.py"
                normalized_path = f"app/{filepath}"
            else:
                # Handle single file names like "main.py" -> "app/main.py"
                normalized_path = f"app/{filepath}"
            
            # Only include files with coverage < 100% and > 0%
            if 0 < coverage < 100:
                python_files.append((normalized_path, coverage))
        
        # Sort by coverage (ascending - lowest first)
        sorted_files = sorted(python_files, key=lambda x: x[1])
        
        logger.info(f"Found {len(sorted_files)} Python files with low coverage (< 100%)")
        
        return sorted_files[:limit]
    
    def get_file_content(self, filepath: str) -> Optional[str]:
        """Mengambil content dari file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return None
    
    def get_existing_test(self, filepath: str) -> Optional[str]:
        """Mencari test file yang sudah ada"""
        # Convert app/file.py to tests/test_file.py
        relative_path = filepath.replace('app/', '')
        test_file = self.test_dir / f"test_{relative_path}"
        
        if test_file.exists():
            return self.get_file_content(str(test_file))
        
        return None
    
    def analyze_and_generate_report(self) -> Dict:
        """Main function untuk analyze coverage dan generate report"""
        logger.info("Starting coverage analysis...")
        
        # Run coverage using coverage CLI
        if not self.run_coverage():
            return {"error": "Failed to run coverage"}
        
        # Parse coverage data
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            logger.warning("No coverage data found in XML, trying alternative method")
            # Try to get coverage from .coverage file directly
            coverage_data = self._parse_coverage_alternative()
            
        if not coverage_data:
            return {"error": "No coverage data found"}
        
        # Find lowest coverage files
        lowest_coverage = self.find_lowest_coverage_files(coverage_data)
        
        # Prepare report
        report = {
            "timestamp": str(Path.cwd()),
            "total_files": len(coverage_data),
            "coverage_data": coverage_data,
            "lowest_coverage_files": []
        }
        
        for filepath, coverage in lowest_coverage:
            file_info = {
                "filepath": filepath,
                "coverage": coverage,
                "content": self.get_file_content(filepath),
                "existing_test": self.get_existing_test(filepath)
            }
            report["lowest_coverage_files"].append(file_info)
        
        logger.info(f"Analysis complete. Found {len(lowest_coverage)} files with low coverage")
        return report

def main():
    """Main function"""
    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_and_generate_report()
    
    # Save report to JSON file
    with open("coverage_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("Coverage report saved to coverage_report.json")
    
    if "error" in report:
        logger.error(f"Analysis failed: {report['error']}")
        sys.exit(1)
    
    # Print summary
    print("\n=== COVERAGE ANALYSIS SUMMARY ===")
    print(f"Total files analyzed: {report['total_files']}")
    print("\nLowest coverage files:")
    for file_info in report["lowest_coverage_files"]:
        print(f"  {file_info['filepath']}: {file_info['coverage']:.1f}%")

if __name__ == "__main__":
    main() 