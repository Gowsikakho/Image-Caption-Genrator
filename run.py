#!/usr/bin/env python3
"""
Simple startup script for the Image Caption Generator
"""
import os
import sys

def main():
    # Set environment variables if not already set
    if not os.environ.get('FLASK_DEBUG'):
        os.environ['FLASK_DEBUG'] = 'false'
    
    if not os.environ.get('FLASK_HOST'):
        os.environ['FLASK_HOST'] = '127.0.0.1'
    
    if not os.environ.get('FLASK_PORT'):
        os.environ['FLASK_PORT'] = '5000'
    
    # Import and run the app
    try:
        from app import app
        print("Starting Image Caption Generator...")
        print(f"Server running at http://{os.environ.get('FLASK_HOST')}:{os.environ.get('FLASK_PORT')}")
        app.run(
            debug=os.environ.get('FLASK_DEBUG').lower() == 'true',
            host=os.environ.get('FLASK_HOST'),
            port=int(os.environ.get('FLASK_PORT'))
        )
    except ImportError as e:
        print(f"Error importing app: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()