#!/usr/bin/env python3
"""
Simple launcher for the Mini Search Engine
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and show the result."""
    print(f"\n{description}")
    print("=" * 50)
    try:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🔍 MINI SEARCH ENGINE LAUNCHER")
    print("=" * 40)
    
    python_exe = r"C:/Users/Dell/AppData/Local/Programs/Python/Python313/python.exe"
    
    print("\nChoose an option:")
    print("1. Start Web Interface (if you have articles)")
    print("2. Crawl TONS of articles (recommended first)")
    print("3. Test crawler (small sample)")
    print("4. Advanced Search")
    print("5. Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        print("\n🌐 Starting web interface...")
        print("Visit http://localhost:5000")
        subprocess.run(f'"{python_exe}" web_search.py')
        
    elif choice == '2':
        print("\n🚀 Starting mass crawler...")
        print("This will collect thousands of articles!")
        print("Press Ctrl+C to stop when you have enough.")
        subprocess.run(f'"{python_exe}" mass_crawler.py')
        
    elif choice == '3':
        print("\n🧪 Running test crawler...")
        subprocess.run(f'"{python_exe}" test_crawler.py')
        
    elif choice == '4':
        print("\n🔬 Starting advanced search...")
        subprocess.run(f'"{python_exe}" advanced_search.py')
        
    else:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
