#!/usr/bin/env python3
"""Temporary local AI server with DATABASE CONNECTION"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI(title="Temp AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini
GEMINI_API_KEY = "AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-pro')

# Database
DATABASE_URL = "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

DATABASE_SCHEMA = """
PostgreSQL Database (YOUR REAL NHL DATA - Current 2024-2025 Season):

Tables:
1. players (3,513 NHL players)
   - id, full_name, position_code, sweater_number, team_id, headshot_url, is_active

2. player_game_stats (game-by-game stats - MUST AGGREGATE!)
   - player_id, game_id, team_id, goals, assists, points, shots, hits, pim, toi
   - This has GAME-BY-GAME data, not totals
   - To get season stats: USE SUM() and GROUP BY player_id

3. teams (32 NHL teams)
   - id, full_name (team name), tri_code (3-letter code like 'MTL')

4. games (16,132 games)
   - id, game_date, home_team_id, away_team_id, home_score, away_score

5. goalie_game_stats (goalie games)
   - player_id, game_id, team_id, saves, shots_against, save_percentage

Rules:
- NO career_stats table! Data is game-by-game only
- MUST use SUM() and GROUP BY to get season totals
- ALWAYS JOIN players table to get player.full_name
- ALWAYS use teams.full_name for team name (NOT team_name!)
- ALWAYS use teams.tri_code for abbreviation (NOT abbreviation!)
- LIMIT to 10 results unless specified
- Use ILIKE '%%name%%' for case-insensitive search

Examples:
- Top scorers (season totals):
  SELECT p.full_name, 
         SUM(pgs.goals) as goals, 
         SUM(pgs.assists) as assists, 
         SUM(pgs.points) as points
  FROM player_game_stats pgs 
  JOIN players p ON pgs.player_id = p.id 
  GROUP BY p.full_name, pgs.player_id
  ORDER BY SUM(pgs.points) DESC 
  LIMIT 10

- Find player info:
  SELECT p.full_name, p.position_code, p.sweater_number, t.full_name as team 
  FROM players p 
  JOIN teams t ON p.team_id = t.id 
  WHERE p.full_name ILIKE '%Caufield%'

- Player season stats:
  SELECT p.full_name,
         COUNT(DISTINCT pgs.game_id) as games_played,
         SUM(pgs.goals) as goals,
         SUM(pgs.assists) as assists,
         SUM(pgs.points) as points
  FROM player_game_stats pgs
  JOIN players p ON pgs.player_id = p.id
  WHERE p.full_name ILIKE '%name%'
  GROUP BY p.full_name
"""

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

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.post("/api/ai/query")
async def ai_query(request: AIQueryRequest):
    try:
        print(f"\n{'='*60}")
        print(f"Question: {request.question}")
        print(f"{'='*60}")
        
        # Step 1: Generate SQL
        sql_prompt = f"""{DATABASE_SCHEMA}

User question: "{request.question}"

Generate a PostgreSQL query to answer this. Return ONLY the SQL, no markdown.

Example for "top 5 scorers":
SELECT p.full_name, 
       SUM(pgs.goals) as goals, 
       SUM(pgs.assists) as assists, 
       SUM(pgs.points) as points
FROM player_game_stats pgs 
JOIN players p ON pgs.player_id = p.id 
GROUP BY p.full_name, pgs.player_id
ORDER BY SUM(pgs.points) DESC 
LIMIT 5
"""
        
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        
        # Clean SQL
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()
        
        print(f"Generated SQL:\n{sql_query}\n")
        
        # Step 2: Execute query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        data = cursor.fetchall()
        data = [dict(row) for row in data]
        cursor.close()
        conn.close()
        
        print(f"Query returned {len(data)} rows\n")
        
        # Step 3: Generate answer from real data
        explain_prompt = f"""User asked: "{request.question}"

YOUR DATABASE returned this REAL data:
{json.dumps(data[:5], indent=2, default=str)}

Provide a helpful 2-4 sentence answer using this ACTUAL data.
Be specific with names and numbers."""

        explain_response = model.generate_content(explain_prompt)
        
        print(f"Answer: {explain_response.text[:100]}...")
        print(f"{'='*60}\n")
        
        return AIQueryResponse(
            answer=explain_response.text,
            data=data,
            sql=sql_query
        )
        
    except Exception as e:
        print(f"ERROR: {str(e)}\n")
        # Fallback without database
        try:
            fallback = model.generate_content(
                f"Answer this fantasy hockey question in 2-3 sentences: {request.question}"
            )
            return AIQueryResponse(
                answer=f"⚠️ Couldn't query database, but here's what I know: {fallback.text}",
                error=str(e)
            )
        except:
            return AIQueryResponse(
                answer="Sorry, I couldn't process that question.",
                error=str(e)
            )

@app.get("/")
async def root():
    return {
        "status": "running with DATABASE", 
        "port": 8000,
        "database": "Cloud SQL (3,513 players)",
        "model": "gemini-2.5-pro"
    }

@app.get("/health")
async def health():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM players")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"status": "ok", "database": "connected", "players": count}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Server with DATABASE: http://localhost:8000")
    print("=" * 60)
    print("📊 Connected to Cloud SQL (3,513 NHL players)")
    print("🤖 Using Gemini 2.5 Pro")
    print("💰 FREE with your $100K credits")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

