"""
FutPrevisão V31 MAXIMUM + SUPERBOT V2.0
Otimizado para Claude Project Files
Versão: 31.1 PROJECT EDITION
Data: 26/12/2024
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import math
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from difflib import get_close_matches
import re
from collections import defaultdict

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="FutPrevisão V31 MAXIMUM",
    layout="wide",
    page_icon="⚽",
    initial_sidebar_state="expanded"
)

# CSS PERSONALIZADO
st.markdown('''
<style>
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) p {
        color: white !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: #2d3748 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin: 10px 0 !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) p {
        color: white !important;
    }
    
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .highlight-green {
        background-color: #90EE90;
        padding: 5px;
        border-radius: 3px;
    }
</style>
''', unsafe_allow_html=True)

# ============================================================
# CONSTANTES - PATH DO PROJETO CLAUDE
# ============================================================

DATA_PATH = '/mnt/project/'

# ============================================================
# MAPEAMENTO DE NOMES
# ============================================================

NAME_MAPPING = {
    'Man United': 'Manchester Utd',
    'Man City': 'Manchester City',
    'Spurs': 'Tottenham',
    'Newcastle': 'Newcastle Utd',
    'Wolves': 'Wolverhampton',
    'Brighton': 'Brighton and Hove Albion',
    'Nottm Forest': "Nott'm Forest",
    'Leicester': 'Leicester City',
    'West Ham': 'West Ham Utd',
    'Sheffield Utd': 'Sheffield United',
    'Inter': 'Inter Milan',
    'AC Milan': 'Milan',
    'Ath Madrid': 'Atletico Madrid',
    'Ath Bilbao': 'Athletic Club',
    'Betis': 'Real Betis',
    'Sociedad': 'Real Sociedad',
    'Celta': 'Celta Vigo',
    "M'gladbach": 'Borussia M.Gladbach',
    'Leverkusen': 'Bayer Leverkusen',
    'FC Koln': 'FC Cologne',
    'Dortmund': 'Borussia Dortmund',
    'Ein Frankfurt': 'Eintracht Frankfurt',
    'Hoffenheim': 'TSG Hoffenheim',
    'Bayern Munich': 'Bayern Munchen',
    'RB Leipzig': 'RasenBallsport Leipzig',
    'Paris SG': 'Paris S-G',
    'Paris S-G': 'Paris Saint Germain',
    'Saint-Etienne': 'St Etienne',
}

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalize_name(name: str, known_teams: List[str]) -> Optional[str]:
    """Normaliza nomes de times com fuzzy matching"""
    if not name or not known_teams:
        return None
    
    name = name.strip()
    
    # Mapeamento direto
    if name in NAME_MAPPING:
        name = NAME_MAPPING[name]
    
    # Verificar se já está correto
    if name in known_teams:
        return name
    
    # Fuzzy matching
    matches = get_close_matches(name, known_teams, n=1, cutoff=0.6)
    return matches[0] if matches else None


def format_currency(value: float) -> str:
    """Formata valor em R$"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_prob_emoji(prob: float) -> str:
    """Retorna emoji baseado na probabilidade"""
    if prob >= 80:
        return "🔥"
    elif prob >= 75:
        return "✅"
    elif prob >= 70:
        return "🎯"
    elif prob >= 65:
        return "⚡"
    else:
        return "⚪"


# ============================================================
# CARREGAMENTO DE DADOS - OTIMIZADO PARA PROJECT
# ============================================================

@st.cache_data(ttl=3600)
def load_all_data():
    """
    Carrega todos os dados do projeto Claude
    Retorna: (stats_db, calendar, referees)
    """
    
    stats_db = {}
    calendar_df = pd.DataFrame()
    referees_db = {}
    
    # Definir arquivos das ligas
    league_files = {
        'Premier League': 'Premier_League_25_26.csv',
        'La Liga': 'La_Liga_25_26.csv',
        'Serie A': 'Serie_A_25_26.csv',
        'Bundesliga': 'Bundesliga_25_26.csv',
        'Ligue 1': 'Ligue_1_25_26.csv',
        'Championship': 'Championship_Inglaterra_25_26.csv',
        'Bundesliga 2': 'Bundesliga_2.csv',
        'Pro League': 'Pro_League_Belgica_25_26.csv',
        'Super Lig': 'Super_Lig_Turquia_25_26.csv',
        'Premiership': 'Premiership_Escocia_25_26.csv'
    }
    
    # Carregar cada liga
    for league_name, filename in league_files.items():
        try:
            filepath = f"{DATA_PATH}{filename}"
            df = pd.read_csv(filepath, encoding='utf-8')
            
            # Extrair times únicos
            teams = set(df['HomeTeam'].dropna().unique()) | set(df['AwayTeam'].dropna().unique())
            
            for team in teams:
                if pd.isna(team):
                    continue
                
                # Filtrar jogos
                h_games = df[df['HomeTeam'] == team]
                a_games = df[df['AwayTeam'] == team]
                
                # Estatísticas CASA
                corners_h = h_games['HC'].mean() if 'HC' in h_games.columns and len(h_games) > 0 else 5.5
                corners_h_std = h_games['HC'].std() if 'HC' in h_games.columns and len(h_games) > 1 else 2.0
                cards_h = h_games[['HY', 'HR']].sum(axis=1).mean() if 'HY' in h_games.columns and len(h_games) > 0 else 2.5
                fouls_h = h_games['HF'].mean() if 'HF' in h_games.columns and len(h_games) > 0 else 12.0
                goals_fh = h_games['FTHG'].mean() if 'FTHG' in h_games.columns and len(h_games) > 0 else 1.5
                goals_ah = h_games['FTAG'].mean() if 'FTAG' in h_games.columns and len(h_games) > 0 else 1.3
                shots_h = h_games['HST'].mean() if 'HST' in h_games.columns and len(h_games) > 0 else 4.5
                reds_h = h_games['HR'].mean() if 'HR' in h_games.columns and len(h_games) > 0 else 0.05
                
                # Estatísticas FORA
                corners_a = a_games['AC'].mean() if 'AC' in a_games.columns and len(a_games) > 0 else 4.5
                corners_a_std = a_games['AC'].std() if 'AC' in a_games.columns and len(a_games) > 1 else 2.0
                cards_a = a_games[['AY', 'AR']].sum(axis=1).mean() if 'AY' in a_games.columns and len(a_games) > 0 else 2.5
                fouls_a = a_games['AF'].mean() if 'AF' in a_games.columns and len(a_games) > 0 else 12.0
                goals_fa = a_games['FTAG'].mean() if 'FTAG' in a_games.columns and len(a_games) > 0 else 1.3
                goals_aa = a_games['FTHG'].mean() if 'FTHG' in a_games.columns and len(a_games) > 0 else 1.5
                shots_a = a_games['AST'].mean() if 'AST' in a_games.columns and len(a_games) > 0 else 4.0
                reds_a = a_games['AR'].mean() if 'AR' in a_games.columns and len(a_games) > 0 else 0.05
                
                # Armazenar no banco de dados
                stats_db[team] = {
                    'corners': (corners_h + corners_a) / 2,
                    'corners_home': corners_h,
                    'corners_away': corners_a,
                    'corners_std': (corners_h_std + corners_a_std) / 2,
                    'cards': (cards_h + cards_a) / 2,
                    'cards_home': cards_h,
                    'cards_away': cards_a,
                    'fouls': (fouls_h + fouls_a) / 2,
                    'fouls_home': fouls_h,
                    'fouls_away': fouls_a,
                    'goals_f': (goals_fh + goals_fa) / 2,
                    'goals_f_home': goals_fh,
                    'goals_f_away': goals_fa,
                    'goals_a': (goals_ah + goals_aa) / 2,
                    'goals_a_home': goals_ah,
                    'goals_a_away': goals_aa,
                    'shots_on_target': (shots_h + shots_a) / 2,
                    'shots_home': shots_h,
                    'shots_away': shots_a,
                    'red_cards_avg': (reds_h + reds_a) / 2,
                    'red_cards_home': reds_h,
                    'red_cards_away': reds_a,
                    'league': league_name,
                    'games': len(h_games) + len(a_games)
                }
            
            st.sidebar.success(f"✅ {league_name}: {len(teams)} times")
            
        except Exception as e:
            st.sidebar.error(f"❌ {league_name}: {str(e)}")
    
    # Carregar calendário
    try:
        cal_path = f"{DATA_PATH}calendario_ligas.csv"
        calendar_df = pd.read_csv(cal_path, encoding='utf-8')
        
        if 'Data' in calendar_df.columns:
            calendar_df['DtObj'] = pd.to_datetime(calendar_df['Data'], format='%d/%m/%Y', errors='coerce')
        
        st.sidebar.success(f"✅ Calendário: {len(calendar_df)} jogos")
        
    except Exception as e:
        st.sidebar.warning(f"⚠️ Calendário: {str(e)}")
    
    # Carregar árbitros
    try:
        ref_path = f"{DATA_PATH}arbitros_5_ligas_2025_2026.csv"
        refs_df = pd.read_csv(ref_path, encoding='utf-8')
        
        for _, row in refs_df.iterrows():
            red_cards = row.get('Cartoes_Vermelhos', 0)
            games = row['Jogos_Apitados']
            
            referees_db[row['Arbitro']] = {
                'factor': row['Media_Cartoes_Por_Jogo'] / 4.0,
                'games': games,
                'avg_cards': row['Media_Cartoes_Por_Jogo'],
                'red_cards': red_cards,
                'red_rate': red_cards / games if games > 0 else 0.08
            }
        
        st.sidebar.success(f"✅ Árbitros: {len(referees_db)}")
        
    except Exception as e:
        st.sidebar.warning(f"⚠️ Árbitros: {str(e)}")
    
    return stats_db, calendar_df, referees_db


# ============================================================
# MOTOR DE CÁLCULO V31 - CAUSALITY ENGINE
# ============================================================

def calcular_jogo_v31(home_stats: Dict, away_stats: Dict, ref_data: Optional[Dict] = None) -> Dict:
    """
    Motor de Cálculo V31 - CAUSALITY ENGINE
    
    Filosofia: CAUSA → EFEITO
    - Chutes no gol → Escanteios
    - Faltas → Cartões
    - Árbitro → Rigidez
    """
    
    # ESCANTEIOS com boost de chutes
    base_corners_h = home_stats.get('corners_home', home_stats['corners'])
    base_corners_a = away_stats.get('corners_away', away_stats['corners'])
    
    # Boost baseado em chutes (V14.0)
    shots_h = home_stats.get('shots_home', 4.5)
    shots_a = away_stats.get('shots_away', 4.0)
    
    if shots_h > 6.0:
        pressure_h = 1.20  # Alto
    elif shots_h > 4.5:
        pressure_h = 1.10  # Médio
    else:
        pressure_h = 1.0   # Baixo
    
    if shots_a > 6.0:
        pressure_a = 1.20
    elif shots_a > 4.5:
        pressure_a = 1.10
    else:
        pressure_a = 1.0
    
    # Fator mando de campo
    corners_h = base_corners_h * 1.15 * pressure_h
    corners_a = base_corners_a * 0.90 * pressure_a
    corners_total = corners_h + corners_a
    
    # CARTÕES
    fouls_h = home_stats.get('fouls_home', home_stats.get('fouls', 12.0))
    fouls_a = away_stats.get('fouls_away', away_stats.get('fouls', 12.0))
    
    # Fator de violência
    violence_h = 1.0 if fouls_h > 12.5 else 0.85
    violence_a = 1.0 if fouls_a > 12.5 else 0.85
    
    # Fator do árbitro
    ref_factor = 1.0
    ref_red_rate = 0.08
    strictness = 1.0
    
    if ref_data:
        ref_factor = ref_data.get('factor', 1.0)
        ref_red_rate = ref_data.get('red_rate', 0.08)
        
        # Rigidez baseada em vermelhos (V14.0)
        if ref_red_rate > 0.12:
            strictness = 1.15
        elif ref_red_rate > 0.08:
            strictness = 1.08
        else:
            strictness = 1.0
    
    cards_h_base = home_stats.get('cards_home', home_stats['cards'])
    cards_a_base = away_stats.get('cards_away', away_stats['cards'])
    
    cards_h = cards_h_base * violence_h * ref_factor * strictness
    cards_a = cards_a_base * violence_a * ref_factor * strictness
    cards_total = cards_h + cards_a
    
    # Probabilidade de cartão vermelho (V14.0)
    reds_h_avg = home_stats.get('red_cards_home', 0.05)
    reds_a_avg = away_stats.get('red_cards_away', 0.05)
    prob_red_card = ((reds_h_avg + reds_a_avg) / 2) * ref_red_rate * 100
    
    # xG (Expected Goals)
    xg_h = (home_stats['goals_f'] * away_stats['goals_a']) / 1.3
    xg_a = (away_stats['goals_f'] * home_stats['goals_a']) / 1.3
    
    return {
        'corners': {
            'h': corners_h,
            'a': corners_a,
            't': corners_total
        },
        'cards': {
            'h': cards_h,
            'a': cards_a,
            't': cards_total
        },
        'goals': {
            'h': xg_h,
            'a': xg_a
        },
        'metadata': {
            'ref_factor': ref_factor,
            'violence_home': fouls_h > 12.5,
            'violence_away': fouls_a > 12.5,
            'pressure_home': pressure_h,
            'pressure_away': pressure_a,
            'shots_home': shots_h,
            'shots_away': shots_a,
            'strictness': strictness,
            'prob_red_card': prob_red_card,
            'red_rate': ref_red_rate
        }
    }


def simulate_game_v31(home_stats: Dict, away_stats: Dict, ref_data: Optional[Dict] = None, n_sims: int = 3000) -> Dict:
    """Simulador Monte Carlo com distribuição de Poisson"""
    calc = calcular_jogo_v31(home_stats, away_stats, ref_data)
    
    return {
        'corners_h': np.random.poisson(calc['corners']['h'], n_sims),
        'corners_a': np.random.poisson(calc['corners']['a'], n_sims),
        'corners_total': np.random.poisson(calc['corners']['t'], n_sims),
        'cards_h': np.random.poisson(calc['cards']['h'], n_sims),
        'cards_a': np.random.poisson(calc['cards']['a'], n_sims),
        'cards_total': np.random.poisson(calc['cards']['t'], n_sims),
        'goals_h': np.random.poisson(calc['goals']['h'], n_sims),
        'goals_a': np.random.poisson(calc['goals']['a'], n_sims)
    }


# ============================================================
# SUPERBOT V2.0 - CLASSES
# ============================================================

class SuperIntentDetector:
    """Detector de intenções avançado"""
    
    def __init__(self):
        self.patterns = {
            'stats_time': [
                'como está', 'como esta', 'estatística', 'estatisticas',
                'dados do', 'números do', 'stats', 'desempenho', 'performance',
                'como joga', 'como anda', 'média de', 'media de'
            ],
            'jogos_hoje': [
                'jogos hoje', 'partidas hoje', 'joga hoje', 'tem jogo hoje',
                'quais jogos hoje', 'que jogo tem hoje', 'hoje'
            ],
            'jogos_amanha': [
                'jogos amanhã', 'jogos amanha', 'partidas amanhã', 'amanhã', 'amanha'
            ],
            'analise_jogo': [
                ' vs ', ' x ', 'versus', 'contra', 'analisa', 'analise',
                'quem ganha', 'previsão', 'previsao', 'favorito'
            ],
            'ranking_cantos': [
                'mais cantos', 'top cantos', 'maiores cantos', 'ranking cantos',
                'times com mais cantos', 'melhores em cantos', 'escanteios'
            ],
            'ranking_cartoes': [
                'mais cartões', 'mais cartoes', 'top cartões', 'top cartoes',
                'maiores cartões', 'ranking cartões', 'times violentos', 'amarelos'
            ],
            'ranking_gols': [
                'mais gols', 'top gols', 'maiores gols', 'ranking gols',
                'artilheiros', 'times ofensivos', 'ataque'
            ],
            'saudacao': ['oi', 'olá', 'ola', 'hey', 'bom dia', 'boa tarde'],
        }
    
    def detect(self, text: str) -> str:
        """Detecta intenção do usuário"""
        text_lower = text.lower()
        
        # Priorizar análise H2H
        if ' vs ' in text_lower or ' x ' in text_lower:
            return 'analise_jogo'
        
        # Detectar por patterns
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent
        
        return 'desconhecido'


class SuperKnowledgeBase:
    """Base de conhecimento com acesso aos dados"""
    
    def __init__(self, stats_db, calendar_df, referees):
        self.stats = stats_db
        self.cal = calendar_df
        self.refs = referees
    
    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Retorna estatísticas do time"""
        team_norm = normalize_name(team_name, list(self.stats.keys()))
        
        if not team_norm or team_norm not in self.stats:
            return None
        
        return {
            'name': team_norm,
            'stats': self.stats[team_norm],
            'league': self.stats[team_norm]['league'],
            'games': self.stats[team_norm]['games']
        }
    
    def get_games_by_date(self, date_str: str) -> List[Dict]:
        """Retorna jogos de uma data"""
        if self.cal.empty:
            return []
        
        jogos = self.cal[self.cal['DtObj'].dt.strftime('%d/%m/%Y') == date_str]
        games_list = []
        
        for _, jogo in jogos.iterrows():
            h = normalize_name(jogo['Time_Casa'], list(self.stats.keys()))
            a = normalize_name(jogo['Time_Visitante'], list(self.stats.keys()))
            
            if h and a and h in self.stats and a in self.stats:
                games_list.append({
                    'home': h,
                    'away': a,
                    'time': jogo.get('Hora', 'N/A'),
                    'league': self.stats[h]['league'],
                })
        
        return games_list
    
    def get_ranking(self, metric: str, n: int = 10, league: Optional[str] = None) -> List[Dict]:
        """Retorna ranking de uma métrica"""
        data = []
        
        for team, stats in self.stats.items():
            if league and stats['league'] != league:
                continue
            
            data.append({
                'time': team,
                'valor': stats.get(metric, 0),
                'liga': stats['league']
            })
        
        return sorted(data, key=lambda x: x['valor'], reverse=True)[:n]


class SuperResponseGenerator:
    """Gerador de respostas naturais"""
    
    def __init__(self, kb):
        self.kb = kb
    
    def team_stats(self, team_name: str) -> str:
        """Resposta com estatísticas do time"""
        data = self.kb.get_team_stats(team_name)
        
        if not data:
            similares = get_close_matches(team_name, list(self.kb.stats.keys()), n=3, cutoff=0.5)
            if similares:
                return f"❌ Time '{team_name}' não encontrado.\n\n💡 Você quis dizer: {', '.join(similares)}?"
            return f"❌ Time '{team_name}' não encontrado."
        
        s = data['stats']
        
        return f"""📊 **ESTATÍSTICAS COMPLETAS - {data['name']}**

🏟️ **INFORMAÇÕES GERAIS:**
• Liga: **{data['league']}**
• Jogos: **{data['games']}**

⚽ **ATAQUE:**
• Gols: **{s['goals_f']:.2f}** por jogo
• Chutes no Gol: **{s['shots_on_target']:.1f}** por jogo

🔶 **ESCANTEIOS:**
• Média: **{s['corners']:.1f}** por jogo
• Casa: **{s['corners_home']:.1f}** | Fora: **{s['corners_away']:.1f}**

🟨 **DISCIPLINA:**
• Cartões: **{s['cards']:.1f}** por jogo
• Faltas: **{s['fouls']:.1f}** por jogo
• Vermelhos: **{s['red_cards_avg']:.2f}** por jogo"""
    
    def games_list(self, date_str: str) -> str:
        """Lista de jogos"""
        games = self.kb.get_games_by_date(date_str)
        
        if not games:
            return f"📅 Não encontrei jogos para {date_str}"
        
        response = f"⚽ **JOGOS DE {date_str}:** ({len(games)} partidas)\n\n"
        
        for i, g in enumerate(games, 1):
            calc = calcular_jogo_v31(self.kb.stats[g['home']], self.kb.stats[g['away']])
            response += f"**{i}. {g['home']} vs {g['away']}**\n"
            response += f"   🕐 {g['time']} | 🏆 {g['league']}\n"
            response += f"   📊 Cantos: {calc['corners']['t']:.1f} | Cartões: {calc['cards']['t']:.1f}\n\n"
        
        return response
    
    def head_to_head(self, team1: str, team2: str) -> str:
        """Análise H2H"""
        t1 = normalize_name(team1, list(self.kb.stats.keys()))
        t2 = normalize_name(team2, list(self.kb.stats.keys()))
        
        if not t1 or not t2 or t1 not in self.kb.stats or t2 not in self.kb.stats:
            return f"❌ Times não encontrados"
        
        calc = calcular_jogo_v31(self.kb.stats[t1], self.kb.stats[t2])
        meta = calc['metadata']
        
        return f"""🎯 **ANÁLISE: {t1} vs {t2}**

⚽ **EXPECTED GOALS (xG):**
• {t1}: **{calc['goals']['h']:.2f}**
• {t2}: **{calc['goals']['a']:.2f}**

🔶 **ESCANTEIOS PREVISTOS:**
• {t1}: **{calc['corners']['h']:.1f}**
• {t2}: **{calc['corners']['a']:.1f}**
• **TOTAL: {calc['corners']['t']:.1f}**

🟨 **CARTÕES PREVISTOS:**
• {t1}: **{calc['cards']['h']:.1f}**
• {t2}: **{calc['cards']['a']:.1f}**
• **TOTAL: {calc['cards']['t']:.1f}**

🎯 **FATORES CHAVE:**
• Boost Chutes {t1}: **{meta['pressure_home']:.2f}x** {get_prob_emoji(meta['pressure_home']*70)}
• Violência {t1}: **{"SIM" if meta['violence_home'] else "NÃO"}**
• Violência {t2}: **{"SIM" if meta['violence_away'] else "NÃO"}**
• Prob. Vermelho: **{meta['prob_red_card']:.1f}%**"""
    
    def ranking(self, metric: str, title: str, n: int = 10) -> str:
        """Gera ranking"""
        data = self.kb.get_ranking(metric, n)
        
        response = f"📊 **TOP {n} - {title.upper()}:**\n\n"
        
        for i, item in enumerate(data, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            response += f"{emoji} **{i}. {item['time']}** - {item['valor']:.2f}\n"
        
        return response


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    """Aplicação principal"""
    
    # Carregar dados
    stats, cal, referees = load_all_data()
    
    # Inicializar session state
    if 'current_ticket' not in st.session_state:
        st.session_state.current_ticket = []
    if 'bet_results' not in st.session_state:
        st.session_state.bet_results = []
    if 'bankroll_history' not in st.session_state:
        st.session_state.bankroll_history = [1000.0]
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Header
    st.title("⚽ FutPrevisão V31 MAXIMUM + SUPERBOT V2.0")
    st.markdown("**Sistema Completo com IA - Project Edition**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Dashboard")
        st.metric("Times", len(stats))
        st.metric("Jogos", len(cal) if not cal.empty else 0)
        st.metric("Árbitros", len(referees))
        st.metric("Banca", format_currency(st.session_state.bankroll_history[-1]))
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎫 Construtor", "🎲 Simulador", "📊 Rankings", "🎨 Viz", "🤖 AI Bot"
    ])
    
    # ============================================================
    # TAB 1: CONSTRUTOR
    # ============================================================
    
    with tab1:
        st.header("🎫 Construtor de Bilhetes")
        
        if not cal.empty:
            dates = sorted(cal['DtObj'].dt.strftime('%d/%m/%Y').unique())
            sel_date = st.selectbox("📅 Selecione a data:", dates, key='c_date')
            jogos_dia = cal[cal['DtObj'].dt.strftime('%d/%m/%Y') == sel_date]
            
            st.markdown(f"### {len(jogos_dia)} jogo(s) encontrado(s)")
            
            for idx, jogo in jogos_dia.iterrows():
                h = normalize_name(jogo['Time_Casa'], list(stats.keys()))
                a = normalize_name(jogo['Time_Visitante'], list(stats.keys()))
                
                if h and a and h in stats and a in stats:
                    calc = calcular_jogo_v31(stats[h], stats[a])
                    
                    with st.expander(f"⚽ **{h}** vs **{a}**", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric("xG Casa", f"{calc['goals']['h']:.2f}")
                        col2.metric("xG Fora", f"{calc['goals']['a']:.2f}")
                        col3.metric("Cantos Total", f"{calc['corners']['t']:.1f}")
                        col4.metric("Cartões Total", f"{calc['cards']['t']:.1f}")
                        
                        st.markdown("---")
                        
                        # Métricas detalhadas
                        meta = calc['metadata']
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.markdown("**🏠 Casa:**")
                            st.write(f"• Chutes: {meta['shots_home']:.1f}")
                            st.write(f"• Boost: {meta['pressure_home']:.2f}x")
                            st.write(f"• Violento: {'✅' if meta['violence_home'] else '❌'}")
                        
                        with col_b:
                            st.markdown("**✈️ Fora:**")
                            st.write(f"• Chutes: {meta['shots_away']:.1f}")
                            st.write(f"• Boost: {meta['pressure_away']:.2f}x")
                            st.write(f"• Violento: {'✅' if meta['violence_away'] else '❌'}")
                        
                        if meta['prob_red_card'] > 10:
                            st.warning(f"🔴 **Probabilidade de Vermelho: {meta['prob_red_card']:.1f}%**")
                        
                        if st.button("➕ Adicionar ao Bilhete", key=f"add_{idx}"):
                            st.session_state.current_ticket.append({
                                'jogo': f"{h} vs {a}",
                                'cantos': calc['corners']['t'],
                                'cartoes': calc['cards']['t']
                            })
                            st.success("✅ Adicionado!")
                            st.rerun()
        else:
            st.warning("⚠️ Calendário não carregado")
        
        # Bilhete atual
        st.markdown("---")
        st.subheader("📋 Bilhete Atual")
        
        if st.session_state.current_ticket:
            st.success(f"✅ **{len(st.session_state.current_ticket)} seleção(ões)**")
            
            for i, sel in enumerate(st.session_state.current_ticket):
                col1, col2 = st.columns([5, 1])
                col1.write(f"**{i+1}.** {sel['jogo']}")
                if col2.button("🗑️", key=f"del_{i}"):
                    st.session_state.current_ticket.pop(i)
                    st.rerun()
            
            col_a, col_b = st.columns(2)
            
            if col_a.button("🗑️ LIMPAR TUDO", use_container_width=True):
                st.session_state.current_ticket = []
                st.rerun()
            
            if col_b.button("📊 ANALISAR", use_container_width=True):
                st.info("Análise em desenvolvimento...")
        else:
            st.info("📭 Bilhete vazio. Adicione jogos acima.")
    
    # ============================================================
    # TAB 2: SIMULADOR
    # ============================================================
    
    with tab2:
        st.header("🎲 Simulador Monte Carlo")
        
        if not cal.empty:
            dates = sorted(cal['DtObj'].dt.strftime('%d/%m/%Y').unique())
            sel_date = st.selectbox("📅 Data:", dates, key='sim_date')
            jogos_dia = cal[cal['DtObj'].dt.strftime('%d/%m/%Y') == sel_date]
            
            jogos_disp = []
            for _, jogo in jogos_dia.iterrows():
                h = normalize_name(jogo['Time_Casa'], list(stats.keys()))
                a = normalize_name(jogo['Time_Visitante'], list(stats.keys()))
                if h and a:
                    jogos_disp.append(f"{h} vs {a}")
            
            if jogos_disp:
                jogo_sel = st.selectbox("⚽ Selecione o jogo:", jogos_disp)
                n_sims = st.slider("Simulações:", 1000, 10000, 3000, step=1000)
                
                if st.button("🎲 SIMULAR", use_container_width=True):
                    with st.spinner("Simulando..."):
                        h_name, a_name = jogo_sel.split(' vs ')
                        sims = simulate_game_v31(stats[h_name], stats[a_name], None, n_sims)
                        
                        st.success(f"✅ {n_sims} simulações concluídas!")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        col1.metric("Cantos Médio", f"{sims['corners_total'].mean():.1f}")
                        col2.metric("Cartões Médio", f"{sims['cards_total'].mean():.1f}")
                        col3.metric("Gols Total Médio", f"{(sims['goals_h'] + sims['goals_a']).mean():.1f}")
                        
                        # Gráficos
                        st.markdown("### 📊 Distribuições")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Histogram(x=sims['corners_total'], name='Cantos', nbinsx=20))
                        fig.update_layout(title='Distribuição de Cantos', xaxis_title='Cantos', yaxis_title='Frequência')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem jogos disponíveis")
        else:
            st.warning("Calendário não carregado")
    
    # ============================================================
    # TAB 3: RANKINGS
    # ============================================================
    
    with tab3:
        st.header("📊 Rankings das Ligas")
        
        metric_map = {
            "🔶 Escanteios": "corners",
            "🟨 Cartões": "cards",
            "⚽ Gols Marcados": "goals_f",
            "🛡️ Gols Sofridos": "goals_a",
            "🎯 Chutes no Gol": "shots_on_target"
        }
        
        sel_metric = st.selectbox("Selecione a métrica:", list(metric_map.keys()))
        n_teams = st.slider("Top N times:", 5, 30, 15)
        
        metric_key = metric_map[sel_metric]
        
        times_sorted = sorted(stats.items(), key=lambda x: x[1][metric_key], reverse=True)[:n_teams]
        
        st.markdown(f"### {sel_metric}")
        
        for i, (team, team_stats) in enumerate(times_sorted, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            valor = team_stats[metric_key]
            liga = team_stats['league']
            
            col1, col2, col3 = st.columns([1, 4, 1])
            col1.write(f"{emoji} **{i}**")
            col2.write(f"**{team}** ({liga})")
            col3.write(f"**{valor:.2f}**")
    
    # ============================================================
    # TAB 4: VISUALIZAÇÕES
    # ============================================================
    
    with tab4:
        st.header("🎨 Visualizações Avançadas")
        
        viz_type = st.selectbox("Tipo de visualização:", [
            "Top 20 - Cantos",
            "Top 20 - Cartões",
            "Top 20 - Gols",
            "Comparação por Liga"
        ])
        
        if viz_type == "Top 20 - Cantos":
            times_sorted = sorted(stats.items(), key=lambda x: x[1]['corners'], reverse=True)[:20]
            
            nomes = [t[0] for t in times_sorted]
            valores = [t[1]['corners'] for t in times_sorted]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=nomes,
                x=valores,
                orientation='h',
                marker=dict(
                    color=valores,
                    colorscale='Oranges',
                    showscale=True
                )
            ))
            fig.update_layout(
                title='Top 20 Times - Escanteios por Jogo',
                xaxis_title='Escanteios',
                yaxis_title='Time',
                height=700
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif viz_type == "Top 20 - Cartões":
            times_sorted = sorted(stats.items(), key=lambda x: x[1]['cards'], reverse=True)[:20]
            
            nomes = [t[0] for t in times_sorted]
            valores = [t[1]['cards'] for t in times_sorted]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=nomes,
                x=valores,
                orientation='h',
                marker=dict(
                    color=valores,
                    colorscale='Reds',
                    showscale=True
                )
            ))
            fig.update_layout(
                title='Top 20 Times - Cartões por Jogo',
                xaxis_title='Cartões',
                yaxis_title='Time',
                height=700
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ============================================================
    # TAB 5: SUPERBOT V2.0
    # ============================================================
    
    with tab5:
        st.header("🤖 FutPrevisão AI Advisor SUPERBOT V2.0")
        st.caption("_Inteligência Artificial com acesso aos dados do projeto_")
        
        # Inicializar componentes do bot
        if 'super_intent' not in st.session_state:
            st.session_state.super_intent = SuperIntentDetector()
        
        if 'super_kb' not in st.session_state:
            st.session_state.super_kb = SuperKnowledgeBase(stats, cal, referees)
        
        if 'super_responder' not in st.session_state:
            st.session_state.super_responder = SuperResponseGenerator(st.session_state.super_kb)
        
        # Mensagem de boas-vindas
        if not st.session_state.chat_history:
            hoje = datetime.now().strftime('%d/%m/%Y')
            welcome = f"""👋 **Olá! Sou o FutPrevisão SUPERBOT V2.0!**

📅 Hoje é **{hoje}**

🧠 **Tenho acesso a:**
• **{len(stats)}** times de **10 ligas**
• **{len(cal) if not cal.empty else 0}** jogos no calendário
• **{len(referees)}** árbitros

💬 **Exemplos de perguntas:**
• "Como está o Arsenal?"
• "Analisa Arsenal vs Chelsea"
• "Top 10 times com mais cantos"
• "Jogos de hoje"

**Fique à vontade para perguntar! 👇**"""
            
            st.session_state.chat_history.append({'role': 'assistant', 'content': welcome})
        
        # Botões rápidos
        st.markdown("### ⚡ Ações Rápidas:")
        col1, col2, col3, col4 = st.columns(4)
        
        if col1.button("🎯 Jogos Hoje", use_container_width=True):
            hoje = datetime.now().strftime('%d/%m/%Y')
            st.session_state.chat_history.append({'role': 'user', 'content': 'Jogos hoje'})
            st.rerun()
        
        if col2.button("🔶 Top Cantos", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': 'Top 10 cantos'})
            st.rerun()
        
        if col3.button("🟨 Top Cartões", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': 'Top 10 cartões'})
            st.rerun()
        
        if col4.button("🗑️ Limpar", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        
        # Exibir histórico do chat
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.chat_message("user", avatar="👤").markdown(msg['content'])
            else:
                st.chat_message("assistant", avatar="🤖").markdown(msg['content'])
        
        # Input do usuário
        user_input = st.chat_input("Digite sua pergunta...")
        
        if user_input:
            # Adicionar mensagem do usuário
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Detectar intenção
            intent = st.session_state.super_intent.detect(user_input)
            responder = st.session_state.super_responder
            
            response = ""
            
            try:
                if intent == 'stats_time':
                    # Extrair nome do time
                    teams = []
                    for team in stats.keys():
                        if team.lower() in user_input.lower():
                            teams.append(team)
                    
                    if teams:
                        response = responder.team_stats(teams[0])
                    else:
                        response = "⚠️ Time não identificado. Por favor, seja mais específico."
                
                elif intent in ['jogos_hoje', 'jogos_amanha']:
                    hoje = datetime.now()
                    if intent == 'jogos_amanha':
                        hoje = hoje + timedelta(days=1)
                    date_str = hoje.strftime('%d/%m/%Y')
                    response = responder.games_list(date_str)
                
                elif intent == 'analise_jogo':
                    # Extrair times
                    teams = []
                    for team in stats.keys():
                        if team.lower() in user_input.lower():
                            teams.append(team)
                    
                    if len(teams) >= 2:
                        response = responder.head_to_head(teams[0], teams[1])
                    else:
                        response = "⚠️ Preciso de dois times para fazer a análise. Ex: 'Arsenal vs Chelsea'"
                
                elif intent == 'ranking_cantos':
                    response = responder.ranking('corners', 'Escanteios', 10)
                
                elif intent == 'ranking_cartoes':
                    response = responder.ranking('cards', 'Cartões', 10)
                
                elif intent == 'ranking_gols':
                    response = responder.ranking('goals_f', 'Gols Marcados', 10)
                
                elif intent == 'saudacao':
                    response = "👋 Olá! Como posso ajudar você hoje?"
                
                else:
                    response = """🤔 Não entendi perfeitamente sua pergunta...

💡 **Tente perguntar:**
• "Como está o [time]?"
• "Analisa [time 1] vs [time 2]"
• "Top 10 cantos"
• "Jogos de hoje"
• "Ranking de cartões"
"""
            
            except Exception as e:
                response = f"❌ Erro ao processar: {str(e)}"
            
            # Adicionar resposta
            st.session_state.chat_history.append({'role': 'assistant', 'content': response})
            st.rerun()


if __name__ == "__main__":
    main()
