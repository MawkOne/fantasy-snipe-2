export type Position = "C" | "LW" | "RW" | "D" | "G";

/** NHL headshots use the official NHL CDN pattern. */
const headshot = (nhlId: number) =>
  `https://assets.nhle.com/mugs/nhl/latest/${nhlId}.png`;

export interface Player {
  id: string;
  name: string;
  position: Position;
  nhlTeam: string;
  headshotUrl?: string;
  // ADP (average draft position) from Matt Larkin's top 300 (2026-27)
  adp: number | null;
  // Larkin's rank
  rank: number;
  // Write-up summary from Larkin's rankings
  writeup: string;
  // Projected season stats (optional — not used when writeup is shown)
  g?: number;
  a?: number;
  pm?: number;
  pim?: number;
  shg?: number;
  shog?: number;
  w?: number;
  ga?: number;
  sv?: number;
  ol?: number;
  shol?: number;
  so?: number;
}

/** League scoring categories from the UHHP owners manual. */
export const SCORING = {
  skater: { g: 3, a: 2, pm: 0.25, pim: 0, shg: 2, shog: 1 },
  dBonus: { g: 2, a: 1 }, // defensemen bonus
  goalie: { w: 2, ga: -1.25, sv: 0.2, ol: 1, shol: 1, so: 1 },
} as const;

export interface ScoringMetric {
  enabled: boolean;
  value: number;
}

export interface ScoringConfig {
  skater: {
    g: ScoringMetric;
    a: ScoringMetric;
    pm: ScoringMetric;
    pim: ScoringMetric;
    shg: ScoringMetric;
    shog: ScoringMetric;
  };
  dBonus: {
    g: ScoringMetric;
    a: ScoringMetric;
  };
  goalie: {
    w: ScoringMetric;
    ga: ScoringMetric;
    sv: ScoringMetric;
    ol: ScoringMetric;
    shol: ScoringMetric;
    so: ScoringMetric;
  };
}

export type ScoringConfigInput = {
  skater?: Partial<
    Record<keyof ScoringConfig["skater"], ScoringMetric | number>
  >;
  dBonus?: Partial<
    Record<keyof ScoringConfig["dBonus"], ScoringMetric | number>
  >;
  goalie?: Partial<
    Record<keyof ScoringConfig["goalie"], ScoringMetric | number>
  >;
};

const enabledMetric = (value: number): ScoringMetric => ({
  enabled: true,
  value,
});

export const DEFAULT_SCORING_CONFIG: ScoringConfig = {
  skater: {
    g: enabledMetric(SCORING.skater.g),
    a: enabledMetric(SCORING.skater.a),
    pm: enabledMetric(SCORING.skater.pm),
    pim: enabledMetric(SCORING.skater.pim),
    shg: enabledMetric(SCORING.skater.shg),
    shog: enabledMetric(SCORING.skater.shog),
  },
  dBonus: {
    g: enabledMetric(SCORING.dBonus.g),
    a: enabledMetric(SCORING.dBonus.a),
  },
  goalie: {
    w: enabledMetric(SCORING.goalie.w),
    ga: enabledMetric(SCORING.goalie.ga),
    sv: enabledMetric(SCORING.goalie.sv),
    ol: enabledMetric(SCORING.goalie.ol),
    shol: enabledMetric(SCORING.goalie.shol),
    so: enabledMetric(SCORING.goalie.so),
  },
};

/** Roster minimum requirements. */
export const ROSTER_REQS: Record<string, number> = {
  C: 2,
  LW: 1,
  RW: 1,
  W: 3, // combined wingers
  F: 4, // forward flex (C or W)
  D: 4,
  G: 2,
  TOTAL: 15,
};

function configuredMetricValue(
  config: ScoringConfigInput | undefined,
  group: keyof ScoringConfig,
  key: string,
): number {
  const activeConfig = config ?? DEFAULT_SCORING_CONFIG;
  const groupConfig = activeConfig[group] as unknown as
    | Record<string, unknown>
    | undefined;
  const metric = groupConfig?.[key];

  if (typeof metric === "number") return Number.isFinite(metric) ? metric : 0;
  if (!metric || typeof metric !== "object") return 0;

  const candidate = metric as Partial<ScoringMetric>;
  if (candidate.enabled === false) return 0;
  return typeof candidate.value === "number" && Number.isFinite(candidate.value)
    ? candidate.value
    : 0;
}

/** Compute projected fantasy points from ADP rank. */
export function projectedPoints(p: Player): number {
  // Invert ADP so rank 1 = 300 pts, rank 300 = 1 pt
  if (p.adp === null || p.adp === undefined) return 0;
  return Math.max(1, Math.round((301 - p.adp) * 10) / 10);
}

export const NHL_TEAMS: Record<string, string> = {
  ANA: "Anaheim Ducks", BOS: "Boston Bruins", BUF: "Buffalo Sabres",
  CGY: "Calgary Flames", CAR: "Carolina Hurricanes", CHI: "Chicago Blackhawks",
  COL: "Colorado Avalanche", CBJ: "Columbus Blue Jackets", DAL: "Dallas Stars",
  DET: "Detroit Red Wings", EDM: "Edmonton Oilers", FLA: "Florida Panthers",
  LAK: "Los Angeles Kings", MIN: "Minnesota Wild", MTL: "Montréal Canadiens",
  NSH: "Nashville Predators", NJD: "New Jersey Devils", NYI: "New York Islanders",
  NYR: "New York Rangers", OTT: "Ottawa Senators", PHI: "Philadelphia Flyers",
  PIT: "Pittsburgh Penguins", SJS: "San Jose Sharks", SEA: "Seattle Kraken",
  STL: "St. Louis Blues", TBL: "Tampa Bay Lightning", TOR: "Toronto Maple Leafs",
  UTA: "Utah Hockey Club", VAN: "Vancouver Canucks", VGK: "Vegas Golden Knights",
  WSH: "Washington Capitals", WPG: "Winnipeg Jets",
};

export const PLAYERS: Player[] = [];
// Players are loaded from DRAFT_PLAYERS in draft_players.ts
// See lib/draft_players.ts for the full 300-player pool from Matt Larkin's rankings.