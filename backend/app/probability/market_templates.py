"""
Market Templates for FRED-backed Prediction Markets

Defines economic indicators that generate rolling monthly/quarterly markets.
Each template maps to a FRED series and includes resolution rules.
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


MARKET_TEMPLATES = [
    {
        "series_id": "CPIAUCSL",
        "category": "cpi",
        "transform": "pct_change_year",
        "title_template": "Will CPI inflation exceed {threshold}% for {period}?",
        "threshold": 3.0,
        "operator": "gt",
        "description": "Consumer Price Index year-over-year change measures inflation.",
        "explainer": "CPI is the most-watched inflation measure. The Fed targets 2%.",
        "investing_connection": "High inflation erodes purchasing power. It hurts bond holders but can benefit commodities producers.",
        "frequency": "monthly",
        "default_probability": 0.45,
    },
    {
        "series_id": "UNRATE",
        "category": "unemployment",
        "transform": "raw",
        "title_template": "Will the unemployment rate stay below {threshold}% in {period}?",
        "threshold": 4.5,
        "operator": "lt",
        "description": "BLS releases monthly employment data on the first Friday.",
        "explainer": "Low unemployment means a strong job market.",
        "investing_connection": "Low unemployment supports consumer spending, which drives ~70% of US GDP.",
        "frequency": "monthly",
        "default_probability": 0.70,
    },
    {
        "series_id": "FEDFUNDS",
        "category": "fed-funds-rate",
        "transform": "raw",
        "title_template": "Will the effective federal funds rate be below {threshold}% in {period}?",
        "threshold": 4.5,
        "operator": "lt",
        "description": "The FOMC sets the target range for the federal funds rate.",
        "explainer": "The federal funds rate affects everything from mortgage rates to savings yields.",
        "investing_connection": "When rates drop, bonds go up and stocks often rally.",
        "frequency": "monthly",
        "default_probability": 0.40,
    },
    {
        "series_id": "DGS10",
        "category": "treasury-yields",
        "transform": "raw",
        "title_template": "Will the 10-year Treasury yield exceed {threshold}% in {period}?",
        "threshold": 4.0,
        "operator": "gt",
        "description": "The 10-year Treasury yield is a benchmark for borrowing costs.",
        "explainer": "Treasury yields move inversely to bond prices.",
        "investing_connection": "Rising yields hurt growth stocks but benefit bank stocks.",
        "frequency": "monthly",
        "default_probability": 0.55,
    },
    {
        "series_id": "PCEPILFE",
        "category": "inflation",
        "transform": "pct_change_year",
        "title_template": "Will core PCE inflation fall below {threshold}% in {period}?",
        "threshold": 2.5,
        "operator": "lt",
        "description": "Core PCE is the Fed's preferred inflation measure, excluding food and energy.",
        "explainer": "The Fed targets 2% PCE. Getting close gives the Fed room to cut rates.",
        "investing_connection": "Falling inflation is good for bonds and growth stocks.",
        "frequency": "monthly",
        "default_probability": 0.35,
    },
    {
        "series_id": "A191RL1Q225SBEA",
        "category": "gdp",
        "transform": "raw",
        "title_template": "Will real GDP growth exceed {threshold}% (annualized) in {period}?",
        "threshold": 2.0,
        "operator": "gt",
        "description": "GDP measures total economic output, released quarterly.",
        "explainer": "GDP growth above 2% is considered solid. Below 0% for two quarters is a recession.",
        "investing_connection": "Strong GDP is generally good for stocks, especially cyclical sectors.",
        "frequency": "quarterly",
        "default_probability": 0.55,
    },
    {
        "series_id": "ICSA",
        "category": "unemployment",
        "transform": "raw",
        "title_template": "Will initial jobless claims exceed {threshold}K in any week of {period}?",
        "threshold": 250,
        "operator": "gt",
        "description": "Weekly jobless claims measure new unemployment filings.",
        "explainer": "Rising jobless claims can be an early warning sign of economic slowdown.",
        "investing_connection": "Spiking claims often precede broader market selloffs.",
        "frequency": "monthly",
        "default_probability": 0.30,
    },
    {
        "series_id": "RSAFS",
        "category": "gdp",
        "transform": "pct_change_year",
        "title_template": "Will retail sales grow more than {threshold}% year-over-year in {period}?",
        "threshold": 3.0,
        "operator": "gt",
        "description": "Retail sales measure consumer spending at stores and online.",
        "explainer": "Consumer spending drives ~70% of the US economy.",
        "investing_connection": "Strong retail data benefits consumer stocks and signals economic expansion.",
        "frequency": "monthly",
        "default_probability": 0.50,
    },
]


# Map seed market title patterns to FRED resolution metadata.
# Used by backfill_seed_markets() to attach resolution rules to existing seeds.
SEED_MARKET_MAPPINGS = {
    "Will US CPI inflation be above 3%": {
        "source": "fred",
        "series_id": "CPIAUCSL",
        "threshold": 3.0,
        "operator": "gt",
        "transform": "pct_change_year",
        "reference_date": "2026-03-01",
    },
    "Will the unemployment rate stay below 4.5%": {
        "source": "fred",
        "series_id": "UNRATE",
        "threshold": 4.5,
        "operator": "lt",
        "transform": "raw",
        "reference_date": "2026-03-01",
    },
    "Will the Federal Reserve cut interest rates": {
        "source": "fred",
        "series_id": "FEDFUNDS",
        "threshold": 4.5,
        "operator": "lt",
        "transform": "raw",
        "reference_date": "2026-03-01",
    },
    "Will US GDP growth exceed 2.5%": {
        "source": "fred",
        "series_id": "A191RL1Q225SBEA",
        "threshold": 2.5,
        "operator": "gt",
        "transform": "raw",
        "reference_date": "2026-03-01",
    },
    "Will the 10-year Treasury yield end March above 4.0%": {
        "source": "fred",
        "series_id": "DGS10",
        "threshold": 4.0,
        "operator": "gt",
        "transform": "raw",
        "reference_date": "2026-03-31",
    },
    "Will the US enter a recession": {
        "source": "fred",
        "series_id": "A191RL1Q225SBEA",
        "threshold": 0.0,
        "operator": "lt",
        "transform": "raw",
        "reference_date": "2026-06-30",
    },
    "Will the Fed Funds rate be below 4.0%": {
        "source": "fred",
        "series_id": "FEDFUNDS",
        "threshold": 4.0,
        "operator": "lt",
        "transform": "raw",
        "reference_date": "2026-06-01",
    },
    "Will core PCE inflation fall below 2.5%": {
        "source": "fred",
        "series_id": "PCEPILFE",
        "threshold": 2.5,
        "operator": "lt",
        "transform": "pct_change_year",
        "reference_date": "2026-06-01",
    },
    "Will US retail sales grow more than 3%": {
        "source": "fred",
        "series_id": "RSAFS",
        "threshold": 3.0,
        "operator": "gt",
        "transform": "pct_change_year",
        "reference_date": "2026-03-01",
    },
    "Will initial jobless claims exceed 250,000": {
        "source": "fred",
        "series_id": "ICSA",
        "threshold": 250,
        "operator": "gt",
        "transform": "raw",
        "reference_date": "2026-03-01",
    },
}


def get_next_reference_date(frequency: str, from_date: date) -> date:
    """Get the next reference date for market generation.

    For monthly: first of next month.
    For quarterly: first of next quarter.
    """
    if frequency == "quarterly":
        # Next quarter start
        current_quarter = (from_date.month - 1) // 3
        next_quarter_month = (current_quarter + 1) * 3 + 1
        if next_quarter_month > 12:
            return date(from_date.year + 1, next_quarter_month - 12, 1)
        return date(from_date.year, next_quarter_month, 1)
    else:
        # Next month start
        return (from_date.replace(day=1) + relativedelta(months=1))


def get_close_date(reference_date: date, series_id: str) -> date:
    """Get the market close date (~2 weeks after typical FRED release).

    Most monthly series are released within the first 2 weeks of the
    following month. We close the market ~2 weeks after the reference
    month ends to allow data to be published.
    """
    # Approximate release delays by series
    release_delays = {
        "CPIAUCSL": 10,   # ~10th of following month
        "UNRATE": 7,      # ~1st Friday of following month
        "FEDFUNDS": 1,    # ~1st of following month
        "DGS10": 1,       # Daily, available next day
        "PCEPILFE": 28,   # ~End of following month
        "A191RL1Q225SBEA": 30,  # ~End of quarter+1 month
        "ICSA": 5,        # Weekly, Thursday
        "RSAFS": 15,      # ~15th of following month
    }
    delay_days = release_delays.get(series_id, 15)

    # Close date = start of month after reference + delay + buffer
    month_after = reference_date.replace(day=1) + relativedelta(months=1)
    return month_after + timedelta(days=delay_days + 3)


def format_period(reference_date: date, frequency: str) -> str:
    """Format a reference date as a human-readable period.

    Monthly: "January 2026"
    Quarterly: "Q1 2026"
    """
    if frequency == "quarterly":
        quarter = (reference_date.month - 1) // 3 + 1
        return f"Q{quarter} {reference_date.year}"
    return reference_date.strftime("%B %Y")
