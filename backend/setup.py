#!/usr/bin/env python3
"""
Setup script for Lemlist Data Puller
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ["lemlist_export", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print("🚀 Setting up Lemlist Data Puller...")
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Create directories
    create_directories()
    
    print("\n✅ Setup completed successfully!")
    print("\nTo run the data puller:")
    print("  python main.py")
    
    return 0

if __name__ == "__main__":
    exit(main())
