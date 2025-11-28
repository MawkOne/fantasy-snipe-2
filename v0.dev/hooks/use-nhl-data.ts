"use client";

import { useState, useEffect } from "react";
import { fetchFromCloudSQL, CLOUD_SQL_API } from "@/lib/google-cloud-sql";

/**
 * NHL Player data from Cloud SQL
 */
export interface NHLPlayer {
  id: number;
  full_name: string;
  first_name: string;
  last_name: string;
  sweater_number: number;
  position_code: string;
  headshot_url: string;
  is_active: boolean;
  team_id: number;
}

/**
 * NHL Game data
 */
export interface NHLGame {
  id: number;
  game_date: string;
  home_team_id: number;
  away_team_id: number;
  home_score: number;
  away_score: number;
  game_state: string;
}

/**
 * Player game stats
 */
export interface PlayerGameStats {
  player_id: number;
  game_id: number;
  goals: number;
  assists: number;
  points: number;
  shots: number;
  hits: number;
  blocked_shots: number;
  pim: number;
  toi: string;
}

/**
 * Hook to search for NHL players
 */
export function usePlayerSearch(searchTerm: string) {
  const [players, setPlayers] = useState<NHLPlayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!searchTerm || searchTerm.length < 2) {
      setPlayers([]);
      return;
    }

    const searchPlayers = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL<NHLPlayer[]>(
          `/api/players/search?q=${encodeURIComponent(searchTerm)}`
        );
        setPlayers(data);
      } catch (err) {
        console.error("Error searching players:", err);
        setError(err instanceof Error ? err.message : "Failed to search players");
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timer = setTimeout(searchPlayers, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  return { players, loading, error };
}

/**
 * Hook to get a single player's details
 */
export function usePlayer(playerId: number | null) {
  const [player, setPlayer] = useState<NHLPlayer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!playerId) {
      setLoading(false);
      return;
    }

    const fetchPlayer = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL<NHLPlayer>(
          `/api/players/${playerId}`
        );
        setPlayer(data);
      } catch (err) {
        console.error("Error fetching player:", err);
        setError(err instanceof Error ? err.message : "Failed to load player");
      } finally {
        setLoading(false);
      }
    };

    fetchPlayer();
  }, [playerId]);

  return { player, loading, error };
}

/**
 * Hook to get player's season stats
 */
export function usePlayerSeasonStats(playerId: number | null, season: string = "20242025") {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!playerId) {
      setLoading(false);
      return;
    }

    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL(
          `/api/players/${playerId}/season-stats?season=${season}`
        );
        setStats(data);
      } catch (err) {
        console.error("Error fetching stats:", err);
        setError(err instanceof Error ? err.message : "Failed to load stats");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [playerId, season]);

  return { stats, loading, error };
}

/**
 * Hook to get upcoming games
 */
export function useUpcomingGames(teamId?: number, limit: number = 10) {
  const [games, setGames] = useState<NHLGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true);
        const url = teamId 
          ? `/api/games/upcoming?team_id=${teamId}&limit=${limit}`
          : `/api/games/upcoming?limit=${limit}`;
        const data = await fetchFromCloudSQL<NHLGame[]>(url);
        setGames(data);
      } catch (err) {
        console.error("Error fetching games:", err);
        setError(err instanceof Error ? err.message : "Failed to load games");
      } finally {
        setLoading(false);
      }
    };

    fetchGames();
  }, [teamId, limit]);

  return { games, loading, error };
}

/**
 * Hook to get player game log (recent games)
 */
export function usePlayerGameLog(playerId: number | null, limit: number = 10) {
  const [gameLogs, setGameLogs] = useState<PlayerGameStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!playerId) {
      setLoading(false);
      return;
    }

    const fetchGameLog = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL<PlayerGameStats[]>(
          `/api/players/${playerId}/game-log?limit=${limit}`
        );
        setGameLogs(data);
      } catch (err) {
        console.error("Error fetching game log:", err);
        setError(err instanceof Error ? err.message : "Failed to load game log");
      } finally {
        setLoading(false);
      }
    };

    fetchGameLog();
  }, [playerId, limit]);

  return { gameLogs, loading, error };
}

/**
 * Hook to get active NHL teams
 */
export function useNHLTeams() {
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL<any[]>('/api/teams');
        setTeams(data);
      } catch (err) {
        console.error("Error fetching teams:", err);
        setError(err instanceof Error ? err.message : "Failed to load teams");
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, []);

  return { teams, loading, error };
}

