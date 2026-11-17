#!/usr/bin/env python3
"""
Test script to run the FastAPI server locally for development
"""
import uvicorn
import sys
import os

# Add the current directory to Python path so we can import f1modelq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting F1 Prediction API locally...")
    print("📍 API will be available at: http://localhost:8000")
    print("📍 Health check: http://localhost:8000/health")
    print("📍 Winner prediction: http://localhost:8000/predict/winner")
    print("📍 Race order prediction: http://localhost:8000/predict/race-order")
    print("\n💡 For Vercel deployment, just push to GitHub and redeploy!")
    print("   Your API will be available at: https://your-app.vercel.app/api")
    
    uvicorn.run(
        "api.index:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

