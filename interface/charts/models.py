"""
Pydantic response models for the AnalyticsResponse API contract.

These models define the structured JSON returned by POST /api/analytics/insights,
replacing the legacy `{"html": "..."}` response with fully typed data sections.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetaSection(BaseModel):
    """Top-level metadata identifying the match context."""

    team1: str
    team2: str
    patch_label: str
    games_t1: int
    games_t2: int


class StatsBadgeData(BaseModel):
    """Descriptive statistics shown in Stats_Badge tooltips (μ, Med, σ, …)."""

    avg: float
    med: float
    std: float
    min: float
    max: float
    mode: float
    p25: float
    p75: float
    n: int


class BetEntryData(BaseModel):
    """A single bet entry card with risk classification and draft projection info."""

    team: str
    market: str
    line: str
    probability: float
    data_points: int
    odd: float  # 100 / probability
    risk_tier: str  # "low" | "med" | "high"
    risk_label: str  # "🟢 Baixo Risco" | "🟡 Risco Médio" | "🔴 Alto Risco"
    explanation: str
    has_draft_projection: bool
    draft_multiplier: Optional[float] = None


class BarData(BaseModel):
    """A single bar in a grouped bar chart."""

    label: str
    value: float
    color: str  # "blue" | "red"


class EGRSection(BaseModel):
    """Early-Game Rating proxy (First Blood %, First Dragon %, First Herald %)."""

    t1_values: Dict[str, float]  # {fb: float, fd: float, fh: float}
    t2_values: Dict[str, float]
    egr_score_t1: float
    egr_score_t2: float
    explain_text: str
    comments: List[str]


class MLRSection(BaseModel):
    """Mid/Late Rating proxy (FBN%, Barões AVG, Inibidores AVG, Torres AVG)."""

    t1: Dict[str, float]  # {fbaron_rate, avg_barons, avg_inhibitors, avg_towers}
    t2: Dict[str, float]
    explain_text: str
    comments: List[str]


class RadarSection(BaseModel):
    """Radar/spider chart data for Team DNA (4 tactical dimensions)."""

    labels: List[str]  # ["Win Rate", "EGR Score", "MLR Score", "Ação"]
    t1_values: List[float]
    t2_values: List[float]
    explain_text: str
    comments: List[str]


class TimelineSection(BaseModel):
    """Gold/CS/XP advantage timeline at minutes 10, 15, 20, 25."""

    minutes: List[int]  # [10, 15, 20, 25]
    gold_diff_t1: List[float]
    cs_diff_t1: List[float]
    xp_diff_t1: List[float]
    gold_diff_t2: List[float]
    cs_diff_t2: List[float]
    xp_diff_t2: List[float]
    draft_projection_active: bool
    draft_gold_diff_t1: Optional[List[float]] = None
    draft_cs_diff_t1: Optional[List[float]] = None
    draft_xp_diff_t1: Optional[List[float]] = None
    draft_gold_diff_t2: Optional[List[float]] = None
    draft_cs_diff_t2: Optional[List[float]] = None
    draft_xp_diff_t2: Optional[List[float]] = None
    mult_t1: Optional[float] = None
    mult_t2: Optional[float] = None
    explain_text: str
    comments: List[str]




class EconomySection(BaseModel):
    """Economy context: EGPM, DPM, and optional Gold Layer metrics."""

    egpm: Dict[str, float]  # {t1: float, t2: float}
    dpm: Dict[str, float]
    gold_layer: Optional[Dict[str, Any]] = None  # {t1: {egdi, throw_rate, comeback_rate}, t2: ...}
    explain_text: str
    comments: List[str]


class PaceSection(BaseModel):
    """Game pace metrics: CKPM and KPM per team."""

    ckpm: Dict[str, float]  # {t1: float, t2: float}
    kpm: Dict[str, float]
    explain_text: str
    comments: List[str]


class WinRateSection(BaseModel):
    """Win rate and record for each team."""

    t1_win_rate: float
    t2_win_rate: float
    t1_wins: int
    t2_wins: int
    t1_total: int
    t2_total: int
    explain_text: str
    comments: List[str]


class RecentFormSection(BaseModel):
    """Recent form (last N games) as W/L sequences with rolling win rate."""

    t1_results: List[str]  # ["1", "0", "1", ...]
    t2_results: List[str]
    t1_recent_wr: float
    t2_recent_wr: float
    comments: List[str]


class DistributionSection(BaseModel):
    """Generic distribution section used for kills total, dragons, towers, barons, duration."""

    title: str
    histogram_data: List[float]  # raw values for histogram
    stats: StatsBadgeData
    bet_entries: List[BetEntryData]
    draft_projection: Optional[Dict[str, Any]] = None
    explain_text: str
    comments: List[str]


class KillsPerTeamSection(BaseModel):
    """Side-by-side kill distribution for T1 and T2."""

    t1_histogram: List[float]
    t2_histogram: List[float]
    t1_stats: Optional[StatsBadgeData] = None
    t2_stats: Optional[StatsBadgeData] = None
    t1_bet_entries: List[BetEntryData]
    t2_bet_entries: List[BetEntryData]
    draft_projection: Optional[Dict[str, Any]] = None
    explain_text: str
    comments: List[str]


class HandicapSection(BaseModel):
    """Kill handicap (kill differential) distribution for both teams."""

    t1_histogram: List[float]  # kill diff values for t1
    t2_histogram: List[float]  # kill diff values for t2
    t1_stats: Optional[StatsBadgeData] = None
    t2_stats: Optional[StatsBadgeData] = None
    bet_entries: List[BetEntryData]
    draft_projection: Optional[Dict[str, Any]] = None
    explain_text: str
    comments: List[str]


class EVFinderTeamCard(BaseModel):
    """EV Finder card for a single team (or joint), grouping bet entries by market."""

    team: str
    color: str
    markets: Dict[str, List[BetEntryData]]  # market_key -> List[BetEntryData]


class EVFinderSection(BaseModel):
    """Expected Value Finder section with cards for T1, T2, and joint markets."""

    t1_card: EVFinderTeamCard
    t2_card: EVFinderTeamCard
    joint_card: EVFinderTeamCard


class SideStatEntry(BaseModel):
    side: str
    games: int
    wins: int
    win_rate: float


class LeagueContextSection(BaseModel):
    league: str
    avg_total_kills: float
    blue_win_rate: float
    avg_duration: float
    total_games_analyzed: int
    insights: List[str]


class ObjectiveCorrelations(BaseModel):
    fb_wr: float
    fd_wr: float
    fbaron_wr: float
    fherald_wr: float
    large_lead_wr: float
    soul_wr: float


class SeriesStatEntry(BaseModel):
    """Detailed stats for a specific game number in a series."""

    game: int
    matches: int
    avg_kills: float
    avg_deaths: float
    avg_dragons: float
    avg_barons: float
    avg_towers: float
    avg_duration_min: float
    win_rate: float


class SeriesSection(BaseModel):
    """Breakdown of performance by game number in a series (Game 1, Game 2, etc.)."""

    t1_series: List[SeriesStatEntry]
    t2_series: List[SeriesStatEntry]
    explain_text: str
    comments: List[str]


class AnalyticsResponse(BaseModel):
    """
    Top-level response model for POST /api/analytics/insights.

    Replaces the legacy ``{"html": "..."}`` response with fully structured,
    typed data that the Svelte frontend can render natively.
    """

    meta: MetaSection
    educational: Dict[str, Any]  # static content (texts, formulas)
    egr: EGRSection
    mlr: MLRSection
    radar: RadarSection
    timeline: TimelineSection
    economy: EconomySection
    pace: PaceSection
    winrate: WinRateSection
    recent_form: RecentFormSection
    kills_total: Optional[DistributionSection] = None
    kills_per_team: Optional[KillsPerTeamSection] = None
    handicap: Optional[HandicapSection] = None
    dragons: Optional[DistributionSection] = None
    towers: Optional[DistributionSection] = None
    barons: Optional[DistributionSection] = None
    duration: Optional[DistributionSection] = None
    series: Optional[SeriesSection] = None
    side_performance: Optional[Dict[str, List[SideStatEntry]]] = None
    league_context: Optional[LeagueContextSection] = None
    objective_correlations: Optional[ObjectiveCorrelations] = None
    ev_finder: Optional[EVFinderSection] = None
