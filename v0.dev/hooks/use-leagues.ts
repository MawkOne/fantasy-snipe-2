"use client";

import { useState, useEffect } from "react";
import {
  collection,
  query,
  where,
  onSnapshot,
  addDoc,
  updateDoc,
  doc,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { League, CreateLeagueInput, UpdateLeagueInput } from "@/types/league";

/**
 * Hook to manage leagues for the current user
 */
export function useLeagues(userId: string) {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [activeLeagueId, setActiveLeagueId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch leagues where user is a member
  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    // Simplified query - removed orderBy to avoid needing a compound index
    const q = query(
      collection(db, "leagues"),
      where("members", "array-contains", { userId })
    );

    const unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        const fetchedLeagues: League[] = snapshot.docs.map((doc) => ({
          id: doc.id,
          ...doc.data(),
          createdAt: doc.data().createdAt?.toDate(),
          updatedAt: doc.data().updatedAt?.toDate(),
          settings: {
            ...doc.data().settings,
            tradeDeadline: doc.data().settings?.tradeDeadline?.toDate(),
            playoffStart: doc.data().settings?.playoffStart?.toDate(),
          },
        })) as League[];

        // Sort by updatedAt in memory (newest first)
        fetchedLeagues.sort((a, b) => {
          const timeA = a.updatedAt?.getTime() || 0;
          const timeB = b.updatedAt?.getTime() || 0;
          return timeB - timeA;
        });

        setLeagues(fetchedLeagues);
        
        // Set first league as active if none selected
        if (!activeLeagueId && fetchedLeagues.length > 0) {
          setActiveLeagueId(fetchedLeagues[0].id);
          localStorage.setItem("activeLeagueId", fetchedLeagues[0].id);
        }
        
        setLoading(false);
      },
      (err) => {
        console.error("Error fetching leagues:", err);
        setError("Failed to load leagues.");
        setLoading(false);
      }
    );

    // Load saved active league from localStorage
    const savedLeagueId = localStorage.getItem("activeLeagueId");
    if (savedLeagueId) {
      setActiveLeagueId(savedLeagueId);
    }

    return () => unsubscribe();
  }, [userId, activeLeagueId]);

  // Get the currently active league
  const activeLeague = leagues.find((league) => league.id === activeLeagueId);

  // Switch to a different league
  const switchLeague = (leagueId: string) => {
    setActiveLeagueId(leagueId);
    localStorage.setItem("activeLeagueId", leagueId);
  };

  // Create a new league
  const createLeague = async (input: CreateLeagueInput) => {
    try {
      const newLeague = {
        name: input.name,
        description: input.description,
        icon: input.icon,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
        settings: {
          season: input.season,
          maxTeams: input.maxTeams,
          salaryCap: input.salaryCap,
          rosterSize: input.rosterSize,
          scoringType: input.scoringType,
        },
        members: [
          {
            userId,
            userName: "User", // TODO: Get from auth context
            teamName: "My Team",
            teamStrategy: "balanced",
            joinedAt: serverTimestamp(),
            isActive: true,
            team: {
              wins: 0,
              losses: 0,
              ties: 0,
              points: 0,
              rank: 1,
              salaryCap: 0,
              rosterCount: 0,
            },
          },
        ],
        commissionerId: userId,
        status: "draft",
        channels: {
          generalChatId: "", // Will be created separately
        },
      };

      const docRef = await addDoc(collection(db, "leagues"), newLeague);
      
      // Switch to the newly created league
      switchLeague(docRef.id);
      
      return docRef.id;
    } catch (err) {
      console.error("Error creating league:", err);
      setError("Failed to create league.");
      throw err;
    }
  };

  // Update league settings
  const updateLeague = async (leagueId: string, updates: UpdateLeagueInput) => {
    try {
      const leagueRef = doc(db, "leagues", leagueId);
      await updateDoc(leagueRef, {
        ...updates,
        updatedAt: serverTimestamp(),
      });
    } catch (err) {
      console.error("Error updating league:", err);
      setError("Failed to update league.");
      throw err;
    }
  };

  return {
    leagues,
    activeLeague,
    activeLeagueId,
    loading,
    error,
    switchLeague,
    createLeague,
    updateLeague,
  };
}

/**
 * Hook to get all members of a specific league
 */
export function useLeagueMembers(leagueId: string | null) {
  const [members, setMembers] = useState<League["members"]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!leagueId) {
      setLoading(false);
      return;
    }

    const leagueRef = doc(db, "leagues", leagueId);
    const unsubscribe = onSnapshot(leagueRef, (snapshot) => {
      if (snapshot.exists()) {
        const data = snapshot.data() as League;
        setMembers(data.members || []);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [leagueId]);

  return { members, loading };
}

