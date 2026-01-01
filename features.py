from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass
class TeamFeatures:
    league: str
    team: str
    n_matches: int
    corners_for_avg: float
    corners_against_avg: float
    cards_for_avg: float
    cards_against_avg: float
    corners_for_home_avg: float
    corners_against_home_avg: float
    corners_for_away_avg: float
    corners_against_away_avg: float
    cards_for_home_avg: float
    cards_against_home_avg: float
    cards_for_away_avg: float
    cards_against_away_avg: float
    corners_std: float
    cards_std: float

def _team_side_features(df: pd.DataFrame, team: str, side: str) -> pd.DataFrame:
    if side == "H":
        m = df[df["HomeTeam"] == team].copy()
        m["corners_for"] = pd.to_numeric(m["Corners_H"], errors="coerce")
        m["corners_against"] = pd.to_numeric(m["Corners_A"], errors="coerce")
        m["cards_for"] = pd.to_numeric(m["Cards_H_Y"], errors="coerce") + 2*pd.to_numeric(m["Cards_H_R"], errors="coerce")
        m["cards_against"] = pd.to_numeric(m["Cards_A_Y"], errors="coerce") + 2*pd.to_numeric(m["Cards_A_R"], errors="coerce")
    else:
        m = df[df["AwayTeam"] == team].copy()
        m["corners_for"] = pd.to_numeric(m["Corners_A"], errors="coerce")
        m["corners_against"] = pd.to_numeric(m["Corners_H"], errors="coerce")
        m["cards_for"] = pd.to_numeric(m["Cards_A_Y"], errors="coerce") + 2*pd.to_numeric(m["Cards_A_R"], errors="coerce")
        m["cards_against"] = pd.to_numeric(m["Cards_H_Y"], errors="coerce") + 2*pd.to_numeric(m["Cards_H_R"], errors="coerce")
    return m

def compute_team_features(matches: pd.DataFrame, league: str, team: str, window: int = 15) -> TeamFeatures:
    df = matches[matches["League"] == league].copy()
    df = df.sort_values("Date")
    # últimos N jogos (tanto casa quanto fora)
    m_all = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)].tail(window).copy()

    m_h = _team_side_features(df, team, "H").tail(window)
    m_a = _team_side_features(df, team, "A").tail(window)

    def avg(series):
        return float(pd.to_numeric(series, errors="coerce").dropna().mean()) if len(series) else float("nan")

    corners_for = []
    corners_against = []
    cards_for = []
    cards_against = []

    # construir séries combinadas
    corners_for.extend(pd.to_numeric(m_h["corners_for"], errors="coerce").dropna().tolist())
    corners_for.extend(pd.to_numeric(m_a["corners_for"], errors="coerce").dropna().tolist())
    corners_against.extend(pd.to_numeric(m_h["corners_against"], errors="coerce").dropna().tolist())
    corners_against.extend(pd.to_numeric(m_a["corners_against"], errors="coerce").dropna().tolist())

    cards_for.extend(pd.to_numeric(m_h["cards_for"], errors="coerce").dropna().tolist())
    cards_for.extend(pd.to_numeric(m_a["cards_for"], errors="coerce").dropna().tolist())
    cards_against.extend(pd.to_numeric(m_h["cards_against"], errors="coerce").dropna().tolist())
    cards_against.extend(pd.to_numeric(m_a["cards_against"], errors="coerce").dropna().tolist())

    corners_series = pd.Series(corners_for + corners_against, dtype="float64")
    cards_series = pd.Series(cards_for + cards_against, dtype="float64")

    return TeamFeatures(
        league=league,
        team=team,
        n_matches=int(len(m_all)),
        corners_for_avg=float(np.nanmean(corners_for)) if len(corners_for) else float("nan"),
        corners_against_avg=float(np.nanmean(corners_against)) if len(corners_against) else float("nan"),
        cards_for_avg=float(np.nanmean(cards_for)) if len(cards_for) else float("nan"),
        cards_against_avg=float(np.nanmean(cards_against)) if len(cards_against) else float("nan"),
        corners_for_home_avg=avg(m_h["corners_for"]),
        corners_against_home_avg=avg(m_h["corners_against"]),
        corners_for_away_avg=avg(m_a["corners_for"]),
        corners_against_away_avg=avg(m_a["corners_against"]),
        cards_for_home_avg=avg(m_h["cards_for"]),
        cards_against_home_avg=avg(m_h["cards_against"]),
        cards_for_away_avg=avg(m_a["cards_for"]),
        cards_against_away_avg=avg(m_a["cards_against"]),
        corners_std=float(corners_series.dropna().std()) if corners_series.dropna().shape[0] > 1 else float("nan"),
        cards_std=float(cards_series.dropna().std()) if cards_series.dropna().shape[0] > 1 else float("nan"),
    )

def list_teams(matches: pd.DataFrame, league: str) -> list[str]:
    df = matches[matches["League"] == league]
    teams = pd.concat([df["HomeTeam"], df["AwayTeam"]], ignore_index=True).dropna().unique().tolist()
    teams = sorted([t for t in teams if str(t).strip()])
    return teams
