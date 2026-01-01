"""
FutPrevisão V2.0 - Validador de Schemas
Validação robusta de dados com mensagens acionáveis

Funcionalidades:
- Validação de CSVs de ligas
- Validação de calendário
- Validação de árbitros
- Relatórios detalhados de cobertura
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import pandas as pd
from pathlib import Path


# ==============================================================================
# DATACLASSES
# ==============================================================================

@dataclass
class ValidationReport:
    """Relatório de validação"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    coverage: Dict[str, float] = field(default_factory=dict)
    total_rows: int = 0
    
    def add_error(self, message: str):
        """Adiciona erro"""
        self.errors.append(f"❌ {message}")
        self.valid = False
    
    def add_warning(self, message: str):
        """Adiciona aviso"""
        self.warnings.append(f"⚠️ {message}")
    
    def is_valid(self) -> bool:
        """Retorna se validação passou"""
        return self.valid and len(self.errors) == 0
    
    def summary(self) -> str:
        """Resumo da validação"""
        status = "✅ VÁLIDO" if self.is_valid() else "❌ INVÁLIDO"
        
        summary = [f"\n{status}"]
        summary.append(f"Total de linhas: {self.total_rows}")
        
        if self.errors:
            summary.append(f"\n🔴 Erros ({len(self.errors)}):")
            summary.extend(self.errors)
        
        if self.warnings:
            summary.append(f"\n🟡 Avisos ({len(self.warnings)}):")
            summary.extend(self.warnings)
        
        if self.coverage:
            summary.append("\n📊 Cobertura:")
            for col, pct in self.coverage.items():
                emoji = "✅" if pct >= 0.8 else "⚠️" if pct >= 0.5 else "❌"
                summary.append(f"  {emoji} {col}: {pct:.1%}")
        
        return "\n".join(summary)


# ==============================================================================
# SCHEMAS OBRIGATÓRIOS
# ==============================================================================

LEAGUE_REQUIRED_COLUMNS = {
    'Date': str,
    'HomeTeam': str,
    'AwayTeam': str,
    'HC': (int, float),  # Home Corners
    'AC': (int, float),  # Away Corners
    'HY': (int, float),  # Home Yellow cards
    'AY': (int, float),  # Away Yellow cards
}

LEAGUE_OPTIONAL_COLUMNS = {
    'Referee': str,
    'HR': (int, float),  # Home Red cards
    'AR': (int, float),  # Away Red cards
    'HF': (int, float),  # Home Fouls
    'AF': (int, float),  # Away Fouls
    'HS': (int, float),  # Home Shots
    'AS': (int, float),  # Away Shots
    'HST': (int, float), # Home Shots on Target
    'AST': (int, float), # Away Shots on Target
    'FTHG': (int, float), # Full Time Home Goals
    'FTAG': (int, float), # Full Time Away Goals
}

CALENDAR_REQUIRED_COLUMNS = {
    'Data': str,
    'Hora': str,
    'Liga': str,
    'Time_Casa': str,
    'Time_Visitante': str,
}

REFEREE_REQUIRED_COLUMNS = {
    'Liga': str,
    'Arbitro': str,
    'Media_Cartoes_Por_Jogo': float,
    'Jogos_Apitados': int,
}


# ==============================================================================
# VALIDADOR PRINCIPAL
# ==============================================================================

class SchemaValidator:
    """Validador de schemas de dados"""
    
    def __init__(self):
        self.min_coverage = 0.5  # 50% mínimo de dados não-nulos
    
    def validate_league(
        self, 
        df: pd.DataFrame, 
        filename: str = "unknown.csv"
    ) -> ValidationReport:
        """
        Valida schema de arquivo de liga
        
        Args:
            df: DataFrame a validar
            filename: Nome do arquivo (para mensagens)
        
        Returns:
            ValidationReport com resultados
        """
        report = ValidationReport(valid=True, total_rows=len(df))
        
        # 1. Verificar se DataFrame vazio
        if df.empty:
            report.add_error(f"{filename}: DataFrame vazio")
            return report
        
        # 2. Verificar colunas obrigatórias
        missing_required = []
        for col, dtype in LEAGUE_REQUIRED_COLUMNS.items():
            if col not in df.columns:
                missing_required.append(col)
        
        if missing_required:
            report.add_error(
                f"{filename}: Colunas obrigatórias faltando: {', '.join(missing_required)}"
            )
            return report
        
        # 3. Verificar tipos de dados
        for col, expected_dtype in LEAGUE_REQUIRED_COLUMNS.items():
            if col not in df.columns:
                continue
            
            # Tentar converter
            try:
                if expected_dtype == str:
                    df[col] = df[col].astype(str)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception as e:
                report.add_error(f"{filename}: Erro ao converter coluna {col}: {str(e)}")
        
        # 4. Verificar cobertura (dados não-nulos)
        for col in LEAGUE_REQUIRED_COLUMNS.keys():
            if col not in df.columns:
                continue
            
            non_null = df[col].notna().sum()
            coverage = non_null / len(df) if len(df) > 0 else 0
            report.coverage[col] = coverage
            
            if coverage < self.min_coverage:
                report.add_error(
                    f"{filename}: Coluna {col} tem cobertura muito baixa ({coverage:.1%})"
                )
        
        # 5. Verificar valores válidos
        # Corners e cartões não podem ser negativos
        for col in ['HC', 'AC', 'HY', 'AY']:
            if col in df.columns:
                negatives = (df[col] < 0).sum()
                if negatives > 0:
                    report.add_error(f"{filename}: {col} tem {negatives} valores negativos")
        
        # 6. Verificar colunas opcionais (avisos)
        missing_optional = []
        for col in LEAGUE_OPTIONAL_COLUMNS.keys():
            if col not in df.columns:
                missing_optional.append(col)
        
        if missing_optional:
            report.add_warning(
                f"{filename}: Colunas opcionais faltando (pode reduzir precisão): "
                f"{', '.join(missing_optional[:5])}"
            )
        
        # 7. Verificar duplicatas
        if 'Date' in df.columns and 'HomeTeam' in df.columns and 'AwayTeam' in df.columns:
            duplicates = df.duplicated(subset=['Date', 'HomeTeam', 'AwayTeam']).sum()
            if duplicates > 0:
                report.add_warning(f"{filename}: {duplicates} jogos duplicados encontrados")
        
        # 8. Verificar consistência de nomes
        if 'HomeTeam' in df.columns:
            unique_teams = df['HomeTeam'].nunique()
            if unique_teams < 10:
                report.add_warning(f"{filename}: Apenas {unique_teams} times únicos (esperado 18-20)")
        
        return report
    
    def validate_calendar(
        self, 
        df: pd.DataFrame, 
        filename: str = "calendario_ligas.csv"
    ) -> ValidationReport:
        """
        Valida schema de calendário
        
        Args:
            df: DataFrame a validar
            filename: Nome do arquivo
        
        Returns:
            ValidationReport
        """
        report = ValidationReport(valid=True, total_rows=len(df))
        
        # 1. Verificar se vazio
        if df.empty:
            report.add_error(f"{filename}: DataFrame vazio")
            return report
        
        # 2. Verificar colunas obrigatórias
        missing = []
        for col in CALENDAR_REQUIRED_COLUMNS.keys():
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            report.add_error(
                f"{filename}: Colunas obrigatórias faltando: {', '.join(missing)}"
            )
            return report
        
        # 3. Verificar cobertura
        for col in CALENDAR_REQUIRED_COLUMNS.keys():
            non_null = df[col].notna().sum()
            coverage = non_null / len(df) if len(df) > 0 else 0
            report.coverage[col] = coverage
            
            if coverage < 0.9:  # Calendário precisa 90% de cobertura
                report.add_error(
                    f"{filename}: Coluna {col} tem cobertura baixa ({coverage:.1%})"
                )
        
        # 4. Verificar formato de data
        if 'Data' in df.columns:
            try:
                # Tentar parsear datas
                pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            except:
                report.add_warning(f"{filename}: Formato de data pode estar incorreto (use DD/MM/YYYY)")
        
        # 5. Verificar ligas conhecidas
        if 'Liga' in df.columns:
            ligas = df['Liga'].unique()
            report.add_warning(f"{filename}: {len(ligas)} ligas encontradas: {', '.join(ligas[:5])}")
        
        return report
    
    def validate_referees(
        self, 
        df: pd.DataFrame, 
        filename: str = "arbitros.csv"
    ) -> ValidationReport:
        """
        Valida schema de árbitros
        
        Args:
            df: DataFrame a validar
            filename: Nome do arquivo
        
        Returns:
            ValidationReport
        """
        report = ValidationReport(valid=True, total_rows=len(df))
        
        # 1. Verificar se vazio
        if df.empty:
            report.add_error(f"{filename}: DataFrame vazio")
            return report
        
        # 2. Verificar colunas obrigatórias
        missing = []
        for col in REFEREE_REQUIRED_COLUMNS.keys():
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            report.add_error(
                f"{filename}: Colunas obrigatórias faltando: {', '.join(missing)}"
            )
            return report
        
        # 3. Verificar tipos
        if 'Jogos_Apitados' in df.columns:
            try:
                df['Jogos_Apitados'] = pd.to_numeric(df['Jogos_Apitados'], errors='coerce')
                zeros = (df['Jogos_Apitados'] == 0).sum()
                if zeros > 0:
                    report.add_warning(f"{filename}: {zeros} árbitros com 0 jogos apitados")
            except:
                report.add_error(f"{filename}: Coluna Jogos_Apitados não numérica")
        
        if 'Media_Cartoes_Por_Jogo' in df.columns:
            try:
                df['Media_Cartoes_Por_Jogo'] = pd.to_numeric(
                    df['Media_Cartoes_Por_Jogo'], 
                    errors='coerce'
                )
                
                # Verificar se valores razoáveis (0-10 cartões)
                outliers = ((df['Media_Cartoes_Por_Jogo'] < 0) | 
                           (df['Media_Cartoes_Por_Jogo'] > 10)).sum()
                if outliers > 0:
                    report.add_warning(
                        f"{filename}: {outliers} árbitros com média fora do esperado (0-10)"
                    )
            except:
                report.add_error(f"{filename}: Coluna Media_Cartoes_Por_Jogo não numérica")
        
        # 4. Verificar cobertura
        for col in REFEREE_REQUIRED_COLUMNS.keys():
            non_null = df[col].notna().sum()
            coverage = non_null / len(df) if len(df) > 0 else 0
            report.coverage[col] = coverage
            
            if coverage < 0.9:
                report.add_warning(
                    f"{filename}: Coluna {col} tem cobertura baixa ({coverage:.1%})"
                )
        
        return report
    
    def validate_directory(self, leagues_dir: str) -> Dict[str, ValidationReport]:
        """
        Valida todos os CSVs em um diretório
        
        Args:
            leagues_dir: Caminho do diretório
        
        Returns:
            Dict com {filename: ValidationReport}
        """
        results = {}
        
        path = Path(leagues_dir)
        
        if not path.exists():
            return results
        
        for csv_file in path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                report = self.validate_league(df, csv_file.name)
                results[csv_file.name] = report
            except Exception as e:
                report = ValidationReport(valid=False)
                report.add_error(f"Erro ao carregar {csv_file.name}: {str(e)}")
                results[csv_file.name] = report
        
        return results


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def get_column_info(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Retorna informações detalhadas sobre colunas
    
    Args:
        df: DataFrame
    
    Returns:
        Dict com info de cada coluna
    """
    info = {}
    
    for col in df.columns:
        info[col] = {
            'dtype': str(df[col].dtype),
            'non_null': df[col].notna().sum(),
            'null': df[col].isna().sum(),
            'coverage': df[col].notna().sum() / len(df) if len(df) > 0 else 0,
            'unique': df[col].nunique(),
        }
        
        # Adicionar stats para numéricos
        if pd.api.types.is_numeric_dtype(df[col]):
            info[col].update({
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
            })
    
    return info


def suggest_fixes(report: ValidationReport) -> List[str]:
    """
    Sugere correções baseadas no relatório
    
    Args:
        report: ValidationReport
    
    Returns:
        Lista de sugestões
    """
    suggestions = []
    
    for error in report.errors:
        if "faltando" in error.lower():
            suggestions.append("💡 Verifique se o CSV está no formato correto do Football-Data.co.uk")
        
        if "cobertura" in error.lower():
            suggestions.append("💡 Dados faltando podem indicar jogos não finalizados ou erros de scraping")
        
        if "negativo" in error.lower():
            suggestions.append("💡 Valores negativos indicam erro nos dados - verifique a fonte")
    
    # Remove duplicatas
    return list(set(suggestions))


def validate_all_data(
    leagues_dir: str,
    calendar_path: str,
    referees_path: str
) -> Dict[str, ValidationReport]:
    """
    Valida todos os dados do sistema
    
    Args:
        leagues_dir: Diretório das ligas
        calendar_path: Caminho do calendário
        referees_path: Caminho dos árbitros
    
    Returns:
        Dict com todos os relatórios
    """
    validator = SchemaValidator()
    results = {}
    
    # 1. Validar ligas
    league_results = validator.validate_directory(leagues_dir)
    results.update(league_results)
    
    # 2. Validar calendário
    try:
        df_calendar = pd.read_csv(calendar_path, encoding='utf-8')
        results['calendario'] = validator.validate_calendar(df_calendar)
    except Exception as e:
        report = ValidationReport(valid=False)
        report.add_error(f"Erro ao carregar calendário: {str(e)}")
        results['calendario'] = report
    
    # 3. Validar árbitros
    try:
        df_referees = pd.read_csv(referees_path, encoding='utf-8')
        results['arbitros'] = validator.validate_referees(df_referees)
    except Exception as e:
        report = ValidationReport(valid=False)
        report.add_error(f"Erro ao carregar árbitros: {str(e)}")
        results['arbitros'] = report
    
    return results


def print_validation_summary(results: Dict[str, ValidationReport]):
    """
    Imprime resumo de todas as validações
    
    Args:
        results: Dict de resultados
    """
    print("\n" + "="*60)
    print("📊 RESUMO DE VALIDAÇÃO")
    print("="*60)
    
    total = len(results)
    valid = sum(1 for r in results.values() if r.is_valid())
    
    print(f"\nTotal de arquivos: {total}")
    print(f"✅ Válidos: {valid}")
    print(f"❌ Inválidos: {total - valid}")
    
    print("\n" + "-"*60)
    
    for filename, report in results.items():
        status = "✅" if report.is_valid() else "❌"
        print(f"\n{status} {filename}")
        
        if report.errors:
            for error in report.errors[:3]:  # Mostrar só primeiros 3
                print(f"  {error}")
        
        if report.warnings and report.is_valid():
            print(f"  ⚠️ {len(report.warnings)} avisos")
    
    print("\n" + "="*60)
