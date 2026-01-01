"""
FutPrevisão V2.0 - Visualizações
Gráficos Plotly interativos para análise

Funcionalidades:
- Distribuição Poisson
- Evolução temporal de times
- Heatmap H2H
- Radar chart de métricas
- Gráfico de comparação
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.stats import poisson
from typing import List, Dict, Optional


# ==============================================================================
# DISTRIBUIÇÃO POISSON
# ==============================================================================

def plot_poisson_distribution(
    mean: float,
    market_line: Optional[float] = None,
    title: str = "Distribuição de Poisson",
    x_label: str = "Valor"
) -> go.Figure:
    """
    Plota distribuição de Poisson com linha de mercado
    
    Args:
        mean: Média da distribuição (λ)
        market_line: Linha do mercado (ex: 10.5 para Over 10.5)
        title: Título do gráfico
        x_label: Label do eixo X
    
    Returns:
        Figura Plotly
    
    Example:
        >>> fig = plot_poisson_distribution(10.5, market_line=10.5)
        >>> fig.show()
    """
    # Gerar valores
    max_x = int(mean * 2.5)
    x_values = list(range(0, max_x + 1))
    
    # Calcular probabilidades
    probabilities = [poisson.pmf(k, mean) for k in x_values]
    
    # Criar gráfico de barras
    fig = go.Figure()
    
    # Adicionar barras
    fig.add_trace(go.Bar(
        x=x_values,
        y=probabilities,
        name='Probabilidade',
        marker_color='rgb(55, 83, 109)',
        hovertemplate='<b>%{x}</b><br>Probabilidade: %{y:.2%}<extra></extra>'
    ))
    
    # Adicionar linha da média
    fig.add_vline(
        x=mean,
        line_dash="dash",
        line_color="red",
        annotation_text=f"μ = {mean:.2f}",
        annotation_position="top"
    )
    
    # Adicionar linha de mercado
    if market_line is not None:
        fig.add_vline(
            x=market_line,
            line_dash="dot",
            line_color="green",
            annotation_text=f"Mercado: {market_line}",
            annotation_position="bottom right"
        )
        
        # Calcular e mostrar probabilidade Over
        prob_over = 1 - poisson.cdf(market_line, mean)
        
        fig.add_annotation(
            x=market_line + 1,
            y=max(probabilities) * 0.8,
            text=f"P(Over {market_line}): {prob_over:.1%}",
            showarrow=False,
            bgcolor="rgba(0, 255, 0, 0.1)",
            bordercolor="green"
        )
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title="Probabilidade",
        yaxis_tickformat=".0%",
        hovermode='x',
        template='plotly_white',
        height=400
    )
    
    return fig


# ==============================================================================
# EVOLUÇÃO TEMPORAL
# ==============================================================================

def plot_team_evolution(
    matches: pd.DataFrame,
    team: str,
    metric: str = "corners",
    window: int = 10,
    title: Optional[str] = None
) -> go.Figure:
    """
    Plota evolução de métrica ao longo do tempo
    
    Args:
        matches: DataFrame de partidas
        team: Nome do time
        metric: 'corners' ou 'cards'
        window: Janela de jogos a mostrar
        title: Título customizado
    
    Returns:
        Figura Plotly
    """
    # Filtrar jogos do time
    team_matches = matches[
        (matches['HomeTeam'] == team) | (matches['AwayTeam'] == team)
    ].copy()
    
    # Ordenar por data
    if 'Date' in team_matches.columns:
        team_matches['Date'] = pd.to_datetime(team_matches['Date'], format='%d/%m/%Y', errors='coerce')
        team_matches = team_matches.sort_values('Date')
    
    # Pegar últimos N jogos
    team_matches = team_matches.tail(window)
    
    # Calcular métrica
    if metric == "corners":
        team_matches['metric'] = team_matches.apply(
            lambda row: row['HC'] if row['HomeTeam'] == team else row['AC'],
            axis=1
        )
        metric_label = "Escanteios"
    else:  # cards
        team_matches['metric'] = team_matches.apply(
            lambda row: row['HY'] if row['HomeTeam'] == team else row['AY'],
            axis=1
        )
        metric_label = "Cartões Amarelos"
    
    # Criar labels de jogos
    team_matches['game_label'] = team_matches.apply(
        lambda row: f"{row['HomeTeam']} vs {row['AwayTeam']}",
        axis=1
    )
    
    # Criar gráfico
    fig = go.Figure()
    
    # Linha principal
    fig.add_trace(go.Scatter(
        x=list(range(1, len(team_matches) + 1)),
        y=team_matches['metric'],
        mode='lines+markers',
        name=metric_label,
        line=dict(color='rgb(55, 83, 109)', width=3),
        marker=dict(size=10),
        hovertemplate='<b>Jogo %{x}</b><br>%{text}<br>' + metric_label + ': %{y}<extra></extra>',
        text=team_matches['game_label']
    ))
    
    # Linha de média
    mean_value = team_matches['metric'].mean()
    fig.add_hline(
        y=mean_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Média: {mean_value:.2f}",
        annotation_position="right"
    )
    
    # Layout
    if title is None:
        title = f"Evolução de {metric_label} - {team}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Jogo",
        yaxis_title=metric_label,
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig


# ==============================================================================
# HEATMAP H2H
# ==============================================================================

def plot_h2h_heatmap(
    home: str,
    away: str,
    h2h_data: List[Dict],
    title: Optional[str] = None
) -> go.Figure:
    """
    Plota heatmap de confrontos diretos
    
    Args:
        home: Time mandante
        away: Time visitante
        h2h_data: Lista de jogos H2H
            [{
                'home': str,
                'away': str,
                'corners': int,
                'cards': int,
                'date': str
            }]
        title: Título customizado
    
    Returns:
        Figura Plotly
    """
    if not h2h_data:
        # Gráfico vazio
        fig = go.Figure()
        fig.add_annotation(
            text="Sem histórico de confrontos diretos",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Converter para DataFrame
    df = pd.DataFrame(h2h_data)
    
    # Criar matriz
    metrics = ['corners', 'cards']
    games = [f"Jogo {i+1}" for i in range(len(df))]
    
    z_data = []
    for metric in metrics:
        if metric in df.columns:
            z_data.append(df[metric].tolist())
        else:
            z_data.append([0] * len(df))
    
    # Criar heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=games,
        y=['Escanteios', 'Cartões'],
        colorscale='YlOrRd',
        hovertemplate='<b>%{y}</b><br>%{x}<br>Valor: %{z}<extra></extra>'
    ))
    
    # Layout
    if title is None:
        title = f"H2H: {home} vs {away}"
    
    fig.update_layout(
        title=title,
        xaxis_title="Confronto",
        yaxis_title="Métrica",
        template='plotly_white',
        height=300
    )
    
    return fig


# ==============================================================================
# RADAR CHART
# ==============================================================================

def plot_radar_chart(
    team_stats: Dict[str, float],
    team_name: str,
    title: Optional[str] = None
) -> go.Figure:
    """
    Plota radar chart de métricas do time
    
    Args:
        team_stats: Dict com estatísticas
            {
                'corners': 5.5,
                'cards': 2.2,
                'fouls': 12.0,
                'shots': 12.5,
                'goals': 1.8
            }
        team_name: Nome do time
        title: Título customizado
    
    Returns:
        Figura Plotly
    """
    # Categorias e valores
    categories = []
    values = []
    
    metric_labels = {
        'corners': 'Escanteios',
        'cards': 'Cartões',
        'fouls': 'Faltas',
        'shots': 'Chutes',
        'goals': 'Gols'
    }
    
    for key, label in metric_labels.items():
        if key in team_stats:
            categories.append(label)
            values.append(team_stats[key])
    
    # Fechar o polígono
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    # Criar radar
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name=team_name,
        line_color='rgb(55, 83, 109)',
        fillcolor='rgba(55, 83, 109, 0.3)'
    ))
    
    # Layout
    if title is None:
        title = f"Perfil Estatístico - {team_name}"
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.2]
            )
        ),
        showlegend=True,
        title=title,
        template='plotly_white',
        height=400
    )
    
    return fig


# ==============================================================================
# COMPARAÇÃO DE JOGOS
# ==============================================================================

def plot_comparison(
    games: List[Dict],
    title: str = "Comparação de Jogos"
) -> go.Figure:
    """
    Plota comparação lado a lado de múltiplos jogos
    
    Args:
        games: Lista de jogos
            [{
                'label': 'Arsenal vs Chelsea',
                'corners_mean': 10.5,
                'corners_p80': 12,
                'cards_mean': 4.2,
                'ev': 0.15,
                'confidence': 'alta'
            }]
        title: Título do gráfico
    
    Returns:
        Figura Plotly com subplots
    """
    if not games:
        fig = go.Figure()
        fig.add_annotation(
            text="Sem jogos para comparar",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Criar subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Escanteios (Média)', 'Escanteios (P80)', 
                       'Cartões (Média)', 'Expected Value'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Labels
    labels = [g['label'] for g in games]
    
    # 1. Cantos média
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[g.get('corners_mean', 0) for g in games],
            name='Cantos μ',
            marker_color='rgb(55, 83, 109)',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # 2. Cantos P80
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[g.get('corners_p80', 0) for g in games],
            name='Cantos P80',
            marker_color='rgb(26, 118, 255)',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Cartões média
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[g.get('cards_mean', 0) for g in games],
            name='Cartões μ',
            marker_color='rgb(255, 193, 7)',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. EV
    colors = ['green' if g.get('ev', 0) > 0.1 else 'orange' if g.get('ev', 0) > 0 else 'red' 
              for g in games]
    
    fig.add_trace(
        go.Bar(
            x=labels,
            y=[g.get('ev', 0) * 100 for g in games],  # Converter para %
            name='EV %',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Layout
    fig.update_layout(
        title_text=title,
        height=600,
        template='plotly_white',
        showlegend=False
    )
    
    # Atualizar eixos
    fig.update_yaxes(title_text="Escanteios", row=1, col=1)
    fig.update_yaxes(title_text="Escanteios", row=1, col=2)
    fig.update_yaxes(title_text="Cartões", row=2, col=1)
    fig.update_yaxes(title_text="EV (%)", row=2, col=2)
    
    return fig


# ==============================================================================
# GRÁFICO DE PROBABILIDADES
# ==============================================================================

def plot_probability_bars(
    markets: Dict[str, float],
    title: str = "Probabilidades por Mercado"
) -> go.Figure:
    """
    Plota barras de probabilidade para diferentes mercados
    
    Args:
        markets: Dict {market: probability}
            {
                'Over 9.5': 0.65,
                'Over 10.5': 0.52,
                'Over 11.5': 0.38
            }
        title: Título
    
    Returns:
        Figura Plotly
    """
    # Ordenar por probabilidade
    sorted_markets = sorted(markets.items(), key=lambda x: x[1], reverse=True)
    
    labels = [m[0] for m in sorted_markets]
    probs = [m[1] for m in sorted_markets]
    
    # Cores baseadas em probabilidade
    colors = ['green' if p >= 0.7 else 'orange' if p >= 0.5 else 'red' for p in probs]
    
    # Criar gráfico
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=probs,
            marker_color=colors,
            text=[f"{p:.1%}" for p in probs],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Probabilidade: %{y:.1%}<extra></extra>'
        )
    ])
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Mercado",
        yaxis_title="Probabilidade",
        yaxis_tickformat=".0%",
        yaxis_range=[0, 1],
        template='plotly_white',
        height=400
    )
    
    return fig


# ==============================================================================
# GRÁFICO DE TENDÊNCIA
# ==============================================================================

def plot_trend_indicator(
    current_value: float,
    historical_avg: float,
    metric_name: str = "Escanteios"
) -> go.Figure:
    """
    Plota indicador de tendência (gauge)
    
    Args:
        current_value: Valor atual
        historical_avg: Média histórica
        metric_name: Nome da métrica
    
    Returns:
        Figura Plotly
    """
    # Calcular % de mudança
    pct_change = ((current_value - historical_avg) / historical_avg) * 100
    
    # Determinar cor
    if pct_change > 10:
        color = "green"
        status = "↗️ ALTO"
    elif pct_change < -10:
        color = "red"
        status = "↘️ BAIXO"
    else:
        color = "orange"
        status = "→ NORMAL"
    
    # Criar gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{metric_name}<br>{status}"},
        delta={'reference': historical_avg, 'valueformat': '.2f'},
        gauge={
            'axis': {'range': [0, historical_avg * 2]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, historical_avg * 0.8], 'color': "lightgray"},
                {'range': [historical_avg * 0.8, historical_avg * 1.2], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': historical_avg
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        template='plotly_white'
    )
    
    return fig
