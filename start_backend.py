#!/usr/bin/env python3
"""
Simple startup script for the Forex Calendar Backend
This script provides an easy way to start the backend server
"""

import sys
import os
import subprocess
import socket
from pathlib import Path

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import redis
        import botasaurus
        import sentence_transformers
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def main():
    print("Forex Calendar Backend Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Find available port
    port = find_available_port(8000)
    if port is None:
        print("✗ No available ports found in range 8000-8010")
        sys.exit(1)
    
    print(f"✓ Starting server on port {port}")
    print(f"✓ Frontend can be accessed at: http://localhost:{port}")
    print(f"✓ API documentation at: http://localhost:{port}/docs")
    print("=" * 40)
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "backend.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"✗ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()



