# League Data Structure

## Overview
This document describes the data structure for managing multiple fantasy hockey leagues in the application.

## Firebase Collections

### `leagues` Collection
Stores all league information and settings.

```typescript
{
  id: string;                    // Auto-generated Firestore ID
  name: string;                  // "UHHP", "Henderson's League", etc.
  icon?: string;                 // URL to league logo
  description?: string;          // League description
  createdAt: Date;
  updatedAt: Date;
  
  settings: {
    season: string;              // "2024-2025"
    maxTeams: number;            // 12
    salaryCap: number;           // e.g., 85000000
    rosterSize: number;          // e.g., 23
    scoringType: "head-to-head" | "points" | "rotisserie";
    tradeDeadline?: Date;
    playoffStart?: Date;
  };
  
  members: LeagueMember[];       // Array of all league members
  commissionerId: string;        // User ID of commissioner
  status: "draft" | "active" | "playoffs" | "completed" | "archived";
  
  channels: {
    generalChatId: string;       // Reference to chat room
    tradeTalkId?: string;
    trashTalkId?: string;
  };
}
```

### `chatRooms` Collection
Each league has associated chat rooms. Messages are stored as subcollections.

```typescript
{
  id: string;
  leagueId: string;              // Reference to parent league
  name: string;                  // "General Chat", "Trade Talk", etc.
  type: "general" | "trade" | "trash" | "private";
  createdAt: Date;
  
  // Messages stored as subcollection: chatRooms/{chatRoomId}/messages/{messageId}
}
```

## Hooks

### `useLeagues(userId)`
Manages all leagues for the current user.

**Returns:**
- `leagues`: Array of all leagues the user is a member of
- `activeLeague`: Currently selected league
- `activeLeagueId`: ID of active league
- `loading`: Loading state
- `error`: Error message if any
- `switchLeague(leagueId)`: Switch to a different league
- `createLeague(input)`: Create a new league
- `updateLeague(leagueId, updates)`: Update league settings

### `useLeagueMembers(leagueId)`
Gets all members of a specific league with real-time updates.

**Returns:**
- `members`: Array of league members
- `loading`: Loading state

## Integration Points

### 1. League Sidebar
- Shows all leagues the user is a member of
- Highlights the active league
- Allows switching between leagues
- Shows "Add League" button for creating new leagues

### 2. Chat System
- Messages are scoped to the active league
- Each league has its own set of chat rooms
- Members list shows only users in the active league

### 3. League JSON Data
You can import historical data from `/uhhp_simulations/uhhp_league_history_full.json` and store it in Firestore:

```typescript
// Import league history
const leagueHistory = require('./uhhp_simulations/uhhp_league_history_full.json');

// Store in Firestore under each league document
await updateDoc(doc(db, 'leagues', leagueId), {
  history: leagueHistory
});
```

## PostgreSQL Alternative (Optional)

If you prefer PostgreSQL instead of Firebase, here's the schema:

```sql
-- Leagues table
CREATE TABLE leagues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  icon TEXT,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  settings JSONB NOT NULL,
  commissioner_id UUID NOT NULL,
  status VARCHAR(50) NOT NULL,
  channels JSONB
);

-- League members table
CREATE TABLE league_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id UUID REFERENCES leagues(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  user_name VARCHAR(255) NOT NULL,
  user_avatar TEXT,
  team_name VARCHAR(255) NOT NULL,
  team_strategy VARCHAR(50),
  joined_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  team_stats JSONB
);

-- Chat rooms table
CREATE TABLE chat_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id UUID REFERENCES leagues(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_room_id UUID REFERENCES chat_rooms(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  user_name VARCHAR(255) NOT NULL,
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_league_members_league_id ON league_members(league_id);
CREATE INDEX idx_chat_rooms_league_id ON chat_rooms(league_id);
CREATE INDEX idx_messages_chat_room_id ON messages(chat_room_id);
```

## FastAPI Endpoints (If Using PostgreSQL + FastAPI)

```python
# Example endpoints for your FastAPI backend

@app.get("/leagues")
async def get_user_leagues(user_id: str):
    """Get all leagues for a user"""
    pass

@app.post("/leagues")
async def create_league(league: CreateLeagueInput):
    """Create a new league"""
    pass

@app.get("/leagues/{league_id}")
async def get_league(league_id: str):
    """Get league details"""
    pass

@app.put("/leagues/{league_id}")
async def update_league(league_id: str, updates: UpdateLeagueInput):
    """Update league settings"""
    pass

@app.get("/leagues/{league_id}/members")
async def get_league_members(league_id: str):
    """Get all members of a league"""
    pass
```

## Next Steps

1. ✅ Create league data structure
2. ✅ Set up Firebase Firestore collections
3. ✅ Create hooks for league management
4. ✅ Update sidebar to use real leagues
5. 🔲 Add "Create League" modal
6. 🔲 Import historical JSON data into Firestore
7. 🔲 Connect chat rooms to active league
8. 🔲 Add league settings page

## Alternative: Using Your Existing Infrastructure

If you want to use your PostgreSQL + FastAPI setup instead:

**Connection String:** 
```
postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway
```

**API Base URL:**
```
https://fastapi-production-45ce.up.railway.app
```

Let me know if you want to switch to PostgreSQL + FastAPI instead of Firebase!

