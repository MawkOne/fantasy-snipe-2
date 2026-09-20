"use client";

import { useState, type FormEvent } from "react";
import {
  Check,
  Copy,
  Mail,
  Pencil,
  Plus,
  Send,
  Trash2,
  UserRoundCheck,
  Users,
  X,
} from "lucide-react";
import type { ActionFeedback, Team, TeamBusyState, TeamInput } from "./types";
import { isValidEmail } from "./setup-utils";
import { FeedbackBanner, IconButtonLabel, SectionCard, Spinner, cx, focusRing } from "./ui";

interface EditValues {
  teamName: string;
  ownerEmail: string;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("") || "TM";
}

function InviteBadge({ state }: { state: Team["inviteState"] }) {
  const config = {
    "not-sent": { label: "Not sent", className: "border-ink-600 bg-ink-800 text-fg-muted" },
    sent: { label: "Sent", className: "border-accent/30 bg-accent/10 text-accent" },
    joined: { label: "Joined", className: "border-win/30 bg-win/10 text-win" },
  }[state];

  return (
    <span className={cx("inline-flex min-h-[26px] items-center gap-1.5 rounded-full border px-2.5 text-[9px] font-bold uppercase tracking-[0.12em]", config.className)}>
      <span className={cx("h-1.5 w-1.5 rounded-full", state === "joined" ? "bg-win" : state === "sent" ? "bg-accent" : "bg-fg-faint")} />
      {config.label}
    </span>
  );
}

export function TeamsSection({
  teams,
  busy,
  feedback,
  copiedTeamId,
  onAdd,
  onUpdate,
  onSetAdmin,
  onSendInvite,
  onCopyInvite,
  onRemove,
}: {
  teams: Team[];
  busy: TeamBusyState | null;
  feedback?: ActionFeedback;
  copiedTeamId: string | null;
  onAdd: (input: TeamInput) => Promise<boolean>;
  onUpdate: (teamId: string, values: EditValues) => Promise<boolean>;
  onSetAdmin: (teamId: string) => Promise<void>;
  onSendInvite: (teamId: string) => Promise<void>;
  onCopyInvite: (teamId: string) => Promise<void>;
  onRemove: (teamId: string) => Promise<void>;
}) {
  const [teamName, setTeamName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [isAdminTeam, setIsAdminTeam] = useState(() => !teams.some((team) => team.isAdminTeam));
  const [formError, setFormError] = useState("");
  const [editId, setEditId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<EditValues>({ teamName: "", ownerEmail: "" });
  const [editError, setEditError] = useState("");
  const [removeConfirmId, setRemoveConfirmId] = useState<string | null>(null);

  const addTeam = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = teamName.trim();
    const email = ownerEmail.trim();
    if (!name) {
      setFormError("Enter a team name.");
      return;
    }
    if (email && !isValidEmail(email)) {
      setFormError("Enter a valid owner email address or leave it blank to share the link manually.");
      return;
    }
    setFormError("");
    const added = await onAdd({ teamName: name, ownerEmail: email, isAdminTeam });
    if (added) {
      setTeamName("");
      setOwnerEmail("");
      setIsAdminTeam(false);
    }
  };

  const beginEdit = (team: Team) => {
    setEditId(team.id);
    setEditValues({ teamName: team.name, ownerEmail: team.ownerEmail });
    setEditError("");
    setRemoveConfirmId(null);
  };

  const saveEdit = async (event: FormEvent<HTMLFormElement>, teamId: string) => {
    event.preventDefault();
    const name = editValues.teamName.trim();
    const email = editValues.ownerEmail.trim();
    if (!name) {
      setEditError("Enter a team name.");
      return;
    }
    if (email && !isValidEmail(email)) {
      setEditError("Enter a valid owner email address or leave it blank to share the link manually.");
      return;
    }
    setEditError("");
    if (await onUpdate(teamId, { teamName: name, ownerEmail: email })) {
      setEditId(null);
    }
  };

  const anyBusy = busy !== null;

  return (
    <SectionCard
      id="teams"
      step="02 · Teams"
      title={`Teams & invitations · ${teams.length}`}
      description="Assign each team, then email or copy its private, team-specific invite."
      icon={<Users className="h-4 w-4" aria-hidden="true" />}
      action={
        teams.some((team) => team.isAdminTeam) ? (
          <span className="inline-flex min-h-[28px] items-center gap-1.5 rounded-full border border-accent/30 bg-accent/10 px-2.5 text-[9px] font-bold uppercase tracking-[0.12em] text-accent">
            <UserRoundCheck className="h-3 w-3" aria-hidden="true" /> My team assigned
          </span>
        ) : (
          <span className="inline-flex min-h-[28px] items-center rounded-full border border-warn/35 bg-warn/10 px-2.5 text-[9px] font-bold uppercase tracking-[0.12em] text-warn">
            Choose My team
          </span>
        )
      }
    >
      <form onSubmit={addTeam} className="border-b border-ink-700 bg-ink-800/30 p-4 sm:p-5" noValidate>
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent/10 text-accent">
            <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          </span>
          <h3 className="text-xs font-extrabold text-fg">Add a team</h3>
        </div>
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto_auto] md:items-end">
          <div>
            <label htmlFor="new-team-name" className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-fg-muted">Team name</label>
            <input
              id="new-team-name"
              value={teamName}
              onChange={(event) => {
                setTeamName(event.target.value);
                if (formError) setFormError("");
              }}
              placeholder="e.g. Harbour Ice"
              maxLength={80}
              autoComplete="organization"
              className={cx("min-h-[44px] w-full rounded-lg border border-ink-600 bg-ink-900 px-3 text-sm text-fg placeholder:text-fg-faint", focusRing)}
            />
          </div>
          <div>
            <label htmlFor="new-owner-email" className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-fg-muted">Owner email</label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-fg-faint" aria-hidden="true" />
              <input
                id="new-owner-email"
                type="email"
                inputMode="email"
                value={ownerEmail}
                onChange={(event) => {
                  setOwnerEmail(event.target.value);
                  if (formError) setFormError("");
                }}
                placeholder="owner@example.com"
                maxLength={254}
                autoComplete="email"
                className={cx("min-h-[44px] w-full rounded-lg border border-ink-600 bg-ink-900 py-2 pl-9 pr-3 text-sm text-fg placeholder:text-fg-faint", focusRing)}
              />
            </div>
          </div>
          <label className={cx("flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border px-3 text-xs font-bold transition", isAdminTeam ? "border-accent/50 bg-accent/10 text-accent" : "border-ink-600 bg-ink-900 text-fg-muted", focusRing)}>
            <input
              type="checkbox"
              checked={isAdminTeam}
              onChange={(event) => setIsAdminTeam(event.target.checked)}
              className="h-4 w-4 accent-[#2AB3FF]"
            />
            My team
          </label>
          <button
            type="submit"
            disabled={anyBusy}
            className={cx("inline-flex min-h-[44px] items-center justify-center gap-2 rounded-lg bg-accent px-4 text-xs font-extrabold text-ink-900 transition hover:bg-accent-bright disabled:cursor-not-allowed disabled:opacity-50", focusRing)}
          >
            {busy?.action === "add" ? <Spinner /> : <Plus className="h-3.5 w-3.5" aria-hidden="true" />}
            Add team
          </button>
        </div>
        {formError ? <p className="mt-2 text-xs text-loss" role="alert">{formError}</p> : null}
      </form>

      {feedback ? <div className="p-4 pb-0 sm:px-5"><FeedbackBanner feedback={feedback} /></div> : null}

      {teams.length > 0 ? (
        <div className="p-4 sm:p-5">
          <div className="hidden grid-cols-[minmax(180px,1.15fr)_minmax(190px,1fr)_110px_100px_minmax(260px,auto)] gap-3 border-b border-ink-700 px-3 pb-2 text-[9px] font-bold uppercase tracking-[0.14em] text-fg-faint lg:grid">
            <span>Team</span><span>Owner</span><span>Assignment</span><span>Invite</span><span className="text-right">Actions</span>
          </div>
          <ul className="mt-2 space-y-2" aria-label="Draft teams">
            {teams.map((team) => {
              const teamBusy = busy?.teamId === team.id;
              const editing = editId === team.id;
              const confirmRemove = removeConfirmId === team.id;

              if (editing) {
                return (
                  <li key={team.id} className="rounded-xl border border-accent/40 bg-accent/5 p-3.5">
                    <form onSubmit={(event) => saveEdit(event, team.id)} noValidate>
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <Pencil className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
                          <p className="text-xs font-extrabold text-fg">Edit team</p>
                        </div>
                        <label className="flex min-h-[36px] cursor-pointer items-center gap-2 rounded-lg px-2 text-xs font-bold text-fg-muted">
                          <input
                            type="radio"
                            name="admin-team-edit"
                            checked={team.isAdminTeam}
                            onChange={() => void onSetAdmin(team.id)}
                            className="h-4 w-4 accent-[#2AB3FF]"
                          />
                          My team
                        </label>
                      </div>
                      <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end">
                        <div>
                          <label htmlFor={`edit-name-${team.id}`} className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-fg-muted">Team name</label>
                          <input
                            id={`edit-name-${team.id}`}
                            value={editValues.teamName}
                            onChange={(event) => setEditValues((current) => ({ ...current, teamName: event.target.value }))}
                            maxLength={80}
                            className={cx("min-h-[44px] w-full rounded-lg border border-ink-600 bg-ink-900 px-3 text-sm text-fg", focusRing)}
                            autoFocus
                          />
                        </div>
                        <div>
                          <label htmlFor={`edit-email-${team.id}`} className="mb-1.5 block text-[10px] font-bold uppercase tracking-wider text-fg-muted">Owner email</label>
                          <input
                            id={`edit-email-${team.id}`}
                            type="email"
                            value={editValues.ownerEmail}
                            onChange={(event) => setEditValues((current) => ({ ...current, ownerEmail: event.target.value }))}
                            maxLength={254}
                            className={cx("min-h-[44px] w-full rounded-lg border border-ink-600 bg-ink-900 px-3 text-sm text-fg", focusRing)}
                          />
                        </div>
                        <div className="flex gap-2">
                          <button type="button" onClick={() => setEditId(null)} className={cx("inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg border border-ink-600 px-3 text-xs font-bold text-fg-muted hover:text-fg", focusRing)}>
                            <X className="h-3.5 w-3.5" aria-hidden="true" /> Cancel
                          </button>
                          <button type="submit" disabled={teamBusy} className={cx("inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg bg-accent px-3 text-xs font-extrabold text-ink-900 disabled:opacity-50", focusRing)}>
                            {busy?.action === "edit" && teamBusy ? <Spinner /> : <Check className="h-3.5 w-3.5" aria-hidden="true" />} Save
                          </button>
                        </div>
                      </div>
                      {editError ? <p className="mt-2 text-xs text-loss" role="alert">{editError}</p> : null}
                    </form>
                  </li>
                );
              }

              return (
                <li key={team.id} className={cx("rounded-xl border bg-ink-800/55 p-3 transition-colors", team.isAdminTeam ? "border-accent/40" : "border-ink-700")}>
                  <div className="grid gap-3 lg:grid-cols-[minmax(180px,1.15fr)_minmax(190px,1fr)_110px_100px_minmax(260px,auto)] lg:items-center">
                    <div className="flex min-w-0 items-center gap-2.5">
                      <span className={cx("flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-[10px] font-black", team.isAdminTeam ? "border-accent/50 bg-accent/10 text-accent" : "border-ink-600 bg-ink-900 text-fg-muted")} aria-hidden="true">
                        {initials(team.name)}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-fg">{team.name}</p>
                        {team.isAdminTeam ? <p className="mt-0.5 text-[9px] font-bold uppercase tracking-wider text-accent">Commissioner team</p> : null}
                      </div>
                    </div>

                    <div className="min-w-0">
                      <p className="mb-0.5 text-[9px] font-bold uppercase tracking-wider text-fg-faint lg:hidden">Owner</p>
                      <p className="truncate text-xs text-fg-muted">{team.ownerEmail || "Email missing"}</p>
                    </div>

                    <label className={cx("flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg px-1 text-xs font-bold", team.isAdminTeam ? "text-accent" : "text-fg-muted", focusRing)}>
                      <input
                        type="radio"
                        name="admin-team"
                        checked={team.isAdminTeam}
                        onChange={() => void onSetAdmin(team.id)}
                        disabled={anyBusy}
                        className="h-4 w-4 accent-[#2AB3FF]"
                      />
                      {team.isAdminTeam ? "My team" : "Choose"}
                    </label>

                    <div><InviteBadge state={team.inviteState} /></div>

                    <div className="flex flex-wrap items-center gap-1.5 lg:justify-end">
                      <button
                        type="button"
                        onClick={() => void onCopyInvite(team.id)}
                        className={cx("inline-flex min-h-[44px] min-w-[44px] items-center justify-center gap-1.5 rounded-lg border border-ink-600 px-2.5 text-[10px] font-bold text-fg-muted hover:border-accent/40 hover:text-accent", focusRing)}
                        aria-label={`Copy invite link for ${team.name}`}
                      >
                        {copiedTeamId === team.id ? <Check className="h-3.5 w-3.5 text-win" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
                        <IconButtonLabel>{copiedTeamId === team.id ? "Copied" : "Copy"}</IconButtonLabel>
                      </button>
                      <button
                        type="button"
                        onClick={() => void onSendInvite(team.id)}
                        disabled={anyBusy || !isValidEmail(team.ownerEmail)}
                        className={cx("inline-flex min-h-[44px] items-center justify-center gap-1.5 rounded-lg border border-accent/35 bg-accent/10 px-2.5 text-[10px] font-bold text-accent hover:bg-accent/15 disabled:cursor-not-allowed disabled:opacity-40", focusRing)}
                      >
                        {busy?.action === "invite" && teamBusy ? <Spinner /> : <Send className="h-3.5 w-3.5" aria-hidden="true" />}
                        {team.inviteState === "not-sent" ? "Send" : "Resend"}
                      </button>
                      <button
                        type="button"
                        onClick={() => beginEdit(team)}
                        disabled={anyBusy}
                        className={cx("inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-fg-muted hover:bg-ink-700 hover:text-fg disabled:opacity-40", focusRing)}
                        aria-label={`Edit ${team.name}`}
                      >
                        <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                      </button>

                      {confirmRemove ? (
                        <div className="flex items-center gap-1 rounded-lg border border-loss/30 bg-loss/10 p-1">
                          <button
                            type="button"
                            onClick={async () => {
                              await onRemove(team.id);
                              setRemoveConfirmId(null);
                            }}
                            disabled={anyBusy}
                            className={cx("inline-flex min-h-[36px] items-center rounded-md bg-loss px-2.5 text-[10px] font-bold text-white disabled:opacity-50", focusRing)}
                          >
                            {busy?.action === "remove" && teamBusy ? <Spinner /> : "Remove"}
                          </button>
                          <button type="button" onClick={() => setRemoveConfirmId(null)} className={cx("flex h-9 w-9 items-center justify-center rounded-md text-fg-muted hover:text-fg", focusRing)} aria-label="Cancel remove">
                            <X className="h-3.5 w-3.5" aria-hidden="true" />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setRemoveConfirmId(team.id)}
                          disabled={anyBusy}
                          className={cx("inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg text-fg-muted hover:bg-loss/10 hover:text-loss disabled:opacity-40", focusRing)}
                          aria-label={`Remove ${team.name}`}
                        >
                          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : (
        <div className="px-4 py-10 text-center sm:px-5">
          <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-full border border-ink-700 bg-ink-800 text-fg-faint">
            <Users className="h-5 w-5" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm font-bold text-fg">No teams yet</p>
          <p className="mt-1 text-xs text-fg-muted">Add the commissioner’s team first, then invite the rest of the league.</p>
        </div>
      )}
    </SectionCard>
  );
}
