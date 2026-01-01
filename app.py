from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from core.data_loader import load_all_data
from core.features import list_teams, compute_team_features
from core.predict import predict_match
from core.assistant import answer


APP_TITLE = "FutPrevisão Analytics — Cantos & Cartões"

st.set_page_config(page_title=APP_TITLE, layout="wide")

CSS = """
<style>
/* layout */
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
h1, h2, h3 {letter-spacing: -0.2px;}
.small-muted {color: #6b7280; font-size: 0.92rem;}
.kpi {padding: 0.9rem 1rem; border-radius: 14px; border: 1px solid rgba(0,0,0,.08);}
.kpi .v {font-size: 1.55rem; font-weight: 700;}
.kpi .t {font-size: 0.9rem; opacity: 0.8;}
.card {padding: 1rem; border-radius: 16px; border: 1px solid rgba(0,0,0,.08); background: rgba(255,255,255,.70);}
hr {border: none; border-top: 1px solid rgba(0,0,0,.08); margin: 1rem 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load_bundle() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    root = Path(__file__).resolve().parent
    bundle = load_all_data(root)
    return bundle.matches, bundle.calendar, bundle.referees, bundle.warnings


def _kpi(col, title: str, value: str, subtitle: str = ""):
    with col:
        st.markdown(
            f"<div class='kpi'><div class='t'>{title}</div><div class='v'>{value}</div><div class='small-muted'>{subtitle}</div></div>",
            unsafe_allow_html=True,
        )


def _league_options(matches: pd.DataFrame) -> list[str]:
    if matches is None or matches.empty:
        return []
    leagues = sorted(matches["League"].dropna().unique().tolist())
    return leagues


def _referees_for_league(referees: pd.DataFrame, league: str) -> list[str]:
    if referees is None or referees.empty:
        return []
    cols = {c.lower(): c for c in referees.columns}
    liga_col = cols.get("liga") or cols.get("league")
    arb_col = cols.get("arbitro") or cols.get("árbitro") or cols.get("referee") or cols.get("nome")
    if not (liga_col and arb_col):
        return []
    df = referees.copy()
    df_l = df[df[liga_col].astype(str) == league] if league else df
    refs = sorted(df_l[arb_col].dropna().astype(str).unique().tolist())
    return refs


def _build_day_ranking(matches: pd.DataFrame, calendar: pd.DataFrame, referees: pd.DataFrame, day: datetime.date) -> pd.DataFrame:
    if calendar is None or calendar.empty:
        return pd.DataFrame()
    cal_day = calendar[calendar["Data"].dt.date == day].copy()
    if cal_day.empty:
        return pd.DataFrame()

    rows = []
    for _, r in cal_day.iterrows():
        league = str(r.get("Liga", "")).strip()
        home = str(r.get("Time_Casa", "")).strip()
        away = str(r.get("Time_Visitante", "")).strip()
        if not league or not home or not away:
            continue
        try:
            p = predict_match(matches, league, home, away, window=25, referees=referees)
            rows.append({
                "Liga": league,
                "Jogo": f"{home} x {away}",
                "Cantos μ": round(p.corners_mean, 2),
                "Cantos P80": int(p.corners_p80),
                "Cartões μ": round(p.cards_mean, 2),
                "Cartões P80": int(p.cards_p80),
                "Confiança": p.confidence,
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # score combinado simples para ordenar (sem ser recomendação)
    df["Score"] = df["Cantos μ"] + 2.0 * df["Cartões μ"]
    df = df.sort_values(["Score"], ascending=False).reset_index(drop=True)
    return df


def _stability_check(matches: pd.DataFrame, league: str, home: str, away: str, referees: pd.DataFrame, referee: str | None, profile: str | None) -> dict:
    p_short = predict_match(matches, league, home, away, window=10, referees=referees, match_referee=referee, referee_profile=profile)
    p_long = predict_match(matches, league, home, away, window=25, referees=referees, match_referee=referee, referee_profile=profile)

    def delta(a: float, b: float) -> float:
        try:
            return float(a) - float(b)
        except Exception:
            return float("nan")

    out = {
        "Δ cantos μ (10-25)": delta(p_short.corners_mean, p_long.corners_mean),
        "Δ cartões μ (10-25)": delta(p_short.cards_mean, p_long.cards_mean),
        "p_short": p_short,
        "p_long": p_long,
    }
    return out


def main():
    st.title(APP_TITLE)

    matches, calendar, referees, warnings = _load_bundle()

    if warnings:
        with st.expander("Diagnóstico rápido de carga", expanded=False):
            for w in warnings[:25]:
                st.write("•", w)
            if len(warnings) > 25:
                st.write(f"(+{len(warnings)-25} avisos)")

    tabs = st.tabs(["📅 Jogos do dia", "🆚 Partida", "🏟️ Times", "🧑‍⚖️ Árbitros", "🤖 Assistente", "🩺 Saúde dos dados", "⚙️ Atualizador"])

    # --- Jogos do dia
    with tabs[0]:
        if calendar is None or calendar.empty:
            st.warning("Calendário não carregado. Verifique data/calendar/calendario_ligas.csv")
        else:
            min_d = calendar["Data"].dropna().min()
            max_d = calendar["Data"].dropna().max()
            default_d = datetime.now().date()
            if pd.notna(min_d) and default_d < min_d.date():
                default_d = min_d.date()
            if pd.notna(max_d) and default_d > max_d.date():
                default_d = max_d.date()

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                day = st.date_input("Data", value=default_d, min_value=min_d.date() if pd.notna(min_d) else None, max_value=max_d.date() if pd.notna(max_d) else None)
            with c2:
                view = st.selectbox("Ordenar por", ["Score combinado", "Cantos μ", "Cartões μ"])
            with c3:
                st.markdown("<div class='small-muted'>Ranking estatístico baseado nos seus CSVs (cantos/cartões). Não é recomendação.</div>", unsafe_allow_html=True)

            df_rank = _build_day_ranking(matches, calendar, referees, day)
            if df_rank.empty:
                st.info("Sem jogos (ou sem cálculo) para a data selecionada.")
            else:
                if view == "Cantos μ":
                    df_rank = df_rank.sort_values(["Cantos μ"], ascending=False)
                elif view == "Cartões μ":
                    df_rank = df_rank.sort_values(["Cartões μ"], ascending=False)
                else:
                    df_rank = df_rank.sort_values(["Score"], ascending=False)

                st.dataframe(df_rank.drop(columns=["Score"], errors="ignore"), use_container_width=True)

    # --- Partida
    with tabs[1]:
        leagues = _league_options(matches)
        if not leagues:
            st.warning("Nenhuma liga carregada. Verifique seus CSVs em data/leagues.")
        else:
            colA, colB, colC, colD = st.columns([1.2, 1.2, 1.2, 1.4])
            with colA:
                league = st.selectbox("Liga", leagues, index=0)
            teams = list_teams(matches, league)
            with colB:
                home = st.selectbox("Mandante", teams, index=0 if teams else 0)
            away_opts = [t for t in teams if t != home] if teams else []
            with colC:
                away = st.selectbox("Visitante", away_opts, index=0 if away_opts else 0)
            with colD:
                window = st.slider("Janela (últimos jogos)", min_value=5, max_value=30, value=20, step=1)

            st.markdown("---")

            ref_col1, ref_col2, ref_col3 = st.columns([1.2, 1.2, 2.0])
            with ref_col1:
                referee = st.selectbox("Árbitro (opcional)", ["(não informar)"] + _referees_for_league(referees, league))
                referee_val = None if referee == "(não informar)" else referee
            with ref_col2:
                profile = st.selectbox("Perfil de cartões (fallback)", ["Normal", "Rigoroso", "Seguro (poucos cartões)"])
            with ref_col3:
                st.markdown("<div class='small-muted'>Se o árbitro não for informado (ou não for encontrado), o perfil ajusta apenas a projeção de cartões.</div>", unsafe_allow_html=True)

            if not (league and home and away):
                st.info("Selecione liga, mandante e visitante.")
            else:
                p = predict_match(matches, league, home, away, window=window, referees=referees, match_referee=referee_val, referee_profile=profile)

                k1, k2, k3, k4 = st.columns(4)
                _kpi(k1, "Cantos (μ)", f"{p.corners_mean:.2f}", f"P50 {p.corners_p50:.0f} | P80 {p.corners_p80:.0f} | P90 {p.corners_p90:.0f}")
                _kpi(k2, "Cartões (μ)", f"{p.cards_mean:.2f}", f"P50 {p.cards_p50:.0f} | P80 {p.cards_p80:.0f} | P90 {p.cards_p90:.0f}")
                _kpi(k3, "Confiança", p.confidence, f"Janela: {p.window} jogos")
                arb_txt = f"{p.referee_used} (x{p.referee_factor:.2f})" if p.referee_used else (f"Perfil (x{p.referee_factor:.2f})" if p.referee_factor != 1.0 else "—")
                _kpi(k4, "Ajuste cartões", arb_txt, f"Confiança árbitro: {p.referee_confidence}")

                st.markdown("---")

                c1, c2 = st.columns([1.1, 1.0])
                with c1:
                    st.subheader("Quebra por time")
                    st.write(f"**{home}** — cantos μ: {p.corners_home_mean:.2f} | cartões μ: {p.cards_home_mean:.2f}")
                    st.write(f"**{away}** — cantos μ: {p.corners_away_mean:.2f} | cartões μ: {p.cards_away_mean:.2f}")
                    if p.notes:
                        st.markdown("<div class='small-muted'>Notas</div>", unsafe_allow_html=True)
                        for n in p.notes:
                            st.write("•", n)

                with c2:
                    st.subheader("Estabilidade (10 vs 25 jogos)")
                    stab = _stability_check(matches, league, home, away, referees, referee_val, profile)
                    dc = stab["Δ cantos μ (10-25)"]
                    dk = stab["Δ cartões μ (10-25)"]
                    st.write(f"Δ cantos μ: **{dc:+.2f}** | Δ cartões μ: **{dk:+.2f}**")
                    if abs(dc) >= 1.0 or abs(dk) >= 0.8:
                        st.warning("A projeção muda bastante entre janelas curtas e longas — trate como sinal de variabilidade nos dados.")
                    st.markdown("<div class='small-muted'>A estabilidade ajuda a entender se a média está muito sensível ao recorte de jogos.</div>", unsafe_allow_html=True)

                # export
                exp = pd.DataFrame([{
                    "League": p.league,
                    "Home": p.home,
                    "Away": p.away,
                    "Window": p.window,
                    "Corners_mean": p.corners_mean,
                    "Corners_p50": p.corners_p50,
                    "Corners_p80": p.corners_p80,
                    "Corners_p90": p.corners_p90,
                    "Cards_mean": p.cards_mean,
                    "Cards_p50": p.cards_p50,
                    "Cards_p80": p.cards_p80,
                    "Cards_p90": p.cards_p90,
                    "Corners_home_mean": p.corners_home_mean,
                    "Corners_away_mean": p.corners_away_mean,
                    "Cards_home_mean": p.cards_home_mean,
                    "Cards_away_mean": p.cards_away_mean,
                    "Confidence": p.confidence,
                    "Referee_used": p.referee_used,
                    "Referee_factor": p.referee_factor,
                    "Referee_confidence": p.referee_confidence,
                }])
                st.download_button(
                    label="Baixar esta análise (CSV)",
                    data=exp.to_csv(index=False).encode("utf-8"),
                    file_name=f"analise_{league}_{home}_x_{away}.csv".replace(" ", "_"),
                    mime="text/csv",
                )

    # --- Times
    with tabs[2]:
        leagues = _league_options(matches)
        if not leagues:
            st.info("Sem ligas carregadas.")
        else:
            c1, c2, c3 = st.columns([1.2, 1.4, 1.4])
            with c1:
                league_t = st.selectbox("Liga", leagues, key="t_league")
            teams = list_teams(matches, league_t)
            with c2:
                team = st.selectbox("Time", teams, key="t_team")
            with c3:
                window_t = st.slider("Janela (últimos jogos)", min_value=5, max_value=30, value=20, step=1, key="t_window")

            tf = compute_team_features(matches, league_t, team, window=window_t)

            k1, k2, k3, k4 = st.columns(4)
            _kpi(k1, "Jogos na janela", f"{tf.n_matches}", "")
            _kpi(k2, "Cantos a favor (média)", f"{tf.corners_for_avg:.2f}", f"Casa {tf.corners_for_home_avg:.2f} | Fora {tf.corners_for_away_avg:.2f}")
            _kpi(k3, "Cartões a favor (média)", f"{tf.cards_for_avg:.2f}", f"Casa {tf.cards_for_home_avg:.2f} | Fora {tf.cards_for_away_avg:.2f}")
            _kpi(k4, "Variância", f"σ cantos {tf.corners_std:.2f}", f"σ cartões {tf.cards_std:.2f}")

            st.markdown("---")

            # últimos jogos do time (para contexto)
            df = matches[(matches["League"] == league_t) & ((matches["HomeTeam"] == team) | (matches["AwayTeam"] == team))].copy()
            df = df.sort_values(["Date"], na_position="last").tail(window_t)
            if not df.empty:
                df_show = df[["Date","HomeTeam","AwayTeam","Corners_H","Corners_A","Cards_H","Cards_A","Referee"]].copy()
                df_show["Date"] = df_show["Date"].dt.date
                st.dataframe(df_show.reset_index(drop=True), use_container_width=True)

    # --- Árbitros
    with tabs[3]:
        if referees is None or referees.empty:
            st.info("Sem base de árbitros carregada. Coloque arbitros.csv ou arbitros_5_ligas_2025_2026.csv em data/referees.")
        else:
            cols = {c.lower(): c for c in referees.columns}
            liga_col = cols.get("liga") or cols.get("league")
            arb_col = cols.get("arbitro") or cols.get("árbitro") or cols.get("referee") or cols.get("nome")
            media_col = cols.get("media_cartoes") or cols.get("media_cartões") or cols.get("avg_cards") or cols.get("cartoes_por_jogo") or cols.get("cartões_por_jogo")

            if not (liga_col and arb_col):
                st.warning("Não consegui identificar colunas de liga/árbitro no CSV.")
            else:
                leagues = sorted(referees[liga_col].dropna().unique().tolist()) if liga_col in referees.columns else []
                league_r = st.selectbox("Liga", ["(todas)"] + leagues)
                df = referees.copy()
                if league_r != "(todas)" and liga_col in df.columns:
                    df = df[df[liga_col].astype(str) == league_r]
                if media_col and media_col in df.columns:
                    df[media_col] = pd.to_numeric(df[media_col], errors="coerce")
                    df = df.sort_values(media_col, ascending=False)
                st.dataframe(df.head(250), use_container_width=True)
                st.markdown("<div class='small-muted'>Dica: se quiser um fallback sem nome do árbitro, use o perfil de cartões na aba Partida.</div>", unsafe_allow_html=True)

    # --- Assistente
    with tabs[4]:
        st.markdown("<div class='small-muted'>O assistente interpreta perguntas simples e retorna análises/rankings com base nos seus dados.</div>", unsafe_allow_html=True)
        q = st.text_input("Pergunta", value="", placeholder="Ex.: analisa Southampton x Millwall | top jogos de hoje por cantos")
        if st.button("Responder"):
            resp = answer(q, matches, calendar, referees)
            st.subheader(resp.title)
            st.write(resp.body)
            if resp.data is not None and isinstance(resp.data, pd.DataFrame) and not resp.data.empty:
                st.dataframe(resp.data, use_container_width=True)

    # --- Saúde dos dados
    with tabs[5]:
        if matches is None or matches.empty:
            st.info("Sem dados carregados.")
        else:
            st.subheader("Resumo por liga")
            g = matches.groupby("League").agg(
                jogos=("League", "size"),
                ultima_data=("Date", "max"),
                times=("HomeTeam", lambda s: len(pd.unique(s.dropna()))),
                cantos_total_na=("Corners_Total", lambda s: int(pd.to_numeric(s, errors="coerce").isna().sum())),
                cartoes_total_na=("Cards_Total", lambda s: int(pd.to_numeric(s, errors="coerce").isna().sum())),
            ).reset_index()
            g["ultima_data"] = pd.to_datetime(g["ultima_data"], errors="coerce").dt.date
            st.dataframe(g.sort_values("jogos", ascending=False), use_container_width=True)

            st.markdown("---")

            st.subheader("Compatibilidade calendário x ligas")
            if calendar is None or calendar.empty:
                st.info("Calendário não carregado.")
            else:
                # procura times no calendário que não aparecem na liga correspondente
                issues = []
                for lg in sorted(calendar["Liga"].dropna().unique().tolist()):
                    cal_l = calendar[calendar["Liga"] == lg]
                    teams_cal = set(pd.concat([cal_l["Time_Casa"], cal_l["Time_Visitante"]], ignore_index=True).dropna().astype(str))
                    teams_data = set(list_teams(matches, lg)) if lg in _league_options(matches) else set()
                    missing = sorted([t for t in teams_cal if t not in teams_data])
                    if missing:
                        issues.append({"Liga": lg, "Times no calendário não encontrados nos CSVs": ", ".join(missing[:20]) + ("..." if len(missing) > 20 else "")})
                if issues:
                    st.warning("Achei times no calendário que não batem com os CSVs da liga (isso atrapalha os cálculos do dia). Veja abaixo:")
                    st.dataframe(pd.DataFrame(issues), use_container_width=True)
                else:
                    st.success("Calendário parece compatível com os CSVs das ligas.")

    # --- Atualizador
    with tabs[6]:
        st.subheader("Atualizador")
        st.markdown(
            """Se você usa um script para atualizar CSVs/PDFs (ex.: `updater/atualizador.py`), a rotina recomendada é:

1) Atualizar arquivos em `data/leagues/`, `data/calendar/` e `data/referees/`  
2) Reiniciar o app Streamlit (ou limpar cache em 'Rerun')  

**Dica:** Você pode adicionar novas ligas apenas colocando um novo `.csv` em `data/leagues/` — o app tenta carregar automaticamente.
"""
        )


if __name__ == "__main__":
    main()
