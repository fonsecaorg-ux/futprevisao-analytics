from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from .utils import parse_date_safe
from .features import list_teams
from .predict import predict_match

@dataclass
class AssistantResponse:
    title: str
    body: str
    data: pd.DataFrame | None = None

def _extract_date(text: str) -> datetime | None:
    # tenta dd/mm/yyyy
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", text)
    if m:
        return parse_date_safe(m.group(1))
    # tenta "hoje"
    if re.search(r"\bhoje\b", text, re.I):
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return None

def answer(user_text: str, matches: pd.DataFrame, calendar: pd.DataFrame, referees: pd.DataFrame) -> AssistantResponse:
    t = (user_text or "").strip()
    if not t:
        return AssistantResponse(title="Assistente", body="Digite uma pergunta (ex.: 'top jogos de hoje por cantos').")

    # intents simples
    if re.search(r"\b(top|melhores|ranking)\b", t, re.I) and re.search(r"\b(cantos|escanteios|cartoes|cartões)\b", t, re.I):
        d = _extract_date(t) or (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        if calendar is None or calendar.empty:
            return AssistantResponse(title="Ranking", body="Calendário não encontrado no projeto.")
        cal = calendar.copy()
        cal = cal[cal["Data"].notna()]
        cal_day = cal[cal["Data"].dt.date == d.date()].copy()
        if cal_day.empty:
            return AssistantResponse(title="Ranking", body=f"Não encontrei jogos no calendário para {d.date().isoformat()}.")
        rows = []
        for _, r in cal_day.iterrows():
            league = r.get("Liga","")
            home = r.get("Time_Casa","")
            away = r.get("Time_Visitante","")
            if not league or not home or not away:
                continue
            try:
                pred = predict_match(matches, referees, league, home, away, window=15)
                rows.append({
                    "Data": r.get("Data"),
                    "Hora": r.get("Hora",""),
                    "Liga": league,
                    "Casa": home,
                    "Visitante": away,
                    "Cantos_μ": round(pred.corners_mean,2),
                    "Cantos_P80": pred.corners_p80,
                    "Cartões_μ": round(pred.cards_mean,2),
                    "Cartões_P80": pred.cards_p80,
                    "Conf": pred.confidence,
                })
            except Exception:
                continue
        if not rows:
            return AssistantResponse(title="Ranking", body="Não consegui calcular previsões para os jogos do dia (verifique nomes de times/ligas).")
        df = pd.DataFrame(rows)
        # ranking: cantos e cartões
        if re.search(r"\b(cartoes|cartões)\b", t, re.I) and not re.search(r"\b(cantos|escanteios)\b", t, re.I):
            df = df.sort_values(["Cartões_μ","Cartões_P80"], ascending=False)
            body = "Ranking por potencial de **cartões** (μ e P80)."
        elif re.search(r"\b(cantos|escanteios)\b", t, re.I) and not re.search(r"\b(cartoes|cartões)\b", t, re.I):
            df = df.sort_values(["Cantos_μ","Cantos_P80"], ascending=False)
            body = "Ranking por potencial de **cantos** (μ e P80)."
        else:
            df["Score"] = df["Cantos_μ"]*0.55 + df["Cartões_μ"]*0.45
            df = df.sort_values(["Score"], ascending=False)
            body = "Ranking combinado (cantos + cartões)."
        return AssistantResponse(title="Ranking do dia", body=body, data=df.head(15))

    if re.search(r"\b(perfil|time|stats)\b", t, re.I):
        # tentar extrair um time
        # fallback: pede ao usuário no UI, mas aqui devolve instrução
        return AssistantResponse(
            title="Perfil de time",
            body="Dica: use a aba **Times** para escolher a liga e o time e ver métricas (rolling, casa/fora, variância)."
        )

    if re.search(r"\b(comparar|vs|x)\b", t, re.I):
        return AssistantResponse(
            title="Comparação",
            body="Dica: use a aba **Partida** para escolher liga, mandante e visitante e ver previsões e explicações."
        )

    return AssistantResponse(
        title="Assistente",
        body="Posso ajudar com: ranking do dia (cantos/cartões), prévia de partida e métricas por time. Ex.: 'top jogos de hoje por cantos'."
    )
