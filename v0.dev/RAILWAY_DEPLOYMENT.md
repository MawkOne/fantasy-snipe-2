# Deploy AI Assistant to Railway

## Quick Setup (5 minutes)

### Step 1: Add Environment Variable to Railway

1. Go to your FastAPI project on Railway
2. Go to **Variables** tab
3. Add:
```bash
GEMINI_API_KEY=AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk
DATABASE_URL=postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
```

### Step 2: Update requirements.txt

Add to your FastAPI `requirements.txt`:
```txt
google-generativeai
```

### Step 3: Add AI Endpoint

Create `ai_routes.py` in your FastAPI project:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
import json
from database import get_db  # Your database connection

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')

class AIQueryRequest(BaseModel):
    question: str
    history: List[dict] = []

class AIQueryResponse(BaseModel):
    answer: str
    data: Optional[List[dict]] = None
    sql: Optional[str] = None
    error: Optional[str] = None

DATABASE_SCHEMA = """
PostgreSQL Database Schema:

1. players (3,513 records)
   - id, full_name, first_name, last_name, sweater_number
   - position_code, headshot_url, is_active, team_id

2. teams (32 teams)
   - id, team_name, abbreviation, conference, division

3. games (16,132 records)
   - id, game_date, home_team_id, away_team_id
   - home_score, away_score, game_state

4. player_game_stats
   - player_id, game_id, goals, assists, points
   - shots, hits, pim, toi

5. player_career_stats
   - player_id, season, games_played, goals, assists, points
   - Use season='20242025' for current season

6. goalie_game_stats
   - player_id, game_id, shots_against, saves
   - goals_against, save_percentage
"""

@router.post("/query", response_model=AIQueryResponse)
async def ai_query(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Natural language query endpoint using Gemini 2.5 Pro
    
    Example questions:
    - "Who are the top 5 scorers?"
    - "Show me Cole Caufield's stats"
    - "Should I trade for Nathan MacKinnon?"
    """
    try:
        # Step 1: Generate SQL query
        sql_prompt = f"""{DATABASE_SCHEMA}

User question: "{request.question}"

Generate a PostgreSQL query to answer this question.
Return ONLY the SQL query, no explanation.
Use season='20242025' for current season.
LIMIT results to 10 unless specified."""

        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        
        # Clean up SQL (remove markdown formatting if present)
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        print(f"Generated SQL: {sql_query}")
        
        # Step 2: Execute query
        result = db.execute(sql_query)
        data = [dict(row._mapping) for row in result.fetchall()]
        
        # Step 3: Generate natural language explanation
        explain_prompt = f"""User asked: "{request.question}"

Database returned:
{json.dumps(data[:5], indent=2, default=str)}

Provide a helpful 2-3 sentence answer for a fantasy hockey player.
Be specific with stats and names."""

        explain_response = model.generate_content(explain_prompt)
        
        return AIQueryResponse(
            answer=explain_response.text,
            data=data,
            sql=sql_query
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        
        # Fallback: Answer without database query
        try:
            fallback_response = model.generate_content(
                f"Answer this fantasy hockey question in 2-3 sentences: {request.question}"
            )
            return AIQueryResponse(
                answer=fallback_response.text,
                error=str(e)
            )
        except:
            return AIQueryResponse(
                answer="I couldn't process that question. Try asking about player stats or team information.",
                error=str(e)
            )

@router.post("/chat", response_model=AIQueryResponse)
async def ai_chat(request: AIQueryRequest):
    """
    Simple chat endpoint without database queries
    For general hockey questions
    """
    try:
        # Build conversation context
        conversation = "You are a helpful fantasy hockey assistant.\n\n"
        for msg in request.history[-5:]:
            conversation += f"{msg['role'].upper()}: {msg['content']}\n"
        conversation += f"USER: {request.question}\nASSISTANT:"
        
        response = model.generate_content(conversation)
        
        return AIQueryResponse(answer=response.text)
        
    except Exception as e:
        return AIQueryResponse(
            answer="Sorry, I couldn't process that question.",
            error=str(e)
        )
```

### Step 4: Register Routes in main.py

```python
from fastapi import FastAPI
from ai_routes import router as ai_router

app = FastAPI()

# Add AI routes
app.include_router(ai_router)

# Your other routes...
```

### Step 5: Deploy

```bash
git add .
git commit -m "Add Gemini AI assistant"
git push
```

Railway will automatically deploy!

---

## Test Your Endpoint

```bash
# Test AI query
curl -X POST https://fastapi-production-45ce.up.railway.app/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are the top 5 NHL scorers this season?"
  }'

# Expected response:
{
  "answer": "The top 5 scorers this season are...",
  "data": [...player stats...],
  "sql": "SELECT * FROM player_career_stats..."
}
```

---

## Monitor Usage

- Railway Dashboard: https://railway.app/project/YOUR_PROJECT
- Google Cloud Console: https://console.cloud.google.com/apis/dashboard?project=fantasy-snipe-ai

---

## 🎉 Done!

Your users can now ask questions and get AI-powered answers from your NHL database!

**Free with your $100K credits!** 💰

