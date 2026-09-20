import { Suspense } from "react";
import { DraftRoomClient } from "@/components/draft-room/DraftRoomClient";
import { LoadingState } from "@/components/draft-room/ui";

export default function AdminRoomPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<LoadingState label="Opening commissioner controls…" />}>
      <DraftRoomClient roomId={params.id} role="admin" />
    </Suspense>
  );
}
