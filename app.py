from __future__ import annotations

import os
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

from core.data_loader import load_all_data
from core.features import list_teams, compute_team_features
from core.predict import predict_match
from core.assistant import answer

APP_TITLE = "FutPrevisão Analytics — Cantos & Cartões"

st.set_page_config(page_title=APP_TITLE, layout="wide")

@st.cache_data(ttl=1800, show_spinner=False)
def cached_bundle(project_root: str):
    return load_all_data(project_root)

def main():
    st.title(APP_TITLE)
    st.caption("Plataforma de análise e previsões estatísticas (cantos e cartões) usando seus CSVs, calendário e árbitros.")

    bundle = cached_bundle(os.path.dirname(__file__))

    if bundle.warnings:
        with st.expander("⚠️ Avisos de dados (clique para ver)", expanded=False):
            for w in bundle.warnings:
                st.write("-", w)

    if bundle.matches is None or bundle.matches.empty:
        st.error("Não encontrei dados de ligas. Verifique a pasta data/leagues.")
        return

    tabs = st.tabs(["📌 Painel do Dia", "⚽ Partida", "🏷️ Times", "🧑‍⚖️ Árbitros", "🤖 Assistente", "🔄 Atualização & Diagnóstico"])

    # Painel do Dia
    with tabs[0]:
        st.subheader("Painel do Dia")
        cal = bundle.calendar.copy() if bundle.calendar is not None else pd.DataFrame()
        if cal.empty:
            st.warning("Calendário vazio. Use data/calendar/calendario_ligas.csv.")
        else:
            min_d = cal["Data"].dropna().min()
            max_d = cal["Data"].dropna().max()
            default_d = datetime.now().date()
            pick = st.date_input("Data", value=default_d, min_value=min_d.date() if pd.notna(min_d) else None, max_value=max_d.date() if pd.notna(max_d) else None)
            mode = st.selectbox("Ranking", ["Combinado (cantos + cartões)", "Somente cantos", "Somente cartões"])
            cal_day = cal[cal["Data"].dt.date == pick].copy()
            if cal_day.empty:
                st.info("Sem jogos para a data selecionada no calendário.")
            else:
                rows=[]
                for _, r in cal_day.iterrows():
                    league=r.get("Liga","")
                    home=r.get("Time_Casa","")
                    away=r.get("Time_Visitante","")
                    if not league or not home or not away:
                        continue
                    try:
                        pred=predict_match(bundle.matches, bundle.referees, league, home, away, window=15)
                        rows.append({
                            "Hora": r.get("Hora",""),
                            "Liga": league,
                            "Casa": home,
                            "Visitante": away,
                            "Cantos μ": round(pred.corners_mean,2),
                            "Cantos P80": pred.corners_p80,
                            "Cartões μ": round(pred.cards_mean,2),
                            "Cartões P80": pred.cards_p80,
                            "Confiança": pred.confidence,
                            "Notas": " | ".join(pred.notes) if pred.notes else ""
                        })
                    except Exception as e:
                        rows.append({
                            "Hora": r.get("Hora",""),
                            "Liga": league,
                            "Casa": home,
                            "Visitante": away,
                            "Erro": str(e)[:120]
                        })
                df=pd.DataFrame(rows)
                if "Erro" in df.columns:
                    st.dataframe(df, use_container_width=True)
                else:
                    if mode.startswith("Somente cantos"):
                        df = df.sort_values(["Cantos μ","Cantos P80"], ascending=False)
                    elif mode.startswith("Somente cartões"):
                        df = df.sort_values(["Cartões μ","Cartões P80"], ascending=False)
                    else:
                        df["Score"] = df["Cantos μ"]*0.55 + df["Cartões μ"]*0.45
                        df = df.sort_values(["Score"], ascending=False)
                    st.dataframe(df, use_container_width=True)

    # Partida
    with tabs[1]:
        st.subheader("Análise de Partida")
        league = st.selectbox("Liga", sorted(bundle.matches["League"].dropna().unique().tolist()))
        teams = list_teams(bundle.matches, league)
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            home = st.selectbox("Mandante", teams, index=0 if teams else None)
        with col2:
            away = st.selectbox("Visitante", teams, index=1 if len(teams)>1 else 0)
        with col3:
            window = st.slider("Janela (últimos N jogos)", 5, 25, 15)

        if home and away and home != away:
            pred = predict_match(bundle.matches, bundle.referees, league, home, away, window=window)
            c1,c2,c3 = st.columns(3)
            c1.metric("Cantos (μ)", f"{pred.corners_mean:.2f}")
            c1.metric("Cantos (P80)", f"{pred.corners_p80:.0f}")
            c2.metric("Cartões (μ)", f"{pred.cards_mean:.2f}")
            c2.metric("Cartões (P80)", f"{pred.cards_p80:.0f}")
            c3.metric("Confiança", pred.confidence)
            if pred.notes:
                st.info(" | ".join(pred.notes))

            with st.expander("📌 Detalhes por time (rolling + casa/fora)"):
                hf = compute_team_features(bundle.matches, league, home, window=window)
                af = compute_team_features(bundle.matches, league, away, window=window)
                df = pd.DataFrame([
                    {"Time": home, "N": hf.n_matches,
                     "Cantos For": hf.corners_for_avg, "Cantos Against": hf.corners_against_avg,
                     "Cartões For": hf.cards_for_avg, "Cartões Against": hf.cards_against_avg},
                    {"Time": away, "N": af.n_matches,
                     "Cantos For": af.corners_for_avg, "Cantos Against": af.corners_against_avg,
                     "Cartões For": af.cards_for_avg, "Cartões Against": af.cards_against_avg},
                ])
                st.dataframe(df, use_container_width=True)

    # Times
    with tabs[2]:
        st.subheader("Explorador de Times")
        league = st.selectbox("Liga (Times)", sorted(bundle.matches["League"].dropna().unique().tolist()), key="league_times")
        teams = list_teams(bundle.matches, league)
        team = st.selectbox("Time", teams, key="team_pick")
        window = st.slider("Janela (Times)", 5, 25, 15, key="window_times")
        if team:
            tf = compute_team_features(bundle.matches, league, team, window=window)
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Jogos na janela", tf.n_matches)
            m2.metric("Cantos For (avg)", f"{tf.corners_for_avg:.2f}")
            m3.metric("Cantos Against (avg)", f"{tf.corners_against_avg:.2f}")
            m4.metric("Cantos (std)", f"{tf.corners_std:.2f}" if tf.corners_std==tf.corners_std else "—")
            n1,n2,n3,n4 = st.columns(4)
            n1.metric("Cartões For (avg)", f"{tf.cards_for_avg:.2f}")
            n2.metric("Cartões Against (avg)", f"{tf.cards_against_avg:.2f}")
            n3.metric("Cartões (std)", f"{tf.cards_std:.2f}" if tf.cards_std==tf.cards_std else "—")
            n4.metric("Liga", league)

            with st.expander("Casa vs Fora"):
                st.write({
                    "Cantos casa (for/against)": (tf.corners_for_home_avg, tf.corners_against_home_avg),
                    "Cantos fora (for/against)": (tf.corners_for_away_avg, tf.corners_against_away_avg),
                    "Cartões casa (for/against)": (tf.cards_for_home_avg, tf.cards_against_home_avg),
                    "Cartões fora (for/against)": (tf.cards_for_away_avg, tf.cards_against_away_avg),
                })

    # Árbitros
    with tabs[3]:
        st.subheader("Árbitros (cartões)")
        ref = bundle.referees.copy() if bundle.referees is not None else pd.DataFrame()
        if ref.empty:
            st.info("Nenhum dado de árbitros carregado.")
        else:
            # tentar filtrar por liga
            cols = [c.lower() for c in ref.columns]
            if "liga" in cols:
                liga_col = ref.columns[cols.index("liga")]
                leagues = sorted(ref[liga_col].dropna().unique().tolist())
                liga = st.selectbox("Liga", leagues)
                view = ref[ref[liga_col] == liga].copy()
            else:
                view = ref
            st.dataframe(view, use_container_width=True)

    # Assistente
    with tabs[4]:
        st.subheader("Assistente (com base nos seus dados)")
        st.caption("Pergunte coisas como: 'top jogos de hoje por cantos' ou 'top jogos de hoje por cartões'.")
        q = st.text_input("Pergunta", value="")
        if st.button("Responder"):
            resp = answer(q, bundle.matches, bundle.calendar, bundle.referees)
            st.markdown(f"### {resp.title}")
            st.write(resp.body)
            if resp.data is not None:
                st.dataframe(resp.data, use_container_width=True)

    # Atualização
    with tabs[5]:
        st.subheader("Atualização & Diagnóstico")
        st.write("O script `updater/atualizador.py` foi mantido no projeto.")
        st.warning("Por segurança, esta UI não executa scripts do sistema automaticamente. Rode o atualizador via terminal quando quiser.")
        st.code("python updater/atualizador.py", language="bash")
        st.write("Depois de atualizar, clique abaixo para recarregar os dados:")
        if st.button("Recarregar dados (limpar cache)"):
            st.cache_data.clear()
            st.success("Cache limpo. Recarregue a página.")

if __name__ == "__main__":
    main()
