#!/usr/bin/env python3
"""
Simple HTTP server for serving the TOBI frontend
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
PORT = 3001
DIRECTORY = "static"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve files from the static directory"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    """Start the frontend server"""
    # Change to the frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Check if static directory exists
    if not os.path.exists(DIRECTORY):
        print(f"Error: {DIRECTORY} directory not found")
        sys.exit(1)
    
    # Start the server
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🌐 TOBI Frontend Server starting...")
        print(f"📍 Serving at: http://localhost:{PORT}")
        print(f"📁 Directory: {os.path.abspath(DIRECTORY)}")
        print(f"🔗 Backend API: http://localhost:8000")
        print(f"🛑 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Frontend server stopped")

if __name__ == "__main__":
    main() 