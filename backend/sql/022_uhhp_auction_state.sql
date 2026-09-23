-- Canonical state and audit schema for the UHHP silent auction.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.uhhp_auction_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  league_id BIGINT NOT NULL,
  draft_year INTEGER NOT NULL,
  rules_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'setup',
  stage TEXT NOT NULL DEFAULT 'superstar',
  stage_round INTEGER NOT NULL DEFAULT 1,
  nomination_cursor INTEGER NOT NULL DEFAULT 0,
  version INTEGER NOT NULL DEFAULT 1,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  voided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_drafts_league_fk
    FOREIGN KEY (league_id)
    REFERENCES public.cbs_leagues (id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_auction_drafts_id_league_uk
    UNIQUE (id, league_id),
  CONSTRAINT uhhp_auction_drafts_league_year_uk
    UNIQUE (league_id, draft_year),
  CONSTRAINT uhhp_auction_drafts_year_ck
    CHECK (draft_year >= 2000),
  CONSTRAINT uhhp_auction_drafts_rules_version_ck
    CHECK (BTRIM(rules_version) <> ''),
  CONSTRAINT uhhp_auction_drafts_status_ck
    CHECK (status IN ('setup', 'active', 'completed', 'void')),
  CONSTRAINT uhhp_auction_drafts_stage_ck
    CHECK (stage IN ('superstar', 'ufa', 'rfa_poaching', 'completed')),
  CONSTRAINT uhhp_auction_drafts_stage_round_ck
    CHECK (stage_round >= 1),
  CONSTRAINT uhhp_auction_drafts_cursor_ck
    CHECK (nomination_cursor >= 0),
  CONSTRAINT uhhp_auction_drafts_version_ck
    CHECK (version >= 1),
  CONSTRAINT uhhp_auction_drafts_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object'),
  CONSTRAINT uhhp_auction_drafts_completed_at_ck
    CHECK (completed_at IS NULL OR completed_at >= created_at),
  CONSTRAINT uhhp_auction_drafts_voided_at_ck
    CHECK (voided_at IS NULL OR voided_at >= created_at)
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_draft_teams (
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  team_id TEXT NOT NULL,
  canonical_abbrev TEXT NOT NULL,
  manager_name TEXT NOT NULL,
  manager_email TEXT,
  nomination_order INTEGER NOT NULL,
  tie_break_priority INTEGER NOT NULL,
  rfa_nominations_active BOOLEAN NOT NULL DEFAULT TRUE,
  rfa_nominations_passed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_draft_teams_pk
    PRIMARY KEY (draft_id, league_id, team_id),
  CONSTRAINT uhhp_auction_draft_teams_draft_fk
    FOREIGN KEY (draft_id, league_id)
    REFERENCES public.uhhp_auction_drafts (id, league_id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_auction_draft_teams_cbs_team_fk
    FOREIGN KEY (league_id, team_id)
    REFERENCES public.cbs_teams (league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_draft_teams_abbrev_uk
    UNIQUE (draft_id, canonical_abbrev),
  CONSTRAINT uhhp_auction_draft_teams_nomination_order_uk
    UNIQUE (draft_id, nomination_order),
  CONSTRAINT uhhp_auction_draft_teams_tie_priority_uk
    UNIQUE (draft_id, tie_break_priority),
  CONSTRAINT uhhp_auction_draft_teams_team_id_ck
    CHECK (BTRIM(team_id) <> ''),
  CONSTRAINT uhhp_auction_draft_teams_abbrev_ck
    CHECK (BTRIM(canonical_abbrev) <> ''),
  CONSTRAINT uhhp_auction_draft_teams_manager_name_ck
    CHECK (BTRIM(manager_name) <> ''),
  CONSTRAINT uhhp_auction_draft_teams_manager_email_ck
    CHECK (manager_email IS NULL OR BTRIM(manager_email) <> ''),
  CONSTRAINT uhhp_auction_draft_teams_nomination_order_ck
    CHECK (nomination_order >= 1),
  CONSTRAINT uhhp_auction_draft_teams_tie_priority_ck
    CHECK (tie_break_priority >= 1),
  CONSTRAINT uhhp_auction_draft_teams_rfa_pass_ck
    CHECK (
      rfa_nominations_passed_at IS NULL
      OR NOT rfa_nominations_active
    )
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_player_pool (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  source_key TEXT NOT NULL,
  cbs_player_id TEXT,
  nhl_player_id BIGINT,
  player_name TEXT NOT NULL,
  positions TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
  nhl_team_abbrev TEXT,
  birthdate DATE,
  age_cutoff_date DATE,
  age_at_cutoff INTEGER,
  source_availability TEXT,
  source_team TEXT,
  contract_years INTEGER,
  salary NUMERIC,
  is_rookie BOOLEAN NOT NULL DEFAULT FALSE,
  source_status TEXT,
  entry_type TEXT NOT NULL DEFAULT 'player',
  eligibility TEXT NOT NULL DEFAULT 'REVIEW',
  controlling_team_id TEXT,
  projection JSONB NOT NULL DEFAULT '{}'::JSONB,
  projected_fantasy_points NUMERIC,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_player_pool_id_context_uk
    UNIQUE (id, draft_id, league_id),
  CONSTRAINT uhhp_auction_player_pool_source_uk
    UNIQUE (draft_id, source_key),
  CONSTRAINT uhhp_auction_player_pool_draft_fk
    FOREIGN KEY (draft_id, league_id)
    REFERENCES public.uhhp_auction_drafts (id, league_id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_auction_player_pool_controller_fk
    FOREIGN KEY (draft_id, league_id, controlling_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_player_pool_source_key_ck
    CHECK (BTRIM(source_key) <> ''),
  CONSTRAINT uhhp_auction_player_pool_cbs_id_ck
    CHECK (cbs_player_id IS NULL OR BTRIM(cbs_player_id) <> ''),
  CONSTRAINT uhhp_auction_player_pool_nhl_id_ck
    CHECK (nhl_player_id IS NULL OR nhl_player_id > 0),
  CONSTRAINT uhhp_auction_player_pool_name_ck
    CHECK (BTRIM(player_name) <> ''),
  CONSTRAINT uhhp_auction_player_pool_dates_ck
    CHECK (
      birthdate IS NULL
      OR age_cutoff_date IS NULL
      OR birthdate <= age_cutoff_date
    ),
  CONSTRAINT uhhp_auction_player_pool_age_ck
    CHECK (age_at_cutoff IS NULL OR age_at_cutoff BETWEEN 0 AND 150),
  CONSTRAINT uhhp_auction_player_pool_age_date_ck
    CHECK (age_at_cutoff IS NULL OR age_cutoff_date IS NOT NULL),
  CONSTRAINT uhhp_auction_player_pool_contract_years_ck
    CHECK (contract_years IS NULL OR contract_years >= 0),
  CONSTRAINT uhhp_auction_player_pool_salary_ck
    CHECK (salary IS NULL OR salary >= 0),
  CONSTRAINT uhhp_auction_player_pool_entry_type_ck
    CHECK (entry_type IN ('player', 'rookie', 'draft_pick', 'cap_hit')),
  CONSTRAINT uhhp_auction_player_pool_eligibility_ck
    CHECK (
      eligibility IN (
        'PROTECTED',
        'RFA',
        'UFA',
        'ROOKIE',
        'ASSET',
        'CAP_HIT',
        'REVIEW'
      )
    ),
  CONSTRAINT uhhp_auction_player_pool_projection_ck
    CHECK (JSONB_TYPEOF(projection) = 'object'),
  CONSTRAINT uhhp_auction_player_pool_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_nominations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  status TEXT NOT NULL DEFAULT 'awaiting_nomination',
  stage TEXT NOT NULL,
  stage_round INTEGER NOT NULL,
  sequence_no INTEGER NOT NULL,
  nominator_team_id TEXT NOT NULL,
  player_pool_id UUID,
  player_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,
  high_bid_team_id TEXT,
  high_bid_amount NUMERIC,
  winning_team_id TEXT,
  winning_bid_amount NUMERIC,
  contract_years INTEGER,
  outcome JSONB,
  version INTEGER NOT NULL DEFAULT 1,
  nominated_at TIMESTAMPTZ,
  bidding_opened_at TIMESTAMPTZ,
  revealed_at TIMESTAMPTZ,
  finalized_at TIMESTAMPTZ,
  voided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_nominations_id_context_uk
    UNIQUE (id, draft_id, league_id),
  CONSTRAINT uhhp_auction_nominations_stage_sequence_uk
    UNIQUE (draft_id, stage, stage_round, sequence_no),
  CONSTRAINT uhhp_auction_nominations_draft_fk
    FOREIGN KEY (draft_id, league_id)
    REFERENCES public.uhhp_auction_drafts (id, league_id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_auction_nominations_nominator_fk
    FOREIGN KEY (draft_id, league_id, nominator_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_nominations_player_fk
    FOREIGN KEY (player_pool_id, draft_id, league_id)
    REFERENCES public.uhhp_auction_player_pool (id, draft_id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_nominations_high_bid_team_fk
    FOREIGN KEY (draft_id, league_id, high_bid_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_nominations_winning_team_fk
    FOREIGN KEY (draft_id, league_id, winning_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_nominations_status_ck
    CHECK (
      status IN (
        'awaiting_nomination',
        'sealed_bidding',
        'revealed',
        'rfa_match_pending',
        'finalized',
        'no_sale',
        'void'
      )
    ),
  CONSTRAINT uhhp_auction_nominations_stage_ck
    CHECK (stage IN ('superstar', 'ufa', 'rfa_poaching')),
  CONSTRAINT uhhp_auction_nominations_stage_round_ck
    CHECK (stage_round >= 1),
  CONSTRAINT uhhp_auction_nominations_sequence_ck
    CHECK (sequence_no >= 1),
  CONSTRAINT uhhp_auction_nominations_player_ck
    CHECK (
      status IN ('awaiting_nomination', 'void')
      OR player_pool_id IS NOT NULL
    ),
  CONSTRAINT uhhp_auction_nominations_player_snapshot_ck
    CHECK (JSONB_TYPEOF(player_snapshot) = 'object'),
  CONSTRAINT uhhp_auction_nominations_high_bid_ck
    CHECK (
      high_bid_amount IS NULL
      OR (
        high_bid_amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
        AND (
          high_bid_amount = 0
          OR (
            high_bid_amount >= 2
            AND high_bid_amount = TRUNC(high_bid_amount)
          )
        )
      )
    ),
  CONSTRAINT uhhp_auction_nominations_high_bid_team_ck
    CHECK (
      high_bid_amount IS NULL
      OR high_bid_amount = 0
      OR high_bid_team_id IS NOT NULL
    ),
  CONSTRAINT uhhp_auction_nominations_winning_bid_ck
    CHECK (
      winning_bid_amount IS NULL
      OR (
        winning_bid_amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
        AND (
          winning_bid_amount = 0
          OR (
            winning_bid_amount >= 2
            AND winning_bid_amount = TRUNC(winning_bid_amount)
          )
        )
      )
    ),
  CONSTRAINT uhhp_auction_nominations_winning_team_ck
    CHECK (
      winning_bid_amount IS NULL
      OR winning_bid_amount = 0
      OR winning_team_id IS NOT NULL
    ),
  CONSTRAINT uhhp_auction_nominations_no_sale_ck
    CHECK (
      status <> 'no_sale'
      OR (
        winning_team_id IS NULL
        AND COALESCE(winning_bid_amount, 0) = 0
      )
    ),
  CONSTRAINT uhhp_auction_nominations_contract_years_ck
    CHECK (contract_years IS NULL OR contract_years >= 0),
  CONSTRAINT uhhp_auction_nominations_outcome_ck
    CHECK (outcome IS NULL OR JSONB_TYPEOF(outcome) = 'object'),
  CONSTRAINT uhhp_auction_nominations_version_ck
    CHECK (version >= 1),
  CONSTRAINT uhhp_auction_nominations_finalized_at_ck
    CHECK (finalized_at IS NULL OR finalized_at >= created_at),
  CONSTRAINT uhhp_auction_nominations_voided_at_ck
    CHECK (voided_at IS NULL OR voided_at >= created_at)
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_bid_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_sequence BIGSERIAL NOT NULL UNIQUE,
  nomination_id UUID NOT NULL,
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  team_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  amount NUMERIC,
  supersedes_bid_event_id UUID,
  idempotency_key TEXT NOT NULL,
  actor_id TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_bid_events_id_context_uk
    UNIQUE (id, nomination_id, draft_id, league_id, team_id),
  CONSTRAINT uhhp_auction_bid_events_idempotency_uk
    UNIQUE (draft_id, idempotency_key),
  CONSTRAINT uhhp_auction_bid_events_nomination_fk
    FOREIGN KEY (nomination_id, draft_id, league_id)
    REFERENCES public.uhhp_auction_nominations (id, draft_id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_bid_events_team_fk
    FOREIGN KEY (draft_id, league_id, team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_bid_events_supersedes_fk
    FOREIGN KEY (
      supersedes_bid_event_id,
      nomination_id,
      draft_id,
      league_id,
      team_id
    )
    REFERENCES public.uhhp_auction_bid_events (
      id,
      nomination_id,
      draft_id,
      league_id,
      team_id
    )
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_bid_events_type_ck
    CHECK (event_type IN ('submit', 'replacement', 'cancel')),
  CONSTRAINT uhhp_auction_bid_events_amount_ck
    CHECK (
      amount IS NULL
      OR (
        amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
        AND (
          amount = 0
          OR (amount >= 2 AND amount = TRUNC(amount))
        )
      )
    ),
  CONSTRAINT uhhp_auction_bid_events_event_amount_ck
    CHECK (
      (event_type = 'cancel' AND amount IS NULL)
      OR (
        event_type IN ('submit', 'replacement')
        AND amount IS NOT NULL
      )
    ),
  CONSTRAINT uhhp_auction_bid_events_supersedes_ck
    CHECK (
      (event_type = 'submit' AND supersedes_bid_event_id IS NULL)
      OR (
        event_type IN ('replacement', 'cancel')
        AND supersedes_bid_event_id IS NOT NULL
      )
    ),
  CONSTRAINT uhhp_auction_bid_events_idempotency_key_ck
    CHECK (BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_bid_events_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_rfa_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nomination_id UUID NOT NULL,
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  controlling_team_id TEXT NOT NULL,
  high_bid_team_id TEXT NOT NULL,
  high_bid_amount NUMERIC NOT NULL,
  decision TEXT NOT NULL,
  decided_by TEXT,
  idempotency_key TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_rfa_decisions_nomination_uk
    UNIQUE (nomination_id),
  CONSTRAINT uhhp_auction_rfa_decisions_nomination_fk
    FOREIGN KEY (nomination_id, draft_id, league_id)
    REFERENCES public.uhhp_auction_nominations (id, draft_id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_rfa_decisions_controller_fk
    FOREIGN KEY (draft_id, league_id, controlling_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_rfa_decisions_high_bidder_fk
    FOREIGN KEY (draft_id, league_id, high_bid_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_rfa_decisions_decision_ck
    CHECK (decision IN ('match', 'pass')),
  CONSTRAINT uhhp_auction_rfa_decisions_high_bid_ck
    CHECK (
      high_bid_amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
      AND high_bid_amount >= 2
      AND high_bid_amount = TRUNC(high_bid_amount)
    ),
  CONSTRAINT uhhp_auction_rfa_decisions_idempotency_key_ck
    CHECK (idempotency_key IS NULL OR BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_rfa_decisions_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_tie_audits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nomination_id UUID NOT NULL,
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  tied_amount NUMERIC NOT NULL,
  tied_team_ids TEXT[] NOT NULL,
  winning_team_id TEXT NOT NULL,
  old_tie_break_order TEXT[] NOT NULL,
  new_tie_break_order TEXT[] NOT NULL,
  idempotency_key TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  resolved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_tie_audits_nomination_uk
    UNIQUE (nomination_id),
  CONSTRAINT uhhp_auction_tie_audits_nomination_fk
    FOREIGN KEY (nomination_id, draft_id, league_id)
    REFERENCES public.uhhp_auction_nominations (id, draft_id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_tie_audits_winner_fk
    FOREIGN KEY (draft_id, league_id, winning_team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_tie_audits_amount_ck
    CHECK (
      tied_amount::TEXT NOT IN ('NaN', 'Infinity', '-Infinity')
      AND tied_amount >= 2
      AND tied_amount = TRUNC(tied_amount)
    ),
  CONSTRAINT uhhp_auction_tie_audits_teams_ck
    CHECK (
      CARDINALITY(tied_team_ids) >= 2
      AND ARRAY_POSITION(tied_team_ids, NULL) IS NULL
      AND winning_team_id = ANY (tied_team_ids)
    ),
  CONSTRAINT uhhp_auction_tie_audits_order_ck
    CHECK (
      CARDINALITY(old_tie_break_order) >= 2
      AND CARDINALITY(old_tie_break_order) = CARDINALITY(new_tie_break_order)
      AND ARRAY_POSITION(old_tie_break_order, NULL) IS NULL
      AND ARRAY_POSITION(new_tie_break_order, NULL) IS NULL
      AND tied_team_ids <@ old_tie_break_order
      AND tied_team_ids <@ new_tie_break_order
    ),
  CONSTRAINT uhhp_auction_tie_audits_idempotency_key_ck
    CHECK (idempotency_key IS NULL OR BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_tie_audits_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object')
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_sequence BIGSERIAL NOT NULL UNIQUE,
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  nomination_id UUID,
  team_id TEXT,
  event_type TEXT NOT NULL,
  actor_type TEXT,
  actor_id TEXT,
  correlation_id UUID,
  idempotency_key TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_events_draft_fk
    FOREIGN KEY (draft_id, league_id)
    REFERENCES public.uhhp_auction_drafts (id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_events_nomination_fk
    FOREIGN KEY (nomination_id, draft_id, league_id)
    REFERENCES public.uhhp_auction_nominations (id, draft_id, league_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_events_team_fk
    FOREIGN KEY (draft_id, league_id, team_id)
    REFERENCES public.uhhp_auction_draft_teams (draft_id, league_id, team_id)
    ON DELETE RESTRICT,
  CONSTRAINT uhhp_auction_events_type_ck
    CHECK (BTRIM(event_type) <> ''),
  CONSTRAINT uhhp_auction_events_idempotency_key_ck
    CHECK (idempotency_key IS NULL OR BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_events_payload_ck
    CHECK (JSONB_TYPEOF(payload) = 'object')
);

CREATE TABLE IF NOT EXISTS public.uhhp_auction_import_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID NOT NULL,
  league_id BIGINT NOT NULL,
  import_type TEXT NOT NULL,
  source TEXT NOT NULL,
  source_uri TEXT,
  source_checksum TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  idempotency_key TEXT,
  rows_seen INTEGER NOT NULL DEFAULT 0,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  rows_updated INTEGER NOT NULL DEFAULT 0,
  rows_rejected INTEGER NOT NULL DEFAULT 0,
  errors JSONB NOT NULL DEFAULT '[]'::JSONB,
  metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT uhhp_auction_import_runs_draft_fk
    FOREIGN KEY (draft_id, league_id)
    REFERENCES public.uhhp_auction_drafts (id, league_id)
    ON DELETE CASCADE,
  CONSTRAINT uhhp_auction_import_runs_type_ck
    CHECK (BTRIM(import_type) <> ''),
  CONSTRAINT uhhp_auction_import_runs_source_ck
    CHECK (BTRIM(source) <> ''),
  CONSTRAINT uhhp_auction_import_runs_status_ck
    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'void')),
  CONSTRAINT uhhp_auction_import_runs_idempotency_key_ck
    CHECK (idempotency_key IS NULL OR BTRIM(idempotency_key) <> ''),
  CONSTRAINT uhhp_auction_import_runs_counts_ck
    CHECK (
      rows_seen >= 0
      AND rows_inserted >= 0
      AND rows_updated >= 0
      AND rows_rejected >= 0
    ),
  CONSTRAINT uhhp_auction_import_runs_errors_ck
    CHECK (JSONB_TYPEOF(errors) = 'array'),
  CONSTRAINT uhhp_auction_import_runs_metadata_ck
    CHECK (JSONB_TYPEOF(metadata) = 'object'),
  CONSTRAINT uhhp_auction_import_runs_finished_at_ck
    CHECK (
      finished_at IS NULL
      OR started_at IS NULL
      OR finished_at >= started_at
    )
);

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_drafts_league_status
  ON public.uhhp_auction_drafts (league_id, status, draft_year DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_pool_draft_cbs_player
  ON public.uhhp_auction_player_pool (draft_id, cbs_player_id)
  WHERE cbs_player_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_pool_draft_nhl_player
  ON public.uhhp_auction_player_pool (draft_id, nhl_player_id)
  WHERE nhl_player_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_pool_eligibility
  ON public.uhhp_auction_player_pool (draft_id, eligibility, entry_type);

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_pool_controller
  ON public.uhhp_auction_player_pool (draft_id, controlling_team_id)
  WHERE controlling_team_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_pool_player_name
  ON public.uhhp_auction_player_pool (draft_id, LOWER(player_name));

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_nominations_one_active
  ON public.uhhp_auction_nominations (league_id)
  WHERE status IN (
    'awaiting_nomination',
    'sealed_bidding',
    'revealed',
    'rfa_match_pending'
  );

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_nominations_stage_status
  ON public.uhhp_auction_nominations (
    draft_id,
    stage,
    stage_round,
    status,
    sequence_no
  );

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_nominations_player
  ON public.uhhp_auction_nominations (draft_id, player_pool_id, created_at DESC)
  WHERE player_pool_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_nominations_nominator
  ON public.uhhp_auction_nominations (draft_id, nominator_team_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_bid_events_latest
  ON public.uhhp_auction_bid_events (
    nomination_id,
    team_id,
    event_sequence DESC
  );

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_bid_events_initial_submit
  ON public.uhhp_auction_bid_events (nomination_id, team_id)
  WHERE event_type = 'submit';

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_bid_events_one_successor
  ON public.uhhp_auction_bid_events (supersedes_bid_event_id)
  WHERE supersedes_bid_event_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_rfa_decisions_idempotency
  ON public.uhhp_auction_rfa_decisions (draft_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_rfa_decisions_draft
  ON public.uhhp_auction_rfa_decisions (draft_id, decided_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_tie_audits_idempotency
  ON public.uhhp_auction_tie_audits (draft_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_tie_audits_draft
  ON public.uhhp_auction_tie_audits (draft_id, resolved_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_events_idempotency
  ON public.uhhp_auction_events (draft_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_events_draft_sequence
  ON public.uhhp_auction_events (draft_id, event_sequence);

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_events_nomination_sequence
  ON public.uhhp_auction_events (nomination_id, event_sequence)
  WHERE nomination_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_events_type_time
  ON public.uhhp_auction_events (draft_id, event_type, occurred_at DESC);

ALTER TABLE public.cbs_rosters
  ADD COLUMN IF NOT EXISTS uhhp_auction_nomination_id UUID;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM pg_constraint
     WHERE conname = 'cbs_rosters_uhhp_auction_nomination_fk'
       AND conrelid = 'public.cbs_rosters'::REGCLASS
  ) THEN
    ALTER TABLE public.cbs_rosters
      ADD CONSTRAINT cbs_rosters_uhhp_auction_nomination_fk
      FOREIGN KEY (uhhp_auction_nomination_id)
      REFERENCES public.uhhp_auction_nominations (id)
      ON DELETE RESTRICT;
  END IF;
END;
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_cbs_rosters_uhhp_auction_nomination
  ON public.cbs_rosters (uhhp_auction_nomination_id)
  WHERE uhhp_auction_nomination_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_uhhp_auction_import_runs_idempotency
  ON public.uhhp_auction_import_runs (draft_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_uhhp_auction_import_runs_draft_status
  ON public.uhhp_auction_import_runs (draft_id, status, created_at DESC);

CREATE OR REPLACE VIEW public.uhhp_auction_latest_effective_bids AS
SELECT
  nomination.id AS nomination_id,
  nomination.draft_id,
  nomination.league_id,
  draft_team.team_id,
  draft_team.canonical_abbrev,
  latest_event.id AS latest_bid_event_id,
  latest_event.event_sequence AS latest_event_sequence,
  latest_event.event_type AS latest_event_type,
  latest_event.amount AS submitted_amount,
  CASE
    WHEN latest_event.id IS NULL OR latest_event.event_type = 'cancel' THEN 0::NUMERIC
    ELSE latest_event.amount
  END AS effective_amount,
  COALESCE(latest_event.event_type IN ('submit', 'replacement'), FALSE) AS responded,
  COALESCE(latest_event.event_type = 'cancel', FALSE) AS canceled,
  latest_event.created_at AS latest_event_at
FROM public.uhhp_auction_nominations AS nomination
JOIN public.uhhp_auction_draft_teams AS draft_team
  ON draft_team.draft_id = nomination.draft_id
 AND draft_team.league_id = nomination.league_id
LEFT JOIN LATERAL (
  SELECT bid_event.*
  FROM public.uhhp_auction_bid_events AS bid_event
  WHERE bid_event.nomination_id = nomination.id
    AND bid_event.draft_id = nomination.draft_id
    AND bid_event.league_id = nomination.league_id
    AND bid_event.team_id = draft_team.team_id
  ORDER BY bid_event.event_sequence DESC
  LIMIT 1
) AS latest_event ON TRUE;

CREATE OR REPLACE FUNCTION public.uhhp_auction_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_uhhp_auction_drafts_updated_at
  ON public.uhhp_auction_drafts;
CREATE TRIGGER trg_uhhp_auction_drafts_updated_at
BEFORE UPDATE ON public.uhhp_auction_drafts
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_set_updated_at();

DROP TRIGGER IF EXISTS trg_uhhp_auction_draft_teams_updated_at
  ON public.uhhp_auction_draft_teams;
CREATE TRIGGER trg_uhhp_auction_draft_teams_updated_at
BEFORE UPDATE ON public.uhhp_auction_draft_teams
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_set_updated_at();

DROP TRIGGER IF EXISTS trg_uhhp_auction_player_pool_updated_at
  ON public.uhhp_auction_player_pool;
CREATE TRIGGER trg_uhhp_auction_player_pool_updated_at
BEFORE UPDATE ON public.uhhp_auction_player_pool
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_set_updated_at();

DROP TRIGGER IF EXISTS trg_uhhp_auction_nominations_updated_at
  ON public.uhhp_auction_nominations;
CREATE TRIGGER trg_uhhp_auction_nominations_updated_at
BEFORE UPDATE ON public.uhhp_auction_nominations
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_set_updated_at();

DROP TRIGGER IF EXISTS trg_uhhp_auction_import_runs_updated_at
  ON public.uhhp_auction_import_runs;
CREATE TRIGGER trg_uhhp_auction_import_runs_updated_at
BEFORE UPDATE ON public.uhhp_auction_import_runs
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_set_updated_at();

CREATE OR REPLACE FUNCTION public.uhhp_auction_reject_event_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION '% is append-only; record a new event instead', TG_TABLE_NAME
    USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS trg_uhhp_auction_bid_events_append_only
  ON public.uhhp_auction_bid_events;
CREATE TRIGGER trg_uhhp_auction_bid_events_append_only
BEFORE UPDATE OR DELETE ON public.uhhp_auction_bid_events
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_reject_event_mutation();

DROP TRIGGER IF EXISTS trg_uhhp_auction_bid_events_no_truncate
  ON public.uhhp_auction_bid_events;
CREATE TRIGGER trg_uhhp_auction_bid_events_no_truncate
BEFORE TRUNCATE ON public.uhhp_auction_bid_events
FOR EACH STATEMENT
EXECUTE FUNCTION public.uhhp_auction_reject_event_mutation();

DROP TRIGGER IF EXISTS trg_uhhp_auction_events_append_only
  ON public.uhhp_auction_events;
CREATE TRIGGER trg_uhhp_auction_events_append_only
BEFORE UPDATE OR DELETE ON public.uhhp_auction_events
FOR EACH ROW
EXECUTE FUNCTION public.uhhp_auction_reject_event_mutation();

DROP TRIGGER IF EXISTS trg_uhhp_auction_events_no_truncate
  ON public.uhhp_auction_events;
CREATE TRIGGER trg_uhhp_auction_events_no_truncate
BEFORE TRUNCATE ON public.uhhp_auction_events
FOR EACH STATEMENT
EXECUTE FUNCTION public.uhhp_auction_reject_event_mutation();
