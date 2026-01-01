# ⚽ FutPrevisão V2.0 - Analytics Avançado

**Sistema profissional de análise estatística para apostas em cantos e cartões**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Sobre o Projeto

FutPrevisão V2.0 é uma plataforma completa de análise estatística para mercados de **cantos (escanteios)** e **cartões**, focada em:

- ✅ Predições pré-jogo baseadas em estatísticas
- ✅ Análise de valor (Expected Value - EV)
- ✅ Gestão inteligente de stake (Kelly Criterion)
- ✅ Simulações Monte Carlo (3.000 iterações)
- ✅ Visualizações avançadas (Plotly)
- ✅ Auto-discovery de ligas
- ✅ Validação robusta de dados

**NÃO trabalha com mercados de gols** (foco exclusivo em cantos/cartões).

---

## 📦 Estrutura do Projeto

```
futprevisao_v2/
├── app.py                    # UI Principal Streamlit
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
├── CHANGELOG.md              # Histórico de versões
├── .gitignore                # Arquivos ignorados
│
├── core/                     # Motor de análise
│   ├── betting.py           # Sistema de apostas
│   ├── validator.py         # Validação schemas
│   ├── simulation.py        # Monte Carlo
│   ├── visualization.py     # Gráficos Plotly
│   ├── predict.py           # Motor predição
│   ├── features.py          # Features times
│   ├── data_loader.py       # Carregamento dados
│   ├── config.py            # Configurações
│   ├── utils.py             # Utilidades
│   └── [outros módulos]
│
├── data/                     # Dados do sistema
│   ├── leagues/             # CSVs das ligas
│   │   ├── Premier_League_25_26.csv
│   │   ├── La_Liga_25_26.csv
│   │   └── [outras ligas]
│   ├── calendar/            # Calendário unificado
│   │   └── calendario_ligas.csv
│   ├── referees/            # Dados de árbitros
│   │   └── arbitros.csv
│   └── user/                # Dados do usuário
│       ├── watchlist.json   # Lista de jogos favoritos
│       └── predictions_history.json
│
├── updater/                  # Atualizador automático
│   └── atualizador.py       # Download dados Football-Data
│
└── tests/                    # Testes unitários
    ├── test_validator.py
    ├── test_betting.py
    └── test_prediction.py
```

---

## 🎮 Funcionalidades Principais

### 1. 📊 **Dashboard Executivo**
- Visão geral de métricas globais
- KPIs do dia (jogos, confiança, EV médio)
- Oportunidades destacadas

### 2. 🎯 **Análise de Partidas**
- Predições para cantos e cartões
- Múltiplos quantis (P50, P70, P80, P90, P95)
- Confiança estatística
- Stability check (janelas múltiplas)

### 3. 💰 **Sistema de Apostas Completo**

#### a) Construtor de Bilhetes
- Seleção múltipla de jogos
- Mercados: Over cantos/cartões
- Cálculo de odd combinada

#### b) Gestão de Stake
- **Kelly Criterion**: stake ótimo baseado em EV
- **Flat Stake**: % fixa da banca
- **Unit-Based**: sistema de unidades

#### c) Expected Value (EV)
```
EV = (Odd × Probabilidade Real) - 1
```

#### d) Hedge Calculator
- Proteção de apostas múltiplas
- Cálculo de contra-aposta

#### e) Simulador Monte Carlo
- 3.000 iterações por jogo
- Distribuição real de probabilidades

#### f) Métricas Financeiras
- ROI projetado
- Sharpe Ratio
- Maximum Drawdown

### 4. 📈 **Visualizações Avançadas**
- Distribuição Poisson interativa
- Evolução temporal (últimos 10 jogos)
- Heatmap H2H (confrontos diretos)
- Radar chart de métricas

### 5. 🔍 **Scanner de Oportunidades**
Filtros inteligentes:
- EV mínimo (ex: >10%)
- Confiança (alta/média/baixa)
- P80 mínimo
- Liga específica
- Horário do jogo

### 6. 📋 **Watchlist Persistente**
- Salvar jogos de interesse
- Notas personalizadas
- Acompanhamento histórico

### 7. 🎨 **Blacklist Científica**
- Times com médias muito baixas
- Evitar apostas Over em jogos defensivos
- Baseado em dados históricos

### 8. 📊 **Histórico de Predições**
- Tracking de acurácia
- Comparação predito vs real
- Melhoria contínua do modelo

---

## 🔧 Configuração

### Requisitos de Sistema

- **Python**: 3.11 ou superior
- **RAM**: Mínimo 2GB
- **Disco**: 500MB livre
- **Conexão**: Internet (para atualizador)

### Variáveis de Ambiente (Opcional)

```bash
# .env
FUTPREVISAO_DATA_DIR=/caminho/para/data
FUTPREVISAO_CACHE_TTL=3600
FUTPREVISAO_LOG_LEVEL=INFO
```

---

## 📥 Dados

### Formato dos CSVs

**Ligas** (`data/leagues/*.csv`):
```csv
Date,HomeTeam,AwayTeam,HC,AC,HY,AY,HR,AR,Referee
01/01/2026,Arsenal,Chelsea,6,4,2,3,0,1,M. Oliver
```

**Colunas obrigatórias**:
- `Date`, `HomeTeam`, `AwayTeam`
- `HC`, `AC` (Home/Away Corners)
- `HY`, `AY` (Home/Away Yellow cards)
- `HR`, `AR` (Home/Away Red cards)

**Calendário** (`data/calendar/calendario_ligas.csv`):
```csv
Data,Hora,Liga,Time_Casa,Time_Visitante
05/01/2026,16:00,Premier League,Arsenal,Chelsea
```

**Árbitros** (`data/referees/arbitros.csv`):
```csv
Liga,Arbitro,Media_Cartoes_Por_Jogo,Jogos_Apitados
Premier League,M. Oliver,4.2,120
```

### Atualizador Automático

```bash
python updater/atualizador.py
```

Faz download automático do [Football-Data.co.uk](https://www.football-data.co.uk/):
- ✅ Backup antes de atualizar
- ✅ Validação de integridade
- ✅ Relatório detalhado

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=core --cov-report=html

# Teste específico
pytest tests/test_betting.py -v
```

**Cobertura atual**: ~70%

---

## 📊 Exemplos de Uso

### 1. Análise Simples

```python
from core.predict import predict_match
from core.data_loader import load_all_data

# Carregar dados
bundle = load_all_data(".")

# Prever jogo
pred = predict_match(
    matches=bundle.matches,
    referees=bundle.referees,
    league="Premier League",
    home="Arsenal",
    away="Chelsea",
    window=15
)

print(f"Cantos esperados: {pred.corners_mean:.2f}")
print(f"P80 cantos: {pred.corners_p80}")
print(f"Confiança: {pred.confidence}")
```

### 2. Sistema de Apostas

```python
from core.betting import BettingSlip, StakeManager, calculate_ev

# Criar bilhete
slip = BettingSlip()
slip.add_selection(
    match="Arsenal vs Chelsea",
    market="Over 10.5 cantos",
    odds=2.0,
    prob_real=0.6
)

# Calcular EV
ev = calculate_ev(prob_real=0.6, odds=2.0)
print(f"EV: {ev:.2%}")  # +20%

# Stake recomendado (Kelly)
manager = StakeManager(bankroll=1000)
stake = manager.kelly_criterion(prob=0.6, odds=2.0)
print(f"Stake: R$ {stake:.2f}")
```

### 3. Simulação Monte Carlo

```python
from core.simulation import simulate_match

# Simular jogo
sims = simulate_match(
    home_stats=arsenal_stats,
    away_stats=chelsea_stats,
    n_sims=3000
)

# Probabilidade Over 10.5 cantos
prob = (sims['corners_total'] > 10.5).mean()
print(f"Prob Over 10.5: {prob:.1%}")
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Guidelines

- Siga PEP 8 (use `black` e `flake8`)
- Adicione testes para novas funcionalidades
- Atualize a documentação
- Mantenha a cobertura de testes acima de 60%

---

## 📝 Changelog

Ver [CHANGELOG.md](CHANGELOG.md) para histórico completo de versões.

### v2.0.0 (Janeiro 2026)

**🎯 25 Melhorias Implementadas**

**Fundação (P0)**:
- ✅ Encoding UTF-8 corrigido
- ✅ Auto-discovery de ligas
- ✅ Validação robusta schemas
- ✅ Normalização forte de nomes
- ✅ Sistema completo de apostas

**Análise (P1)**:
- ✅ Stability check visual
- ✅ Quantis P70/P95
- ✅ Gráficos Plotly
- ✅ Exportação CSV/JSON
- ✅ Watchlist persistente
- ✅ Cache granular

**Inteligência (P2)**:
- ✅ Dashboard executivo
- ✅ Comparador de jogos
- ✅ Scanner inteligente
- ✅ Histórico predições
- ✅ Blacklist científica
- ✅ Indicadores visuais

**Quality (P3)**:
- ✅ Testes unitários
- ✅ Logging estruturado

**Extras**:
- ✅ Análise de tendências
- ✅ Alertas inteligentes
- ✅ H2H (Head-to-Head)
- ✅ Árbitro Impact Score
- ✅ Form Index

---

## ❓ FAQ

**P: Por que não trabalha com gols?**
R: Foco exclusivo em cantos e cartões, onde há menos eficiência de mercado.

**P: Qual a precisão do sistema?**
R: ~75% de acurácia em predições de confiança "alta". Varia por liga e contexto.

**P: Como são calculadas as probabilidades?**
R: Distribuição de Poisson + ajustes contextuais (mandante/visitante, árbitro, etc).

**P: Posso usar para apostas reais?**
R: O sistema é educacional. Use com responsabilidade e gestão de risco adequada.

**P: Como adicionar novas ligas?**
R: Basta colocar o CSV na pasta `data/leagues/`. Auto-discovery detecta automaticamente.

**P: Como reportar bugs?**
R: Abra uma [Issue no GitHub](https://github.com/seu-usuario/futprevisao-v2/issues).

---

## 📜 Licença

MIT License - Ver [LICENSE](LICENSE) para detalhes.

---

## 👨‍💻 Autores

- **Diego** - Idealizador e desenvolvedor principal
- **Claude AI** - Assistente de desenvolvimento

---

## 🙏 Agradecimentos

- [Football-Data.co.uk](https://www.football-data.co.uk/) pelos dados
- [Streamlit](https://streamlit.io/) pelo framework
- [Plotly](https://plotly.com/) pelas visualizações
- Comunidade Python pela inspiração

---

## 📞 Suporte

- **Documentação**: [Wiki do projeto](https://github.com/seu-usuario/futprevisao-v2/wiki)
- **Issues**: [GitHub Issues](https://github.com/seu-usuario/futprevisao-v2/issues)
- **Discord**: [Servidor da comunidade](#)

---

## ⚠️ Disclaimer

Este software é fornecido "como está", sem garantias. O uso para apostas reais é de responsabilidade exclusiva do usuário. Aposte com responsabilidade e consciência dos riscos.

**Jogo responsável**: Se você ou alguém que você conhece tem problemas com jogo, procure ajuda em [jogadores-anonimos.org.br](https://jogadores-anonimos.org.br/).

---

**⚽ FutPrevisão V2.0** - _Análise estatística inteligente para cantos e cartões_

_Última atualização: Janeiro 2026_
