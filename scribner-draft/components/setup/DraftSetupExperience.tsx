"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, ClipboardCheck, ShieldAlert } from "lucide-react";
import { ApiError, asRecord, clearAdminSession, copyText, postJson, readAdminSession, saveAdminSession } from "./api";
import { CreateDraftScreen, RestoringSetup } from "./CreateDraftScreen";
import { DraftFormatSection } from "./DraftFormatSection";
import { IdentitySection } from "./IdentitySection";
import { ReviewSetupDialog } from "./ReviewSetupDialog";
import { ScoringSection } from "./ScoringSection";
import { SetupHeader } from "./SetupHeader";
import { TeamsSection } from "./TeamsSection";
import type {
  ActionFeedback,
  DraftSetup,
  RosterRequirements,
  SaveStatus,
  ScoringMetric,
  Team,
  TeamBusyState,
  TeamInput,
} from "./types";
import {
  createEmptySetup,
  normalizeSetupResponse,
  normalizeTeam,
  rosterTarget,
  sameRoster,
  sameScoring,
  scoringPayload,
  validateSetup,
} from "./setup-utils";
import { cx, focusRing } from "./ui";

interface SavedFormat {
  rounds: number;
  rosterReqs: RosterRequirements;
}

function messageFrom(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

function stringFrom(record: Record<string, unknown>, ...keys: string[]): string | undefined {
  for (const key of keys) {
    if (typeof record[key] === "string" && record[key]) return record[key] as string;
  }
  return undefined;
}

function teamsFromResponse(data: Record<string, unknown>): Team[] | null {
  const source = data.teams ?? asRecord(data.room).teams;
  return Array.isArray(source) ? source.map((team) => normalizeTeam(team)) : null;
}

function inviteDeliveryUnavailable(data: Record<string, unknown>): boolean {
  if (data.emailSent === false || data.emailConfigured === false) return true;
  const status = String(data.emailStatus ?? data.deliveryStatus ?? data.code ?? "").toLowerCase();
  return ["not-configured", "not_configured", "disabled", "unavailable", "no-provider"].some((value) => status.includes(value));
}

export function DraftSetupExperience() {
  const [booting, setBooting] = useState(true);
  const [setup, setSetup] = useState<DraftSetup | null>(null);
  const [createLoading, setCreateLoading] = useState(false);
  const [createFeedback, setCreateFeedback] = useState<ActionFeedback>();

  const [savedName, setSavedName] = useState<string | null>(null);
  const [savedFormat, setSavedFormat] = useState<SavedFormat | null>(null);
  const [savedScoring, setSavedScoring] = useState<ScoringMetric[] | null>(null);

  const [identityStatus, setIdentityStatus] = useState<SaveStatus>("idle");
  const [formatStatus, setFormatStatus] = useState<SaveStatus>("idle");
  const [scoringStatus, setScoringStatus] = useState<SaveStatus>("idle");
  const [identityFeedback, setIdentityFeedback] = useState<ActionFeedback>();
  const [formatFeedback, setFormatFeedback] = useState<ActionFeedback>();
  const [scoringFeedback, setScoringFeedback] = useState<ActionFeedback>();

  const [teamBusy, setTeamBusy] = useState<TeamBusyState | null>(null);
  const [teamFeedback, setTeamFeedback] = useState<ActionFeedback>();
  const [copiedTeamId, setCopiedTeamId] = useState<string | null>(null);
  const [roomCodeCopied, setRoomCodeCopied] = useState(false);

  const [showValidation, setShowValidation] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startFeedback, setStartFeedback] = useState<ActionFeedback>();

  useEffect(() => {
    let cancelled = false;
    const session = readAdminSession();
    if (!session) {
      setBooting(false);
      return () => {
        cancelled = true;
      };
    }

    void postJson(
      `/api/room/${encodeURIComponent(session.roomId)}`,
      { action: "get-setup", adminToken: session.adminToken },
      "Could not reopen this draft setup.",
    )
      .then((data) => {
        if (cancelled) return;
        const restored = normalizeSetupResponse(data, session.roomId, session.adminToken);
        setSetup(restored);
        setSavedName(restored.draftName);
        setSavedFormat({ rounds: restored.rounds, rosterReqs: { ...restored.rosterReqs } });
        setSavedScoring(restored.scoring.map((metric) => ({ ...metric })));
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        clearAdminSession();
        setCreateFeedback({
          tone: "warning",
          message: `${messageFrom(error, "The saved draft could not be reopened.")} Create a new room or reopen setup from the original browser link.`,
        });
      })
      .finally(() => {
        if (!cancelled) setBooting(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const pollingRoomId = setup?.roomId;
  const pollingAdminToken = setup?.adminToken;
  useEffect(() => {
    if (!pollingRoomId || !pollingAdminToken || teamBusy || starting) return;
    let cancelled = false;

    const refreshSharedSetup = async () => {
      if (document.hidden) return;
      try {
        const data = await postJson(
          `/api/room/${encodeURIComponent(pollingRoomId)}`,
          { action: "get-setup", adminToken: pollingAdminToken },
          "Could not refresh setup.",
        );
        if (cancelled) return;
        const refreshed = normalizeSetupResponse(data, pollingRoomId, pollingAdminToken);
        setSetup((current) =>
          current && current.roomId === pollingRoomId
            ? { ...current, status: refreshed.status, teams: refreshed.teams }
            : current,
        );
      } catch {
        // Keep local edits intact; the next polling interval will retry.
      }
    };

    const intervalId = window.setInterval(() => void refreshSharedSetup(), 3000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [pollingRoomId, pollingAdminToken, starting, teamBusy]);

  const createDraft = async (draftName: string) => {
    setCreateLoading(true);
    setCreateFeedback(undefined);
    try {
      const data = await postJson(
        "/api/room",
        { draftName },
        "The draft could not be created.",
      );
      const roomId = stringFrom(data, "roomId", "id");
      const adminToken = stringFrom(data, "adminToken");
      if (!roomId || !adminToken) {
        throw new Error("The server created a room but did not return commissioner access. Try again.");
      }
      const confirmedName = stringFrom(data, "draftName", "name") ?? draftName;
      const nextSetup = createEmptySetup(roomId, adminToken, confirmedName);
      saveAdminSession({ roomId, adminToken });
      setSetup(nextSetup);
      setSavedName(confirmedName);
      setSavedFormat(null);
      setSavedScoring(null);
    } catch (error) {
      setCreateFeedback({ tone: "error", message: messageFrom(error, "The draft could not be created.") });
    } finally {
      setCreateLoading(false);
    }
  };

  const identityDirty = Boolean(setup && savedName !== setup.draftName);
  const formatDirty = Boolean(
    setup &&
      (!savedFormat ||
        savedFormat.rounds !== setup.rounds ||
        !sameRoster(savedFormat.rosterReqs, setup.rosterReqs)),
  );
  const scoringDirty = Boolean(setup && (!savedScoring || !sameScoring(savedScoring, setup.scoring)));
  const unsavedCount = [identityDirty, formatDirty, scoringDirty].filter(Boolean).length;
  const validationIssues = useMemo(() => (setup ? validateSetup(setup) : []), [setup]);

  const saveIdentity = async () => {
    if (!setup) return;
    const draftName = setup.draftName.trim();
    if (!draftName || draftName.length > 80) {
      setIdentityStatus("error");
      setIdentityFeedback({ tone: "error", message: "Enter a draft name from 1 to 80 characters." });
      return;
    }
    setIdentityStatus("saving");
    setIdentityFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "update-room-name", adminToken: setup.adminToken, draftName },
        "The draft name could not be saved.",
      );
      const confirmedName = stringFrom(data, "draftName", "name") ?? draftName;
      setSetup((current) => (current ? { ...current, draftName: confirmedName } : current));
      setSavedName(confirmedName);
      setIdentityStatus("saved");
      setIdentityFeedback({ tone: "success", message: "Draft name saved." });
    } catch (error) {
      setIdentityStatus("error");
      setIdentityFeedback({ tone: "error", message: messageFrom(error, "The draft name could not be saved.") });
    }
  };

  const saveFormat = async () => {
    if (!setup) return;
    const formatIssues = validateSetup(setup).filter((issue) => issue.section === "format");
    if (formatIssues.length) {
      setFormatStatus("error");
      setFormatFeedback({ tone: "error", message: formatIssues.map((issue) => issue.message).join(" ") });
      return;
    }
    setFormatStatus("saving");
    setFormatFeedback(undefined);
    try {
      await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        {
          action: "update-draft-config",
          adminToken: setup.adminToken,
          rounds: setup.rounds,
          rosterReqs: setup.rosterReqs,
        },
        "Draft format could not be saved.",
      );
      setSavedFormat({ rounds: setup.rounds, rosterReqs: { ...setup.rosterReqs } });
      setFormatStatus("saved");
      setFormatFeedback({ tone: "success", message: "Draft format and roster target saved." });
    } catch (error) {
      setFormatStatus("error");
      setFormatFeedback({ tone: "error", message: messageFrom(error, "Draft format could not be saved.") });
    }
  };

  const saveScoring = async () => {
    if (!setup) return;
    const scoringIssues = validateSetup(setup).filter((issue) => issue.section === "scoring");
    if (scoringIssues.length) {
      setScoringStatus("error");
      setScoringFeedback({ tone: "error", message: scoringIssues.map((issue) => issue.message).join(" ") });
      return;
    }
    setScoringStatus("saving");
    setScoringFeedback(undefined);
    try {
      await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        {
          action: "update-scoring-config",
          adminToken: setup.adminToken,
          config: scoringPayload(setup.scoring),
        },
        "Scoring could not be saved.",
      );
      setSavedScoring(setup.scoring.map((metric) => ({ ...metric })));
      setScoringStatus("saved");
      setScoringFeedback({ tone: "success", message: "Scoring saved. Player projections will use these values." });
    } catch (error) {
      setScoringStatus("error");
      setScoringFeedback({ tone: "error", message: messageFrom(error, "Scoring could not be saved.") });
    }
  };

  const addTeam = async (input: TeamInput): Promise<boolean> => {
    if (!setup) return false;
    setTeamBusy({ action: "add" });
    setTeamFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "add-team", adminToken: setup.adminToken, ...input },
        "The team could not be added.",
      );
      const returnedTeams = teamsFromResponse(data);
      if (returnedTeams) {
        setSetup((current) => (current ? { ...current, teams: returnedTeams } : current));
      } else {
        const source = data.team ?? data;
        const team = normalizeTeam(source, {
          name: input.teamName,
          ownerEmail: input.ownerEmail,
          isAdminTeam: input.isAdminTeam,
        });
        if (!team.id) throw new Error("The server did not return the new team ID. Refresh setup and try again.");
        setSetup((current) =>
          current
            ? {
                ...current,
                teams: [
                  ...current.teams.map((existing) =>
                    input.isAdminTeam ? { ...existing, isAdminTeam: false } : existing,
                  ),
                  team,
                ],
              }
            : current,
        );
      }
      setTeamFeedback({ tone: "success", message: `${input.teamName} added. Copy or send their private invite when ready.` });
      return true;
    } catch (error) {
      setTeamFeedback({ tone: "error", message: messageFrom(error, "The team could not be added.") });
      return false;
    } finally {
      setTeamBusy(null);
    }
  };

  const updateTeam = async (teamId: string, values: { teamName: string; ownerEmail: string }): Promise<boolean> => {
    if (!setup) return false;
    setTeamBusy({ action: "edit", teamId });
    setTeamFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "update-team", adminToken: setup.adminToken, teamId, ...values },
        "The team could not be updated.",
      );
      const returnedTeams = teamsFromResponse(data);
      setSetup((current) => {
        if (!current) return current;
        if (returnedTeams) return { ...current, teams: returnedTeams };
        const source = data.team ?? data;
        return {
          ...current,
          teams: current.teams.map((team) =>
            team.id === teamId
              ? normalizeTeam(source, { ...team, name: values.teamName, ownerEmail: values.ownerEmail })
              : team,
          ),
        };
      });
      setTeamFeedback({ tone: "success", message: `${values.teamName} updated.` });
      return true;
    } catch (error) {
      setTeamFeedback({ tone: "error", message: messageFrom(error, "The team could not be updated.") });
      return false;
    } finally {
      setTeamBusy(null);
    }
  };

  const setAdminTeam = async (teamId: string) => {
    if (!setup || setup.teams.find((team) => team.id === teamId)?.isAdminTeam) return;
    setTeamBusy({ action: "admin", teamId });
    setTeamFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "set-admin-team", adminToken: setup.adminToken, teamId },
        "My team could not be assigned.",
      );
      const returnedTeams = teamsFromResponse(data);
      setSetup((current) =>
        current
          ? {
              ...current,
              teams:
                returnedTeams ??
                current.teams.map((team) => ({ ...team, isAdminTeam: team.id === teamId })),
            }
          : current,
      );
      const teamName = setup.teams.find((team) => team.id === teamId)?.name ?? "Team";
      setTeamFeedback({ tone: "success", message: `${teamName} is now My team.` });
    } catch (error) {
      setTeamFeedback({ tone: "error", message: messageFrom(error, "My team could not be assigned.") });
    } finally {
      setTeamBusy(null);
    }
  };

  const removeTeam = async (teamId: string) => {
    if (!setup) return;
    const teamName = setup.teams.find((team) => team.id === teamId)?.name ?? "Team";
    setTeamBusy({ action: "remove", teamId });
    setTeamFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "remove-team", adminToken: setup.adminToken, teamId },
        "The team could not be removed.",
      );
      const returnedTeams = teamsFromResponse(data);
      setSetup((current) =>
        current
          ? { ...current, teams: returnedTeams ?? current.teams.filter((team) => team.id !== teamId) }
          : current,
      );
      setTeamFeedback({ tone: "success", message: `${teamName} removed. Assign My team again if needed.` });
    } catch (error) {
      setTeamFeedback({ tone: "error", message: messageFrom(error, "The team could not be removed.") });
    } finally {
      setTeamBusy(null);
    }
  };

  const inviteUrl = useCallback(
    (team: Team, explicitLink?: string): string => {
      const value = explicitLink || team.inviteLink;
      if (value) {
        try {
          return new URL(value, window.location.origin).toString();
        } catch {
          return value;
        }
      }
      if (!setup || !team.inviteToken) return "";
      return `${window.location.origin}/room/${encodeURIComponent(setup.roomId)}?invite=${encodeURIComponent(team.inviteToken)}`;
    },
    [setup],
  );

  const copyInvite = async (teamId: string) => {
    if (!setup) return;
    const team = setup.teams.find((candidate) => candidate.id === teamId);
    if (!team) return;
    const link = inviteUrl(team);
    if (!link) {
      setTeamFeedback({ tone: "error", message: `No invite link is available for ${team.name}. Try Send Invite to generate one.` });
      return;
    }
    if (await copyText(link)) {
      setCopiedTeamId(teamId);
      setTeamFeedback({ tone: "success", message: `${team.name} invite link copied. Anyone with this private link can enter as that team.` });
      window.setTimeout(() => setCopiedTeamId((current) => (current === teamId ? null : current)), 1800);
    } else {
      setTeamFeedback({ tone: "error", message: `Clipboard access was blocked. Copy this link manually: ${link}` });
    }
  };

  const sendInvite = async (teamId: string) => {
    if (!setup) return;
    const team = setup.teams.find((candidate) => candidate.id === teamId);
    if (!team) return;
    setTeamBusy({ action: "invite", teamId });
    setTeamFeedback(undefined);
    try {
      const data = await postJson(
        `/api/room/${encodeURIComponent(setup.roomId)}`,
        { action: "send-invite", adminToken: setup.adminToken, teamId, origin: window.location.origin },
        "The invite could not be sent.",
      );
      const explicitLink = stringFrom(data, "inviteLink", "inviteUrl", "link");
      const delivered = !inviteDeliveryUnavailable(data);
      const source = data.team ?? data;
      setSetup((current) =>
        current
          ? {
              ...current,
              teams: current.teams.map((candidate) =>
                candidate.id === teamId
                  ? normalizeTeam(source, {
                      ...candidate,
                      inviteLink: explicitLink ?? candidate.inviteLink,
                      inviteState:
                        candidate.inviteState === "joined"
                          ? "joined"
                          : delivered
                            ? "sent"
                            : candidate.inviteState,
                    })
                  : candidate,
              ),
            }
          : current,
      );

      if (!delivered) {
        const link = inviteUrl(team, explicitLink);
        const copied = Boolean(link) && (await copyText(link));
        setTeamFeedback({
          tone: "warning",
          message: copied
            ? `Email delivery is not configured. ${team.name}’s private invite link was copied instead.`
            : `Email delivery is not configured. Use Copy Invite Link for ${team.name}.`,
        });
      } else {
        setTeamFeedback({ tone: "success", message: `Invite sent to ${team.ownerEmail}. You can resend or copy the same private link at any time.` });
      }
    } catch (error) {
      const data = error instanceof ApiError ? error.data : {};
      const explicitLink = stringFrom(data, "inviteLink", "inviteUrl", "link");
      if (explicitLink && (error instanceof ApiError ? inviteDeliveryUnavailable(data) || error.status >= 400 : false)) {
        const copied = await copyText(inviteUrl(team, explicitLink));
        setSetup((current) =>
          current
            ? {
                ...current,
                teams: current.teams.map((candidate) =>
                  candidate.id === teamId ? { ...candidate, inviteLink: explicitLink } : candidate,
                ),
              }
            : current,
        );
        setTeamFeedback({
          tone: "warning",
          message: copied
            ? `Email delivery is unavailable. ${team.name}’s private invite link was copied instead.`
            : `Email delivery is unavailable. Use Copy Invite Link for ${team.name}.`,
        });
      } else {
        setTeamFeedback({ tone: "error", message: messageFrom(error, "The invite could not be sent. Use Copy Invite Link instead.") });
      }
    } finally {
      setTeamBusy(null);
    }
  };

  const openReview = () => {
    if (!setup) return;
    setShowValidation(true);
    setStartFeedback(undefined);
    if (validationIssues.length) {
      window.setTimeout(() => document.getElementById("setup-validation")?.focus(), 0);
      return;
    }
    setReviewOpen(true);
  };

  const closeReview = useCallback(() => {
    setReviewOpen(false);
  }, []);

  const startDraft = async () => {
    if (!setup) return;
    const issues = validateSetup(setup);
    if (issues.length) {
      setStartFeedback({ tone: "error", message: issues.map((issue) => issue.message).join(" ") });
      return;
    }
    setStarting(true);
    setStartFeedback(undefined);
    try {
      const endpoint = `/api/room/${encodeURIComponent(setup.roomId)}`;
      const draftName = setup.draftName.trim();

      await postJson(
        endpoint,
        { action: "update-room-name", adminToken: setup.adminToken, draftName },
        "The draft name could not be saved before starting.",
      );
      setSavedName(draftName);
      setSetup((current) => (current ? { ...current, draftName } : current));
      setIdentityStatus("saved");

      await postJson(
        endpoint,
        {
          action: "update-draft-config",
          adminToken: setup.adminToken,
          rounds: setup.rounds,
          rosterReqs: setup.rosterReqs,
        },
        "Draft format could not be saved before starting.",
      );
      setSavedFormat({ rounds: setup.rounds, rosterReqs: { ...setup.rosterReqs } });
      setFormatStatus("saved");

      await postJson(
        endpoint,
        {
          action: "update-scoring-config",
          adminToken: setup.adminToken,
          config: scoringPayload(setup.scoring),
        },
        "Scoring could not be saved before starting.",
      );
      setSavedScoring(setup.scoring.map((metric) => ({ ...metric })));
      setScoringStatus("saved");

      await postJson(
        endpoint,
        { action: "start-draft", adminToken: setup.adminToken },
        "The draft could not be started. Review the setup and try again.",
      );

      window.location.assign(
        `/room/${encodeURIComponent(setup.roomId)}/admin?token=${encodeURIComponent(setup.adminToken)}`,
      );
    } catch (error) {
      setStartFeedback({ tone: "error", message: messageFrom(error, "The draft could not be started.") });
      setStarting(false);
    }
  };

  if (booting) return <RestoringSetup />;
  if (!setup) {
    return <CreateDraftScreen onCreate={createDraft} loading={createLoading} feedback={createFeedback} />;
  }

  if (setup.status !== "setup") {
    const completed = setup.status === "completed";
    return (
      <div className="min-h-screen bg-ink-900 px-4 py-10 text-fg sm:px-6">
        <div className="mx-auto w-full max-w-lg overflow-hidden rounded-card border border-ink-700 bg-ink-850 shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
          <div className="border-b border-ink-700 bg-ink-800/45 p-5 sm:p-6">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-accent">
              Commissioner session
            </p>
            <h1 className="mt-2 text-2xl font-black tracking-tight text-fg">
              {setup.draftName}
            </h1>
            <p className="mt-1 text-sm text-fg-muted">
              Room {setup.roomId} · {completed ? "Draft complete" : "Draft in progress"}
            </p>
          </div>
          <div className="p-5 sm:p-6">
            <p className="text-sm leading-6 text-fg-muted">
              {completed
                ? "Review the final rosters and revealed results, or clear this browser session to create another draft."
                : "Your draft is still active. Resume the commissioner room without changing teams, scoring, or draft progress."}
            </p>
            <div className="mt-5 grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() =>
                  window.location.assign(
                    `/room/${encodeURIComponent(setup.roomId)}/admin?token=${encodeURIComponent(setup.adminToken)}`,
                  )
                }
                className={cx(
                  "inline-flex min-h-[48px] items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 hover:bg-accent-bright",
                  focusRing,
                )}
              >
                {completed ? "View final draft" : "Resume draft"}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
              <button
                type="button"
                onClick={() => {
                  clearAdminSession();
                  setSetup(null);
                  setSavedName(null);
                  setSavedFormat(null);
                  setSavedScoring(null);
                }}
                className={cx(
                  "min-h-[48px] rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg-muted hover:border-accent/40 hover:text-fg",
                  focusRing,
                )}
              >
                Create another draft
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const adminTeam = setup.teams.find((team) => team.isAdminTeam);
  const target = rosterTarget(setup.rosterReqs);
  const invitedCount = setup.teams.filter((team) => team.inviteState !== "not-sent").length;

  return (
    <div className="min-h-screen bg-ink-900 text-fg">
      <SetupHeader
        draftName={setup.draftName}
        roomId={setup.roomId}
        copied={roomCodeCopied}
        onCopyRoomCode={() => {
          void copyText(setup.roomId).then((copied) => {
            setRoomCodeCopied(copied);
            if (copied) window.setTimeout(() => setRoomCodeCopied(false), 1600);
          });
        }}
      />

      <main className="mx-auto w-full max-w-7xl px-4 pb-28 pt-6 sm:px-6 sm:pt-8 lg:px-8">
        <div className="mb-6 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Commissioner setup</p>
            <h1 className="mt-1.5 text-2xl font-black tracking-[-0.03em] text-fg sm:text-3xl">Build the room before puck drop.</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-fg-muted">
              Add owners, assign your team, set roster targets, then review and lock the draft.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 sm:min-w-[440px]">
            <OverviewStat label="Teams" value={String(setup.teams.length)} detail={adminTeam ? "My team set" : "Assign yours"} warning={!adminTeam} />
            <OverviewStat label="Invited" value={`${invitedCount}/${setup.teams.length}`} detail="Sent or joined" warning={setup.teams.length > invitedCount} />
            <OverviewStat label="Roster" value={`${target}`} detail={`${setup.rounds} rounds`} warning={setup.rounds < target} />
          </div>
        </div>

        {showValidation && validationIssues.length > 0 ? (
          <div
            id="setup-validation"
            tabIndex={-1}
            className={cx("mb-4 rounded-card border border-loss/40 bg-loss/10 p-4", focusRing)}
            role="alert"
          >
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-loss" aria-hidden="true" />
              <div>
                <h2 className="text-sm font-extrabold text-red-100">Finish these items before review</h2>
                <ul className="mt-2 space-y-1.5 text-xs leading-5 text-red-100/85">
                  {validationIssues.map((issue, index) => (
                    <li key={`${issue.section}-${issue.message}`}>
                      <a className={cx("underline decoration-red-300/40 underline-offset-2 hover:text-white", focusRing)} href={`#${issue.section}`}>
                        {index + 1}. {issue.message}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-12">
          <div className="xl:col-span-5">
            <IdentitySection
              draftName={setup.draftName}
              roomId={setup.roomId}
              status={setup.status}
              dirty={identityDirty}
              saveStatus={identityStatus}
              feedback={identityFeedback}
              onDraftNameChange={(value) => {
                setSetup((current) => (current ? { ...current, draftName: value } : current));
                setIdentityStatus("idle");
                setIdentityFeedback(undefined);
              }}
              onSave={() => void saveIdentity()}
            />
          </div>
          <div className="xl:col-span-7">
            <DraftFormatSection
              rounds={setup.rounds}
              rosterReqs={setup.rosterReqs}
              dirty={formatDirty}
              saveStatus={formatStatus}
              feedback={formatFeedback}
              onRoundsChange={(rounds) => {
                setSetup((current) => (current ? { ...current, rounds } : current));
                setFormatStatus("idle");
                setFormatFeedback(undefined);
              }}
              onRosterChange={(position, value) => {
                setSetup((current) =>
                  current
                    ? { ...current, rosterReqs: { ...current.rosterReqs, [position]: value } }
                    : current,
                );
                setFormatStatus("idle");
                setFormatFeedback(undefined);
              }}
              onSave={() => void saveFormat()}
            />
          </div>
          <div className="xl:col-span-12">
            <TeamsSection
              teams={setup.teams}
              busy={teamBusy}
              feedback={teamFeedback}
              copiedTeamId={copiedTeamId}
              onAdd={addTeam}
              onUpdate={updateTeam}
              onSetAdmin={setAdminTeam}
              onSendInvite={sendInvite}
              onCopyInvite={copyInvite}
              onRemove={removeTeam}
            />
          </div>
          <div className="xl:col-span-12">
            <ScoringSection
              scoring={setup.scoring}
              dirty={scoringDirty}
              saveStatus={scoringStatus}
              feedback={scoringFeedback}
              onToggle={(metricId) => {
                setSetup((current) =>
                  current
                    ? {
                        ...current,
                        scoring: current.scoring.map((metric) =>
                          metric.id === metricId ? { ...metric, enabled: !metric.enabled } : metric,
                        ),
                      }
                    : current,
                );
                setScoringStatus("idle");
                setScoringFeedback(undefined);
              }}
              onValueChange={(metricId, value) => {
                setSetup((current) =>
                  current
                    ? {
                        ...current,
                        scoring: current.scoring.map((metric) =>
                          metric.id === metricId ? { ...metric, value } : metric,
                        ),
                      }
                    : current,
                );
                setScoringStatus("idle");
                setScoringFeedback(undefined);
              }}
              onSave={() => void saveScoring()}
            />
          </div>
        </div>
      </main>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-ink-700 bg-ink-900/95 px-4 py-3 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            {validationIssues.length ? (
              <p className="text-xs font-bold text-warn">{validationIssues.length} setup item{validationIssues.length === 1 ? "" : "s"} need attention</p>
            ) : (
              <p className="flex items-center gap-1.5 text-xs font-bold text-win"><CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Ready to review</p>
            )}
            <p className="mt-0.5 truncate text-[10px] text-fg-faint">
              {unsavedCount ? `${unsavedCount} section${unsavedCount === 1 ? "" : "s"} will be saved before start.` : "All section changes are saved."}
            </p>
          </div>
          <button
            type="button"
            onClick={openReview}
            className={cx("inline-flex min-h-[48px] items-center justify-center gap-2 rounded-full bg-accent px-6 text-sm font-extrabold text-ink-900 transition hover:bg-accent-bright", focusRing)}
          >
            Review Draft Setup <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      <ReviewSetupDialog
        open={reviewOpen}
        setup={setup}
        unsavedCount={unsavedCount}
        starting={starting}
        startFeedback={startFeedback}
        onClose={closeReview}
        onStart={() => void startDraft()}
      />
    </div>
  );
}

function OverviewStat({
  label,
  value,
  detail,
  warning = false,
}: {
  label: string;
  value: string;
  detail: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-850 px-3 py-2.5">
      <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-fg-faint">{label}</p>
      <div className="mt-1 flex items-end justify-between gap-2">
        <p className={cx("text-lg font-black tabular-nums", warning ? "text-warn" : "text-fg")}>{value}</p>
        <ClipboardCheck className={cx("mb-1 h-3.5 w-3.5", warning ? "text-warn" : "text-accent")} aria-hidden="true" />
      </div>
      <p className="mt-0.5 truncate text-[9px] text-fg-faint">{detail}</p>
    </div>
  );
}
