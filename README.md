# futprevisao-analytics
A modular football analytics project built with Python + Streamlit. It loads multi-league datasets, official calendars and referee profiles to produce match dashboards, daily rankings, team profiles and explainable pre-match forecasts for corners &amp; cards. Includes data validation, caching and an assistant that answers based on computed metrics.


# FutPrevisão Analytics

Plataforma de **análise de partidas de futebol** feita em **Python + Streamlit**, focada em **pré-jogo** (pre-match) com métricas e previsões para **escanteios e cartões**, usando bases de ligas, calendários e dados de árbitros.

> Projeto voltado para estudo, melhoria contínua e uso pessoal.

---

## ✨ Principais recursos

- 📊 **Painel do Dia**: ranking de jogos por potencial de escanteios e cartões (com base em métricas calculadas)
- 🧠 **Assistente inteligente**: responde com base nos dados carregados e nas métricas do app
- 🏟️ **Perfil por time e por partida**: resumo, tendências e contexto
- 🗓️ **Calendário de ligas**: suporte a calendário unificado para puxar jogos do dia
- 🧑‍⚖️ **Árbitros**: integração de perfil disciplinar para enriquecer a leitura de cartões
- ✅ **Validação e consistência de dados**: checagem de colunas mínimas e normalização
- ⚡ **Performance**: cache e processamento otimizado para evitar recálculo desnecessário

---

## 🧱 Stack

- Python 3.10+
- Streamlit
- Pandas / NumPy
- (Opcional) Scikit-learn / Statsmodels (caso evolua para modelos adicionais)

---

## 📂 Estrutura do projeto (visão geral)

> A estrutura pode variar conforme evolução do projeto, mas a ideia é manter o app modular.

- `app.py` → aplicação Streamlit (UI e orquestração)
- `core/` → motor do projeto (cálculos, métricas, previsões, assistente)
- `data/` → bases (CSVs das ligas, calendário, árbitros)
- `updater/` → scripts de atualização de dados (ex: `atualizador.py`)
- `legacy/` → versão antiga preservada (quando aplicável)

---

