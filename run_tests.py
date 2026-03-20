"""
Test runner for SatarkSetu
Runs all pytest tests and generates report
"""
import subprocess
import sys

def run_tests(args=None):
    """Run pytest with optional arguments"""
    cmd = ['pytest']
    
    if args:
        cmd.extend(args)
    else:
        # Default: run all tests with coverage
        cmd.extend([
            'tests/',
            '-v',
            '--tb=short',
            '--color=yes'
        ])
    
    print("🧪 Running SatarkSetu Test Suite\n")
    print(f"Command: {' '.join(cmd)}\n")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    # Pass any command line arguments to pytest
    exit_code = run_tests(sys.argv[1:] if len(sys.argv) > 1 else None)
    sys.exit(exit_code)
