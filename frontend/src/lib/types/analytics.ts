// frontend/src/lib/types/analytics.ts
// TypeScript interfaces mirroring the Pydantic models in the backend

export interface StatsBadgeData {
  avg: number;
  med: number;
  std: number;
  min: number;
  max: number;
  mode: number;
  p25: number;
  p75: number;
  n: number;
}

export interface BetEntryData {
  team: string;
  market: string;
  line: string;
  probability: number;
  data_points: number;
  odd: number;
  risk_tier: 'low' | 'med' | 'high';
  risk_label: string;
  explanation: string;
  has_draft_projection: boolean;
  draft_multiplier?: number;
}

export interface BarData {
  label: string;
  value: number;
  color: string;
}

export interface EGRSection {
  t1_values: { fb: number; fd: number; fh: number };
  t2_values: { fb: number; fd: number; fh: number };
  egr_score_t1: number;
  egr_score_t2: number;
  explain_text: string;
  comments: string[];
}

export interface MLRSection {
  t1: { fbaron_rate: number; avg_barons: number; avg_inhibitors: number; avg_towers: number };
  t2: { fbaron_rate: number; avg_barons: number; avg_inhibitors: number; avg_towers: number };
  explain_text: string;
  comments: string[];
}

export interface RadarSection {
  labels: string[];
  t1_values: number[];
  t2_values: number[];
  explain_text: string;
  comments: string[];
}

export interface TimelineSection {
  minutes: number[];
  gold_diff_t1: number[];
  cs_diff_t1: number[];
  xp_diff_t1: number[];
  gold_diff_t2: number[];
  cs_diff_t2: number[];
  xp_diff_t2: number[];
  draft_projection_active: boolean;
  draft_gold_diff_t1?: number[];
  draft_cs_diff_t1?: number[];
  draft_xp_diff_t1?: number[];
  draft_gold_diff_t2?: number[];
  draft_cs_diff_t2?: number[];
  draft_xp_diff_t2?: number[];
  mult_t1?: number;
  mult_t2?: number;
  explain_text: string;
  comments: string[];
}

// VisionSection removed as part of the simplification

export interface EconomySection {
  egpm: { t1: number; t2: number; t1_history?: number[]; t2_history?: number[] };
  dpm: { t1: number; t2: number };
  gold_layer?: {
    t1: { egdi: number; throw_rate: number; comeback_rate: number };
    t2: { egdi: number; throw_rate: number; comeback_rate: number };
  };
  explain_text: string;
  comments: string[];
}

export interface PaceSection {
  ckpm: { t1: number; t2: number };
  kpm: { t1: number; t2: number };
  explain_text: string;
  comments: string[];
}

export interface WinRateSection {
  t1_win_rate: number;
  t2_win_rate: number;
  t1_wins: number;
  t2_wins: number;
  t1_total: number;
  t2_total: number;
  explain_text: string;
  comments: string[];
}

export interface RecentFormSection {
  t1_results: string[];
  t2_results: string[];
  t1_recent_wr: number;
  t2_recent_wr: number;
  comments: string[];
}

export interface DistributionSection {
  title: string;
  histogram_data: number[];
  stats: StatsBadgeData;
  bet_entries: BetEntryData[];
  draft_projection?: Record<string, unknown>;
  explain_text: string;
  comments: string[];
}

export interface KillsPerTeamSection {
  t1_histogram: number[];
  t2_histogram: number[];
  t1_stats?: StatsBadgeData;
  t2_stats?: StatsBadgeData;
  t1_bet_entries: BetEntryData[];
  t2_bet_entries: BetEntryData[];
  draft_projection?: Record<string, unknown>;
  explain_text: string;
  comments: string[];
}

export interface HandicapSection {
  t1_histogram: number[];
  t2_histogram: number[];
  t1_stats?: StatsBadgeData;
  t2_stats?: StatsBadgeData;
  bet_entries: BetEntryData[];
  draft_projection?: Record<string, unknown>;
  explain_text: string;
  comments: string[];
}

export interface EVFinderTeamCard {
  team: string;
  color: string;
  markets: Record<string, BetEntryData[]>;
}

export interface EVFinderSection {
  t1_card: EVFinderTeamCard;
  t2_card: EVFinderTeamCard;
  joint_card: EVFinderTeamCard;
}

export interface SeriesStatEntry {
  game: number;
  matches: number;
  avg_kills: number;
  avg_deaths: number;
  avg_dragons: number;
  avg_barons: number;
  avg_towers: number;
  avg_duration_min: number;
  win_rate: number;
}

export interface SeriesSection {
  t1_series: SeriesStatEntry[];
  t2_series: SeriesStatEntry[];
  explain_text: string;
  comments: string[];
}

export interface SideStatEntry {
  side: string;
  games: number;
  wins: number;
  win_rate: number;
}

export interface LeagueContextSection {
  league: string;
  avg_total_kills: number;
  blue_win_rate: number;
  avg_duration: number;
  total_games_analyzed: number;
  insights: string[];
}

export interface ObjectiveCorrelations {
  fb_wr: number;
  fd_wr: number;
  fbaron_wr: number;
  fherald_wr: number;
  large_lead_wr: number;
  soul_wr: number;
}

export interface AnalyticsResponse {
  meta: {
    team1: string;
    team2: string;
    patch_label: string;
    games_t1: number;
    games_t2: number;
  };
  educational: Record<string, unknown>;
  egr: EGRSection;
  mlr: MLRSection;
  radar: RadarSection;
  timeline: TimelineSection;
  // vision field removed
  economy: EconomySection;
  pace: PaceSection;
  winrate: WinRateSection;
  recent_form: RecentFormSection;
  kills_total?: DistributionSection;
  kills_per_team?: KillsPerTeamSection;
  handicap?: HandicapSection;
  dragons?: DistributionSection;
  towers?: DistributionSection;
  barons?: DistributionSection;
  duration?: DistributionSection;
  series?: SeriesSection;
  side_performance?: Record<string, SideStatEntry[]>;
  league_context?: LeagueContextSection;
  objective_correlations?: ObjectiveCorrelations;
  ev_finder?: EVFinderSection;
}
