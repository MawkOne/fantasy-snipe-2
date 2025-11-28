#!/usr/bin/env python3
"""
Temporary local FastAPI server for testing AI
Run this while you update your main FastAPI on Railway
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import uvicorn

app = FastAPI(title="Temp AI Assistant")

# Allow CORS for localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = "AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

class AIMessage(BaseModel):
    role: str
    content: str

class AIQueryRequest(BaseModel):
    question: str
    history: List[AIMessage] = []

class AIQueryResponse(BaseModel):
    answer: str
    data: Optional[List[dict]] = None
    sql: Optional[str] = None
    error: Optional[str] = None

@app.post("/api/ai/query")
async def ai_query(request: AIQueryRequest):
    """
    Temporary AI endpoint for testing
    """
    try:
        print(f"\n🤖 Question: {request.question}")
        
        # For now, just use AI without database
        prompt = f"""You are a helpful fantasy hockey assistant.

User question: {request.question}

Provide a helpful, conversational answer (2-4 sentences).
Be specific and knowledgeable about NHL and fantasy hockey."""

        response = model.generate_content(prompt)
        
        print(f"✅ Answer: {response.text[:100]}...")
        
        return AIQueryResponse(
            answer=response.text,
            data=None,
            sql=None
        )
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return AIQueryResponse(
            answer="Sorry, I encountered an error. Please try again.",
            error=str(e)
        )

@app.get("/")
async def root():
    return {"status": "Temporary AI server running", "model": "gemini-2.5-pro"}

@app.get("/health")
async def health():
    return {"status": "ok", "gemini": "configured"}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting temporary AI server on http://localhost:8000")
    print("=" * 60)
    print("\n📝 Update your .env.local:")
    print("   NEXT_PUBLIC_API_URL=http://localhost:8000")
    print("\n🔄 Then restart your Next.js dev server")
    print("\n⚠️  This is temporary - add the code to your Railway FastAPI next!")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

