#!/usr/bin/env python3
"""
Test runner for skillpilot tests.

This script can run all tests or specific categories of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestRunner:
    """Test runner for skillpilot tests."""
    
    def __init__(self):
        self.test_categories = {
            "core": [
                "test_document_splitting.py",
                "test_real_structure.py", 
                "test_modular_extract.py"
            ],
            "graph": [
                "test_graph_data_in_results.py",
                "analyze_graph_data.py"
            ],
            "search": [
                "test_graph_enhanced_search.py"
            ],
            "llm": [
                "test_llm_memory_fix.py",
                "test_memory_optimization.py",
                "test_model_instance_balancing.py",
                "test_sequential_model_balancing.py",
                "test_sync_llm.py",
                "test_llm_server.py"
            ],
            "data": [
                "test_chunk_cross_reference.py",
                "test_duplicate_detection.py",
                "test_file_saving.py",
                "test_json_repair.py"
            ],
            "database": [
                "test_schema_alignment.py",
                "test_entity_processing.py"
            ],
            "all": []  # Will be populated with all tests
        }
        
        # Populate "all" category
        for category_tests in self.test_categories.values():
            if category_tests:  # Skip "all" category itself
                self.test_categories["all"].extend(category_tests)
        
        # Remove duplicates from "all"
        self.test_categories["all"] = list(set(self.test_categories["all"]))
    
    def list_tests(self) -> None:
        """List all available tests by category."""
        logger.info("📋 Available Tests by Category:")
        
        for category, tests in self.test_categories.items():
            if category == "all":
                continue
            logger.info(f"\n🔹 {category.upper()} Tests ({len(tests)}):")
            for test in tests:
                logger.info(f"   • {test}")
        
        logger.info(f"\n🔹 ALL Tests ({len(self.test_categories['all'])}):")
        for test in sorted(self.test_categories["all"]):
            logger.info(f"   • {test}")
    
    def run_test(self, test_file: str) -> bool:
        """Run a single test file."""
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            logger.error(f"❌ Test file not found: {test_file}")
            return False
        
        logger.info(f"🧪 Running test: {test_file}")
        
        try:
            # Run the test as a subprocess
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent  # Project root
            )
            
            if result.returncode == 0:
                logger.success(f"✅ {test_file} passed")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ {test_file} failed")
                if result.stderr:
                    logger.error(f"Error: {result.stderr.strip()}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.strip()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error running {test_file}: {e}")
            return False
    
    def run_category(self, category: str) -> Dict[str, Any]:
        """Run all tests in a category."""
        if category not in self.test_categories:
            logger.error(f"❌ Unknown category: {category}")
            return {"success": False, "passed": 0, "failed": 0, "total": 0}
        
        tests = self.test_categories[category]
        logger.info(f"🚀 Running {category.upper()} tests ({len(tests)} tests)")
        
        passed = 0
        failed = 0
        
        for test in tests:
            if self.run_test(test):
                passed += 1
            else:
                failed += 1
        
        total = passed + failed
        
        logger.info(f"\n📊 {category.upper()} Results:")
        logger.info(f"   ✅ Passed: {passed}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   📈 Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "   📈 Success Rate: N/A")
        
        return {
            "success": failed == 0,
            "passed": passed,
            "failed": failed,
            "total": total
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests."""
        return self.run_category("all")
    
    def run_interactive(self) -> None:
        """Run tests interactively."""
        logger.info("🎯 Interactive Test Runner")
        logger.info("=" * 40)
        
        while True:
            print("\nAvailable options:")
            print("1. List all tests")
            print("2. Run core tests")
            print("3. Run graph tests")
            print("4. Run search tests")
            print("5. Run LLM tests")
            print("6. Run data processing tests")
            print("7. Run database tests")
            print("8. Run all tests")
            print("9. Run specific test")
            print("10. Exit")
            
            choice = input("\nEnter your choice (1-10): ").strip()
            
            if choice == "1":
                self.list_tests()
            elif choice == "2":
                self.run_category("core")
            elif choice == "3":
                self.run_category("graph")
            elif choice == "4":
                self.run_category("search")
            elif choice == "5":
                self.run_category("llm")
            elif choice == "6":
                self.run_category("data")
            elif choice == "7":
                self.run_category("database")
            elif choice == "8":
                self.run_all_tests()
            elif choice == "9":
                test_name = input("Enter test filename: ").strip()
                if test_name:
                    self.run_test(test_name)
            elif choice == "10":
                logger.info("👋 Goodbye!")
                break
            else:
                logger.warning("❌ Invalid choice. Please enter 1-10.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test runner for skillpilot tests")
    parser.add_argument(
        "--category", "-c",
        choices=["core", "graph", "search", "llm", "data", "database", "all"],
        help="Run tests in a specific category"
    )
    parser.add_argument(
        "--test", "-t",
        help="Run a specific test file"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tests"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run tests interactively"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.list:
        runner.list_tests()
    elif args.interactive:
        runner.run_interactive()
    elif args.test:
        success = runner.run_test(args.test)
        sys.exit(0 if success else 1)
    elif args.category:
        result = runner.run_category(args.category)
        sys.exit(0 if result["success"] else 1)
    else:
        # Default: run all tests
        result = runner.run_all_tests()
        sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main() 