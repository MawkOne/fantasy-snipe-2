"""
AI Assistant Routes for FastAPI
Add this to your FastAPI project

File: ai_routes.py (create this file in your FastAPI project)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
import json

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')
else:
    model = None
    print("WARNING: GEMINI_API_KEY not set")

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

DATABASE_SCHEMA = """
PostgreSQL Database Schema (Cloud SQL):

1. players (3,513 records)
   - id (integer)
   - full_name (text)
   - first_name (text)
   - last_name (text)
   - sweater_number (integer)
   - position_code (text) - e.g., 'C', 'LW', 'RW', 'D', 'G'
   - headshot_url (text)
   - is_active (boolean)
   - team_id (integer)

2. teams (32 NHL teams)
   - id (integer)
   - team_name (text)
   - abbreviation (text) - e.g., 'MTL', 'TOR', 'NYR'
   - conference (text)
   - division (text)

3. games (16,132 records)
   - id (integer)
   - game_date (date)
   - home_team_id (integer)
   - away_team_id (integer)
   - home_score (integer)
   - away_score (integer)
   - game_state (text)

4. player_game_stats (game-by-game stats)
   - player_id (integer)
   - game_id (integer)
   - goals (integer)
   - assists (integer)
   - points (integer)
   - shots (integer)
   - hits (integer)
   - pim (integer) - penalty minutes
   - toi (integer) - time on ice

5. player_career_stats (season totals)
   - player_id (integer)
   - season (text) - format: '20242025' for 2024-25 season
   - games_played (integer)
   - goals (integer)
   - assists (integer)
   - points (integer)
   - plus_minus (integer)
   - pim (integer)

6. goalie_game_stats
   - player_id (integer)
   - game_id (integer)
   - shots_against (integer)
   - saves (integer)
   - goals_against (integer)
   - save_percentage (float)
   - shutouts (integer)

Important Notes:
- Current season is '20242025'
- Always JOIN players table to get player names
- Always LIMIT results to 10 unless user specifies otherwise
- Use ILIKE for case-insensitive search (e.g., WHERE full_name ILIKE '%caufield%')
"""

# Dependency to get database session
# Replace this with your actual database dependency
def get_db():
    """
    Replace this with your actual database session getter
    Example:
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    """
    # TODO: Import your database session here
    from database import SessionLocal  # Adjust import based on your setup
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/query", response_model=AIQueryResponse)
async def ai_query(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Natural language query endpoint using Gemini 2.5 Pro
    
    Examples:
    - "Who are the top 5 scorers this season?"
    - "Show me Cole Caufield's stats"
    - "Which goalies have the best save percentage?"
    """
    
    if not model:
        return AIQueryResponse(
            answer="AI Assistant is not configured. Please set GEMINI_API_KEY environment variable.",
            error="GEMINI_API_KEY not set"
        )
    
    try:
        # Step 1: Generate SQL query
        sql_prompt = f"""{DATABASE_SCHEMA}

User question: "{request.question}"

Task: Generate a PostgreSQL query to answer this question.
Return ONLY the SQL query, no explanation, no markdown formatting.
The query must be valid PostgreSQL syntax.

Rules:
- Use season='20242025' for current season queries
- LIMIT results to 10 unless user specifies otherwise
- JOIN players table when you need player names
- Use ILIKE for case-insensitive text search
- Return actual column names from the schema above

Example for "top 5 scorers":
SELECT p.full_name, pcs.goals, pcs.assists, pcs.points 
FROM player_career_stats pcs 
JOIN players p ON pcs.player_id = p.id 
WHERE pcs.season = '20242025' 
ORDER BY pcs.points DESC 
LIMIT 5
"""

        print(f"Asking AI to generate SQL for: {request.question}")
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        
        # Clean up SQL (remove markdown formatting if present)
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()
        
        print(f"Generated SQL: {sql_query}")
        
        # Step 2: Execute query
        try:
            result = db.execute(text(sql_query))
            data = [dict(row._mapping) for row in result.fetchall()]
            print(f"Query returned {len(data)} rows")
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            # If SQL fails, try to answer without database
            fallback_response = model.generate_content(
                f"Answer this fantasy hockey question in 2-3 sentences (without accessing a database): {request.question}"
            )
            return AIQueryResponse(
                answer=f"I couldn't query the database, but here's what I know: {fallback_response.text}",
                error=f"SQL error: {str(db_error)}"
            )
        
        # Step 3: Generate natural language explanation
        explain_prompt = f"""User asked: "{request.question}"

Database query returned this data:
{json.dumps(data[:5], indent=2, default=str)}

Task: Provide a helpful, conversational answer (2-4 sentences) for a fantasy hockey player.
Be specific with player names and stats. Make it interesting and insightful.
"""

        explain_response = model.generate_content(explain_prompt)
        
        return AIQueryResponse(
            answer=explain_response.text,
            data=data,
            sql=sql_query
        )
        
    except Exception as e:
        print(f"Error in ai_query: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: Answer without database query
        try:
            fallback_response = model.generate_content(
                f"Answer this fantasy hockey question in 2-3 sentences: {request.question}"
            )
            return AIQueryResponse(
                answer=fallback_response.text,
                error=f"Error: {str(e)}"
            )
        except:
            return AIQueryResponse(
                answer="I'm having trouble processing that question. Could you try rephrasing it?",
                error=str(e)
            )

@router.post("/chat", response_model=AIQueryResponse)
async def ai_chat(request: AIQueryRequest):
    """
    Simple chat endpoint without database queries.
    For general hockey questions that don't need data.
    """
    
    if not model:
        return AIQueryResponse(
            answer="AI Assistant is not configured.",
            error="GEMINI_API_KEY not set"
        )
    
    try:
        # Build conversation context
        conversation = "You are a helpful fantasy hockey assistant with deep NHL knowledge.\n\n"
        for msg in request.history[-5:]:
            conversation += f"{msg.role.upper()}: {msg.content}\n"
        conversation += f"USER: {request.question}\nASSISTANT:"
        
        response = model.generate_content(conversation)
        
        return AIQueryResponse(answer=response.text)
        
    except Exception as e:
        print(f"Error in ai_chat: {str(e)}")
        return AIQueryResponse(
            answer="Sorry, I couldn't process that question.",
            error=str(e)
        )

@router.get("/health")
async def ai_health():
    """Check if AI is configured"""
    return {
        "gemini_configured": model is not None,
        "model": "gemini-2.5-pro" if model else None,
        "status": "ready" if model else "not_configured"
    }


"""
==============================================
STEP 2: Register routes in your main.py
==============================================

Add this to your main.py:

from fastapi import FastAPI
from ai_routes import router as ai_router

app = FastAPI()

# Add AI routes
app.include_router(ai_router)

# Your other routes...

==============================================
STEP 3: Update requirements.txt
==============================================

Add to requirements.txt:

google-generativeai
sqlalchemy

==============================================
STEP 4: Deploy to Railway
==============================================

git add .
git commit -m "Add Gemini AI assistant endpoint"
git push

==============================================
STEP 5: Test
==============================================

curl -X POST https://fastapi-production-45ce.up.railway.app/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the top 5 scorers?"}'

"""

