-- Persist each team's draft-room lineup/layout state.
-- Replaces browser-only storage for dress/sit, empty slots, and targets.

CREATE TABLE IF NOT EXISTS public.uhhp_team_layouts (
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  team_id TEXT NOT NULL,
  bench JSONB NOT NULL DEFAULT '[]'::JSONB,
  empty_slots JSONB NOT NULL DEFAULT '[]'::JSONB,
  targets JSONB NOT NULL DEFAULT '{}'::JSONB,
  version INTEGER NOT NULL DEFAULT 1,
  updated_by TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (draft_id, team_id),
  CONSTRAINT uhhp_team_layouts_team_fk
    FOREIGN KEY (draft_id, league_id, team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_team_layouts_bench_ck CHECK (JSONB_TYPEOF(bench) = 'array'),
  CONSTRAINT uhhp_team_layouts_empty_ck CHECK (JSONB_TYPEOF(empty_slots) = 'array'),
  CONSTRAINT uhhp_team_layouts_targets_ck CHECK (JSONB_TYPEOF(targets) = 'object'),
  CONSTRAINT uhhp_team_layouts_version_ck CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS idx_uhhp_team_layouts_league_team
  ON public.uhhp_team_layouts (league_id, team_id);
