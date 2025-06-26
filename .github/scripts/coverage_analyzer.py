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
        """Menjalankan coverage test dan generate XML report"""
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest", 
                "--cov=" + str(self.source_dir),
                "--cov-report=xml",
                "--cov-report=term-missing",
                str(self.test_dir),
                "-v"
            ]
            
            logger.info(f"Running coverage command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # 2 minutes timeout
            
            if result.returncode != 0:
                logger.warning(f"Coverage run had issues: {result.stderr}")
                # Don't return False immediately, check if XML was generated
                if not self.xml_file.exists():
                    logger.error("Coverage XML file not generated")
                    return False
                
            logger.info("Coverage analysis completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Coverage analysis timed out after 2 minutes")
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
            
            # Try different XML structures
            for package in root.findall(".//package"):
                for class_elem in package.findall(".//class"):
                    filename = class_elem.get("filename", "")
                    if filename:
                        # Convert to relative path
                        if filename.startswith("/"):
                            filename = filename[1:]
                        
                        # Get coverage percentage - try different attributes
                        line_rate = class_elem.get("line-rate", "0")
                        try:
                            lines_covered = float(line_rate) * 100
                            coverage_data[filename] = lines_covered
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid line-rate for {filename}: {line_rate}")
                            coverage_data[filename] = 0.0
            
            # If no data found with class elements, try package level
            if not coverage_data:
                for package in root.findall(".//package"):
                    filename = package.get("name", "")
                    if filename:
                        if filename.startswith("/"):
                            filename = filename[1:]
                        
                        line_rate = package.get("line-rate", "0")
                        try:
                            lines_covered = float(line_rate) * 100
                            coverage_data[filename] = lines_covered
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid line-rate for {filename}: {line_rate}")
                            coverage_data[filename] = 0.0
            
            # If still no data, try to parse manually
            if not coverage_data:
                logger.warning("No coverage data found in XML, attempting manual parsing")
                coverage_data = self._parse_coverage_manual()
                        
            logger.info(f"Parsed coverage for {len(coverage_data)} files")
            return coverage_data
            
        except Exception as e:
            logger.error(f"Error parsing coverage XML: {e}")
            return self._parse_coverage_manual()
    
    def _parse_coverage_manual(self) -> Dict[str, float]:
        """Manual parsing jika XML parsing gagal"""
        try:
            # Try to get coverage from terminal output
            cmd = [
                "python", "-m", "pytest", 
                "--cov=" + str(self.source_dir),
                "--cov-report=term",
                str(self.test_dir),
                "-q"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            coverage_data = {}
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'app/' in line and '%' in line:
                        # Parse line like "app/file.py                   10      8    20%"
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            filename = parts[0]
                            try:
                                coverage_str = parts[-1].replace('%', '')
                                coverage = float(coverage_str)
                                coverage_data[filename] = coverage
                            except (ValueError, IndexError):
                                continue
            
            return coverage_data
            
        except Exception as e:
            logger.error(f"Manual parsing failed: {e}")
            return {}
    
    def find_lowest_coverage_files(self, coverage_data: Dict[str, float], limit: int = 5) -> List[Tuple[str, float]]:
        """Mencari file dengan coverage terendah"""
        if not coverage_data:
            return []
            
        # Filter hanya file Python dan sort berdasarkan coverage
        python_files = [(f, c) for f, c in coverage_data.items() 
                       if f.endswith('.py') and f.startswith('app/')]
        
        # Sort by coverage (ascending)
        sorted_files = sorted(python_files, key=lambda x: x[1])
        
        logger.info(f"Found {len(sorted_files)} Python files with coverage data")
        
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
        
        # Run coverage
        if not self.run_coverage():
            return {"error": "Failed to run coverage"}
        
        # Parse coverage data
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            return {"error": "No coverage data found"}
        
        # Find lowest coverage files
        lowest_coverage = self.find_lowest_coverage_files(coverage_data)
        
        # Prepare report
        report = {
            "timestamp": str(Path.cwd()),
            "total_files": len(coverage_data),
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