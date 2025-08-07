#!/usr/bin/env python3
"""
VectorCAST SI Report Generator

This script automates the process of generating various reports and test scripts 
for a given unit using VectorCAST. It provides a streamlined workflow for 
software integration testing and reporting.

Author: Your Name
Version: 2.0.0
License: MIT
"""

import os
import sys
import re
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorcast_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class VectorCastConfig:
    """Configuration class for VectorCAST report generation"""
    unit_name: str
    env_file: str
    output_directory: str
    compound_test_cases: bool = False
    vectorcast_dir: Optional[str] = None


class VectorCastError(Exception):
    """Custom exception for VectorCAST related errors"""
    pass


class ReportGenerator:
    """
    Main class for generating VectorCAST SI reports
    
    This class handles the automation of VectorCAST report generation,
    including folder creation, environment parsing, and report execution.
    """
    
    def __init__(self, config: VectorCastConfig):
        """
        Initialize the ReportGenerator
        
        Args:
            config: VectorCastConfig object containing all necessary configuration
        """
        self.config = config
        self.vectorcast_dir = self._get_vectorcast_directory()
        self.reports_generated = []
        
        logger.info(f"Initializing ReportGenerator for unit: {config.unit_name}")
    
    def _get_vectorcast_directory(self) -> str:
        """
        Get VectorCAST installation directory
        
        Returns:
            str: Path to VectorCAST installation directory
            
        Raises:
            VectorCastError: If VECTORCAST_DIR environment variable is not set
        """
        vectorcast_dir = (
            self.config.vectorcast_dir or 
            os.environ.get('VECTORCAST_DIR')
        )
        
        if not vectorcast_dir:
            raise VectorCastError(
                "VECTORCAST_DIR environment variable not set. "
                "Please ensure VectorCAST is properly installed."
            )
        
        if not Path(vectorcast_dir).exists():
            raise VectorCastError(
                f"VectorCAST directory does not exist: {vectorcast_dir}"
            )
        
        logger.info(f"Using VectorCAST directory: {vectorcast_dir}")
        return vectorcast_dir
    
    def create_folder(self, base_path: str, folder_name: str) -> str:
        """
        Create a folder and return its path
        
        Args:
            base_path: Base directory path
            folder_name: Name of the folder to create
            
        Returns:
            str: Full path to the created folder
        """
        folder_path = Path(base_path) / folder_name
        
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified folder: {folder_path}")
            return str(folder_path)
        except OSError as e:
            logger.error(f"Failed to create folder {folder_path}: {e}")
            raise VectorCastError(f"Could not create folder: {folder_path}")
    
    def generate_report_path(self, main_path: str, unit_name: str, 
                           report_type: str) -> str:
        """
        Generate a report path based on unit name and report type
        
        Args:
            main_path: Base path for reports
            unit_name: Name of the unit being tested
            report_type: Type of report (e.g., 'html', 'xml', 'csv')
            
        Returns:
            str: Full path for the report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{unit_name}_{report_type}_{timestamp}.{report_type}"
        return str(Path(main_path) / report_filename)
    
    def extract_strings_from_env(self, env_file_path: str) -> Dict[str, str]:
        """
        Extract specific strings from the VectorCAST environment file
        
        Args:
            env_file_path: Path to the environment file
            
        Returns:
            Dict containing extracted configuration values
            
        Raises:
            VectorCastError: If the environment file cannot be read or parsed
        """
        env_path = Path(env_file_path)
        
        if not env_path.exists():
            raise VectorCastError(f"Environment file not found: {env_file_path}")
        
        extracted_data = {}
        
        try:
            with open(env_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Extract common VectorCAST environment variables
                patterns = {
                    'compiler': r'COMPILER:\s*(.+)',
                    'coverage_type': r'COVERAGE_TYPE:\s*(.+)',
                    'unit_directory': r'UNIT_DIRECTORY:\s*(.+)',
                    'search_list': r'SEARCH_LIST:\s*(.+)',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        extracted_data[key] = match.group(1).strip()
                        logger.debug(f"Extracted {key}: {extracted_data[key]}")
                
                logger.info(f"Successfully parsed environment file: {env_file_path}")
                
        except IOError as e:
            logger.error(f"Failed to read environment file {env_file_path}: {e}")
            raise VectorCastError(f"Could not read environment file: {env_file_path}")
        
        return extracted_data
    
    def execute_vectorcast_command(self, command: List[str], 
                                 description: str) -> Tuple[bool, str]:
        """
        Execute a VectorCAST command and return the result
        
        Args:
            command: List of command parts to execute
            description: Description of the command for logging
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            logger.info(f"Executing: {description}")
            logger.debug(f"Command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True
            )
            
            logger.info(f"Successfully completed: {description}")
            return True, result.stdout
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out: {description}"
            logger.error(error_msg)
            return False, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {description}\nError: {e.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Unexpected error executing {description}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def generate_coverage_report(self, output_path: str) -> bool:
        """
        Generate coverage report using VectorCAST
        
        Args:
            output_path: Path where the coverage report should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = [
            os.path.join(self.vectorcast_dir, 'clicast'),
            '--coverage',
            '--environment', self.config.env_file,
            '--output', output_path,
            '--format', 'html'
        ]
        
        success, output = self.execute_vectorcast_command(
            command, 
            f"Generate coverage report: {output_path}"
        )
        
        if success:
            self.reports_generated.append(('Coverage Report', output_path))
            
        return success
    
    def generate_test_results_report(self, output_path: str) -> bool:
        """
        Generate test results report using VectorCAST
        
        Args:
            output_path: Path where the test results report should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = [
            os.path.join(self.vectorcast_dir, 'clicast'),
            '--test-results',
            '--environment', self.config.env_file,
            '--output', output_path,
            '--format', 'xml'
        ]
        
        success, output = self.execute_vectorcast_command(
            command,
            f"Generate test results report: {output_path}"
        )
        
        if success:
            self.reports_generated.append(('Test Results Report', output_path))
            
        return success
    
    def generate_metrics_report(self, output_path: str) -> bool:
        """
        Generate metrics report using VectorCAST
        
        Args:
            output_path: Path where the metrics report should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        command = [
            os.path.join(self.vectorcast_dir, 'clicast'),
            '--metrics',
            '--environment', self.config.env_file,
            '--output', output_path,
            '--format', 'csv'
        ]
        
        success, output = self.execute_vectorcast_command(
            command,
            f"Generate metrics report: {output_path}"
        )
        
        if success:
            self.reports_generated.append(('Metrics Report', output_path))
            
        return success
    
    def generate_compound_test_cases(self, output_path: str) -> bool:
        """
        Generate compound test cases if requested
        
        Args:
            output_path: Path where compound test cases should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.config.compound_test_cases:
            logger.info("Compound test cases not requested, skipping...")
            return True
        
        command = [
            os.path.join(self.vectorcast_dir, 'clicast'),
            '--compound-tests',
            '--environment', self.config.env_file,
            '--output', output_path
        ]
        
        success, output = self.execute_vectorcast_command(
            command,
            f"Generate compound test cases: {output_path}"
        )
        
        if success:
            self.reports_generated.append(('Compound Test Cases', output_path))
            
        return success
    
    def generate_summary_report(self, output_path: str) -> None:
        """
        Generate a summary report of all generated reports
        
        Args:
            output_path: Path where the summary should be saved
        """
        summary_content = [
            "# VectorCAST SI Report Generation Summary",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Unit Name: {self.config.unit_name}",
            f"Environment File: {self.config.env_file}",
            f"Compound Test Cases: {'Yes' if self.config.compound_test_cases else 'No'}",
            "",
            "## Generated Reports:",
            ""
        ]
        
        for report_name, report_path in self.reports_generated:
            summary_content.append(f"- **{report_name}**: `{report_path}`")
        
        summary_content.extend([
            "",
            "## Configuration Details:",
            f"- VectorCAST Directory: {self.vectorcast_dir}",
            f"- Output Directory: {self.config.output_directory}",
            "",
            "---",
            "*Generated by VectorCAST SI Report Generator v2.0.0*"
        ])
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_content))
            logger.info(f"Summary report generated: {output_path}")
        except IOError as e:
            logger.error(f"Failed to write summary report: {e}")
    
    def run(self) -> bool:
        """
        Main execution method for generating all reports
        
        Returns:
            bool: True if all reports were generated successfully
        """
        logger.info("Starting VectorCAST SI report generation process...")
        
        try:
            # Create main output directory
            output_dir = self.create_folder(
                os.getcwd(), 
                self.config.output_directory
            )
            
            # Extract environment configuration
            env_data = self.extract_strings_from_env(self.config.env_file)
            logger.info(f"Environment data extracted: {list(env_data.keys())}")
            
            # Generate various reports
            reports_to_generate = [
                (
                    self.generate_coverage_report,
                    self.generate_report_path(output_dir, self.config.unit_name, 'coverage.html')
                ),
                (
                    self.generate_test_results_report,
                    self.generate_report_path(output_dir, self.config.unit_name, 'test_results.xml')
                ),
                (
                    self.generate_metrics_report,
                    self.generate_report_path(output_dir, self.config.unit_name, 'metrics.csv')
                ),
                (
                    self.generate_compound_test_cases,
                    self.generate_report_path(output_dir, self.config.unit_name, 'compound_tests')
                )
            ]
            
            success_count = 0
            total_reports = len(reports_to_generate)
            
            for report_func, output_path in reports_to_generate:
                if report_func(output_path):
                    success_count += 1
                else:
                    logger.warning(f"Failed to generate report: {output_path}")
            
            # Generate summary report
            summary_path = os.path.join(output_dir, 'generation_summary.md')
            self.generate_summary_report(summary_path)
            
            success_rate = (success_count / total_reports) * 100
            logger.info(f"Report generation completed. Success rate: {success_rate:.1f}% ({success_count}/{total_reports})")
            
            return success_count == total_reports
            
        except Exception as e:
            logger.error(f"Fatal error during report generation: {e}")
            return False


def get_user_input() -> VectorCastConfig:
    """
    Get user input for report generation configuration
    
    Returns:
        VectorCastConfig: Configuration object with user preferences
    """
    print("=" * 60)
    print("VectorCAST SI Report Generator v2.0.0")
    print("=" * 60)
    
    # Detect unit name from current directory or ask user
    current_dir = Path.cwd().name
    unit_name = input(f"Enter unit name (default: {current_dir}): ").strip() or current_dir
    
    # Look for .env file
    env_files = list(Path.cwd().glob("*.env"))
    if env_files:
        default_env = env_files[0].name
        env_file = input(f"Environment file (default: {default_env}): ").strip() or default_env
    else:
        env_file = input("Environment file (.env): ").strip()
        if not env_file.endswith('.env'):
            env_file += '.env'
    
    # Ask for compound test cases
    compound_choice = input("Generate compound test cases? (y/N): ").strip().lower()
    compound_test_cases = compound_choice in ['y', 'yes', '1']
    
    output_directory = f"{unit_name}_VCAST_SI_Results"
    
    return VectorCastConfig(
        unit_name=unit_name,
        env_file=env_file,
        output_directory=output_directory,
        compound_test_cases=compound_test_cases
    )


def main():
    """
    Main entry point for the VectorCAST SI Report Generator
    """
    try:
        # Get configuration from user
        config = get_user_input()
        
        # Create and run the report generator
        generator = ReportGenerator(config)
        success = generator.run()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ All reports generated successfully!")
            print(f"📁 Output directory: {config.output_directory}")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("⚠️  Some reports failed to generate. Check the logs for details.")
            print("=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(130)
        
    except VectorCastError as e:
        logger.error(f"VectorCAST error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
