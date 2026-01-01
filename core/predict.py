from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from .features import compute_team_features

@dataclass
class Prediction:
    league: str
    home: str
    away: str
    corners_mean: float
    cards_mean: float
    corners_p50: float
    corners_p80: float
    cards_p50: float
    cards_p80: float
    confidence: str
    notes: list[str]

def _poisson_quantile(lam: float, q: float, max_k: int = 60) -> int:
    if lam <= 0:
        return 0
    # CDF incremental
    cdf = 0.0
    k = 0
    p = math.exp(-lam)
    cdf = p
    while cdf < q and k < max_k:
        k += 1
        p *= lam / k
        cdf += p
    return k

def _confidence(n: int, std: float) -> str:
    # heurística simples
    if n >= 12 and (not np.isnan(std)) and std < 4.5:
        return "alta"
    if n >= 8:
        return "média"
    return "baixa"

def _ref_factor(referees: pd.DataFrame, league: str, referee: str) -> float:
    if referees is None or referees.empty or not referee:
        return 1.0
    # tentar coluna Arbitro/Liga
    cols = [c.lower() for c in referees.columns]
    if "arbitro" in cols and "liga" in cols:
        tmp = referees.copy()
        # padroniza nomes de colunas
        liga_col = referees.columns[cols.index("liga")]
        arb_col = referees.columns[cols.index("arbitro")]
        m = tmp[(tmp[liga_col].astype(str) == league) & (tmp[arb_col].astype(str) == referee)]
        if not m.empty:
            # média de cartões por jogo, se existir
            for c in referees.columns:
                if c.lower() == "media_cartoes_por_jogo":
                    val = pd.to_numeric(m.iloc[0][c], errors="coerce")
                    if pd.notna(val):
                        # normaliza em torno de 4.0
                        return float(val) / 4.0 if float(val) > 0 else 1.0
    return 1.0

def predict_match(matches: pd.DataFrame, referees: pd.DataFrame, league: str, home: str, away: str, window: int = 15, match_referee: str | None = None) -> Prediction:
    # Features dos dois times
    hf = compute_team_features(matches, league, home, window=window)
    af = compute_team_features(matches, league, away, window=window)

    notes = []
    if hf.n_matches < 6: notes.append(f"Amostra pequena para {home} ({hf.n_matches} jogos).")
    if af.n_matches < 6: notes.append(f"Amostra pequena para {away} ({af.n_matches} jogos).")

    # Baseline liga
    dfL = matches[matches["League"] == league]
    league_corners = pd.to_numeric(dfL["Corners_T"], errors="coerce").dropna()
    league_cards = pd.to_numeric(dfL["Cards_T"], errors="coerce").dropna()
    lc = float(league_corners.mean()) if len(league_corners) else 10.0
    lca = float(league_cards.mean()) if len(league_cards) else 4.0

    # Cantos: combinação simples (home for + away against) e (away for + home against) -> total
    mu_corners_home = np.nanmean([hf.corners_for_home_avg, af.corners_against_away_avg])
    mu_corners_away = np.nanmean([af.corners_for_away_avg, hf.corners_against_home_avg])
    corners_mean = float(np.nanmean([mu_corners_home + mu_corners_away, lc]))
    if np.isnan(corners_mean):
        corners_mean = lc

    # Cartões: base dos times + ajuste árbitro
    mu_cards_home = np.nanmean([hf.cards_for_home_avg, af.cards_against_away_avg])
    mu_cards_away = np.nanmean([af.cards_for_away_avg, hf.cards_against_home_avg])
    cards_mean = float(np.nanmean([mu_cards_home + mu_cards_away, lca]))
    if np.isnan(cards_mean):
        cards_mean = lca

    # Ajuste por árbitro (se disponível)
    rf = _ref_factor(referees, league, match_referee or "")
    if rf != 1.0:
        cards_mean *= rf
        notes.append(f"Ajuste por árbitro aplicado (fator {rf:.2f}).")

    corners_p50 = _poisson_quantile(corners_mean, 0.50)
    corners_p80 = _poisson_quantile(corners_mean, 0.80)
    cards_p50 = _poisson_quantile(cards_mean, 0.50)
    cards_p80 = _poisson_quantile(cards_mean, 0.80)

    conf = _confidence(min(hf.n_matches, af.n_matches), np.nanmean([hf.corners_std, af.corners_std]))

    return Prediction(
        league=league, home=home, away=away,
        corners_mean=corners_mean, cards_mean=cards_mean,
        corners_p50=float(corners_p50), corners_p80=float(corners_p80),
        cards_p50=float(cards_p50), cards_p80=float(cards_p80),
        confidence=conf, notes=notes
    )
