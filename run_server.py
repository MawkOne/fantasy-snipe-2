#!/usr/bin/env python3
"""
Fantasy Sports API Server Startup Script
Runs the FastAPI server with proper configuration
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting Fantasy Sports API Server")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 