/**
 * AI Assistant for querying NHL/Fantasy Hockey data
 * Uses Google Gemini AI (free with your $100K Google Cloud credits!)
 */

export interface AIMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AIQueryResult {
  answer: string;
  data?: any;
  sql?: string;
  error?: string;
}

/**
 * System prompt that teaches the AI about your database structure
 */
export const FANTASY_HOCKEY_SYSTEM_PROMPT = `You are a fantasy hockey AI assistant with access to a comprehensive NHL database. You can answer questions about players, teams, games, and statistics.

**Available Data:**

Tables:
- players (id, full_name, first_name, last_name, sweater_number, position_code, headshot_url, is_active, team_id)
  - 3,513 NHL players with current roster info
  
- teams (id, team_name, abbreviation, etc.)
  - All 32 NHL teams
  
- games (id, game_date, home_team_id, away_team_id, home_score, away_score, game_state)
  - 16,132 games of historical data
  
- player_game_stats (player_id, game_id, goals, assists, points, shots, hits, blocked_shots, pim, toi)
  - Individual game performance stats
  
- player_career_stats (player_id, season, games_played, goals, assists, points, plus_minus, pim, etc.)
  - Season aggregated stats
  
- goalie_game_stats (player_id, game_id, shots_against, saves, goals_against, save_percentage, shutouts)
  - Goalie-specific stats
  
- player_game_advanced_metrics (player_id, game_id, corsi_for, corsi_against, fenwick_for, etc.)
  - Advanced analytics

**Your Job:**
1. Understand the user's question
2. Determine what data they need
3. Provide a clear, conversational answer
4. Include relevant stats and player info
5. Suggest follow-up questions or insights

**Example Interactions:**

User: "Who is Cole Caufield?"
You: "Cole Caufield is a right wing for the Montreal Canadiens, wearing #13. He's known for his elite shooting ability."

User: "Show me the top 5 scorers this season"
You: "Here are the top 5 scorers for the 2024-25 season: [query player_career_stats, order by points]"

User: "Should I trade for Nathan MacKinnon?"
You: "Nathan MacKinnon is an elite center playing for Colorado. Let me pull his recent stats... [provide analysis based on goals, assists, advanced metrics]"

**Guidelines:**
- Be conversational and helpful
- Use real data from the database
- Explain stats in fantasy hockey terms
- Consider fantasy relevance (goals, assists, shots, hits)
- Provide context (team, position, recent performance)
- Be honest if you don't have specific data
`;

/**
 * Query the AI assistant with context from your database
 */
export async function queryAIAssistant(
  userQuestion: string,
  conversationHistory: AIMessage[] = []
): Promise<AIQueryResult> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://fastapi-production-45ce.up.railway.app";
  
  try {
    const response = await fetch(`${API_URL}/api/ai/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: userQuestion,
        history: conversationHistory,
      }),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("AI API Error:", response.status, errorText);
      throw new Error(`AI query failed: ${response.status} - ${errorText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error("Error querying AI:", error);
    return {
      answer: "Sorry, I'm having trouble accessing the data right now. Please try again.",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Generate suggested questions based on context
 */
export function getSuggestedQuestions(context?: string): string[] {
  const suggestions = [
    // Player questions
    "Who are the top 10 scorers this season?",
    "Show me Cole Caufield's stats",
    "Who has the most goals in the last 5 games?",
    "Which players have the best plus/minus?",
    
    // Team questions
    "How are the Montreal Canadiens doing?",
    "Show me the Maple Leafs roster",
    "Which team scores the most goals?",
    
    // Fantasy questions
    "Should I pick up a specific player?",
    "Who are the best goalies right now?",
    "Which rookies are performing well?",
    "Show me waiver wire targets",
    
    // Game questions
    "Who plays tonight?",
    "Show me last night's scores",
    "When does my player's team play next?",
    
    // League questions
    "Show me my league standings",
    "Who made the most transactions?",
    "Analyze my team's roster",
  ];
  
  // Return random 4 suggestions
  return suggestions.sort(() => Math.random() - 0.5).slice(0, 4);
}

/**
 * Format AI response with markdown and data
 */
export function formatAIResponse(result: AIQueryResult): string {
  let formatted = result.answer;
  
  // Add data tables if present
  if (result.data && Array.isArray(result.data) && result.data.length > 0) {
    formatted += "\n\n**Results:**\n";
    
    // Format first 10 results as a table
    const items = result.data.slice(0, 10);
    items.forEach((item, index) => {
      formatted += `\n${index + 1}. ${formatDataItem(item)}`;
    });
    
    if (result.data.length > 10) {
      formatted += `\n\n_...and ${result.data.length - 10} more results_`;
    }
  }
  
  return formatted;
}

function formatDataItem(item: any): string {
  // Format player data
  if (item.full_name) {
    const position = item.position_code ? ` (${item.position_code})` : "";
    const number = item.sweater_number ? `#${item.sweater_number}` : "";
    const stats = item.goals !== undefined 
      ? ` - ${item.goals}G, ${item.assists}A, ${item.points}P`
      : "";
    return `**${item.full_name}**${position} ${number}${stats}`;
  }
  
  // Format game data
  if (item.game_date) {
    return `${item.home_team} vs ${item.away_team} - ${item.game_date}`;
  }
  
  // Generic formatting
  return JSON.stringify(item);
}

