import { NextRequest, NextResponse } from "next/server";
import { apiErrorResponse, readJsonObject } from "@/lib/api";
import {
  DraftError,
  deleteDraft,
  finishDraft,
  getAdminState,
  getGmState,
  manualAssignPlayer,
  manualRemovePlayer,
  manualReplacePlayer,
  revealRound,
  startRound,
  submitAdminPick,
  submitPick,
  updateLiveSetup,
} from "@/lib/store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface RouteContext {
  params: { roomId: string };
}

export async function POST(request: NextRequest, { params }: RouteContext) {
  try {
    const body = await readJsonObject(request);
    const action = typeof body.action === "string" ? body.action : "";

    switch (action) {
      case "get-gm-state": {
        const state = await getGmState(
          params.roomId,
          body.teamToken ?? body.inviteToken,
        );
        return NextResponse.json(state);
      }
      case "submit-pick": {
        const pick = await submitPick(
          params.roomId,
          body.teamToken ?? body.inviteToken,
          body.playerId,
        );
        return NextResponse.json({ ok: true, pick });
      }
      case "get-admin-state": {
        const state = await getAdminState(params.roomId, body.adminToken);
        return NextResponse.json(state);
      }
      case "submit-admin-pick": {
        const pick = await submitAdminPick(
          params.roomId,
          body.adminToken,
          body.playerId,
        );
        return NextResponse.json({ ok: true, pick });
      }
      case "start-round": {
        const result = await startRound(params.roomId, body.adminToken);
        return NextResponse.json({ ok: true, ...result });
      }
      case "reveal": {
        const result = await revealRound(
          params.roomId,
          body.adminToken,
          body.confirmMissing,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "finish-draft": {
        const result = await finishDraft(params.roomId, body.adminToken);
        return NextResponse.json({ ok: true, ...result });
      }
      case "manual-assign-player": {
        const result = await manualAssignPlayer(
          params.roomId,
          body.adminToken,
          body.teamId,
          body.playerId,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "manual-replace-player": {
        const result = await manualReplacePlayer(
          params.roomId,
          body.adminToken,
          body.teamId,
          body.oldPlayerId,
          body.newPlayerId,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "manual-remove-player": {
        const result = await manualRemovePlayer(
          params.roomId,
          body.adminToken,
          body.teamId,
          body.playerId,
        );
        return NextResponse.json({ ok: true, ...result });
      }
      case "update-live-setup": {
        const state = await updateLiveSetup(params.roomId, body.adminToken, {
          draftName: body.draftName,
          rounds: body.rounds,
          rosterReqs: body.rosterReqs,
          scoringConfig: body.scoringConfig,
        });
        return NextResponse.json({ ok: true, ...state });
      }
      case "delete-draft": {
        const result = await deleteDraft(
          params.roomId,
          body.adminToken,
          body.confirmationName,
        );
        return NextResponse.json(result);
      }
      default:
        throw new DraftError(
          400,
          "unknown_action",
          "Unknown draft action. Supported actions: get-gm-state, submit-pick, get-admin-state, submit-admin-pick, start-round, reveal, finish-draft, manual-assign-player, manual-replace-player, manual-remove-player, update-live-setup, delete-draft.",
        );
    }
  } catch (error) {
    return apiErrorResponse(error);
  }
}
