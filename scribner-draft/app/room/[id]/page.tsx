import { Suspense } from "react";
import { DraftRoomClient } from "@/components/draft-room/DraftRoomClient";
import { LoadingState } from "@/components/draft-room/ui";

export default function GmRoomPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<LoadingState label="Opening your team room…" />}>
      <DraftRoomClient roomId={params.id} role="gm" />
    </Suspense>
  );
}
