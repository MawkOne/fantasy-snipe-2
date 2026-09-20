"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  DoorOpen,
  Eye,
  Flag,
  Hourglass,
  LoaderCircle,
  LockKeyhole,
  RefreshCw,
  ShieldAlert,
  Trophy,
  UsersRound,
} from "lucide-react";
import type {
  CommissionerAction,
  ConnectionStatus,
  DraftManagementView,
  DraftRoomState,
  RoomRole,
  RoomTab,
} from "./types";
import {
  latestRevealedRound,
  nextRoundNumber,
  normalizeRoomState,
  playerStatLine,
  selectionRosterImpact,
  formatProjectedPoints,
} from "./state";
import { RoomShell } from "./RoomShell";
import { PlayerBrowser } from "./PlayerBrowser";
import { SelectionReview, SealedPickCard } from "./SelectionReview";
import { FinalRostersView, RosterSnapshot, RosterView } from "./RosterView";
import { ResultsView } from "./ResultsView";
import { CommissionerPanel } from "./CommissionerPanel";
import {
  DeleteDraftDialog,
  EditLiveSetupDialog,
  ManageRostersDialog,
  type CommissionerMutation,
} from "./CommissionerDialogs";
import {
  Dialog,
  focusRing,
  InlineNotice,
  LoadingState,
  PositionBadge,
  StatusPill,
  TeamMark,
} from "./ui";

const POLL_INTERVAL_MS = 2500;
const REQUEST_TIMEOUT_MS = 12000;

class RoomApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function errorMessage(value: unknown, fallback: string): string {
  if (value instanceof Error && value.message) return value.message;
  const record = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return typeof record.error === "string"
    ? record.error
    : typeof record.message === "string"
      ? record.message
      : fallback;
}

async function responsePayload(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { error: text };
  }
}

function missingNamesFrom(value: unknown): string[] {
  const record = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const candidate =
    record.missingTeamNames ?? record.missingTeams ?? record.teamsMissing ?? record.missing;
  if (!Array.isArray(candidate)) return [];
  return candidate
    .map((item) => {
      if (typeof item === "string") return item;
      if (!item || typeof item !== "object") return "";
      const team = item as Record<string, unknown>;
      return typeof team.name === "string"
        ? team.name
        : typeof team.teamName === "string"
          ? team.teamName
          : "";
    })
    .filter(Boolean);
}

export function DraftRoomClient({ roomId, role }: { roomId: string; role: RoomRole }) {
  const searchParams = useSearchParams();
  const searchSnapshot = searchParams.toString();
  const [credential, setCredential] = useState("");
  const [credentialReady, setCredentialReady] = useState(false);
  const [state, setState] = useState<DraftRoomState | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [loadError, setLoadError] = useState("");
  const [activeTab, setActiveTab] = useState<RoomTab>("draft");
  const [selectedId, setSelectedId] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [mutationError, setMutationError] = useState("");
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [leaveDialogOpen, setLeaveDialogOpen] = useState(false);
  const [revealDialogOpen, setRevealDialogOpen] = useState(false);
  const [finishDialogOpen, setFinishDialogOpen] = useState(false);
  const [managementView, setManagementView] = useState<DraftManagementView | null>(null);
  const [missingTeamNames, setMissingTeamNames] = useState<string[]>([]);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef(false);
  const requestSequenceRef = useRef(0);
  const appliedSequenceRef = useRef(0);
  const failureCountRef = useRef(0);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const storageKey = `scribner-draft:${role === "admin" ? "admin" : "team"}-token:${roomId}`;
    const queryCredential =
      role === "admin"
        ? searchParams.get("token") || searchParams.get("adminToken") || ""
        : searchParams.get("invite") || searchParams.get("teamToken") || searchParams.get("token") || "";

    if (queryCredential) {
      window.localStorage.setItem(storageKey, queryCredential);
      setCredential(queryCredential);

      const url = new URL(window.location.href);
      ["token", "adminToken", "invite", "teamToken"].forEach((key) => url.searchParams.delete(key));
      window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
    } else {
      setCredential(window.localStorage.getItem(storageKey) || "");
    }
    setCredentialReady(true);
  }, [role, roomId, searchParams, searchSnapshot]);

  const loadRoom = useCallback(
    async (force = false) => {
      if (!credential || (!force && pollingRef.current)) return false;
      pollingRef.current = true;
      const sequence = ++requestSequenceRef.current;
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch(`/api/room/${encodeURIComponent(roomId)}/admin`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          cache: "no-store",
          signal: controller.signal,
          body: JSON.stringify(
            role === "admin"
              ? { action: "get-admin-state", adminToken: credential }
              : { action: "get-gm-state", teamToken: credential },
          ),
        });
        const payload = await responsePayload(response);
        if (!response.ok) {
          throw new RoomApiError(
            errorMessage(payload, "Unable to load this draft room."),
            response.status,
            payload,
          );
        }

        if (!mountedRef.current || sequence < appliedSequenceRef.current) return true;
        appliedSequenceRef.current = sequence;
        setState(normalizeRoomState(payload, role, roomId));
        setConnectionStatus("connected");
        setLoadError("");
        failureCountRef.current = 0;
        return true;
      } catch (error) {
        if (!mountedRef.current) return false;
        failureCountRef.current += 1;
        const unauthorized =
          error instanceof RoomApiError && [401, 403, 404].includes(error.status);
        setLoadError(
          unauthorized
            ? errorMessage(error, "This room link is invalid or no longer available.")
            : errorMessage(error, "Live room updates could not be reached."),
        );
        setConnectionStatus(
          unauthorized || failureCountRef.current >= 3 ? "error" : "reconnecting",
        );
        return false;
      } finally {
        window.clearTimeout(timeout);
        pollingRef.current = false;
      }
    },
    [credential, role, roomId],
  );

  useEffect(() => {
    if (!credential) return;
    setConnectionStatus("connecting");
    void loadRoom(true);
    const interval = window.setInterval(() => void loadRoom(), POLL_INTERVAL_MS);
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") void loadRoom(true);
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [credential, loadRoom]);

  const postAction = useCallback(
    async (action: string, extra: Record<string, unknown> = {}) => {
      const response = await fetch(`/api/room/${encodeURIComponent(roomId)}/admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          ...(role === "admin" ? { adminToken: credential } : { teamToken: credential }),
          ...extra,
        }),
      });
      const payload = await responsePayload(response);
      if (!response.ok) {
        throw new RoomApiError(errorMessage(payload, "The room action failed."), response.status, payload);
      }
      return payload;
    },
    [credential, role, roomId],
  );

  const selectedPlayer = useMemo(
    () => state?.availablePlayers.find((player) => player.id === selectedId) ?? null,
    [selectedId, state?.availablePlayers],
  );
  const canPick = Boolean(
    state?.phase === "picking" && state.viewer && !state.viewer.myPick,
  );
  const pendingSelection = Boolean(canPick && selectedPlayer);
  const impact =
    state?.viewer && selectedPlayer
      ? selectionRosterImpact(state.viewer.roster, state.rosterReqs, selectedPlayer)
      : "Select a player to preview positional impact.";

  useEffect(() => {
    if (!canPick || (selectedId && !selectedPlayer)) setSelectedId("");
  }, [canPick, selectedId, selectedPlayer]);

  const executeLeave = useCallback(() => {
    if (role === "admin") {
      window.location.assign("/");
      return;
    }
    const team = state?.viewer?.teamName || "Your team";
    window.location.assign(
      `/left?room=${encodeURIComponent(roomId)}&team=${encodeURIComponent(team)}`,
    );
  }, [role, roomId, state?.viewer?.teamName]);

  const requestLeave = useCallback(() => {
    if (pendingSelection) setLeaveDialogOpen(true);
    else executeLeave();
  }, [executeLeave, pendingSelection]);

  useEffect(() => {
    if (!pendingSelection) return;
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [pendingSelection]);

  const closeSubmitDialog = useCallback(() => {
    if (!busyAction) setSubmitDialogOpen(false);
  }, [busyAction]);
  const closeLeaveDialog = useCallback(() => setLeaveDialogOpen(false), []);
  const closeRevealDialog = useCallback(() => {
    if (!busyAction) setRevealDialogOpen(false);
  }, [busyAction]);
  const closeFinishDialog = useCallback(() => {
    if (!busyAction) setFinishDialogOpen(false);
  }, [busyAction]);

  const confirmSubmit = useCallback(async () => {
    if (!selectedPlayer) return;
    const submittedPlayer = selectedPlayer;
    const action = role === "admin" ? "submit-admin-pick" : "submit-pick";
    setBusyAction(action);
    setMutationError("");
    try {
      await postAction(action, { playerId: submittedPlayer.id });
      setState((current) => {
        if (!current?.viewer) return current;
        const teams = current.teams.map((team) =>
          team.isViewer || (current.viewer?.teamId && team.id === current.viewer.teamId)
            ? { ...team, submitted: true }
            : team,
        );
        return {
          ...current,
          teams,
          submittedCount: teams.filter((team) => team.submitted).length,
          viewer: { ...current.viewer, myPick: submittedPlayer },
        };
      });
      setSubmitDialogOpen(false);
      setSelectedId("");
      await loadRoom(true);
    } catch (error) {
      setMutationError(errorMessage(error, "Your sealed pick could not be submitted."));
    } finally {
      setBusyAction("");
    }
  }, [loadRoom, postAction, role, selectedPlayer]);

  const runCommissionerAction = useCallback(
    async (action: CommissionerAction, confirmMissing = false) => {
      setBusyAction(action);
      setMutationError("");
      try {
        await postAction(action, action === "reveal" && confirmMissing ? { confirmMissing: true } : {});
        setRevealDialogOpen(false);
        setFinishDialogOpen(false);
        setMissingTeamNames([]);
        await loadRoom(true);
      } catch (error) {
        if (action === "reveal" && error instanceof RoomApiError && error.status === 409) {
          const serverNames = missingNamesFrom(error.data);
          const fallbackNames = state?.teams.filter((team) => !team.submitted).map((team) => team.name) ?? [];
          setMissingTeamNames(serverNames.length > 0 ? serverNames : fallbackNames);
          setRevealDialogOpen(true);
        } else {
          setMutationError(errorMessage(error, "The commissioner action could not be completed."));
        }
      } finally {
        setBusyAction("");
      }
    },
    [loadRoom, postAction, state?.teams],
  );

  const requestCommissionerAction = useCallback(
    (action: CommissionerAction) => {
      if (action === "finish-draft") {
        setFinishDialogOpen(true);
        return;
      }
      void runCommissionerAction(action);
    },
    [runCommissionerAction],
  );

  const openManagement = useCallback(
    (view: DraftManagementView) => {
      if (role !== "admin") return;
      setMutationError("");
      setManagementView(view);
    },
    [role],
  );
  const closeManagement = useCallback(() => setManagementView(null), []);

  const runManagementMutation = useCallback<CommissionerMutation>(
    async (action, payload) => {
      if (role !== "admin") {
        throw new Error("Commissioner access is required for draft management.");
      }
      setBusyAction(action);
      setMutationError("");
      try {
        await postAction(action, payload);
        return await loadRoom(true);
      } catch (error) {
        throw new Error(errorMessage(error, "The commissioner change could not be completed."));
      } finally {
        setBusyAction("");
      }
    },
    [loadRoom, postAction, role],
  );

  const deleteDraft = useCallback(
    async (confirmationName: string) => {
      if (role !== "admin") {
        throw new Error("Commissioner access is required to delete a draft.");
      }
      setBusyAction("delete-draft");
      setMutationError("");
      try {
        await postAction("delete-draft", { confirmationName });
        try {
          window.localStorage.removeItem(`scribner-draft:admin-token:${roomId}`);
          window.localStorage.removeItem("fantasy-snipe:scribner-admin-session");
        } catch {
          // A successful deletion still redirects when storage is unavailable.
        }
        setCredential("");
        setManagementView(null);
        window.location.replace("/");
      } catch (error) {
        throw new Error(errorMessage(error, "The draft could not be deleted."));
      } finally {
        if (mountedRef.current) setBusyAction("");
      }
    },
    [postAction, role, roomId],
  );

  const changeSelection = useCallback(() => {
    searchInputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    window.setTimeout(() => searchInputRef.current?.focus(), 350);
  }, []);

  if (!credentialReady) return <LoadingState label="Opening your private room…" />;

  if (!credential) {
    return (
      <AccessState
        title={role === "admin" ? "Commissioner link required" : "Private invite required"}
        message={
          role === "admin"
            ? "Open the commissioner room from the admin link created with this draft."
            : "Open your team-specific invite link once. This device will remember your team for future visits."
        }
      />
    );
  }

  if (!state) {
    if (connectionStatus === "error" || loadError) {
      return (
        <AccessState
          title="Unable to open the room"
          message={loadError || "The room did not respond."}
          onRetry={() => void loadRoom(true)}
        />
      );
    }
    return <LoadingState />;
  }

  const latestRound = latestRevealedRound(state);
  const viewer = state.viewer;
  const isSubmitBusy = ["submit-pick", "submit-admin-pick"].includes(busyAction);
  const mobileReviewOpen = activeTab === "draft" && canPick && Boolean(selectedPlayer);

  const mainContent = (() => {
    if (activeTab === "roster") {
      return viewer ? <RosterView viewer={viewer} /> : <NoDraftTeam />;
    }
    if (activeTab === "results") {
      return <ResultsView rounds={state.revealedRounds} title="Draft results" />;
    }
    if (activeTab === "commissioner" && role === "admin") {
      return (
        <CommissionerPanel
          state={state}
          onAction={requestCommissionerAction}
          busyAction={busyAction}
          error={mutationError}
          onManagement={openManagement}
        />
      );
    }

    if (state.phase === "completed") {
      return (
        <div className="space-y-5">
          <CompletionBanner state={state} />
          <FinalRostersView teams={state.teams} viewerTeamId={viewer?.teamId} />
        </div>
      );
    }

    if (state.phase === "waiting") {
      return (
        <WaitingView
          state={state}
          role={role}
          latestRound={latestRound}
        />
      );
    }

    if (state.phase === "revealed") {
      return (
        <div className="space-y-5">
          <RevealedBanner state={state} role={role} />
          <ResultsView rounds={state.revealedRounds} title={`Round ${state.currentRound} results`} compact />
        </div>
      );
    }

    if (!viewer) return <NoDraftTeam />;

    if (viewer.myPick) {
      return (
        <div className="space-y-4">
          <div className="lg:hidden">
            <SealedPickCard
              player={viewer.myPick}
              submittedCount={state.submittedCount}
              teamCount={state.teams.length}
              prominent
            />
          </div>
          <SubmissionBoard state={state} />
        </div>
      );
    }

    return (
      <PlayerBrowser
        players={state.availablePlayers}
        selectedId={selectedId}
        onSelect={(player) => {
          setSelectedId(player.id);
          setMutationError("");
        }}
        round={Math.max(1, state.currentRound)}
        searchInputRef={searchInputRef}
      />
    );
  })();

  return (
    <>
      <RoomShell
        state={state}
        role={role}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLeave={requestLeave}
        connectionStatus={connectionStatus}
        onRetry={() => void loadRoom(true)}
        mobileReviewOpen={mobileReviewOpen}
      >
        <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0">{mainContent}</div>

          <aside className="hidden min-w-0 lg:block" aria-label="Draft room side rail">
            <div className="sticky top-[76px] space-y-4">
              {activeTab === "draft" && canPick ? (
                <SelectionReview
                  player={selectedPlayer}
                  impact={impact}
                  onChange={changeSelection}
                  onClear={() => setSelectedId("")}
                  onSubmit={() => setSubmitDialogOpen(true)}
                  busy={isSubmitBusy}
                />
              ) : null}

              {activeTab === "draft" && state.phase === "picking" && viewer?.myPick ? (
                <SealedPickCard
                  player={viewer.myPick}
                  submittedCount={state.submittedCount}
                  teamCount={state.teams.length}
                />
              ) : null}

              {viewer ? <RosterSnapshot viewer={viewer} /> : null}

              {role === "admin" && activeTab !== "commissioner" ? (
                <CommissionerPanel
                  state={state}
                  onAction={requestCommissionerAction}
                  busyAction={busyAction}
                  error={mutationError}
                  onManagement={openManagement}
                  compact
                />
              ) : null}
            </div>
          </aside>
        </div>

        {activeTab === "draft" && canPick ? (
          <SelectionReview
            player={selectedPlayer}
            impact={impact}
            onChange={changeSelection}
            onClear={() => setSelectedId("")}
            onSubmit={() => setSubmitDialogOpen(true)}
            busy={isSubmitBusy}
            variant="mobile"
          />
        ) : null}
      </RoomShell>

      <Dialog
        open={submitDialogOpen && Boolean(selectedPlayer)}
        title="Submit sealed pick?"
        description="Your selection is final for this round and stays hidden from every other team until reveal."
        onClose={closeSubmitDialog}
      >
        {selectedPlayer ? (
          <div className="flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-800 p-3">
            <PositionBadge position={selectedPlayer.position} selected />
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-sm font-extrabold text-fg">{selectedPlayer.name}</h3>
              <p className="mt-0.5 text-xs text-fg-muted">{selectedPlayer.team} · {selectedPlayer.position} · ADP {selectedPlayer.adp != null ? selectedPlayer.adp.toFixed(1) : "—"}</p>
              <p className="mt-1 line-clamp-3 text-[10px] leading-4 text-fg-faint">{playerStatLine(selectedPlayer)}</p>
            </div>
            <div className="text-right">
              <strong className="text-lg font-black tabular-nums text-accent">
                {selectedPlayer.adp != null ? selectedPlayer.adp.toFixed(1) : "—"}
              </strong>
              <p className="text-[9px] uppercase tracking-wider text-fg-faint">ADP</p>
            </div>
          </div>
        ) : null}
        {mutationError ? (
          <div className="mt-3">
            <InlineNotice tone="danger">{mutationError}</InlineNotice>
          </div>
        ) : null}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={closeSubmitDialog}
            disabled={isSubmitBusy}
            className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg-muted hover:text-fg disabled:opacity-50 ${focusRing}`}
          >
            Review again
          </button>
          <button
            type="button"
            data-autofocus
            onClick={() => void confirmSubmit()}
            disabled={isSubmitBusy}
            className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 hover:bg-accent-bright disabled:opacity-60 ${focusRing}`}
          >
            {isSubmitBusy ? (
              <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
            ) : (
              <LockKeyhole size={16} aria-hidden="true" />
            )}
            {isSubmitBusy ? "Sealing…" : "Seal Pick"}
          </button>
        </div>
      </Dialog>

      <Dialog
        open={leaveDialogOpen}
        title="Leave with a pending selection?"
        description="This player has not been submitted. Leaving now discards only the local selection; it does not change draft progress."
        onClose={closeLeaveDialog}
      >
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            data-autofocus
            onClick={closeLeaveDialog}
            className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg ${focusRing}`}
          >
            Stay in Room
          </button>
          <button
            type="button"
            onClick={executeLeave}
            className={`flex min-h-11 items-center justify-center gap-2 rounded-xl border border-loss/40 bg-loss/10 px-4 text-sm font-black text-loss hover:bg-loss/20 ${focusRing}`}
          >
            <DoorOpen size={16} aria-hidden="true" /> Leave Room
          </button>
        </div>
      </Dialog>

      <Dialog
        open={revealDialogOpen}
        title="Reveal with missing picks?"
        description="The named teams will receive No Pick this round. Submitted picks will be revealed simultaneously."
        onClose={closeRevealDialog}
      >
        <div className="rounded-xl border border-warn/30 bg-warn/10 p-3">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-warn">Still waiting for</p>
          <ul className="mt-2 space-y-1.5">
            {missingTeamNames.map((name) => (
              <li key={name} className="flex items-center gap-2 text-sm font-bold text-fg">
                <AlertTriangle size={14} className="text-warn" aria-hidden="true" /> {name}
              </li>
            ))}
          </ul>
        </div>
        {mutationError ? (
          <div className="mt-3">
            <InlineNotice tone="danger">{mutationError}</InlineNotice>
          </div>
        ) : null}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            data-autofocus
            onClick={closeRevealDialog}
            disabled={busyAction === "reveal"}
            className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg ${focusRing}`}
          >
            Keep Waiting
          </button>
          <button
            type="button"
            onClick={() => void runCommissionerAction("reveal", true)}
            disabled={busyAction === "reveal"}
            className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-warn px-4 text-sm font-black text-ink-950 hover:bg-amber-400 disabled:opacity-60 ${focusRing}`}
          >
            {busyAction === "reveal" ? (
              <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
            ) : (
              <Eye size={16} aria-hidden="true" />
            )}
            Reveal Anyway
          </button>
        </div>
      </Dialog>

      <Dialog
        open={finishDialogOpen}
        title="Finish this draft?"
        description="Final rosters and projected totals will remain available, but no more rounds can be started."
        onClose={closeFinishDialog}
      >
        <div className="flex items-start gap-2.5 rounded-xl border border-accent/25 bg-accent/10 px-3 py-3 text-xs leading-5 text-fg-muted">
          <Trophy size={17} className="mt-0.5 shrink-0 text-warn" aria-hidden="true" />
          Round {state.currentRound} of {state.totalRounds} is revealed. Finishing locks the completed state for all GMs.
        </div>
        {mutationError ? (
          <div className="mt-3">
            <InlineNotice tone="danger">{mutationError}</InlineNotice>
          </div>
        ) : null}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            data-autofocus
            onClick={closeFinishDialog}
            disabled={busyAction === "finish-draft"}
            className={`min-h-11 rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg ${focusRing}`}
          >
            Not Yet
          </button>
          <button
            type="button"
            onClick={() => void runCommissionerAction("finish-draft")}
            disabled={busyAction === "finish-draft"}
            className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 hover:bg-accent-bright disabled:opacity-60 ${focusRing}`}
          >
            {busyAction === "finish-draft" ? (
              <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />
            ) : (
              <Flag size={16} aria-hidden="true" />
            )}
            Finish Draft
          </button>
        </div>
      </Dialog>

      {role === "admin" && managementView === "rosters" ? (
        <ManageRostersDialog
          open
          state={state}
          busyAction={busyAction}
          onClose={closeManagement}
          onMutation={runManagementMutation}
        />
      ) : null}

      {role === "admin" && managementView === "setup" ? (
        <EditLiveSetupDialog
          open
          state={state}
          busyAction={busyAction}
          onClose={closeManagement}
          onMutation={runManagementMutation}
        />
      ) : null}

      {role === "admin" && managementView === "delete" ? (
        <DeleteDraftDialog
          open
          draftName={state.draftName}
          busyAction={busyAction}
          onClose={closeManagement}
          onDelete={deleteDraft}
        />
      ) : null}
    </>
  );
}

function AccessState({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-ink-900 px-4">
      <div className="w-full max-w-md rounded-card border border-ink-700 bg-ink-850 p-6 text-center shadow-2xl">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-warn/30 bg-warn/10 text-warn">
          <ShieldAlert size={24} aria-hidden="true" />
        </div>
        <h1 className="mt-4 text-xl font-extrabold tracking-tight text-fg">{title}</h1>
        <p className="mt-2 text-sm leading-6 text-fg-muted">{message}</p>
        <div className="mt-5 grid gap-2 sm:grid-cols-2">
          <a
            href="/"
            className={`flex min-h-11 items-center justify-center rounded-xl border border-ink-600 bg-ink-800 px-4 text-sm font-bold text-fg-muted hover:text-fg ${focusRing}`}
          >
            Go Home
          </a>
          {onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className={`flex min-h-11 items-center justify-center gap-2 rounded-xl bg-accent px-4 text-sm font-black text-ink-950 ${focusRing}`}
            >
              <RefreshCw size={15} aria-hidden="true" /> Retry
            </button>
          ) : (
            <span className="hidden sm:block" />
          )}
        </div>
      </div>
    </main>
  );
}

function WaitingView({
  state,
  role,
  latestRound,
}: {
  state: DraftRoomState;
  role: RoomRole;
  latestRound: ReturnType<typeof latestRevealedRound>;
}) {
  const round = nextRoundNumber(state);
  const previewSearchRef = useRef<HTMLInputElement>(null);
  return (
    <div className="space-y-5">
      <section className="relative overflow-hidden rounded-card border border-ink-700 bg-ink-850 p-5 sm:p-6">
        <div className="absolute right-0 top-0 h-40 w-40 translate-x-12 -translate-y-12 rounded-full bg-accent/10 blur-3xl" aria-hidden="true" />
        <div className="relative flex items-start gap-3.5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-ink-600 bg-ink-800 text-accent">
            <Hourglass size={21} aria-hidden="true" />
          </div>
          <div>
            <StatusPill tone="neutral">Waiting</StatusPill>
            <h2 className="mt-3 text-xl font-extrabold tracking-tight text-fg">
              {role === "admin"
                ? `Round ${round} is ready to start`
                : `Waiting for the commissioner to start Round ${round}`}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-fg-muted">
              {role === "admin"
                ? "Open the Commissioner view or use the desktop side rail when every GM is ready."
                : "The player browser will unlock automatically. You can review your roster and previous results while you wait."}
            </p>
          </div>
        </div>
      </section>

      <PlayerBrowser
        players={state.availablePlayers}
        selectedId=""
        round={round}
        searchInputRef={previewSearchRef}
        readOnly
      />

      {state.viewer ? (
        <div className="lg:hidden">
          <RosterSnapshot viewer={state.viewer} title="Current roster" />
        </div>
      ) : null}

      {latestRound ? (
        <ResultsView rounds={state.revealedRounds} title="Previous round" compact />
      ) : (
        <div className="rounded-card border border-dashed border-ink-600 bg-ink-850/50 px-5 py-7 text-center">
          <Clock3 size={19} className="mx-auto text-fg-faint" aria-hidden="true" />
          <p className="mt-2 text-xs font-semibold text-fg-muted">No previous round results yet.</p>
        </div>
      )}
    </div>
  );
}

function RevealedBanner({ state, role }: { state: DraftRoomState; role: RoomRole }) {
  const finalRound = state.currentRound >= state.totalRounds;
  return (
    <section className="flex items-start gap-3.5 rounded-card border border-win/30 bg-win/10 p-5">
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-win/30 bg-win/10 text-win">
        <CheckCircle2 size={21} aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <StatusPill tone="success">Round {state.currentRound} revealed</StatusPill>
        <h2 className="mt-2 text-lg font-extrabold text-fg">
          {finalRound ? "The final round is complete" : "Every submitted pick is now visible"}
        </h2>
        <p className="mt-1 text-xs leading-5 text-fg-muted">
          {finalRound
            ? role === "admin"
              ? "Review the results, then finish the draft from Commissioner controls."
              : "Waiting for the commissioner to finish the draft and lock final rosters."
            : role === "admin"
              ? `Start Round ${state.currentRound + 1} when the room is ready.`
              : `Waiting for the commissioner to start Round ${state.currentRound + 1}.`}
        </p>
      </div>
    </section>
  );
}

function SubmissionBoard({ state }: { state: DraftRoomState }) {
  return (
    <section className="overflow-hidden rounded-card border border-ink-700 bg-ink-850" aria-labelledby="submission-board-title">
      <div className="flex items-center justify-between gap-3 border-b border-ink-700 px-4 py-3">
        <div className="flex items-center gap-2">
          <UsersRound size={16} className="text-accent" aria-hidden="true" />
          <h2 id="submission-board-title" className="text-sm font-extrabold text-fg">Round {state.currentRound} status</h2>
        </div>
        <span className="text-xs font-bold tabular-nums text-fg-muted">
          {state.submittedCount}/{state.teams.length} submitted
        </span>
      </div>
      <div className="grid gap-px bg-ink-700 sm:grid-cols-2">
        {state.teams.map((team) => (
          <div key={team.id} className="flex min-h-14 items-center gap-2.5 bg-ink-850 px-3 py-2.5">
            <TeamMark name={team.name} highlight={team.isViewer} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-xs font-bold text-fg">{team.name}</span>
                {team.isViewer ? <span className="text-[9px] font-black uppercase text-accent">You</span> : null}
              </div>
              <span className="text-[10px] text-fg-faint">
                {team.submitted ? "Pick received" : "Waiting to submit"}
              </span>
            </div>
            <StatusPill tone={team.submitted ? "success" : "neutral"}>
              {team.submitted ? "Submitted" : "Waiting"}
            </StatusPill>
          </div>
        ))}
      </div>
    </section>
  );
}

function CompletionBanner({ state }: { state: DraftRoomState }) {
  const leader = [...state.teams].sort((a, b) => b.totalProjectedPts - a.totalProjectedPts)[0];
  return (
    <section className="relative overflow-hidden rounded-card border border-accent/30 bg-ink-850 p-6 text-center sm:p-8">
      <div className="absolute inset-x-1/4 top-0 h-28 rounded-full bg-accent/10 blur-3xl" aria-hidden="true" />
      <div className="relative">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-warn/40 bg-warn/10 text-warn shadow-[0_0_35px_rgba(245,158,11,0.12)]">
          <Trophy size={30} aria-hidden="true" />
        </div>
        <StatusPill tone="success">Draft complete</StatusPill>
        <h2 className="mt-3 text-2xl font-black tracking-tight text-fg">All {state.totalRounds} rounds are in</h2>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-fg-muted">
          Final rosters and projected totals are locked. Every revealed pick remains available in Results.
        </p>
        {leader ? (
          <div className="mx-auto mt-5 inline-flex items-center gap-3 rounded-xl border border-ink-600 bg-ink-800 px-4 py-3 text-left">
            <TeamMark name={leader.name} highlight />
            <div>
              <p className="text-[10px] font-black uppercase tracking-wider text-fg-faint">Top projection</p>
              <p className="mt-0.5 text-sm font-extrabold text-fg">{leader.name}</p>
            </div>
            <strong className="ml-2 text-lg font-black tabular-nums text-accent">
              {formatProjectedPoints(leader.totalProjectedPts)}
            </strong>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function NoDraftTeam() {
  return (
    <section className="rounded-card border border-warn/30 bg-ink-850 px-5 py-12 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-warn/30 bg-warn/10 text-warn">
        <AlertTriangle size={23} aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-lg font-extrabold text-fg">No commissioner team assigned</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-fg-muted">
        Commissioner controls remain available, but drafting requires an explicit admin team assignment from room setup.
      </p>
    </section>
  );
}
