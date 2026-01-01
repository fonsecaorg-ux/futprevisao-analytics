"""
FutPrevisão V2.0 - Sistema de Apostas
Módulo completo de gestão de apostas esportivas

Funcionalidades:
- Construtor de bilhetes
- Gestão de stake (Kelly, Flat, Units)
- Expected Value (EV)
- Hedge Calculator
- Métricas financeiras (ROI, Sharpe, MDD)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import numpy as np
from pathlib import Path


# ==============================================================================
# DATACLASSES
# ==============================================================================

@dataclass
class Selection:
    """Seleção individual em um bilhete"""
    match: str
    market: str
    odds: float
    prob_real: float
    stake: Optional[float] = None
    ev: Optional[float] = None
    
    def __post_init__(self):
        """Calcula EV automaticamente"""
        self.ev = calculate_ev(self.prob_real, self.odds)


@dataclass
class BettingSlip:
    """Bilhete de apostas"""
    selections: List[Selection] = field(default_factory=list)
    stake_total: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_selection(self, match: str, market: str, odds: float, prob_real: float):
        """Adiciona seleção ao bilhete"""
        sel = Selection(match, market, odds, prob_real)
        self.selections.append(sel)
    
    def remove_selection(self, index: int):
        """Remove seleção por índice"""
        if 0 <= index < len(self.selections):
            self.selections.pop(index)
    
    def calculate_combined_odds(self) -> float:
        """Calcula odd combinada do bilhete"""
        if not self.selections:
            return 1.0
        
        combined = 1.0
        for sel in self.selections:
            combined *= sel.odds
        
        return combined
    
    def calculate_combined_prob(self) -> float:
        """Calcula probabilidade real combinada"""
        if not self.selections:
            return 0.0
        
        prob = 1.0
        for sel in self.selections:
            prob *= sel.prob_real
        
        return prob
    
    def calculate_ev(self) -> float:
        """Calcula EV do bilhete completo"""
        combined_odds = self.calculate_combined_odds()
        combined_prob = self.calculate_combined_prob()
        
        return calculate_ev(combined_prob, combined_odds)
    
    def validate(self) -> Tuple[bool, str]:
        """Valida bilhete"""
        if not self.selections:
            return False, "Bilhete vazio"
        
        if len(self.selections) > 10:
            return False, "Máximo 10 seleções por bilhete"
        
        for sel in self.selections:
            if sel.odds < 1.01:
                return False, f"Odd muito baixa: {sel.market}"
            if sel.prob_real <= 0 or sel.prob_real >= 1:
                return False, f"Probabilidade inválida: {sel.market}"
        
        return True, "Bilhete válido"
    
    def to_dict(self) -> Dict:
        """Exporta para dicionário"""
        return {
            'selections': [
                {
                    'match': s.match,
                    'market': s.market,
                    'odds': s.odds,
                    'prob_real': s.prob_real,
                    'ev': s.ev
                }
                for s in self.selections
            ],
            'combined_odds': self.calculate_combined_odds(),
            'combined_prob': self.calculate_combined_prob(),
            'ev': self.calculate_ev(),
            'stake': self.stake_total,
            'created_at': self.created_at.isoformat()
        }


# ==============================================================================
# FUNÇÕES DE CÁLCULO
# ==============================================================================

def calculate_ev(prob_real: float, odds: float) -> float:
    """
    Calcula Expected Value (EV)
    
    Fórmula: EV = (Odd × Prob_Real) - 1
    
    Args:
        prob_real: Probabilidade real (0-1)
        odds: Odd da casa de apostas
    
    Returns:
        EV em decimal (ex: 0.15 = +15%)
    
    Example:
        >>> calculate_ev(0.6, 2.0)
        0.2  # +20% de valor
    """
    if prob_real <= 0 or prob_real >= 1:
        return -1.0
    
    if odds < 1.01:
        return -1.0
    
    return (odds * prob_real) - 1.0


def calculate_implied_prob(odds: float) -> float:
    """
    Calcula probabilidade implícita da odd
    
    Args:
        odds: Odd da casa
    
    Returns:
        Probabilidade implícita (0-1)
    
    Example:
        >>> calculate_implied_prob(2.0)
        0.5  # 50%
    """
    if odds <= 1.0:
        return 1.0
    
    return 1.0 / odds


def calculate_value(prob_real: float, odds: float) -> float:
    """
    Calcula % de valor na aposta
    
    Args:
        prob_real: Probabilidade real
        odds: Odd da casa
    
    Returns:
        % de valor (positivo = valor, negativo = overround)
    """
    implied = calculate_implied_prob(odds)
    
    return (prob_real / implied) - 1.0


# ==============================================================================
# GESTÃO DE STAKE
# ==============================================================================

class StakeManager:
    """Gerenciador de stakes"""
    
    def __init__(self, bankroll: float):
        """
        Inicializa manager
        
        Args:
            bankroll: Banca total disponível
        """
        self.bankroll = bankroll
        self.min_stake = 10.0  # R$ 10 mínimo
        self.max_stake_pct = 0.10  # 10% máximo da banca
    
    def kelly_criterion(
        self, 
        prob: float, 
        odds: float, 
        fraction: float = 0.25
    ) -> float:
        """
        Calcula stake usando Kelly Criterion
        
        Fórmula: f* = (bp - q) / b
        onde:
        - b = odds - 1
        - p = probabilidade de ganhar
        - q = probabilidade de perder (1-p)
        
        Args:
            prob: Probabilidade real (0-1)
            odds: Odd da aposta
            fraction: Fração do Kelly (0.25 = Quarter Kelly)
        
        Returns:
            Stake recomendado em R$
        
        Example:
            >>> manager = StakeManager(1000)
            >>> manager.kelly_criterion(0.6, 2.0)
            50.0  # R$ 50 (5% da banca)
        """
        if prob <= 0 or prob >= 1:
            return self.min_stake
        
        if odds <= 1.0:
            return self.min_stake
        
        # Kelly formula
        b = odds - 1
        p = prob
        q = 1 - p
        
        kelly_pct = (b * p - q) / b
        
        # Aplicar fração (Quarter Kelly = mais conservador)
        kelly_pct *= fraction
        
        # Kelly negativo = sem valor
        if kelly_pct <= 0:
            return 0.0
        
        # Calcular stake
        stake = self.bankroll * kelly_pct
        
        # Limites
        max_allowed = self.bankroll * self.max_stake_pct
        stake = min(stake, max_allowed)
        stake = max(stake, self.min_stake)
        
        return round(stake, 2)
    
    def flat_stake(self, percentage: float = 0.02) -> float:
        """
        Stake fixo como % da banca
        
        Args:
            percentage: % da banca (0.02 = 2%)
        
        Returns:
            Stake em R$
        
        Example:
            >>> manager = StakeManager(1000)
            >>> manager.flat_stake(0.02)
            20.0  # R$ 20 (2% da banca)
        """
        stake = self.bankroll * percentage
        
        max_allowed = self.bankroll * self.max_stake_pct
        stake = min(stake, max_allowed)
        stake = max(stake, self.min_stake)
        
        return round(stake, 2)
    
    def unit_based(self, units: float, unit_value: float = 10.0) -> float:
        """
        Stake baseado em unidades
        
        Args:
            units: Número de unidades (1, 2, 3, etc)
            unit_value: Valor de 1 unidade em R$
        
        Returns:
            Stake em R$
        
        Example:
            >>> manager = StakeManager(1000)
            >>> manager.unit_based(3, 10)
            30.0  # 3 unidades × R$ 10
        """
        stake = units * unit_value
        
        max_allowed = self.bankroll * self.max_stake_pct
        stake = min(stake, max_allowed)
        
        return round(stake, 2)
    
    def validate_stake(self, stake: float) -> Tuple[bool, str]:
        """
        Valida stake proposto
        
        Args:
            stake: Valor a validar
        
        Returns:
            (válido, mensagem)
        """
        if stake < self.min_stake:
            return False, f"Stake mínimo: R$ {self.min_stake:.2f}"
        
        max_allowed = self.bankroll * self.max_stake_pct
        
        if stake > max_allowed:
            return False, f"Stake muito alto (máx {self.max_stake_pct:.0%} da banca)"
        
        pct = (stake / self.bankroll) * 100
        
        if pct > 5:
            return True, f"⚠️ Stake agressivo ({pct:.1f}% da banca)"
        
        return True, f"✅ Stake seguro ({pct:.1f}% da banca)"


# ==============================================================================
# HEDGE CALCULATOR
# ==============================================================================

def calculate_hedge(
    main_stake: float,
    main_odds: float,
    hedge_odds: float
) -> Dict[str, float]:
    """
    Calcula contra-aposta (hedge) para garantir lucro ou reduzir perda
    
    Args:
        main_stake: Stake da aposta principal
        main_odds: Odd da aposta principal
        hedge_odds: Odd da contra-aposta
    
    Returns:
        Dict com hedge_stake, profit_if_main, profit_if_hedge
    
    Example:
        >>> calculate_hedge(100, 3.0, 1.5)
        {
            'hedge_stake': 200.0,
            'profit_if_main': 100.0,
            'profit_if_hedge': 100.0,
            'guaranteed_profit': 100.0
        }
    """
    # Retorno potencial da aposta principal
    potential_return = main_stake * main_odds
    
    # Stake necessário na hedge para igualar retorno
    hedge_stake = potential_return / hedge_odds
    
    # Cenário 1: Aposta principal bate
    profit_if_main = potential_return - main_stake - hedge_stake
    
    # Cenário 2: Hedge bate
    hedge_return = hedge_stake * hedge_odds
    profit_if_hedge = hedge_return - main_stake - hedge_stake
    
    # Lucro garantido (se ambos positivos)
    guaranteed = min(profit_if_main, profit_if_hedge) if profit_if_main > 0 and profit_if_hedge > 0 else None
    
    return {
        'hedge_stake': round(hedge_stake, 2),
        'profit_if_main': round(profit_if_main, 2),
        'profit_if_hedge': round(profit_if_hedge, 2),
        'guaranteed_profit': round(guaranteed, 2) if guaranteed else None
    }


# ==============================================================================
# MÉTRICAS FINANCEIRAS
# ==============================================================================

class BettingMetrics:
    """Cálculo de métricas financeiras"""
    
    def __init__(self, history: List[Dict]):
        """
        Inicializa com histórico de apostas
        
        Args:
            history: Lista de apostas passadas
                [{
                    'stake': 100,
                    'odds': 2.0,
                    'result': 'win'  # 'win', 'loss', 'void'
                }]
        """
        self.history = history
    
    def roi(self) -> float:
        """
        Return on Investment
        
        Returns:
            ROI em % (ex: 0.15 = +15%)
        """
        if not self.history:
            return 0.0
        
        total_staked = sum(bet['stake'] for bet in self.history)
        
        if total_staked == 0:
            return 0.0
        
        total_returned = sum(
            bet['stake'] * bet['odds'] if bet['result'] == 'win' else 0
            for bet in self.history
        )
        
        profit = total_returned - total_staked
        
        return profit / total_staked
    
    def win_rate(self) -> float:
        """Taxa de acerto"""
        if not self.history:
            return 0.0
        
        wins = sum(1 for bet in self.history if bet['result'] == 'win')
        
        return wins / len(self.history)
    
    def sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """
        Sharpe Ratio (risco-ajustado)
        
        Args:
            risk_free_rate: Taxa livre de risco (ex: 0.10 = 10% ao ano)
        
        Returns:
            Sharpe ratio
        """
        if len(self.history) < 2:
            return 0.0
        
        # Retornos individuais
        returns = []
        for bet in self.history:
            if bet['result'] == 'win':
                ret = (bet['odds'] - 1)
            elif bet['result'] == 'loss':
                ret = -1.0
            else:  # void
                ret = 0.0
            
            returns.append(ret)
        
        returns_arr = np.array(returns)
        
        mean_return = returns_arr.mean()
        std_return = returns_arr.std()
        
        if std_return == 0:
            return 0.0
        
        return (mean_return - risk_free_rate) / std_return
    
    def max_drawdown(self) -> float:
        """
        Maximum Drawdown (maior perda do pico)
        
        Returns:
            MDD em % (ex: -0.25 = -25%)
        """
        if not self.history:
            return 0.0
        
        # Calcular equity ao longo do tempo
        equity = [0]
        
        for bet in self.history:
            if bet['result'] == 'win':
                profit = bet['stake'] * (bet['odds'] - 1)
            elif bet['result'] == 'loss':
                profit = -bet['stake']
            else:  # void
                profit = 0
            
            equity.append(equity[-1] + profit)
        
        equity = np.array(equity)
        
        # Calcular drawdown
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        
        # Replace NaN/inf
        drawdown = np.nan_to_num(drawdown, nan=0.0, posinf=0.0, neginf=0.0)
        
        return float(drawdown.min())
    
    def profit_factor(self) -> float:
        """
        Profit Factor (lucros / perdas)
        
        Returns:
            PF (>1 = lucrativo)
        """
        if not self.history:
            return 0.0
        
        total_wins = sum(
            bet['stake'] * (bet['odds'] - 1)
            for bet in self.history
            if bet['result'] == 'win'
        )
        
        total_losses = sum(
            bet['stake']
            for bet in self.history
            if bet['result'] == 'loss'
        )
        
        if total_losses == 0:
            return float('inf') if total_wins > 0 else 0.0
        
        return total_wins / total_losses
    
    def to_dict(self) -> Dict:
        """Exporta métricas"""
        return {
            'roi': self.roi(),
            'win_rate': self.win_rate(),
            'sharpe_ratio': self.sharpe_ratio(),
            'max_drawdown': self.max_drawdown(),
            'profit_factor': self.profit_factor(),
            'total_bets': len(self.history)
        }


# ==============================================================================
# PERSISTÊNCIA
# ==============================================================================

def save_betting_slip(slip: BettingSlip, filepath: str = "data/user/betting_slips.json"):
    """Salva bilhete em arquivo JSON"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Carregar existentes
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {'slips': []}
    
    # Adicionar novo
    data['slips'].append(slip.to_dict())
    
    # Salvar
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_betting_history(filepath: str = "data/user/betting_history.json") -> List[Dict]:
    """Carrega histórico de apostas"""
    path = Path(filepath)
    
    if not path.exists():
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('bets', [])
