#!/usr/bin/env python3
"""
Simple wrapper to run tests from the tests subpackage.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the test runner from the tests subpackage."""
    test_runner_path = Path(__file__).parent / "tests" / "run_tests.py"
    
    if not test_runner_path.exists():
        print(f"❌ Test runner not found: {test_runner_path}")
        sys.exit(1)
    
    # Pass all arguments to the test runner
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    try:
        result = subprocess.run([sys.executable, str(test_runner_path)] + args)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n👋 Test run interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 