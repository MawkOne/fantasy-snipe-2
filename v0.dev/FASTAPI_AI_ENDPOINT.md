# FastAPI AI Assistant Endpoint

## Add AI Query Endpoint to Your FastAPI Backend

This endpoint uses OpenAI to convert natural language questions into database queries.

### 1. Install Dependencies

```bash
pip install openai sqlalchemy
```

Add to `requirements.txt`:
```txt
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
openai
```

### 2. Add Environment Variable to Railway

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Create AI Query Endpoint

```python
# main.py or ai_routes.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
import json
from database import get_db

app = FastAPI()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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

SYSTEM_PROMPT = """You are a fantasy hockey AI assistant with access to a PostgreSQL database containing NHL data.

Database Schema:
- players: id, full_name, first_name, last_name, sweater_number, position_code, headshot_url, is_active, team_id
- teams: id, team_name, abbreviation, conference, division
- games: id, game_date, home_team_id, away_team_id, home_score, away_score, game_state
- player_game_stats: player_id, game_id, goals, assists, points, shots, hits, pim, toi
- player_career_stats: player_id, season, games_played, goals, assists, points
- goalie_game_stats: player_id, game_id, shots_against, saves, goals_against, save_percentage

When the user asks a question:
1. Determine if you need to query the database
2. If yes, generate a SQL query to answer the question
3. Return the SQL in a JSON object: {"sql": "SELECT ...", "needs_query": true}
4. If no query needed, just answer conversationally: {"needs_query": false, "answer": "..."}

Examples:
- "Who is Cole Caufield?" → Query players table
- "Top 5 scorers" → Query player_career_stats, order by points
- "What is a power play?" → No query needed, just explain

Be helpful, conversational, and fantasy hockey focused!"""

@app.post("/api/ai/query", response_model=AIQueryResponse)
async def ai_query(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Process natural language question and query database
    """
    try:
        # Build conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in request.history[-5:]:  # Keep last 5 messages for context
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current question
        messages.append({"role": "user", "content": request.question})
        
        # Call OpenAI to determine if we need to query
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",  # or "gpt-3.5-turbo" for cheaper
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Try to parse as JSON (if AI returns SQL query)
        try:
            parsed = json.loads(ai_response)
            
            if parsed.get("needs_query") and parsed.get("sql"):
                # Execute the SQL query
                sql_query = parsed["sql"]
                result = db.execute(sql_query)
                data = [dict(row) for row in result.fetchall()]
                
                # Generate natural language response with data
                summary_messages = messages + [
                    {"role": "assistant", "content": ai_response},
                    {"role": "user", "content": f"Here's the data: {json.dumps(data[:10])}. Summarize this for the user in 2-3 sentences."}
                ]
                
                summary_response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=summary_messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                return AIQueryResponse(
                    answer=summary_response.choices[0].message.content,
                    data=data,
                    sql=sql_query
                )
            else:
                # No query needed, return conversational answer
                return AIQueryResponse(
                    answer=parsed.get("answer", ai_response)
                )
                
        except json.JSONDecodeError:
            # AI didn't return JSON, treat as direct answer
            return AIQueryResponse(answer=ai_response)
            
    except Exception as e:
        print(f"AI query error: {str(e)}")
        return AIQueryResponse(
            answer="I encountered an error processing your question. Please try rephrasing it.",
            error=str(e)
        )

# Alternative: Direct SQL generation (more reliable)
@app.post("/api/ai/query-simple")
async def ai_query_simple(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Simpler version: Let AI generate SQL directly
    """
    try:
        # Step 1: Generate SQL
        sql_prompt = f"""Given this database schema:
- players (id, full_name, position_code, sweater_number, team_id, is_active)
- player_career_stats (player_id, season, games_played, goals, assists, points)
- teams (id, team_name, abbreviation)

Generate a PostgreSQL query to answer: "{request.question}"

Return ONLY the SQL query, nothing else. Use season='20242025' for current season.
Limit results to 10 unless specified."""

        sql_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": sql_prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        sql_query = sql_response.choices[0].message.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Step 2: Execute SQL
        result = db.execute(sql_query)
        data = [dict(row) for row in result.fetchall()]
        
        # Step 3: Explain results
        explain_prompt = f"""User asked: "{request.question}"

Query results:
{json.dumps(data[:5], indent=2)}

Explain these results in 2-3 conversational sentences for a fantasy hockey player."""

        explain_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": explain_prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        return AIQueryResponse(
            answer=explain_response.choices[0].message.content,
            data=data,
            sql=sql_query
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return AIQueryResponse(
            answer="I couldn't process that question. Try asking about player stats or team information.",
            error=str(e)
        )
```

### 4. Alternative: Use LangChain (More Robust)

```python
# Install: pip install langchain langchain-openai

from langchain_openai import ChatOpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase

# Create database connection for LangChain
db_url = os.getenv("DATABASE_URL")
db = SQLDatabase.from_uri(db_url)

# Create LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

# Create SQL agent
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="openai-tools"
)

@app.post("/api/ai/query-langchain")
async def ai_query_langchain(request: AIQueryRequest):
    """Use LangChain SQL agent"""
    try:
        response = agent.run(request.question)
        return AIQueryResponse(answer=response)
    except Exception as e:
        return AIQueryResponse(
            answer="Sorry, I couldn't answer that question.",
            error=str(e)
        )
```

## 5. Test the Endpoint

```bash
# Test AI query
curl -X POST https://fastapi-production-45ce.up.railway.app/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are the top 5 scorers this season?"
  }'

# Example response:
{
  "answer": "The top 5 scorers this season are: 1. Nathan MacKinnon with 89 points, 2. Nikita Kucherov with 87 points...",
  "data": [
    {"full_name": "Nathan MacKinnon", "points": 89},
    {"full_name": "Nikita Kucherov", "points": 87}
  ],
  "sql": "SELECT full_name, goals + assists as points FROM player_career_stats..."
}
```

## 6. Cost Optimization

**For production:**
- Use `gpt-3.5-turbo` instead of `gpt-4` (10x cheaper)
- Cache common queries
- Rate limit API calls
- Consider fine-tuning a model on your schema

**Pricing (OpenAI):**
- GPT-3.5-Turbo: ~$0.002 per query
- GPT-4-Turbo: ~$0.03 per query

## 7. Deploy to Railway

1. Add `OPENAI_API_KEY` to Railway environment variables
2. Push code
3. Test: `https://fastapi-production-45ce.up.railway.app/api/ai/query`

## Next Steps

- Add to your Next.js chat interface
- Show player headshots in AI responses
- Add voice input for questions
- Create suggested questions UI
- Track popular queries for optimization

