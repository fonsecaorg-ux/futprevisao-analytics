"""
FutPrevisão V2.0 - Simulador Monte Carlo
Simulação estatística com 3.000 iterações

Funcionalidades:
- Simulação de partidas completas
- Distribuições de cantos e cartões
- Cálculo de probabilidades reais
- Análise de cenários
"""

import numpy as np
from scipy.stats import poisson
from typing import Dict, Tuple, List
from dataclasses import dataclass


# ==============================================================================
# DATACLASSES
# ==============================================================================

@dataclass
class SimulationResult:
    """Resultado de simulação"""
    corners_mean: float
    corners_std: float
    corners_p50: int
    corners_p70: int
    corners_p80: int
    corners_p90: int
    corners_p95: int
    
    cards_mean: float
    cards_std: float
    cards_p50: int
    cards_p70: int
    cards_p80: int
    cards_p90: int
    cards_p95: int
    
    prob_over_corners: Dict[float, float]
    prob_over_cards: Dict[float, float]
    
    n_simulations: int


# ==============================================================================
# SIMULAÇÃO PRINCIPAL
# ==============================================================================

def simulate_match(
    corners_home_mean: float,
    corners_away_mean: float,
    cards_home_mean: float,
    cards_away_mean: float,
    n_sims: int = 3000,
    random_seed: int = 42
) -> SimulationResult:
    """
    Simula partida usando Monte Carlo
    
    Args:
        corners_home_mean: Média de escanteios do mandante
        corners_away_mean: Média de escanteios do visitante
        cards_home_mean: Média de cartões do mandante
        cards_away_mean: Média de cartões do visitante
        n_sims: Número de simulações (padrão: 3000)
        random_seed: Seed para reprodutibilidade
    
    Returns:
        SimulationResult com todas as estatísticas
    
    Example:
        >>> result = simulate_match(6.0, 4.5, 2.2, 2.0, n_sims=3000)
        >>> print(f"Cantos P80: {result.corners_p80}")
        >>> print(f"Prob Over 10.5: {result.prob_over_corners[10.5]:.1%}")
    """
    # Set seed para reprodutibilidade
    np.random.seed(random_seed)
    
    # Arrays para armazenar resultados
    corners_total = np.zeros(n_sims)
    cards_total = np.zeros(n_sims)
    
    # Executar simulações
    for i in range(n_sims):
        # Simular cantos
        corners_home = np.random.poisson(corners_home_mean)
        corners_away = np.random.poisson(corners_away_mean)
        corners_total[i] = corners_home + corners_away
        
        # Simular cartões
        cards_home = np.random.poisson(cards_home_mean)
        cards_away = np.random.poisson(cards_away_mean)
        cards_total[i] = cards_home + cards_away
    
    # Calcular estatísticas de cantos
    corners_stats = {
        'mean': corners_total.mean(),
        'std': corners_total.std(),
        'p50': int(np.percentile(corners_total, 50)),
        'p70': int(np.percentile(corners_total, 70)),
        'p80': int(np.percentile(corners_total, 80)),
        'p90': int(np.percentile(corners_total, 90)),
        'p95': int(np.percentile(corners_total, 95)),
    }
    
    # Calcular estatísticas de cartões
    cards_stats = {
        'mean': cards_total.mean(),
        'std': cards_total.std(),
        'p50': int(np.percentile(cards_total, 50)),
        'p70': int(np.percentile(cards_total, 70)),
        'p80': int(np.percentile(cards_total, 80)),
        'p90': int(np.percentile(cards_total, 90)),
        'p95': int(np.percentile(cards_total, 95)),
    }
    
    # Calcular probabilidades Over para diferentes linhas
    prob_over_corners = {}
    for line in [8.5, 9.5, 10.5, 11.5, 12.5, 13.5]:
        prob_over_corners[line] = (corners_total > line).mean()
    
    prob_over_cards = {}
    for line in [2.5, 3.5, 4.5, 5.5, 6.5]:
        prob_over_cards[line] = (cards_total > line).mean()
    
    # Criar resultado
    result = SimulationResult(
        corners_mean=corners_stats['mean'],
        corners_std=corners_stats['std'],
        corners_p50=corners_stats['p50'],
        corners_p70=corners_stats['p70'],
        corners_p80=corners_stats['p80'],
        corners_p90=corners_stats['p90'],
        corners_p95=corners_stats['p95'],
        cards_mean=cards_stats['mean'],
        cards_std=cards_stats['std'],
        cards_p50=cards_stats['p50'],
        cards_p70=cards_stats['p70'],
        cards_p80=cards_stats['p80'],
        cards_p90=cards_stats['p90'],
        cards_p95=cards_stats['p95'],
        prob_over_corners=prob_over_corners,
        prob_over_cards=prob_over_cards,
        n_simulations=n_sims
    )
    
    return result


# ==============================================================================
# SIMULAÇÃO DE CANTOS
# ==============================================================================

def simulate_corners(
    home_mean: float,
    away_mean: float,
    n_sims: int = 3000
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simula apenas cantos
    
    Args:
        home_mean: Média mandante
        away_mean: Média visitante
        n_sims: Número de simulações
    
    Returns:
        (corners_home, corners_away, corners_total) como arrays numpy
    
    Example:
        >>> home, away, total = simulate_corners(6.0, 4.5)
        >>> print(f"Média total: {total.mean():.2f}")
    """
    corners_home = np.random.poisson(home_mean, n_sims)
    corners_away = np.random.poisson(away_mean, n_sims)
    corners_total = corners_home + corners_away
    
    return corners_home, corners_away, corners_total


# ==============================================================================
# SIMULAÇÃO DE CARTÕES
# ==============================================================================

def simulate_cards(
    home_mean: float,
    away_mean: float,
    n_sims: int = 3000
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simula apenas cartões
    
    Args:
        home_mean: Média mandante
        away_mean: Média visitante
        n_sims: Número de simulações
    
    Returns:
        (cards_home, cards_away, cards_total) como arrays numpy
    """
    cards_home = np.random.poisson(home_mean, n_sims)
    cards_away = np.random.poisson(away_mean, n_sims)
    cards_total = cards_home + cards_away
    
    return cards_home, cards_away, cards_total


# ==============================================================================
# ANÁLISE DE DISTRIBUIÇÃO
# ==============================================================================

def analyze_distribution(values: np.ndarray) -> Dict:
    """
    Analisa distribuição estatística
    
    Args:
        values: Array de valores
    
    Returns:
        Dict com estatísticas completas
    """
    return {
        'count': len(values),
        'mean': float(values.mean()),
        'median': float(np.median(values)),
        'std': float(values.std()),
        'min': int(values.min()),
        'max': int(values.max()),
        'p10': int(np.percentile(values, 10)),
        'p25': int(np.percentile(values, 25)),
        'p50': int(np.percentile(values, 50)),
        'p75': int(np.percentile(values, 75)),
        'p90': int(np.percentile(values, 90)),
        'p95': int(np.percentile(values, 95)),
        'p99': int(np.percentile(values, 99)),
    }


# ==============================================================================
# CÁLCULO DE PROBABILIDADES
# ==============================================================================

def calculate_over_probability(
    values: np.ndarray,
    line: float
) -> float:
    """
    Calcula probabilidade de Over em uma linha
    
    Args:
        values: Array de valores simulados
        line: Linha do mercado (ex: 10.5)
    
    Returns:
        Probabilidade (0-1)
    
    Example:
        >>> corners = np.random.poisson(10.5, 3000)
        >>> prob = calculate_over_probability(corners, 10.5)
        >>> print(f"P(Over 10.5): {prob:.1%}")
    """
    return (values > line).mean()


def calculate_under_probability(
    values: np.ndarray,
    line: float
) -> float:
    """
    Calcula probabilidade de Under em uma linha
    
    Args:
        values: Array de valores simulados
        line: Linha do mercado
    
    Returns:
        Probabilidade (0-1)
    """
    return (values < line).mean()


def calculate_exact_probability(
    values: np.ndarray,
    target: int
) -> float:
    """
    Calcula probabilidade de valor exato
    
    Args:
        values: Array de valores simulados
        target: Valor exato
    
    Returns:
        Probabilidade (0-1)
    """
    return (values == target).mean()


# ==============================================================================
# ANÁLISE DE CONFIANÇA
# ==============================================================================

def calculate_confidence_interval(
    values: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calcula intervalo de confiança
    
    Args:
        values: Array de valores
        confidence: Nível de confiança (0.95 = 95%)
    
    Returns:
        (lower_bound, upper_bound)
    
    Example:
        >>> corners = np.random.poisson(10.5, 3000)
        >>> lower, upper = calculate_confidence_interval(corners, 0.95)
        >>> print(f"95% CI: [{lower:.1f}, {upper:.1f}]")
    """
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    lower = np.percentile(values, lower_percentile)
    upper = np.percentile(values, upper_percentile)
    
    return float(lower), float(upper)


# ==============================================================================
# SIMULAÇÃO DE CENÁRIOS
# ==============================================================================

def simulate_scenarios(
    corners_mean: float,
    cards_mean: float,
    scenarios: List[Dict],
    n_sims: int = 1000
) -> Dict[str, Dict]:
    """
    Simula múltiplos cenários (ex: com/sem árbitro rigoroso)
    
    Args:
        corners_mean: Média base de cantos
        cards_mean: Média base de cartões
        scenarios: Lista de ajustes
            [
                {'name': 'Base', 'corners_mult': 1.0, 'cards_mult': 1.0},
                {'name': 'Árbitro Rigoroso', 'corners_mult': 1.0, 'cards_mult': 1.15},
            ]
        n_sims: Simulações por cenário
    
    Returns:
        Dict {scenario_name: statistics}
    """
    results = {}
    
    for scenario in scenarios:
        # Aplicar multiplicadores
        adj_corners = corners_mean * scenario.get('corners_mult', 1.0)
        adj_cards = cards_mean * scenario.get('cards_mult', 1.0)
        
        # Simular
        corners = np.random.poisson(adj_corners, n_sims)
        cards = np.random.poisson(adj_cards, n_sims)
        
        # Analisar
        results[scenario['name']] = {
            'corners': analyze_distribution(corners),
            'cards': analyze_distribution(cards),
        }
    
    return results


# ==============================================================================
# COMPARAÇÃO DE MODELOS
# ==============================================================================

def compare_predictions(
    predicted_mean: float,
    simulated_values: np.ndarray
) -> Dict:
    """
    Compara predição teórica vs simulação
    
    Args:
        predicted_mean: Média prevista pelo modelo
        simulated_values: Valores da simulação
    
    Returns:
        Dict com métricas de comparação
    """
    simulated_mean = simulated_values.mean()
    difference = simulated_mean - predicted_mean
    pct_diff = (difference / predicted_mean) * 100 if predicted_mean > 0 else 0
    
    return {
        'predicted_mean': predicted_mean,
        'simulated_mean': simulated_mean,
        'difference': difference,
        'pct_difference': pct_diff,
        'agreement': abs(pct_diff) < 5,  # <5% = boa concordância
    }


# ==============================================================================
# STRESS TESTING
# ==============================================================================

def stress_test(
    base_mean: float,
    variance_range: Tuple[float, float] = (0.8, 1.2),
    n_tests: int = 100,
    n_sims: int = 1000
) -> Dict:
    """
    Testa robustez da predição com variações
    
    Args:
        base_mean: Média base
        variance_range: Range de variação (0.8 = -20%, 1.2 = +20%)
        n_tests: Número de testes
        n_sims: Simulações por teste
    
    Returns:
        Dict com resultados de stress test
    """
    results = []
    
    for _ in range(n_tests):
        # Variar média aleatoriamente
        mult = np.random.uniform(*variance_range)
        adj_mean = base_mean * mult
        
        # Simular
        values = np.random.poisson(adj_mean, n_sims)
        
        # Armazenar
        results.append({
            'multiplier': mult,
            'mean': values.mean(),
            'std': values.std(),
        })
    
    # Analisar resultados
    means = [r['mean'] for r in results]
    stds = [r['std'] for r in results]
    
    return {
        'tests_run': n_tests,
        'mean_range': (min(means), max(means)),
        'std_range': (min(stds), max(stds)),
        'stability_score': 1 - (np.std(means) / np.mean(means)),  # >0.9 = estável
    }


# ==============================================================================
# HELPERS
# ==============================================================================

def get_distribution_histogram(
    values: np.ndarray,
    bins: int = 30
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gera histograma da distribuição
    
    Args:
        values: Array de valores
        bins: Número de bins
    
    Returns:
        (counts, bin_edges)
    """
    counts, bin_edges = np.histogram(values, bins=bins)
    return counts, bin_edges


def get_percentile_values(
    values: np.ndarray,
    percentiles: List[int] = [10, 25, 50, 75, 90, 95]
) -> Dict[int, float]:
    """
    Calcula múltiplos percentis
    
    Args:
        values: Array de valores
        percentiles: Lista de percentis (0-100)
    
    Returns:
        Dict {percentil: valor}
    """
    return {
        p: float(np.percentile(values, p))
        for p in percentiles
    }
