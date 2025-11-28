#!/usr/bin/env python3
"""AI Server using Google BigQuery - MUCH BETTER than Cloud SQL!"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from google.cloud import bigquery
import uvicorn
import json

app = FastAPI(title="AI Assistant with BigQuery")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini - Using FLASH for speed (10x faster than Pro!)
GEMINI_API_KEY = "AIzaSyDDhhmGWEwW_4dDG6yyCMMP3qkc-00e8Bk"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')  # Changed from 'pro' to 'flash'

# BigQuery
PROJECT_ID = "fantasy-snipe-ai"
DATASET = "nhl_processed"  # Changed from nhl_external (which is empty!)
bigquery_client = bigquery.Client(project=PROJECT_ID)

DATABASE_SCHEMA = """
Google BigQuery - Fantasy Snipe AI (NHL Advanced Stats):

Project: fantasy-snipe-ai
Dataset: nhl_processed

Main Table: player_game_advanced_metrics_flat (571,081 game records)
Columns:
- player_id (INTEGER) - use to JOIN with Cloud SQL players table
- game_id, team_id, season (e.g. 20152016, 20242025)
- game_type: 2 = regular season, 3 = playoffs
- CF, CA (Corsi For/Against), FF, FA (Fenwick), SF, SA (Shots), GF, GA (Goals)
- CF_pct, FF_pct, SF_pct, GF_pct (percentages)
- CF60, FF60, SF60, GF60, pts60 (per-60-minute rates)
- TOI_seconds (time on ice), shifts, PDO

⚠️ NO player names in BigQuery! Player names are in Cloud SQL.

Rules for Queries:
- Use fully qualified name: `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
- For current season (2024-25): WHERE season = 20242025
- For regular season only: WHERE game_type = 2
- MUST use SUM() and GROUP BY player_id to get season totals
- Always ORDER BY the aggregated stat DESC
- LIMIT to 10 results

Example Queries:

Top 10 scorers by Corsi For (shot attempts):
SELECT player_id,
       SUM(CF) as total_corsi_for,
       SUM(SF) as total_shots,
       SUM(GF) as total_goals,
       COUNT(DISTINCT game_id) as games_played
FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
WHERE season = 20242025 AND game_type = 2
GROUP BY player_id
ORDER BY SUM(CF) DESC
LIMIT 10

Player season stats (by player_id):
SELECT player_id,
       SUM(CF) as corsi_for,
       SUM(SF) as shots,
       SUM(GF) as goals,
       AVG(CF_pct) as corsi_pct,
       SUM(TOI_seconds)/3600.0 as total_hours,
       COUNT(DISTINCT game_id) as games
FROM `fantasy-snipe-ai.nhl_processed.player_game_advanced_metrics_flat`
WHERE player_id = 8480069 AND season = 20242025 AND game_type = 2
GROUP BY player_id

⚠️ IMPORTANT: Results will only have player_id. To get names:
"The player with ID 8480069 has X goals..." 
(User will need to look up name separately, OR we add Cloud SQL players JOIN later)
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

@app.post("/api/ai/query")
async def ai_query(request: AIQueryRequest):
    try:
        print(f"\n{'='*60}")
        print(f"Question: {request.question}")
        print(f"{'='*60}")
        
        # Step 1: Generate SQL
        sql_prompt = f"""{DATABASE_SCHEMA}

User question: "{request.question}"

Generate a BigQuery SQL query to answer this question.
Return ONLY the SQL query, no markdown, no explanation.

Remember:
- Use fully qualified table names: `fantasy-snipe-ai.nhl_external.ep_player_season_stats`
- For current season: WHERE season IN ('2024-2025', '20242025', '2024-25')
- Use LOWER() for case-insensitive searches
"""
        
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        
        # Clean SQL
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()
        
        print(f"Generated SQL:\n{sql_query}\n")
        
        # Step 2: Execute query on BigQuery
        query_job = bigquery_client.query(sql_query)
        results = query_job.result()
        
        # Convert to list of dicts
        data = [dict(row) for row in results]
        
        print(f"BigQuery returned {len(data)} rows\n")
        
        # Step 3: Generate natural language explanation
        explain_prompt = f"""User asked: "{request.question}"

BigQuery returned this REAL data from the NHL database:
{json.dumps(data[:5], indent=2, default=str)}

Provide a helpful 2-4 sentence answer using this ACTUAL data.
Be specific with player names and numbers. Make it conversational for fantasy hockey."""

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
        "status": "running with BigQuery", 
        "port": 8000,
        "database": "fantasy-snipe-ai.nhl_processed",
        "model": "gemini-2.5-flash (FAST)",
        "cost": "FREE with $100K credits"
    }

@app.get("/health")
async def health():
    try:
        # Test query
        query = "SELECT COUNT(*) as count FROM `fantasy-snipe-ai.nhl_external.ep_player_season_stats` LIMIT 1"
        result = bigquery_client.query(query).result()
        count = list(result)[0]['count']
        return {
            "status": "ok", 
            "database": "BigQuery connected",
            "table": "ep_player_season_stats",
            "rows": count
        }
    except Exception as e:
        return {
            "status": "error", 
            "database": "disconnected", 
            "error": str(e)
        }

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Server with BigQuery: http://localhost:8000")
    print("=" * 60)
    print("📊 Project: fantasy-snipe-ai")
    print("📊 Dataset: nhl_external")
    print("📊 Table: ep_player_season_stats")
    print("🤖 Model: Gemini 2.5 Pro")
    print("💰 Cost: FREE ($100K credits)")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

