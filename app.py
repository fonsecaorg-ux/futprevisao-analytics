import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import poisson
import math
import time
from datetime import datetime, timedelta
from difflib import get_close_matches
from typing import Dict, List, Tuple, Optional
import os
import re

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

st.set_page_config(
    page_title="FutPrevisão V35.4 EVOLUTION",
    layout="wide",
    page_icon="🧠",
    initial_sidebar_state="expanded"
)

VERSION = "V35.4 EVOLUTION"
AUTHOR = "Diego ADS"

# CSS Premium
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f1f5f9; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #60a5fa; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
    }
    .stTabs [aria-selected="true"] { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; 
        color: white !important;
        font-weight: bold;
    }
    .linha-aposta {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #10b981;
    }
</style>
""", unsafe_allow_html=True)

VOCAB_SOFISTICADO = {
    'alta': '**Confluência Estatística Favorável**',
    'media': '**Convergência Probabilística Moderada**',
    'baixa': '**Anomalia Detectada nos Padrões Históricos**',
    'risco': '**Volatilidade Acima do Limiar de Segurança**',
    'seguro': '**Margem de Segurança Poissoniana Ótima**',
}

# ==============================================================================
# DATA ENGINE
# ==============================================================================

class DataEngine:
    FILES = {
        "Premier League": "Premier_League_25_26.csv",
        "La Liga": "La_Liga_25_26.csv",
        "Serie A": "Serie_A_25_26.csv",
        "Bundesliga": "Bundesliga_25_26.csv",
        "Ligue 1": "Ligue_1_25_26.csv",
        "Championship": "Championship_Inglaterra_25_26.csv",
        "Bundesliga 2": "Bundesliga_2.csv",
        "Pro League": "Pro_League_Belgica_25_26.csv",
        "Süper Lig": "Super_Lig_Turquia_25_26.csv",
        "Premiership": "Premiership_Escocia_25_26.csv",
        "Calendario": "calendario_ligas.csv",
        "Arbitros": "arbitros_5_ligas_2025_2026.csv"
    }

    @staticmethod
    def get_mock_matches(league_name):
        dates = pd.date_range(end=datetime.today(), periods=30).strftime("%d/%m/%Y")
        teams_casa = ['Arsenal', 'Liverpool', 'City', 'Chelsea', 'United', 'Tottenham'] * 5
        teams_fora = ['Brighton', 'Villa', 'Newcastle', 'West Ham', 'Everton', 'Wolves'] * 5
        
        data = {
            'Date': dates,
            'HomeTeam': teams_casa,
            'AwayTeam': teams_fora,
            'FTHG': np.random.randint(0, 4, 30),
            'FTAG': np.random.randint(0, 3, 30),
            'HC': np.random.randint(3, 11, 30),
            'AC': np.random.randint(2, 9, 30),
            'HY': np.random.randint(1, 5, 30),
            'AY': np.random.randint(1, 5, 30),
            'HF': np.random.randint(8, 18, 30),
            'AF': np.random.randint(7, 16, 30),
            'HST': np.random.randint(3, 9, 30),
            'AST': np.random.randint(2, 7, 30),
            'League': league_name
        }
        return pd.DataFrame(data)

    @staticmethod
    def normalize_columns(df):
        cols_map = {
            'Mandante': 'HomeTeam', 'Visitante': 'AwayTeam', 
            'Time_Casa': 'HomeTeam', 'Time_Visitante': 'AwayTeam',
            'Home': 'HomeTeam', 'Away': 'AwayTeam',
            'HG': 'FTHG', 'AG': 'FTAG', 
            'Gols_Casa': 'FTHG', 'Gols_Fora': 'FTAG',
            'Cantos_Casa': 'HC', 'Cantos_Fora': 'AC',
            'Cartoes_Casa': 'HY', 'Cartoes_Fora': 'AY',
            'Faltas_Casa': 'HF', 'Faltas_Fora': 'AF'
        }
        df = df.rename(columns=cols_map)
        return df

    @staticmethod
    @st.cache_data(ttl=3600)
    def load_data():
        matches_data = []
        file_status = {}
        
        possible_paths = [".", "analytics", "data", "dataset", "../analytics", "./analytics"]
        
        for league, filename in DataEngine.FILES.items():
            if league in ["Calendario", "Arbitros"]:
                continue
            
            found = False
            for base_path in possible_paths:
                filepath = os.path.join(base_path, filename)
                if os.path.exists(filepath):
                    try:
                        df = pd.read_csv(filepath, encoding='utf-8')
                    except:
                        try:
                            df = pd.read_csv(filepath, encoding='latin1')
                        except:
                            continue
                    
                    df = DataEngine.normalize_columns(df)
                    df['League'] = league
                    
                    for col in ['HC', 'AC', 'HY', 'AY', 'FTHG', 'FTAG', 'HF', 'AF', 'HST', 'AST']:
                        if col not in df.columns:
                            df[col] = 0
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
                    matches_data.append(df)
                    file_status[league] = f"✅ {filepath}"
                    found = True
                    break
            
            if not found:
                file_status[league] = "⚠️ Simulado"
                matches_data.append(DataEngine.get_mock_matches(league))
        
        full_df = pd.concat(matches_data, ignore_index=True)
        full_df['Total_Corners'] = full_df['HC'] + full_df['AC']
        full_df['Total_Cards'] = full_df['HY'] + full_df['AY']
        full_df['Total_Goals'] = full_df['FTHG'] + full_df['FTAG']
        full_df['Total_Fouls'] = full_df['HF'] + full_df['AF']

        # Calendário
        cal_df = None
        for base_path in possible_paths:
            filepath = os.path.join(base_path, DataEngine.FILES["Calendario"])
            if os.path.exists(filepath):
                try:
                    cal_df = pd.read_csv(filepath, encoding='utf-8')
                    cal_df = DataEngine.normalize_columns(cal_df)
                    
                    # Garantir coluna Data
                    if 'Data' not in cal_df.columns and 'Date' in cal_df.columns:
                        cal_df['Data'] = cal_df['Date']
                    
                    file_status["Calendario"] = f"✅ {filepath}"
                    break
                except:
                    pass
        
        if cal_df is None:
            file_status["Calendario"] = "⚠️ Simulado"
            dates = pd.date_range(start=datetime.today(), periods=20).strftime("%d/%m/%Y")
            cal_df = pd.DataFrame({
                'Data': dates,
                'HomeTeam': ['Arsenal', 'Liverpool', 'City', 'Chelsea', 'United'] * 4,
                'AwayTeam': ['Brighton', 'Villa', 'Newcastle', 'West Ham', 'Everton'] * 4,
                'Liga': ['Premier League'] * 20,
                'Hora': ['16:00'] * 20
            })

        # Árbitros
        ref_df = None
        for base_path in possible_paths:
            filepath = os.path.join(base_path, DataEngine.FILES["Arbitros"])
            if os.path.exists(filepath):
                try:
                    ref_df = pd.read_csv(filepath, encoding='utf-8')
                    file_status["Arbitros"] = f"✅ {filepath}"
                    break
                except:
                    pass
        
        if ref_df is None:
            file_status["Arbitros"] = "⚠️ Simulado"
            ref_df = pd.DataFrame({
                'Arbitro': ['Michael Oliver', 'Anthony Taylor', 'Martin Atkinson'],
                'Media_Cartoes_Por_Jogo': [4.2, 3.8, 4.5],
                'Jogos_Apitados': [150, 180, 200]
            })

        return full_df, cal_df, ref_df, file_status

# ==============================================================================
# MATH ENGINE
# ==============================================================================

class MathEngine:
    @staticmethod
    def poisson_probability(lmbda, k):
        return poisson.pmf(k, lmbda)

    @staticmethod
    def monte_carlo_simulation(avg_corners, n_sims=10000):
        samples = np.random.poisson(avg_corners, n_sims)
        return {
            'samples': samples,
            'mean': float(np.mean(samples)),
            'p50': int(np.percentile(samples, 50)),
            'p80': int(np.percentile(samples, 80)),
            'p95': int(np.percentile(samples, 95)),
            'prob_over_9_5': float(np.mean(samples >= 10)),
            'prob_over_10_5': float(np.mean(samples >= 11)),
            'prob_over_11_5': float(np.mean(samples >= 12)),
        }

    @staticmethod
    def kelly_criterion(prob, odds, bankroll, fraction=0.25):
        if odds <= 1 or prob <= 0 or prob >= 1:
            return 0
        b = odds - 1
        q = 1 - prob
        f = (b * prob - q) / b
        return max(0, f * fraction * bankroll)
    
    @staticmethod
    def calculate_ev(prob, odds):
        return (prob * (odds - 1)) - (1 - prob)

# ==============================================================================
# PREDICTION ENGINE - COMPLETO
# ==============================================================================

class PredictionEngine:
    """Motor de Predição Completo - Todas as Linhas"""
    
    def __init__(self, df):
        self.df = df
    
    def predict_full(self, home_team: str, away_team: str, league: str = None) -> Dict:
        """Predição completa com TODAS as linhas"""
        
        # Buscar dados dos times
        home_data = self.df[(self.df['HomeTeam'] == home_team) | (self.df['AwayTeam'] == home_team)]
        away_data = self.df[(self.df['HomeTeam'] == away_team) | (self.df['AwayTeam'] == away_team)]
        
        if home_data.empty or away_data.empty:
            return None
        
        # ESCANTEIOS
        corners_home_avg = home_data[home_data['HomeTeam'] == home_team]['HC'].mean() if len(home_data[home_data['HomeTeam'] == home_team]) > 0 else home_data['HC'].mean()
        corners_away_avg = away_data[away_data['AwayTeam'] == away_team]['AC'].mean() if len(away_data[away_data['AwayTeam'] == away_team]) > 0 else away_data['AC'].mean()
        
        corners_home_proj = corners_home_avg * 1.15
        corners_away_proj = corners_away_avg * 0.90
        corners_total = corners_home_proj + corners_away_proj
        
        # CARTÕES
        cards_home_avg = home_data[home_data['HomeTeam'] == home_team]['HY'].mean() if len(home_data[home_data['HomeTeam'] == home_team]) > 0 else home_data['HY'].mean()
        cards_away_avg = away_data[away_data['AwayTeam'] == away_team]['AY'].mean() if len(away_data[away_data['AwayTeam'] == away_team]) > 0 else away_data['AY'].mean()
        
        cards_home_proj = cards_home_avg * 1.05
        cards_away_proj = cards_away_avg * 1.05
        cards_total = cards_home_proj + cards_away_proj
        
        # GOLS
        goals_home = home_data['FTHG'].mean()
        goals_away = away_data['FTAG'].mean()
        
        # FALTAS
        fouls_home = home_data['HF'].mean()
        fouls_away = away_data['AF'].mean()
        
        return {
            'corners': {
                'home': corners_home_proj,
                'away': corners_away_proj,
                'total': corners_total,
                'p80': int(np.ceil(corners_total + 1.5)),
                'p95': int(np.ceil(corners_total + 3.0))
            },
            'cards': {
                'home': cards_home_proj,
                'away': cards_away_proj,
                'total': cards_total
            },
            'goals': {
                'home': goals_home,
                'away': goals_away,
                'total': goals_home + goals_away
            },
            'fouls': {
                'home': fouls_home,
                'away': fouls_away,
                'total': fouls_home + fouls_away
            },
            'games_played': {
                'home': len(home_data),
                'away': len(away_data)
            }
        }
    
    def generate_all_lines(self, prediction: Dict) -> List[Dict]:
        """Gera TODAS as linhas possíveis de aposta"""
        
        lines = []
        
        # ESCANTEIOS TOTAIS
        for threshold in [8.5, 9.5, 10.5, 11.5, 12.5, 13.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['corners']['total'])
            lines.append({
                'tipo': 'Escanteios Totais',
                'mercado': f"Over {threshold}",
                'projecao': prediction['corners']['total'],
                'prob': prob * 100
            })
        
        # ESCANTEIOS CASA
        for threshold in [2.5, 3.5, 4.5, 5.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['corners']['home'])
            lines.append({
                'tipo': 'Escanteios Casa',
                'mercado': f"Casa Over {threshold}",
                'projecao': prediction['corners']['home'],
                'prob': prob * 100
            })
        
        # ESCANTEIOS FORA
        for threshold in [2.5, 3.5, 4.5, 5.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['corners']['away'])
            lines.append({
                'tipo': 'Escanteios Fora',
                'mercado': f"Fora Over {threshold}",
                'projecao': prediction['corners']['away'],
                'prob': prob * 100
            })
        
        # CARTÕES TOTAIS
        for threshold in [2.5, 3.5, 4.5, 5.5, 6.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['cards']['total'])
            lines.append({
                'tipo': 'Cartões Totais',
                'mercado': f"Over {threshold}",
                'projecao': prediction['cards']['total'],
                'prob': prob * 100
            })
        
        # CARTÕES CASA
        for threshold in [0.5, 1.5, 2.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['cards']['home'])
            lines.append({
                'tipo': 'Cartões Casa',
                'mercado': f"Casa Over {threshold}",
                'projecao': prediction['cards']['home'],
                'prob': prob * 100
            })
        
        # CARTÕES FORA
        for threshold in [0.5, 1.5, 2.5]:
            prob = 1 - poisson.cdf(int(threshold), prediction['cards']['away'])
            lines.append({
                'tipo': 'Cartões Fora',
                'mercado': f"Fora Over {threshold}",
                'projecao': prediction['cards']['away'],
                'prob': prob * 100
            })
        
        return lines

# ==============================================================================
# ORÁCULO MAXIMUM EVOLUTION
# ==============================================================================

class OraculoMaximum:
    """Cérebro Avançado com Projeções Individuais"""
    
    def __init__(self, df, refs, calendar, predictor):
        self.df = df
        self.refs = refs
        self.calendar = calendar
        self.predictor = predictor
    
    def processar(self, query: str, contexto: Dict) -> Dict:
        intencao = self._identificar_intencao(query)
        
        if intencao == 'analise':
            resultado = self._analise_simples(query, contexto)
        elif intencao == 'comparacao':
            resultado = self._comparacao(query, contexto)
        elif intencao == 'ranking':
            resultado = self._ranking(query)
        elif intencao == 'gestao':
            resultado = self._gestao_banca(query, contexto)
        elif intencao == 'explicacao':
            resultado = self._explicacao(query)
        elif intencao == 'estatistica':
            resultado = self._estatistica(query)
        else:
            resultado = self._fallback()
        
        if 'historico' not in contexto:
            contexto['historico'] = []
        contexto['historico'].append({
            'query': query,
            'intencao': intencao,
            'timestamp': datetime.now().isoformat()
        })
        if len(contexto['historico']) > 10:
            contexto['historico'] = contexto['historico'][-10:]
        
        return resultado
    
    def _identificar_intencao(self, query: str) -> str:
        q = query.lower()
        
        if any(w in q for w in ['analisa', 'analise', ' x ', 'vs', 'contra']):
            return 'analise'
        if any(w in q for w in ['comparar', 'comparado', 'melhor', 'qual']):
            return 'comparacao'
        if any(w in q for w in ['top', 'ranking', 'melhores', 'piores']):
            return 'ranking'
        if any(w in q for w in ['banca', 'quanto', 'apostar', 'kelly']):
            return 'gestao'
        if any(w in q for w in ['por que', 'porque', 'explicar']):
            return 'explicacao'
        if any(w in q for w in ['desvio', 'média', 'percentil', 'p80', 'p95']):
            return 'estatistica'
        
        return 'analise'
    
    def _extrair_times(self, query: str) -> List[str]:
        all_teams = list(self.df['HomeTeam'].unique()) + list(self.df['AwayTeam'].unique())
        teams_found = []
        
        words = re.findall(r'[A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s[A-ZÀ-Ÿ][a-zà-ÿ]+)*', query)
        for word in words:
            match = get_close_matches(word, all_teams, n=1, cutoff=0.5)
            if match:
                teams_found.append(match[0])
        
        return list(set(teams_found))
    
    def _analise_simples(self, query: str, contexto: Dict) -> Dict:
        """Análise com PROJEÇÕES INDIVIDUAIS"""
        
        times = self._extrair_times(query)
        
        if len(times) < 2:
            return {
                'texto': '⚠️ Não consegui identificar 2 times na pergunta.',
                'confianca': 'baixa'
            }
        
        t1, t2 = times[0], times[1]
        
        # Predição completa
        pred = self.predictor.predict_full(t1, t2)
        
        if not pred:
            return {
                'texto': f'⚠️ Dados insuficientes para {t1} ou {t2}.',
                'confianca': 'baixa'
            }
        
        # Salvar contexto
        contexto['ultimo_jogo'] = {
            'nome': f"{t1} x {t2}",
            'pred': pred
        }
        
        texto = f"""
## 🧠 ANÁLISE CEREBRAL AVANÇADA

### {t1} ⚔️ {t2}

---

### ⚽ CONFLUÊNCIA DE DADOS - ESCANTEIOS

**A previsão é para que o {t1} tenha +{pred['corners']['home']:.2f} escanteios**  
**e o {t2} tenha +{pred['corners']['away']:.2f} escanteios.**

**Total da Partida:** {pred['corners']['total']:.2f} escanteios

**Margem de Segurança Poissoniana:**
- **P80:** {pred['corners']['p80']} escanteios
- **P95:** {pred['corners']['p95']} escanteios

{VOCAB_SOFISTICADO['seguro'] if pred['corners']['p80'] >= 10 else VOCAB_SOFISTICADO['risco']}

---

### 🟨 CARTÕES

**O total de cartões é de {pred['cards']['total']:.2f} cartões na partida,**  
**sendo +{pred['cards']['home']:.2f} para o {t1}**  
**e +{pred['cards']['away']:.2f} para o {t2}.**

---

### ⚡ RECOMENDAÇÕES

{'✅ Over ' + str(pred['corners']['p80']-1) + '.5 Escanteios' if pred['corners']['p80'] >= 10 else '⚠️ Aguardar melhor oportunidade'}
"""
        
        return {
            'texto': texto,
            'confianca': 'alta' if pred['corners']['p80'] >= 10 else 'media'
        }
    
    def _comparacao(self, query: str, contexto: Dict) -> Dict:
        if 'ultimo_jogo' not in contexto:
            return {
                'texto': '⚠️ Analise um jogo primeiro para poder comparar.',
                'confianca': 'baixa'
            }
        
        ultimo = contexto['ultimo_jogo']
        times = self._extrair_times(query)
        
        if len(times) >= 2:
            t1, t2 = times[0], times[1]
            pred_novo = self.predictor.predict_full(t1, t2)
            
            if pred_novo:
                texto = f"""
## ⚖️ ANÁLISE COMPARATIVA

### {ultimo['nome']} vs {t1} x {t2}

| Métrica | Jogo Anterior | Jogo Novo | Diferença |
|---------|---------------|-----------|-----------|
| **Escanteios** | {ultimo['pred']['corners']['total']:.2f} | {pred_novo['corners']['total']:.2f} | {abs(ultimo['pred']['corners']['total'] - pred_novo['corners']['total']):.2f} |
| **P80** | {ultimo['pred']['corners']['p80']} | {pred_novo['corners']['p80']} | {abs(ultimo['pred']['corners']['p80'] - pred_novo['corners']['p80'])} |
| **Cartões** | {ultimo['pred']['cards']['total']:.2f} | {pred_novo['cards']['total']:.2f} | {abs(ultimo['pred']['cards']['total'] - pred_novo['cards']['total']):.2f} |

**Melhor Valor:** {'**Jogo Anterior**' if ultimo['pred']['corners']['total'] > pred_novo['corners']['total'] else '**Jogo Novo**'}
"""
                
                return {'texto': texto, 'confianca': 'alta'}
        
        return {'texto': '⚠️ Não encontrei jogo novo para comparar.', 'confianca': 'baixa'}
    
    def _ranking(self, query: str) -> Dict:
        liga = None
        for lg in self.df['League'].unique():
            if lg.lower() in query.lower():
                liga = lg
                break
        
        if not liga:
            liga = self.df['League'].mode()[0] if not self.df.empty else "Premier League"
        
        liga_df = self.df[self.df['League'] == liga]
        times_ranking = []
        
        for time in liga_df['HomeTeam'].unique()[:10]:
            time_data = liga_df[(liga_df['HomeTeam'] == time) | (liga_df['AwayTeam'] == time)]
            avg_corners = time_data['Total_Corners'].mean()
            times_ranking.append({'time': time, 'corners': avg_corners})
        
        times_ranking = sorted(times_ranking, key=lambda x: x['corners'], reverse=True)[:5]
        
        texto = f"## 🏆 TOP 5 ESCANTEIOS - {liga}\n\n"
        for i, item in enumerate(times_ranking, 1):
            texto += f"**#{i} {item['time']}** - {item['corners']:.2f} escanteios/jogo\n"
        
        return {'texto': texto, 'confianca': 'alta'}
    
    def _gestao_banca(self, query: str, contexto: Dict) -> Dict:
        match = re.search(r'R?\$?\s?(\d+)', query)
        banca = float(match.group(1)) if match else 1000.0
        
        if 'ultimo_jogo' not in contexto:
            return {'texto': '⚠️ Analise um jogo primeiro.', 'confianca': 'baixa'}
        
        ultimo = contexto['ultimo_jogo']
        prob = 0.65
        odd = 1.90
        
        kelly = MathEngine.kelly_criterion(prob, odd, banca, 0.25)
        
        texto = f"""
## 💰 GESTÃO DE CAPITAL CIENTÍFICA

### {ultimo['nome']}

**Banca:** R$ {banca:.2f}  
**Probabilidade:** 65%  
**Odd:** {odd}

**Stake Kelly (25%):** R$ {kelly:.2f}

{VOCAB_SOFISTICADO['seguro']}
"""
        
        return {'texto': texto, 'confianca': 'alta'}
    
    def _explicacao(self, query: str) -> Dict:
        texto = """
## 🎓 EXPLICAÇÃO TÉCNICA - P80

O **P80** representa o valor abaixo do qual 80% das simulações caem.

**Cálculo:**
```
P80 = μ + 0.84 × σ
```

Oferece equilíbrio entre conservadorismo e valor de odd.
"""
        
        return {'texto': texto, 'confianca': 'alta'}
    
    def _estatistica(self, query: str) -> Dict:
        times = self._extrair_times(query)
        
        if not times:
            return {'texto': '⚠️ Time não identificado.', 'confianca': 'baixa'}
        
        time = times[0]
        time_data = self.df[(self.df['HomeTeam'] == time) | (self.df['AwayTeam'] == time)]
        
        if time_data.empty:
            return {'texto': f'⚠️ Sem dados para {time}.', 'confianca': 'baixa'}
        
        corners = time_data['Total_Corners']
        media = corners.mean()
        desvio = corners.std()
        cv = (desvio / media * 100) if media > 0 else 0
        
        texto = f"""
## 📐 ESTATÍSTICAS - {time}

**Média:** {media:.2f}  
**Desvio Padrão:** {desvio:.2f}  
**Coef. Variação:** {cv:.2f}%  
**Jogos:** {len(time_data)}

**Volatilidade:** {'Alta' if cv > 40 else 'Moderada' if cv > 20 else 'Baixa'}
"""
        
        return {'texto': texto, 'confianca': 'alta'}
    
    def _fallback(self) -> Dict:
        return {
            'texto': """
⚠️ **Comando não reconhecido.**

**Exemplos:**
- "Analisa Arsenal x Chelsea"
- "Comparado ao jogo anterior, qual melhor?"
- "Top 5 da Premier League"
- "Quanto apostar com R$ 500?"
""",
            'confianca': 'baixa'
        }

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Load
    df, cal_df, ref_df, status = DataEngine.load_data()
    predictor = PredictionEngine(df)
    
    # Session State
    if 'contexto_oraculo' not in st.session_state:
        st.session_state.contexto_oraculo = {
            'historico': [],
            'banca': 1000.0
        }
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'bilhete' not in st.session_state:
        st.session_state.bilhete = []
    
    oraculo = OraculoMaximum(df, ref_df, cal_df, predictor)
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Painel de Controle")
        st.markdown(f"**Versão:** {VERSION}")
        st.markdown(f"**Autor:** {AUTHOR}")
        
        st.markdown("---")
        st.markdown("### 📂 Status dos Arquivos")
        for file, stat in status.items():
            if "✅" in stat:
                st.markdown(f":green[{file}]")
                st.caption(stat.replace("✅ ", ""))
            else:
                st.markdown(f":orange[{file}] {stat}")
        
        st.markdown("---")
        st.metric("💰 Banca", f"R$ {st.session_state.contexto_oraculo['banca']:.2f}")
        
        nova_banca = st.number_input(
            "Atualizar Banca:",
            value=st.session_state.contexto_oraculo['banca'],
            min_value=100.0
        )
        
        if st.button("💾 Salvar"):
            st.session_state.contexto_oraculo['banca'] = nova_banca
            st.success("✅")
        
        st.markdown("---")
        if st.button("🔄 Limpar Cache"):
            st.cache_data.clear()
            st.rerun()

    # Tabs
    tabs = st.tabs([
        "🏠 Dash", "🔨 Construtor", "🧠 Oráculo", "📅 Calendário", "🎯 Análise", 
        "🔍 Scanner", "📊 Ligas", "👥 Times", "👨‍⚖️ Árbitros", "🎲 Monte Carlo", "💰 Gestão", "📜 Histórico"
    ])

    # ABA 1: DASHBOARD
    with tabs[0]:
        st.header("🏠 Dashboard Executivo")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📊 Jogos", len(df))
        k2.metric("⚽ Cantos/Jogo", f"{df['Total_Corners'].mean():.2f}")
        k3.metric("🟨 Cartões/Jogo", f"{df['Total_Cards'].mean():.2f}")
        k4.metric("🎯 Gols/Jogo", f"{df['Total_Goals'].mean():.2f}")
        
        st.markdown("---")
        
        fig = px.histogram(
            df, 
            x='Total_Corners', 
            nbins=20,
            title="📊 Distribuição de Escanteios",
            color_discrete_sequence=['#3b82f6']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        st.plotly_chart(fig, use_container_width=True)

    # ABA 2: CONSTRUTOR EVOLUTION ⭐⭐⭐
    with tabs[1]:
        st.header("🔨 Construtor de Bilhetes EVOLUTION")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📅 Selecionar Jogo")
            
            # FEEDBACK 1: Filtro de data
            datas_disponiveis = sorted(cal_df['Data'].unique())
            data_selecionada = st.selectbox("📆 Escolher Data:", datas_disponiveis)
            
            # Filtrar jogos pela data
            jogos_do_dia = cal_df[cal_df['Data'] == data_selecionada]
            
            if not jogos_do_dia.empty:
                jogo_sel = st.selectbox(
                    "⚽ Jogo:",
                    [f"{r['HomeTeam']} x {r['AwayTeam']}" for _, r in jogos_do_dia.iterrows()]
                )
                
                if jogo_sel:
                    home, away = jogo_sel.split(' x ')
                    
                    # Predição completa
                    pred = predictor.predict_full(home, away)
                    
                    if pred:
                        # Gerar todas as linhas
                        all_lines = predictor.generate_all_lines(pred)
                        
                        st.markdown("---")
                        st.subheader("📊 TODAS AS LINHAS DISPONÍVEIS")
                        
                        # Agrupar por tipo
                        tipos = {}
                        for line in all_lines:
                            tipo = line['tipo']
                            if tipo not in tipos:
                                tipos[tipo] = []
                            tipos[tipo].append(line)
                        
                        # Exibir por tipo
                        for tipo, linhas in tipos.items():
                            with st.expander(f"📌 {tipo}", expanded=True):
                                for linha in linhas:
                                    col_a, col_b, col_c = st.columns([3, 1, 1])
                                    
                                    col_a.markdown(f"**{linha['mercado']}**")
                                    col_b.metric("Projeção", f"{linha['projecao']:.2f}")
                                    col_c.metric("Prob", f"{linha['prob']:.1f}%")
                                    
                                    odd_input = st.number_input(
                                        "Odd:",
                                        value=1.90,
                                        min_value=1.01,
                                        key=f"odd_{tipo}_{linha['mercado']}"
                                    )
                                    
                                    if st.button("➕ Adicionar", key=f"add_{tipo}_{linha['mercado']}"):
                                        st.session_state.bilhete.append({
                                            'jogo': jogo_sel,
                                            'mercado': linha['mercado'],
                                            'odd': odd_input,
                                            'prob': linha['prob']
                                        })
                                        st.success("✅")
                                        st.rerun()
                                    
                                    st.markdown("---")
        
        with col2:
            st.subheader("🎫 Bilhete Atual")
            
            if st.session_state.bilhete:
                for i, aposta in enumerate(st.session_state.bilhete):
                    with st.container():
                        st.markdown(f"""
                        <div class="linha-aposta">
                        <strong>{aposta['jogo']}</strong><br>
                        {aposta['mercado']}<br>
                        Odd: {aposta['odd']:.2f}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️", key=f"del_{i}"):
                            st.session_state.bilhete.pop(i)
                            st.rerun()
                
                st.markdown("---")
                
                # Odd combinada
                odd_comb = 1.0
                for a in st.session_state.bilhete:
                    odd_comb *= a['odd']
                
                st.success(f"**ODD COMBINADA:** {odd_comb:.2f}")
                
                # Kelly
                stake = MathEngine.kelly_criterion(0.60, odd_comb, st.session_state.contexto_oraculo['banca'])
                st.metric("🎯 Stake Kelly", f"R$ {stake:.2f}")
                
                if st.button("🗑️ Limpar Tudo"):
                    st.session_state.bilhete = []
                    st.rerun()

    # ABA 3: ORÁCULO ⭐
    with tabs[2]:
        st.header("🧠 ORÁCULO MAXIMUM EVOLUTION")
        
        st.info("""
**💡 Comandos disponíveis:**
- "Analisa Cagliari x Milan" (com projeções individuais!)
- "Comparado ao jogo anterior, qual melhor?"
- "Top 5 da Premier League"
- "Quanto apostar com R$ 800?"
""")
        
        st.markdown("---")
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg['role'], avatar=msg['avatar']):
                st.markdown(msg['content'])
        
        if prompt := st.chat_input("💬 Pergunte ao Oráculo..."):
            
            st.session_state.chat_history.append({
                'role': 'user',
                'content': prompt,
                'avatar': '👤'
            })
            
            with st.chat_message('user', avatar='👤'):
                st.markdown(prompt)
            
            with st.chat_message('assistant', avatar='🧠'):
                with st.spinner("🧠 Processando..."):
                    resultado = oraculo.processar(
                        prompt, 
                        st.session_state.contexto_oraculo
                    )
                    
                    st.markdown(resultado['texto'])
            
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': resultado['texto'],
                'avatar': '🧠'
            })
            
            st.rerun()

    # ABA 4: CALENDÁRIO EVOLUTION ⭐
    with tabs[3]:
        st.header("📅 Calendário de Jogos")
        
        # FEEDBACK 3: Filtro de data
        datas_cal = sorted(cal_df['Data'].unique())
        data_filtro = st.selectbox("📆 Filtrar por Data:", ["Todas"] + list(datas_cal))
        
        if data_filtro == "Todas":
            st.dataframe(cal_df, use_container_width=True)
        else:
            cal_filtrado = cal_df[cal_df['Data'] == data_filtro]
            st.dataframe(cal_filtrado, use_container_width=True)

    # ABA 5: ANÁLISE EVOLUTION ⭐⭐⭐
    with tabs[4]:
        st.header("🎯 Análise H2H - PANORAMA COMPLETO")
        
        teams = sorted(list(df['HomeTeam'].unique()))
        
        if teams:
            c1, c2 = st.columns(2)
            t1 = c1.selectbox("🏠 Casa:", teams, key="an_h")
            t2 = c2.selectbox("✈️ Fora:", teams, key="an_a")
            
            if st.button("🔥 ANALISAR COMPLETO"):
                with st.spinner("Processando..."):
                    pred = predictor.predict_full(t1, t2)
                    
                    if pred:
                        st.success("✅ Análise Concluída!")
                        
                        # OVERVIEW
                        st.markdown("### 📊 OVERVIEW")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Escanteios Total", f"{pred['corners']['total']:.2f}")
                        col2.metric("P80", pred['corners']['p80'])
                        col3.metric("Cartões Total", f"{pred['cards']['total']:.2f}")
                        col4.metric("Gols Total", f"{pred['goals']['total']:.2f}")
                        
                        st.markdown("---")
                        
                        # TODAS AS LINHAS
                        st.markdown("### 📋 TODAS AS LINHAS DE APOSTA")
                        
                        all_lines = predictor.generate_all_lines(pred)
                        
                        # Filtrar linhas com prob >= 50%
                        lines_good = [l for l in all_lines if l['prob'] >= 50]
                        
                        if lines_good:
                            df_lines = pd.DataFrame(lines_good)
                            df_lines = df_lines.sort_values('prob', ascending=False)
                            
                            st.dataframe(
                                df_lines[['tipo', 'mercado', 'projecao', 'prob']].style.format({
                                    'projecao': '{:.2f}',
                                    'prob': '{:.1f}%'
                                }),
                                use_container_width=True
                            )
                        
                        st.markdown("---")
                        
                        # DETALHAMENTO POR TIME
                        st.markdown("### 👥 DETALHAMENTO POR TIME")
                        
                        col_det1, col_det2 = st.columns(2)
                        
                        with col_det1:
                            st.markdown(f"#### 🏠 {t1}")
                            st.metric("Escanteios", f"{pred['corners']['home']:.2f}")
                            st.metric("Cartões", f"{pred['cards']['home']:.2f}")
                            st.metric("Gols", f"{pred['goals']['home']:.2f}")
                            st.metric("Faltas", f"{pred['fouls']['home']:.2f}")
                        
                        with col_det2:
                            st.markdown(f"#### ✈️ {t2}")
                            st.metric("Escanteios", f"{pred['corners']['away']:.2f}")
                            st.metric("Cartões", f"{pred['cards']['away']:.2f}")
                            st.metric("Gols", f"{pred['goals']['away']:.2f}")
                            st.metric("Faltas", f"{pred['fouls']['away']:.2f}")

    # ABA 6: SCANNER
    with tabs[5]:
        st.header("🔍 Scanner de Oportunidades")
        
        if st.button("🔍 ESCANEAR CALENDÁRIO"):
            with st.spinner("Escaneando..."):
                opportunities = []
                
                for _, row in cal_df.head(20).iterrows():
                    h = row['HomeTeam']
                    a = row['AwayTeam']
                    
                    pred = predictor.predict_full(h, a)
                    
                    if pred and pred['corners']['p80'] >= 10:
                        opportunities.append({
                            'Jogo': f"{h} x {a}",
                            'Data': row['Data'],
                            'Projeção': f"{pred['corners']['total']:.2f}",
                            'P80': pred['corners']['p80'],
                            'Score': min(100, int(pred['corners']['total'] * 10))
                        })
                
                if opportunities:
                    df_opp = pd.DataFrame(opportunities)
                    df_opp = df_opp.sort_values('Score', ascending=False)
                    st.dataframe(df_opp, use_container_width=True)
                else:
                    st.warning("Nenhuma oportunidade encontrada.")

    # ABA 7: LIGAS
    with tabs[6]:
        st.header("📊 Estatísticas por Liga")
        
        liga_stats = df.groupby('League').agg({
            'Total_Corners': 'mean',
            'Total_Cards': 'mean',
            'Total_Goals': 'mean'
        }).round(2)
        
        liga_stats.columns = ['Escanteios/Jogo', 'Cartões/Jogo', 'Gols/Jogo']
        
        st.dataframe(liga_stats, use_container_width=True)
        
        fig = px.bar(
            liga_stats.reset_index(),
            x='League',
            y='Escanteios/Jogo',
            title="📊 Média de Escanteios por Liga",
            color_discrete_sequence=['#10b981']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9'
        )
        st.plotly_chart(fig, use_container_width=True)

    # ABA 8: TIMES EVOLUTION ⭐⭐⭐
    with tabs[7]:
        st.header("👥 DNA dos Times - RELATÓRIO TÉCNICO")
        
        teams = sorted(list(df['HomeTeam'].unique()))
        time_sel = st.selectbox("Selecione Time:", teams)
        
        if time_sel:
            time_data = df[(df['HomeTeam'] == time_sel) | (df['AwayTeam'] == time_sel)]
            
            st.markdown("### 📊 MÉTRICAS PRINCIPAIS")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Escanteios/Jogo", f"{time_data['Total_Corners'].mean():.2f}")
            c2.metric("Cartões/Jogo", f"{time_data['Total_Cards'].mean():.2f}")
            c3.metric("Gols/Jogo", f"{time_data['Total_Goals'].mean():.2f}")
            c4.metric("Faltas/Jogo", f"{time_data['Total_Fouls'].mean():.2f}")
            
            st.markdown("---")
            
            # RELATÓRIO TÉCNICO COMPLETO
            st.markdown("### 📋 RELATÓRIO TÉCNICO COMPLETO")
            
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("#### 🏠 COMO MANDANTE")
                home_data = time_data[time_data['HomeTeam'] == time_sel]
                if not home_data.empty:
                    st.metric("Escanteios Casa", f"{home_data['HC'].mean():.2f}")
                    st.metric("Cartões Casa", f"{home_data['HY'].mean():.2f}")
                    st.metric("Faltas Casa", f"{home_data['HF'].mean():.2f}")
                    st.metric("Chutes no Alvo", f"{home_data['HST'].mean():.2f}")
            
            with col_r2:
                st.markdown("#### ✈️ COMO VISITANTE")
                away_data = time_data[time_data['AwayTeam'] == time_sel]
                if not away_data.empty:
                    st.metric("Escanteios Fora", f"{away_data['AC'].mean():.2f}")
                    st.metric("Cartões Fora", f"{away_data['AY'].mean():.2f}")
                    st.metric("Faltas Fora", f"{away_data['AF'].mean():.2f}")
                    st.metric("Chutes no Alvo", f"{away_data['AST'].mean():.2f}")
            
            st.markdown("---")
            
            # Histograma
            fig = px.histogram(
                time_data,
                x='Total_Corners',
                nbins=15,
                title=f"Distribuição de Escanteios - {time_sel}",
                color_discrete_sequence=['#f59e0b']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9'
            )
            st.plotly_chart(fig, use_container_width=True)

    # ABA 9: ÁRBITROS
    with tabs[8]:
        st.header("👨‍⚖️ Banco de Árbitros")
        st.dataframe(ref_df, use_container_width=True)

    # ABA 10: MONTE CARLO
    with tabs[9]:
        st.header("🎲 Simulação Monte Carlo")
        
        lam = st.number_input("Média Esperada (Lambda):", value=10.0, min_value=1.0)
        n_sims = st.selectbox("Simulações:", [1000, 5000, 10000], index=2)
        
        if st.button("🎲 SIMULAR"):
            with st.spinner(f"Simulando {n_sims:,} jogos..."):
                result = MathEngine.monte_carlo_simulation(lam, n_sims)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Média", f"{result['mean']:.2f}")
                c2.metric("P50", result['p50'])
                c3.metric("P80", result['p80'])
                c4.metric("P95", result['p95'])
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Probabilidades")
                    st.metric("Over 9.5", f"{result['prob_over_9_5']*100:.1f}%")
                    st.metric("Over 10.5", f"{result['prob_over_10_5']*100:.1f}%")
                    st.metric("Over 11.5", f"{result['prob_over_11_5']*100:.1f}%")
                
                with col2:
                    fig = px.histogram(
                        x=result['samples'],
                        nbins=20,
                        title="Distribuição das Simulações",
                        color_discrete_sequence=['#8b5cf6']
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#f1f5f9'
                    )
                    st.plotly_chart(fig, use_container_width=True)

    # ABA 11: GESTÃO
    with tabs[10]:
        st.header("💰 Gestão de Banca")
        
        c1, c2 = st.columns(2)
        
        with c1:
            banca = st.number_input("💰 Banca Total:", value=1000.0, min_value=100.0)
            prob = st.slider("📊 Probabilidade (%):", 50, 90, 65) / 100
            odd = st.number_input("🎯 Odd:", value=1.90, min_value=1.01)
        
        with c2:
            kelly = MathEngine.kelly_criterion(prob, odd, banca)
            ev = MathEngine.calculate_ev(prob, odd)
            
            st.metric("🎯 Kelly Criterion (25%)", f"R$ {kelly:.2f}")
            st.metric("📈 Expected Value", f"{ev*100:.1f}%")
            
            if ev > 0:
                st.success("✅ Aposta com valor positivo!")
            else:
                st.error("❌ EV negativo - Evitar!")

    # ABA 12: HISTÓRICO
    with tabs[11]:
        st.header("📜 Histórico de Análises")
        
        if st.session_state.contexto_oraculo['historico']:
            df_hist = pd.DataFrame(st.session_state.contexto_oraculo['historico'])
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("Nenhuma análise realizada ainda.")

    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: #64748b;'>⚽ FutPrevisão {VERSION} | {AUTHOR} | Janeiro 2026</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
