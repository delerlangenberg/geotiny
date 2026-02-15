#!/usr/bin/env python3
"""
Startup script for Geotiny web interface
Run this script to start the development server
"""

import os
import sys
import subprocess
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

def check_requirements():
    """Check if all requirements are installed"""
    print("Checking dependencies...")
    try:
        import flask
        import flask_socketio
        import numpy
        import scipy
        print("✓ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements-web.txt")
        return False


def check_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = script_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"✓ Logs directory: {logs_dir}")


def main():
    print("=" * 70)
    print("GEOTINY WEB INTERFACE - STARTUP")
    print("=" * 70)
    print()

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Check logs directory
    check_logs_directory()

    print()
    print("Starting Flask application...")
    print()
    print("Dashboard will be available at:")
    print("  http://localhost:5000/")
    print()
    print("API documentation:")
    print("  GET  /api/devices/status")
    print("  POST /api/spectrum/fft")
    print("  POST /api/spectrum/spectrogram")
    print("  GET  /api/global/earthquakes")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 70)
    print()

    try:
        # Import and run the app
        from app import socketio, app
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            allow_unsafe_werkzeug=True
        )
    except ImportError as e:
        print(f"Error importing app: {e}")
        print("\nMake sure you're in the web directory and dependencies are installed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
