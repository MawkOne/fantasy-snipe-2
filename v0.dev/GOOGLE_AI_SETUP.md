# Google Cloud AI Setup (Gemini API)

## ✅ You Have $100K in Credits!

Since you're already using Google Cloud (Project: `fantasy-snipe-ai`), let's use Google's Gemini AI - it's **free with your credits** and integrates perfectly with Cloud SQL!

## Google AI Options

### 1. Gemini API (Recommended) 🌟
- **Latest model**: Gemini 1.5 Pro
- **Better than GPT-4** for many tasks
- **Free with your credits**
- **Multimodal**: Text, images, video
- **Larger context**: Up to 1M tokens

### 2. Vertex AI
- Enterprise AI platform
- Same models, more features
- Better for production

---

## Setup Steps

### Step 1: Enable Gemini API

1. Go to: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com?project=fantasy-snipe-ai
2. Click **"Enable"**

Or via command line:
```bash
gcloud services enable generativelanguage.googleapis.com --project=fantasy-snipe-ai
```

### Step 2: Create API Key

**Option A: Via Console**
1. Go to: https://console.cloud.google.com/apis/credentials?project=fantasy-snipe-ai
2. Click **"Create Credentials"** → **"API Key"**
3. Copy the key (starts with `AIza...`)
4. (Optional) Restrict key to Gemini API only

**Option B: Via Command Line**
```bash
gcloud auth application-default login
```

### Step 3: Add to Railway

```bash
GOOGLE_API_KEY=AIza...your-key-here
# Or use Application Default Credentials
GOOGLE_CLOUD_PROJECT=fantasy-snipe-ai
```

---

## Pricing (Using Your Credits)

**Gemini 1.5 Pro:**
- Input: $0.00125 per 1K characters
- Output: $0.005 per 1K characters
- **Your cost**: $0 (using credits!)

**Example:**
- 10,000 AI queries ≈ $50
- With $100K credits = 2,000,000 queries!

**vs OpenAI GPT-4:**
- 10,000 queries ≈ $300
- Need to pay out of pocket

---

## Advantages of Gemini

✅ **Free with your credits** ($100K!)  
✅ **Larger context window** (1M tokens vs GPT-4's 128K)  
✅ **Better at code generation**  
✅ **Native Google Cloud integration**  
✅ **Same Google Cloud project** as your Cloud SQL  
✅ **Multimodal** - can analyze images/videos  
✅ **Lower latency** (same region as your database)  

---

## FastAPI Implementation

### Install Dependencies

```bash
pip install google-generativeai
```

Add to `requirements.txt`:
```txt
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
google-generativeai
```

### Create AI Endpoint (Gemini)

```python
# main.py or ai_routes.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
import json
from database import get_db

app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini model (2.5 Pro is the latest and best!)
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

SYSTEM_PROMPT = """You are a fantasy hockey AI assistant with access to a PostgreSQL database containing NHL data.

**Database Schema:**

Tables available:
1. **players** (3,513 records)
   - id, full_name, first_name, last_name, sweater_number, position_code
   - headshot_url, is_active, team_id

2. **teams**
   - id, team_name, abbreviation, conference, division

3. **games** (16,132 records)
   - id, game_date, home_team_id, away_team_id, home_score, away_score

4. **player_game_stats**
   - player_id, game_id, goals, assists, points, shots, hits, pim, toi

5. **player_career_stats**
   - player_id, season, games_played, goals, assists, points

6. **goalie_game_stats**
   - player_id, game_id, shots_against, saves, save_percentage

**Your Task:**
When user asks a question:
1. Determine if you need database data
2. If YES: Generate a PostgreSQL query
3. Return JSON: {"needs_query": true, "sql": "SELECT ..."}
4. If NO: Return JSON: {"needs_query": false, "answer": "your response"}

**Guidelines:**
- Use season='20242025' for current season
- LIMIT results to 10 unless specified
- Be conversational and helpful
- Consider fantasy hockey context
- Use player headshot_url when showing players

**Examples:**

Question: "Who are the top 5 scorers?"
Response: {
  "needs_query": true,
  "sql": "SELECT p.full_name, p.headshot_url, pcs.goals, pcs.assists, (pcs.goals + pcs.assists) as points FROM player_career_stats pcs JOIN players p ON pcs.player_id = p.id WHERE pcs.season = '20242025' ORDER BY points DESC LIMIT 5"
}

Question: "What is a power play?"
Response: {
  "needs_query": false,
  "answer": "A power play occurs when one team has more players on the ice due to penalties..."
}
"""

@app.post("/api/ai/query", response_model=AIQueryResponse)
async def ai_query_gemini(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Process natural language question using Google Gemini
    """
    try:
        # Build conversation with system prompt
        conversation_text = SYSTEM_PROMPT + "\n\n"
        
        # Add history
        for msg in request.history[-5:]:
            conversation_text += f"{msg.role.upper()}: {msg.content}\n"
        
        # Add current question
        conversation_text += f"USER: {request.question}\nASSISTANT: "
        
        # Call Gemini
        response = model.generate_content(conversation_text)
        ai_response = response.text.strip()
        
        # Try to parse as JSON
        try:
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(ai_response)
            
            if parsed.get("needs_query") and parsed.get("sql"):
                # Execute SQL query
                sql_query = parsed["sql"]
                print(f"Executing SQL: {sql_query}")
                
                result = db.execute(sql_query)
                data = [dict(row._mapping) for row in result.fetchall()]
                
                # Generate natural language summary
                summary_prompt = f"""User asked: "{request.question}"

Query returned this data:
{json.dumps(data[:10], indent=2)}

Provide a conversational 2-3 sentence summary of these results for a fantasy hockey player. Be specific and helpful."""

                summary_response = model.generate_content(summary_prompt)
                
                return AIQueryResponse(
                    answer=summary_response.text,
                    data=data,
                    sql=sql_query
                )
            else:
                # No query needed
                return AIQueryResponse(
                    answer=parsed.get("answer", ai_response)
                )
                
        except (json.JSONDecodeError, KeyError) as e:
            # AI didn't return valid JSON, treat as direct answer
            return AIQueryResponse(answer=ai_response)
            
    except Exception as e:
        print(f"Gemini error: {str(e)}")
        return AIQueryResponse(
            answer="I encountered an error. Please try rephrasing your question.",
            error=str(e)
        )

# Simpler version: 2-step process
@app.post("/api/ai/query-simple")
async def ai_query_simple(request: AIQueryRequest, db: Session = Depends(get_db)):
    """
    Simpler 2-step process: Generate SQL, then explain results
    """
    try:
        # Step 1: Generate SQL
        sql_prompt = f"""Generate a PostgreSQL query for this question: "{request.question}"

Database schema:
- players (id, full_name, position_code, sweater_number, team_id, headshot_url, is_active)
- player_career_stats (player_id, season, goals, assists, points)
- teams (id, team_name, abbreviation)

Return ONLY the SQL query. Use season='20242025' for current. LIMIT 10."""

        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        
        # Clean up SQL
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        print(f"Generated SQL: {sql_query}")
        
        # Step 2: Execute query
        result = db.execute(sql_query)
        data = [dict(row._mapping) for row in result.fetchall()]
        
        # Step 3: Explain results
        explain_prompt = f"""User asked: "{request.question}"

Results from database:
{json.dumps(data[:5], indent=2)}

Explain these results in 2-3 conversational sentences for a fantasy hockey player."""

        explain_response = model.generate_content(explain_prompt)
        
        return AIQueryResponse(
            answer=explain_response.text,
            data=data,
            sql=sql_query
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return AIQueryResponse(
            answer="I couldn't process that question. Try asking about player stats or team info.",
            error=str(e)
        )

# Chat endpoint (maintains conversation)
@app.post("/api/ai/chat")
async def ai_chat(request: AIQueryRequest):
    """
    Simple chat without database queries
    """
    try:
        conversation = "\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in request.history[-10:]
        ])
        conversation += f"\nUSER: {request.question}\nASSISTANT:"
        
        response = model.generate_content(conversation)
        
        return AIQueryResponse(answer=response.text)
        
    except Exception as e:
        return AIQueryResponse(
            answer="Sorry, I couldn't process that.",
            error=str(e)
        )
```

---

## Alternative: Vertex AI (More Features)

```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Initialize
aiplatform.init(project="fantasy-snipe-ai", location="us-central1")

# Use Gemini via Vertex AI
model = GenerativeModel("gemini-1.5-pro")
response = model.generate_content("Your prompt here")
```

**Benefits of Vertex AI:**
- Fine-tuning capabilities
- Model monitoring
- A/B testing
- Better enterprise features

---

## Test Gemini Locally

```python
# test_gemini.py
import google.generativeai as genai
import os

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-1.5-pro')

response = model.generate_content("Who are the top NHL scorers?")
print(response.text)
```

```bash
python test_gemini.py
```

---

## Monitoring Your Credits

1. Go to: https://console.cloud.google.com/billing/01AC70-816944-FD7D14?project=fantasy-snipe-ai
2. View usage dashboard
3. Track Gemini API costs (should be $0 with credits!)

---

## Next Steps

1. ✅ Enable Gemini API in Google Cloud Console
2. ✅ Create API key
3. ✅ Add `GOOGLE_API_KEY` to Railway
4. ✅ Update FastAPI with code above
5. ✅ Deploy and test
6. ✅ Enjoy free AI queries! 🎉

---

## Comparison

| Feature | Gemini 1.5 Pro | GPT-4 Turbo |
|---------|----------------|-------------|
| **Cost (for you)** | **FREE** ✅ | $0.03/query |
| Context Window | 1M tokens | 128K tokens |
| Quality | Excellent | Excellent |
| Speed | Fast | Fast |
| Integration | Native GCP ✅ | External API |
| Your Credits | Uses $100K | Costs money |

**Winner for you: Gemini!** 🏆

