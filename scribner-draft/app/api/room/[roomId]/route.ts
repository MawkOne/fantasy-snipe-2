import { NextRequest, NextResponse } from "next/server";
import {
  apiErrorResponse,
  readJsonObject,
  requestOrigin,
} from "@/lib/api";
import {
  DraftError,
  addTeam,
  getSetupState,
  joinByInvite,
  markInviteSent,
  removeTeam,
  sendTeamInvite,
  setAdminTeam,
  startDraft,
  updateDraftConfig,
  updateRoomName,
  updateScoringConfig,
  updateTeam,
  type Team,
} from "@/lib/store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface RouteContext {
  params: { roomId: string };
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function teamInput(body: Record<string, unknown>) {
  const nested = asObject(body.team);
  return {
    name: nested.name ?? body.name ?? body.teamName,
    email:
      nested.email ?? nested.ownerEmail ?? body.email ?? body.ownerEmail,
    isAdminTeam: nested.isAdminTeam ?? body.isAdminTeam,
  };
}

function teamResponse(team: Team, roomId: string, origin: string) {
  const inviteLink = new URL(
    `/room/${encodeURIComponent(roomId)}?invite=${encodeURIComponent(team.inviteToken)}`,
    `${origin.replace(/\/$/, "")}/`,
  ).toString();
  return {
    teamId: team.id,
    teamName: team.name,
    name: team.name,
    email: team.ownerEmail,
    ownerEmail: team.ownerEmail,
    inviteToken: team.inviteToken,
    teamToken: team.inviteToken,
    inviteState: team.inviteState,
    inviteLink,
  };
}


export async function POST(request: NextRequest, { params }: RouteContext) {
  try {
    const body = await readJsonObject(request);
    const action = typeof body.action === "string" ? body.action : "";
    const origin = requestOrigin(request);

    switch (action) {
      case "get-setup": {
        const state = await getSetupState(
          params.roomId,
          body.adminToken,
          origin,
        );
        return NextResponse.json(state);
      }
      case "join-by-invite": {
        const joined = await joinByInvite(
          params.roomId,
          body.teamToken ?? body.inviteToken,
        );
        return NextResponse.json(joined);
      }
      case "update-room-name": {
        const updated = await updateRoomName(
          params.roomId,
          body.adminToken,
          body.draftName ?? body.name,
        );
        return NextResponse.json({ ok: true, draftName: updated.name });
      }
      case "add-team": {
        const team = await addTeam(
          params.roomId,
          body.adminToken,
          teamInput(body),
        );
        return NextResponse.json(
          teamResponse(team, params.roomId, origin),
          { status: 201 },
        );
      }
      case "update-team": {
        const team = await updateTeam(
          params.roomId,
          body.adminToken,
          body.teamId,
          teamInput(body),
        );
        return NextResponse.json({
          ok: true,
          ...teamResponse(team, params.roomId, origin),
        });
      }
      case "remove-team": {
        const result = await removeTeam(
          params.roomId,
          body.adminToken,
          body.teamId,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "set-admin-team": {
        const result = await setAdminTeam(
          params.roomId,
          body.adminToken,
          body.teamId,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "mark-invite-sent":
      case "mark-send-invite": {
        const team = await markInviteSent(
          params.roomId,
          body.adminToken,
          body.teamId,
        );
        return NextResponse.json({
          ok: true,
          emailConfigured: !!process.env.RESEND_API_KEY,
          emailSent: false,
          ...teamResponse(team, params.roomId, origin),
        });
      }
      case "send-invite": {
        const result = await sendTeamInvite(
          params.roomId,
          body.adminToken,
          body.teamId,
          origin,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "update-draft-config": {
        const directConfig: Record<string, unknown> = {};
        if ("rounds" in body) directConfig.rounds = body.rounds;
        if ("rosterReqs" in body) directConfig.rosterReqs = body.rosterReqs;
        const config = body.config ?? directConfig;
        const draftConfig = await updateDraftConfig(
          params.roomId,
          body.adminToken,
          config,
        );
        return NextResponse.json({ ok: true, draftConfig });
      }
      case "update-scoring-config": {
        const scoringConfig = await updateScoringConfig(
          params.roomId,
          body.adminToken,
          body.config ?? body.scoringConfig,
        );
        return NextResponse.json({ ok: true, scoringConfig });
      }
      case "start-draft": {
        const result = await startDraft(params.roomId, body.adminToken);
        return NextResponse.json({ ok: true, ...result });
      }
      default:
        throw new DraftError(
          400,
          "unknown_action",
          "Unknown setup action. Supported actions: get-setup, join-by-invite, update-room-name, add-team, update-team, remove-team, set-admin-team, mark-invite-sent, send-invite, update-draft-config, update-scoring-config, start-draft.",
        );
    }
  } catch (error) {
    return apiErrorResponse(error);
  }
}
