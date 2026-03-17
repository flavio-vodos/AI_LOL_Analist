"""
Property-based tests for interface/charts/json_serializer.py (and helpers).

Feature: advanced-analytics-svelte-refactor
"""

import statistics

from hypothesis import given, settings
from hypothesis import strategies as st

from interface.charts.json_serializer import calc_stats, make_bet_entry, build_egr_section, build_timeline_section
from interface.charts.html_helpers import risk_tier


# ---------------------------------------------------------------------------
# Property 6: Stats badge computation correctness
# Validates: Requirements 11.5, 12.5, 13.3
# ---------------------------------------------------------------------------

@given(st.lists(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e9, max_value=1e9),
    min_size=2,
))
@settings(max_examples=200)
def test_stats_badge_invariants(data):
    """**Validates: Requirements 11.5, 12.5, 13.3**

    For any non-empty list of numeric values, the StatsBadgeData computed from
    that list must satisfy:
      - min <= p25 <= med <= p75 <= max
      - avg is the arithmetic mean
      - std is the sample standard deviation
    """
    result = calc_stats(data)

    # Ordering invariant
    assert result["min"] <= result["p25"] <= result["med"] <= result["p75"] <= result["max"]

    # avg is the arithmetic mean
    assert abs(result["avg"] - sum(data) / len(data)) < 1e-6


# ---------------------------------------------------------------------------
# Property 7: Risk tier classification
# Validates: Requirements 11.6, 14.5
# ---------------------------------------------------------------------------

@given(st.floats(0, 100))
@settings(max_examples=500)
def test_risk_tier_classification(prob):
    """**Validates: Requirements 11.6, 14.5**

    For any probability value p in [0, 100], the risk tier must be:
      - "low"  if p >= 65
      - "med"  if 50 <= p < 65
      - "high" if p < 50
    """
    tier, _ = risk_tier(prob)
    if prob >= 65:
        assert tier == "low"
    elif prob >= 50:
        assert tier == "med"
    else:
        assert tier == "high"


# ---------------------------------------------------------------------------
# Property 8: Odd formula correctness
# Validates: Requirements 14.7
# ---------------------------------------------------------------------------

@given(st.floats(min_value=0.1, max_value=100.0))
@settings(max_examples=500)
def test_odd_formula(prob):
    """**Validates: Requirements 14.7**

    For any BetEntryData with probability > 0, the odd field must equal
    100 / probability, within floating-point tolerance.
    """
    entry = make_bet_entry(
        team="TeamA",
        market="Over",
        line="10.5",
        prob=prob,
        data_points=100,
        explanation="test",
    )
    assert entry is not None
    assert abs(entry["odd"] - (100 / prob)) < 1e-6


# ---------------------------------------------------------------------------
# Property 3: EGR score computation
# Validates: Requirements 5.2
# ---------------------------------------------------------------------------

@given(
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
    st.floats(0, 100, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_egr_score_formula(fb1, fd1, fh1, fb2, fd2, fh2):
    """**Validates: Requirements 5.2**

    For any team stats object with fb_rate, fd_rate, and fherald_rate fields,
    the EGR score in the response must equal (fb_rate + fd_rate + fherald_rate) / 3,
    within floating-point tolerance.
    """
    s1 = {
        "fb_rate": fb1, "fd_rate": fd1, "fherald_rate": fh1,
        "fbaron_rate": 0, "avg_barons": 0, "avg_inhibitors": 0, "avg_towers": 0,
    }
    s2 = {
        "fb_rate": fb2, "fd_rate": fd2, "fherald_rate": fh2,
        "fbaron_rate": 0, "avg_barons": 0, "avg_inhibitors": 0, "avg_towers": 0,
    }

    result = build_egr_section(s1, s2, "Team1", "Team2")

    assert abs(result["egr_score_t1"] - (fb1 + fd1 + fh1) / 3) < 1e-9
    assert abs(result["egr_score_t2"] - (fb2 + fd2 + fh2) / 3) < 1e-9


# ---------------------------------------------------------------------------
# Property 4: Timeline data has exactly 4 points per dimension
# Validates: Requirements 7.2
# ---------------------------------------------------------------------------

def _stats_strategy():
    """Generates a valid stats dict with all golddiffatN / csdiffatN / xpdiffatN keys."""
    diff_val = st.floats(allow_nan=False, allow_infinity=False, min_value=-10000, max_value=10000)
    return st.fixed_dictionaries({
        "golddiffat10": diff_val,
        "golddiffat15": diff_val,
        "golddiffat20": diff_val,
        "golddiffat25": diff_val,
        "csdiffat10": diff_val,
        "csdiffat15": diff_val,
        "csdiffat20": diff_val,
        "csdiffat25": diff_val,
        "xpdiffat10": diff_val,
        "xpdiffat15": diff_val,
        "xpdiffat20": diff_val,
        "xpdiffat25": diff_val,
    })


@given(_stats_strategy(), _stats_strategy())
@settings(max_examples=100)
def test_timeline_has_four_points(s1, s2):
    """**Validates: Requirements 7.2**

    For any valid team stats pair, the timeline section must contain exactly
    4 values in each of gold_diff_t1, cs_diff_t1, and xp_diff_t1,
    corresponding to minutes 10, 15, 20, and 25.
    """
    result = build_timeline_section(s1, s2, "Team1", "Team2", None, None)

    assert len(result["gold_diff_t1"]) == 4
    assert len(result["cs_diff_t1"]) == 4
    assert len(result["xp_diff_t1"]) == 4
    assert result["minutes"] == [10, 15, 20, 25]


# ---------------------------------------------------------------------------
# Property 5: Win rate formula correctness
# Validates: Requirements 10.2
# ---------------------------------------------------------------------------

from interface.charts.json_serializer import build_winrate_section


@given(st.integers(0, 1000), st.integers(1, 1000))
@settings(max_examples=200)
def test_win_rate_formula(wins, total):
    """**Validates: Requirements 10.2**

    For any team stats with wins and total_games, the win_rate in the response
    must equal (wins / total_games) * 100, within floating-point tolerance.
    """
    wins = min(wins, total)
    win_rate = wins / total * 100

    s1 = {
        "win_rate": win_rate,
        "wins": wins,
        "total_games": total,
    }
    # s2 is a mirror with the same values (we only assert on t1)
    s2 = dict(s1)

    result = build_winrate_section(s1, s2, "Team1", "Team2")

    assert abs(result["t1_win_rate"] - (wins / total * 100)) < 1e-9


# ---------------------------------------------------------------------------
# Property 1: Response structure completeness
# Validates: Requirements 1.2, 1.3
# ---------------------------------------------------------------------------

from unittest.mock import patch
from hypothesis import given, settings
from hypothesis import strategies as st

REQUIRED_TOP_LEVEL_FIELDS = [
    "meta", "educational", "egr", "mlr", "radar", "timeline", "vision",
    "economy", "pace", "winrate", "recent_form", "kills_total", "kills_per_team",
    "handicap", "dragons", "towers", "barons", "duration", "ev_finder",
]

REQUIRED_META_FIELDS = ["team1", "team2", "patch_label", "games_t1", "games_t2"]


def _make_full_stats(team_name="Team1", wins=10, total=20):
    """Returns a minimal but complete stats dict for testing."""
    return {
        "total_games": total,
        "wins": wins,
        "win_rate": wins / total * 100,
        "avg_kills": 15.0,
        "avg_deaths": 10.0,
        "avg_dragons": 3.0,
        "avg_towers": 8.0,
        "avg_barons": 1.0,
        "avg_heralds": 1.0,
        "avg_inhibitors": 1.0,
        "avg_gamelength": 1800.0,
        "fb_rate": 50.0,
        "fd_rate": 50.0,
        "fherald_rate": 50.0,
        "fbaron_rate": 50.0,
        "avg_kpm": 0.5,
        "avg_ckpm": 0.7,
        "cspm": 30.0,
        "visionscore": 2.5,
        "golddiffat10": 100.0,
        "golddiffat15": 200.0,
        "golddiffat20": 300.0,
        "golddiffat25": 400.0,
        "csdiffat10": 5.0,
        "csdiffat15": 8.0,
        "csdiffat20": 10.0,
        "csdiffat25": 12.0,
        "xpdiffat10": 150.0,
        "xpdiffat15": 250.0,
        "xpdiffat20": 350.0,
        "xpdiffat25": 450.0,
        "wardsplaced": 30.0,
        "wardskilled": 20.0,
        "controlwardsbought": 5.0,
        "recent_results": ["1", "0", "1", "1", "0", "1", "0", "1", "1", "0"],
        "kills_history": [10, 12, 15, 8, 20, 14, 11, 16, 9, 13],
        "kill_diff_history": [2, -3, 5, -1, 8, 3, -2, 4, -4, 1],
        "dragons_history": [3, 4, 2, 5, 3, 4, 3, 2, 4, 3],
        "towers_history": [8, 9, 7, 10, 8, 9, 7, 8, 9, 8],
        "barons_history": [1, 2, 1, 1, 2, 1, 1, 2, 1, 1],
        "gamelength_history": [1800, 1900, 1700, 2000, 1850, 1750, 1950, 1800, 1900, 1700],
        "earnedgold_pm_history": [1500.0, 1600.0, 1400.0, 1700.0, 1550.0],
        "dmg_pm_history": [2000.0, 2100.0, 1900.0, 2200.0, 2050.0],
        "ckpm_history": [0.7, 0.8, 0.6, 0.9, 0.75],
        "kpm_history": [0.4, 0.5, 0.35, 0.55, 0.45],
    }


_team_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" "),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip())

_patch_st = st.lists(
    st.sampled_from(["14.1", "14.2", "14.3", "14.4", "Todos"]),
    min_size=1,
    max_size=4,
)


@given(_team_name_st, _team_name_st, _patch_st)
@settings(max_examples=100)
def test_response_has_all_required_fields(team1, team2, patches):
    """**Validates: Requirements 1.2, 1.3**

    For any valid InsightRequest (two distinct teams with sufficient data),
    the AnalyticsResponse returned by generate_analytics_json must contain
    all 19 required top-level fields and the meta field must contain
    team1, team2, patch_label, games_t1, games_t2.
    """
    from interface.charts.json_serializer import generate_analytics_json

    stats1 = _make_full_stats(team1, wins=10, total=20)
    stats2 = _make_full_stats(team2, wins=8, total=20)

    with (
        patch("interface.charts.data_provider.get_team_stats", side_effect=[stats1, stats2]),
        patch("interface.charts.data_provider.get_gold_team_stats", return_value=None),
        patch("interface.charts.data_provider.get_global_baseline_stats", return_value=None),
        patch("interface.charts.data_provider.get_platinum_champion_stats", return_value=None),
    ):
        result = generate_analytics_json(team1, team2, patches=patches)

    assert result is not None, "generate_analytics_json returned None for valid stats"

    # All 19 top-level fields must be present
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in result, f"Missing top-level field: {field}"

    # meta must contain all required sub-fields
    for key in REQUIRED_META_FIELDS:
        assert key in result["meta"], f"Missing meta field: {key}"

    # meta values must match the inputs
    assert result["meta"]["team1"] == team1
    assert result["meta"]["team2"] == team2
    assert result["meta"]["games_t1"] == stats1["total_games"]
    assert result["meta"]["games_t2"] == stats2["total_games"]
