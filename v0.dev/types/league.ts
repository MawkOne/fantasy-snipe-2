/**
 * League data structure for fantasy hockey leagues
 */

export interface League {
  id: string;
  name: string;
  icon?: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  
  // League Settings
  settings: {
    season: string; // e.g., "2024-2025"
    maxTeams: number;
    salaryCap: number;
    rosterSize: number;
    scoringType: "head-to-head" | "points" | "rotisserie";
    tradeDeadline?: Date;
    playoffStart?: Date;
  };
  
  // Members
  members: LeagueMember[];
  
  // Commissioner
  commissionerId: string;
  
  // Status
  status: "draft" | "active" | "playoffs" | "completed" | "archived";
  
  // League Rules (reference to JSON file or embedded)
  rulesUrl?: string;
  
  // Chat Channels
  channels: {
    generalChatId: string;
    tradeTalkId?: string;
    trashTalkId?: string;
  };
}

export interface LeagueMember {
  userId: string;
  userName: string;
  userAvatar?: string;
  teamName: string;
  teamStrategy: "win-now" | "rebuild" | "balanced";
  joinedAt: Date;
  isActive: boolean;
  
  // Team Info
  team: {
    wins: number;
    losses: number;
    ties: number;
    points: number;
    rank: number;
    salaryCap: number;
    rosterCount: number;
  };
}

export interface CreateLeagueInput {
  name: string;
  description?: string;
  icon?: string;
  season: string;
  maxTeams: number;
  salaryCap: number;
  rosterSize: number;
  scoringType: "head-to-head" | "points" | "rotisserie";
}

export interface UpdateLeagueInput {
  name?: string;
  description?: string;
  icon?: string;
  settings?: Partial<League["settings"]>;
}

