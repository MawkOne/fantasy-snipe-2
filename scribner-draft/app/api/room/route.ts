import { NextRequest, NextResponse } from "next/server";
import { apiErrorResponse, readJsonObject } from "@/lib/api";
import { createRoom } from "@/lib/store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await readJsonObject(request);
    const room = await createRoom(body.draftName ?? body.name);
    return NextResponse.json(
      {
        roomId: room.id,
        roomCode: room.id,
        draftName: room.name,
        roomStatus: room.status,
        adminToken: room.adminToken,
        adminUrl: `/room/${encodeURIComponent(room.id)}/admin?token=${encodeURIComponent(room.adminToken)}`,
        gmUrl: `/room/${encodeURIComponent(room.id)}`,
      },
      { status: 201 },
    );
  } catch (error) {
    return apiErrorResponse(error);
  }
}
