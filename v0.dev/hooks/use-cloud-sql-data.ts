"use client";

import { useState, useEffect } from "react";
import { fetchFromCloudSQL, CLOUD_SQL_API } from "@/lib/google-cloud-sql";

/**
 * Hook to fetch league data from Google Cloud SQL
 */
export function useCloudSQLLeagues() {
  const [leagues, setLeagues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeagues = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL(CLOUD_SQL_API.endpoints.getLeagues);
        setLeagues(data);
      } catch (err) {
        console.error("Error fetching leagues from Cloud SQL:", err);
        setError(err instanceof Error ? err.message : "Failed to load leagues");
      } finally {
        setLoading(false);
      }
    };

    fetchLeagues();
  }, []);

  return { leagues, loading, error };
}

/**
 * Hook to fetch historical data for a specific league and season
 */
export function useLeagueHistory(leagueId: string | null, season: string) {
  const [history, setHistory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!leagueId) {
      setLoading(false);
      return;
    }

    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL(
          CLOUD_SQL_API.endpoints.getLeagueHistory(leagueId, season)
        );
        setHistory(data);
      } catch (err) {
        console.error("Error fetching league history:", err);
        setError(err instanceof Error ? err.message : "Failed to load history");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [leagueId, season]);

  return { history, loading, error };
}

/**
 * Hook to fetch team roster from Cloud SQL
 */
export function useTeamRoster(teamId: string | null) {
  const [roster, setRoster] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!teamId) {
      setLoading(false);
      return;
    }

    const fetchRoster = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL(
          CLOUD_SQL_API.endpoints.getTeamRoster(teamId)
        );
        setRoster(data);
      } catch (err) {
        console.error("Error fetching roster:", err);
        setError(err instanceof Error ? err.message : "Failed to load roster");
      } finally {
        setLoading(false);
      }
    };

    fetchRoster();
  }, [teamId]);

  return { roster, loading, error };
}

/**
 * Hook to fetch player stats
 */
export function usePlayerStats(playerId: string | null, season: string) {
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
          CLOUD_SQL_API.endpoints.getPlayerStats(playerId, season)
        );
        setStats(data);
      } catch (err) {
        console.error("Error fetching player stats:", err);
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
 * Hook to fetch league analytics
 */
export function useLeagueAnalytics(leagueId: string | null) {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!leagueId) {
      setLoading(false);
      return;
    }

    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await fetchFromCloudSQL(
          CLOUD_SQL_API.endpoints.getLeagueAnalytics(leagueId)
        );
        setAnalytics(data);
      } catch (err) {
        console.error("Error fetching analytics:", err);
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [leagueId]);

  return { analytics, loading, error };
}

