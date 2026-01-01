from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, List
import pandas as pd

from .utils import parse_date_safe, normalize_text
from .config import LEAGUE_FILES

# Colunas que usamos (evitamos colunas de odds)
NEEDED_COLUMNS = [
    "Date","Time","HomeTeam","AwayTeam","Referee",
    "HC","AC","HY","AY","HR","AR",
    "HF","AF","HS","AS","HST","AST",
    "FTHG","FTAG"
]

@dataclass
class DataBundle:
    matches: pd.DataFrame
    calendar: pd.DataFrame
    referees: pd.DataFrame
    warnings: List[str]

def _coalesce_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    # Garante que todas as colunas existam
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df

def load_league_csv(path: Path, league_name: str) -> Tuple[pd.DataFrame, List[str]]:
    warnings = []
    df = pd.read_csv(path)
    df = _coalesce_columns(df, NEEDED_COLUMNS)

    # parse date
    df["Date"] = df["Date"].apply(parse_date_safe)
    if df["Date"].isna().all():
        warnings.append(f"[{league_name}] coluna Date não pôde ser interpretada.")
    df["League"] = league_name

    # normalização leve (sem destruir nomes)
    for c in ["HomeTeam","AwayTeam","Referee"]:
        df[c] = df[c].astype(str).map(normalize_text)

    # métricas derivadas
    df["Corners_H"] = pd.to_numeric(df["HC"], errors="coerce")
    df["Corners_A"] = pd.to_numeric(df["AC"], errors="coerce")
    df["Cards_H_Y"] = pd.to_numeric(df["HY"], errors="coerce")
    df["Cards_A_Y"] = pd.to_numeric(df["AY"], errors="coerce")
    df["Cards_H_R"] = pd.to_numeric(df["HR"], errors="coerce")
    df["Cards_A_R"] = pd.to_numeric(df["AR"], errors="coerce")

    # total corners/cards
    df["Corners_T"] = df["Corners_H"].fillna(0) + df["Corners_A"].fillna(0)
    # cartão vermelho conta como 2 por padrão (ajustável no engine)
    df["Cards_T"] = df["Cards_H_Y"].fillna(0) + df["Cards_A_Y"].fillna(0) + 2*(df["Cards_H_R"].fillna(0) + df["Cards_A_R"].fillna(0))

    # goals (usado só como contexto, não como alvo)
    df["Goals_H"] = pd.to_numeric(df["FTHG"], errors="coerce")
    df["Goals_A"] = pd.to_numeric(df["FTAG"], errors="coerce")

    # ordenação
    df = df.sort_values(["Date","Time","HomeTeam","AwayTeam"], na_position="last").reset_index(drop=True)

    # avisos de cobertura
    coverage = df["Corners_T"].notna().mean()
    if coverage < 0.6:
        warnings.append(f"[{league_name}] cobertura de cantos baixa ({coverage:.0%}).")
    coverage_cards = df["Cards_T"].notna().mean()
    if coverage_cards < 0.6:
        warnings.append(f"[{league_name}] cobertura de cartões baixa ({coverage_cards:.0%}).")

    # manter apenas colunas relevantes + derivadas
    keep = ["League"] + NEEDED_COLUMNS + [
        "Corners_H","Corners_A","Corners_T",
        "Cards_H_Y","Cards_A_Y","Cards_H_R","Cards_A_R","Cards_T",
        "Goals_H","Goals_A"
    ]
    df = df[keep]
    return df, warnings

def load_calendar_csv(path: Path) -> Tuple[pd.DataFrame, List[str]]:
    warnings = []
    cal = pd.read_csv(path)
    # Esperado: Data, Hora, Liga, Time_Casa, Time_Visitante
    expected = ["Data","Hora","Liga","Time_Casa","Time_Visitante"]
    for c in expected:
        if c not in cal.columns:
            warnings.append(f"[Calendário] coluna ausente: {c}")
            cal[c] = pd.NA
    cal["Data"] = cal["Data"].apply(parse_date_safe)
    cal["Liga"] = cal["Liga"].astype(str).map(normalize_text)
    cal["Time_Casa"] = cal["Time_Casa"].astype(str).map(normalize_text)
    cal["Time_Visitante"] = cal["Time_Visitante"].astype(str).map(normalize_text)
    cal = cal.sort_values(["Data","Hora","Liga"], na_position="last").reset_index(drop=True)
    return cal, warnings

def load_referees(dir_path: Path) -> Tuple[pd.DataFrame, List[str]]:
    warnings = []
    # preferir arquivo mais rico, se existir
    candidates = [
        dir_path / "arbitros_5_ligas_2025_2026.csv",
        dir_path / "arbitros.csv",
    ]
    for p in candidates:
        if p.exists():
            ref = pd.read_csv(p)
            # normalizações
            for c in ref.columns:
                if ref[c].dtype == object:
                    ref[c] = ref[c].astype(str).map(normalize_text)
            return ref, warnings
    warnings.append("[Árbitros] nenhum arquivo encontrado.")
    return pd.DataFrame(), warnings

def load_all_data(project_root: str | Path) -> DataBundle:
    root = Path(project_root).resolve()
    leagues_dir = root / "data" / "leagues"
    calendar_dir = root / "data" / "calendar"
    referees_dir = root / "data" / "referees"

    all_matches = []
    warnings = []

    for league_name, filename in LEAGUE_FILES.items():
        p = leagues_dir / filename
        if not p.exists():
            warnings.append(f"[{league_name}] arquivo não encontrado: {filename}")
            continue
        df, w = load_league_csv(p, league_name)
        warnings.extend(w)
        all_matches.append(df)

    matches = pd.concat(all_matches, ignore_index=True) if all_matches else pd.DataFrame()

    cal_path = calendar_dir / "calendario_ligas.csv"
    calendar, wcal = load_calendar_csv(cal_path) if cal_path.exists() else (pd.DataFrame(), ["[Calendário] calendario_ligas.csv não encontrado"])
    warnings.extend(wcal)

    referees, wref = load_referees(referees_dir)
    warnings.extend(wref)

    return DataBundle(matches=matches, calendar=calendar, referees=referees, warnings=warnings)
