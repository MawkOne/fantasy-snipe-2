# AI Assistant for NHL Data Queries

## ✅ What I Created

### 1. **AI Assistant Library** (`lib/ai-assistant.ts`)
- System prompt that teaches AI about your database schema
- Query function to ask questions in natural language
- Response formatting for clean display
- Suggested questions for users

### 2. **React Hook** (`hooks/use-ai-assistant.ts`)
- `useAIAssistant()` - Complete AI chat management
- Maintains conversation history
- Loading states
- Error handling

### 3. **FastAPI Backend Endpoint** (`FASTAPI_AI_ENDPOINT.md`)
- Complete code to add to your FastAPI
- OpenAI integration
- SQL query generation
- Natural language responses

### 4. **NHL Data Hooks** (`hooks/use-nhl-data.ts`)
- Direct database access hooks
- Player search, stats, game logs
- Ready to use in UI components

---

## 🤖 How It Works

```
User Question
"Who are the top scorers?"
       ↓
   AI Assistant
   (OpenAI GPT-4)
       ↓
  Generate SQL Query
"SELECT * FROM player_career_stats ORDER BY points DESC LIMIT 10"
       ↓
   Execute Query
   (Cloud SQL)
       ↓
  Format Response
"The top scorers are Nathan MacKinnon (89 pts), Nikita Kucherov..."
       ↓
   Display to User
```

---

## 💬 Example Questions Users Can Ask

### Player Questions:
- "Who is Cole Caufield?"
- "Show me Connor McDavid's stats"
- "Top 10 goal scorers this season"
- "Which players have the best plus/minus?"
- "Who leads in shots on goal?"

### Team Questions:
- "How are the Canadiens doing?"
- "Show me the Maple Leafs roster"
- "Which team scores the most goals?"

### Fantasy Questions:
- "Should I pick up Player X?"
- "Who are the best goalies right now?"
- "Show me waiver wire targets"
- "Compare Player A vs Player B"

### Game Questions:
- "Who plays tonight?"
- "Show me last night's scores"
- "When does my player's team play next?"

---

## 🚀 Setup Steps

### Step 1: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy it (starts with `sk-...`)

### Step 2: Add to Railway
1. Go to your FastAPI project on Railway
2. Add environment variable:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

### Step 3: Add Endpoint to FastAPI
Copy the code from `FASTAPI_AI_ENDPOINT.md` into your FastAPI `main.py`

### Step 4: Test
```bash
curl -X POST https://fastapi-production-45ce.up.railway.app/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who are the top 5 scorers?"}'
```

### Step 5: Use in Your App
```typescript
import { useAIAssistant } from '@/hooks/use-ai-assistant';

function AIChat() {
  const { messages, askQuestion, isLoading } = useAIAssistant();
  
  const handleSubmit = async (question: string) => {
    await askQuestion(question);
  };
  
  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>{msg.content}</div>
      ))}
    </div>
  );
}
```

---

## 💰 Cost Estimate

**Using GPT-3.5-Turbo (Recommended):**
- ~$0.002 per query
- 1,000 questions = $2
- Very affordable for most use cases

**Using GPT-4-Turbo (Better quality):**
- ~$0.03 per query
- 1,000 questions = $30
- More accurate SQL generation

---

## 🎯 Features

### ✅ What's Built:
- Natural language to SQL conversion
- Conversational responses
- Conversation history
- Error handling
- Suggested questions
- Data formatting

### 🔜 Can Add Later:
- Voice input (speech-to-text)
- Player comparisons with charts
- Trade recommendations
- Lineup optimization
- Injury alerts
- Game day notifications

---

## 📊 Example Conversations

**User:** "Who are the top 5 scorers this season?"

**AI:** "The top 5 scorers for the 2024-25 season are:
1. Nathan MacKinnon (COL) - 89 points (34G, 55A)
2. Nikita Kucherov (TBL) - 87 points (31G, 56A)
3. Auston Matthews (TOR) - 85 points (48G, 37A)
4. Connor McDavid (EDM) - 84 points (29G, 55A)
5. David Pastrnak (BOS) - 82 points (38G, 44A)

These players have been dominant this season!"

---

**User:** "Should I trade for Cole Caufield?"

**AI:** "Cole Caufield (#13, MTL) is a dynamic right winger with elite shooting ability. This season he has:
- 26 goals, 24 assists (50 points)
- 245 shots on goal (high shooting volume)
- Playing on PP1 with Nick Suzuki

For fantasy, he's a great source of goals and shots. If you need scoring, he's a solid pickup. However, his assists and +/- can be inconsistent. What does your current roster need?"

---

## 🔐 Security Notes

✅ **Safe:**
- AI queries your database read-only
- No direct SQL from users (AI generates it)
- API key stored securely in Railway

⚠️ **Best Practices:**
- Rate limit AI queries (prevent abuse)
- Cache common questions
- Monitor API costs
- Sanitize user inputs

---

## 📚 Next Steps

1. **Get OpenAI API key** → platform.openai.com
2. **Add to Railway** → Environment variables
3. **Copy FastAPI code** → See `FASTAPI_AI_ENDPOINT.md`
4. **Test endpoint** → curl command
5. **Integrate in UI** → Use the React hooks
6. **Launch!** 🚀

---

## Alternative: Use Your Own AI

Don't want to pay OpenAI? You can also:
- Run Llama 3 locally (free, slower)
- Use Google's Gemini API (similar pricing)
- Use Anthropic Claude (similar pricing)
- Pre-build common queries (no AI needed)

---

**Your users can now ask questions in plain English and get answers from your 3,513 player database!** 🏒🤖

