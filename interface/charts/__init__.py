"""
charts/__init__.py — Re-exporta a API pública do pacote.
Mantém compatibilidade: `from interface.charts import generate_charts`
"""

from .renderer import generate_charts
from .html_helpers import INSIGHTS_CSS
from .models import (
    AnalyticsResponse,
    MetaSection,
    StatsBadgeData,
    BetEntryData,
    BarData,
    EGRSection,
    MLRSection,
    RadarSection,
    TimelineSection,
    TimelineSection,
    EconomySection,
    PaceSection,
    WinRateSection,
    RecentFormSection,
    DistributionSection,
    KillsPerTeamSection,
    HandicapSection,
    EVFinderTeamCard,
    EVFinderSection,
)

__all__ = [
    "generate_charts",
    "INSIGHTS_CSS",
    # Pydantic response models
    "AnalyticsResponse",
    "MetaSection",
    "StatsBadgeData",
    "BetEntryData",
    "BarData",
    "EGRSection",
    "MLRSection",
    "RadarSection",
    "TimelineSection",
    "TimelineSection",
    "EconomySection",
    "PaceSection",
    "WinRateSection",
    "RecentFormSection",
    "DistributionSection",
    "KillsPerTeamSection",
    "HandicapSection",
    "EVFinderTeamCard",
    "EVFinderSection",
]
