#!/usr/bin/env python3
"""
Setup script for MAC Cosmetics Scrapy Scraper with Splash

This script helps set up the environment for running the Scrapy scraper with Splash
for JavaScript rendering.

Author: AI Assistant
Date: 2024
"""

import subprocess
import sys
import time
import requests
import os

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Docker is installed")
            return True
        else:
            print("Docker is not installed or not running")
            return False
    except FileNotFoundError:
        print("Docker is not installed")
        return False

def check_splash_running():
    """Check if Splash is running on localhost:8050"""
    try:
        response = requests.get('http://localhost:8050', timeout=5)
        if response.status_code == 200:
            print("Splash is running on http://localhost:8050")
            return True
        else:
            print("Splash is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("Splash is not running on http://localhost:8050")
        return False

def start_splash():
    """Start Splash using Docker"""
    print("Starting Splash container...")
    try:
        # Stop any existing Splash container
        subprocess.run(['docker', 'stop', 'splash'], capture_output=True)
        subprocess.run(['docker', 'rm', 'splash'], capture_output=True)
        
        # Start new Splash container
        result = subprocess.run([
            'docker', 'run', '-d', '--name', 'splash', '-p', '8050:8050', 
            'scrapinghub/splash'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Splash container started successfully")
            print("Waiting for Splash to be ready...")
            
            # Wait for Splash to be ready
            for i in range(30):  # Wait up to 30 seconds
                if check_splash_running():
                    print("Splash is ready!")
                    return True
                time.sleep(1)
                print(f"Waiting... ({i+1}/30)")
            
            print("Splash failed to start properly")
            return False
        else:
            print(f"Failed to start Splash: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error starting Splash: {e}")
        return False

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements_scrapy.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Requirements installed successfully")
            return True
        else:
            print(f"Failed to install requirements: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error installing requirements: {e}")
        return False

def run_scraper():
    """Run the Scrapy scraper"""
    print("Starting MAC Cosmetics Scrapy Scraper...")
    try:
        result = subprocess.run([
            sys.executable, 'mac_scrapy_splash_scraper.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Scraper completed successfully!")
            return True
        else:
            print(f"Scraper failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running scraper: {e}")
        return False

def main():
    """Main setup function"""
    print("MAC Cosmetics Scrapy Scraper Setup")
    print("=" * 50)
    
    # Check Docker
    if not check_docker():
        print("\nTo install Docker:")
        print("   - Windows: Download from https://www.docker.com/products/docker-desktop")
        print("   - macOS: Download from https://www.docker.com/products/docker-desktop")
        print("   - Linux: Follow instructions at https://docs.docker.com/engine/install/")
        return False
    
    # Install requirements
    if not install_requirements():
        print("\nManual installation:")
        print("   pip install scrapy>=2.11.0 scrapy-splash>=0.8.0")
        return False
    
    # Check if Splash is running
    if not check_splash_running():
        print("\nStarting Splash...")
        if not start_splash():
            print("\nManual Splash setup:")
            print("   docker run -p 8050:8050 scrapinghub/splash")
            return False
    
    # Run scraper
    print("\nAll set! Running scraper...")
    return run_scraper()

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSetup and scraping completed successfully!")
    else:
        print("\nSetup or scraping failed. Please check the errors above.") 