from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Paths:
    root: Path
    leagues_dir: Path
    calendar_dir: Path
    referees_dir: Path

def get_paths(root: str | Path) -> Paths:
    root = Path(root).resolve()
    return Paths(
        root=root,
        leagues_dir=root / "data" / "leagues",
        calendar_dir=root / "data" / "calendar",
        referees_dir=root / "data" / "referees",
    )

LEAGUE_FILES = {
    "Premier League": "Premier_League_25_26.csv",
    "Championship": "Championship_Inglaterra_25_26.csv",
    "La Liga": "La_Liga_25_26.csv",
    "Serie A": "Serie_A_25_26.csv",
    "Bundesliga 2": "Bundesliga_2.csv",
    "Ligue 1": "Ligue_1_25_26.csv",
    "Pro League": "Pro_League_Belgica_25_26.csv",
    "Süper Lig": "Super_Lig_Turquia_25_26.csv",
}
