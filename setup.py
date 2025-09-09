#!/usr/bin/env python3
"""
Setup script for Mini Wikipedia Search Engine
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install required packages."""
    try:
        print("📦 Installing Python packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        return False

def test_mysql_connection():
    """Test MySQL connection."""
    try:
        # Try to connect with default settings
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='admin'  # Default from your current setup
        )
        if connection.is_connected():
            print("✅ MySQL connection successful")
            
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            # Check if our database exists
            db_exists = any('search_engine_db' in db for db in databases)
            if db_exists:
                print("✅ Database 'search_engine_db' found")
            else:
                print("⚠️  Database 'search_engine_db' not found - will be created automatically")
            
            cursor.close()
            connection.close()
            return True
    except Error as e:
        print(f"❌ MySQL connection failed: {e}")
        print("💡 Make sure MySQL is running and credentials are correct")
        return False

def create_config_file():
    """Create config file from template."""
    if not os.path.exists('config.py'):
        if os.path.exists('config_template.py'):
            import shutil
            shutil.copy('config_template.py', 'config.py')
            print("✅ Created config.py from template")
            print("💡 Please edit config.py with your actual database credentials")
        else:
            print("⚠️  config_template.py not found")
    else:
        print("✅ config.py already exists")

def main():
    """Main setup function."""
    print("🚀 Setting up Mini Wikipedia Search Engine...")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Install Packages", install_requirements),
        ("MySQL Connection", test_mysql_connection),
        ("Config File", create_config_file)
    ]
    
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            print(f"\n❌ Setup failed at: {name}")
            print("Please fix the issues above and run setup again.")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit config.py with your database credentials")
    print("2. Run: python mass_crawler.py (to collect articles)")
    print("3. Run: python web_search.py (to start web interface)")
    print("4. Visit: http://localhost:5000")
    print("\nOr use the launcher: python launcher.py")
    
    return True

if __name__ == "__main__":
    main()
