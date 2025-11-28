/**
 * Google Cloud SQL Connection Configuration
 * 
 * For security, Cloud SQL should be accessed via:
 * 1. Cloud SQL Proxy (for local development)
 * 2. Private IP (for production in GCP)
 * 3. API Backend (recommended for Next.js frontend)
 */

export const CLOUD_SQL_CONFIG = {
  projectId: 'fantasy-snipe-ai',
  region: 'northamerica-northeast1', // Montreal
  instanceName: 'nhl-api-db-montreal',
  
  // Connection string format for Cloud SQL Proxy
  connectionName: 'fantasy-snipe-ai:northamerica-northeast1:nhl-api-db-montreal',
  
  // Network details
  privateIP: '10.112.0.3',
  publicIP: '34.47.23.137',
  port: 5432,
  
  // Database credentials (store in environment variables)
  database: process.env.NEXT_PUBLIC_CLOUD_SQL_DATABASE || 'nhl_api',
  user: process.env.NEXT_PUBLIC_CLOUD_SQL_USER,
  password: process.env.NEXT_PUBLIC_CLOUD_SQL_PASSWORD,
};

/**
 * API endpoints to access Cloud SQL data
 * These should be implemented in your FastAPI backend
 */
export const CLOUD_SQL_API = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://fastapi-production-45ce.up.railway.app',
  
  endpoints: {
    // League data
    getLeagues: '/api/leagues',
    getLeague: (leagueId: string) => `/api/leagues/${leagueId}`,
    getLeagueHistory: (leagueId: string, season: string) => `/api/leagues/${leagueId}/history/${season}`,
    
    // Player data
    getPlayers: '/api/players',
    getPlayer: (playerId: string) => `/api/players/${playerId}`,
    getPlayerStats: (playerId: string, season: string) => `/api/players/${playerId}/stats/${season}`,
    
    // Team data
    getTeams: (leagueId: string) => `/api/leagues/${leagueId}/teams`,
    getTeam: (teamId: string) => `/api/teams/${teamId}`,
    getTeamRoster: (teamId: string) => `/api/teams/${teamId}/roster`,
    
    // Transaction data
    getTransactions: (leagueId: string, season: string) => `/api/leagues/${leagueId}/transactions/${season}`,
    
    // Weekly results
    getWeeklyResults: (leagueId: string, season: string) => `/api/leagues/${leagueId}/weekly/${season}`,
    
    // Analytics
    getLeagueAnalytics: (leagueId: string) => `/api/leagues/${leagueId}/analytics`,
    getCompetitiveBalance: (leagueId: string) => `/api/leagues/${leagueId}/competitive-balance`,
  },
};

/**
 * Helper function to make API calls to Cloud SQL backend
 */
export async function fetchFromCloudSQL<T>(endpoint: string): Promise<T> {
  const url = `${CLOUD_SQL_API.baseUrl}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }
  
  return response.json();
}

