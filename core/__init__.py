"""
Modulo core - Logica di business per FISTF Tournament Manager.
Espone tutte le funzionalità principali dell'applicazione.
"""

# ========================================
# REGOLE FISTF (importazione diretta, OK)
# ========================================
from .fistf_rules import (
    Category, CompetitionType,
    get_category_rules, get_competition_type, get_standings_criteria,
    apply_youth_cap, validate_team_roster, validate_team_match_foreigners,
    LICENCE_FORMAT, TEAM_ID_FORMAT
)

# ========================================
# GENERATORI (importazione diretta, OK)
# ========================================
from .scheduler import TournamentScheduler, generate_tournament_schedule, print_schedule_summary
from .knockout_generator import KnockoutGenerator, get_qualifiers_per_group

# ========================================
# GENERATORI SQUADRE (importazione diretta, OK)
# ========================================
from .team_scheduler import TeamTournamentScheduler, generate_team_tournament_schedule
from .team_knockout_generator import TeamKnockoutGenerator

# ========================================
# CLASSIFICHE (importazione diretta, OK)
# ========================================
from .standings_calculator import StandingsCalculator
from .team_standings_calculator import TeamStandingsCalculator

# ========================================
# MARCATORI - NON IMPORTARE DIRETTAMENTE PER EVITARE CIRCULAR IMPORT
# ========================================
# NOTA: scorers_calculator e team_scorers_calculator importano models
# quindi li importiamo in modo differito (lazy import)

# ========================================
# PDF EXPORTER
# ========================================
from .pdf_exporter import (PDFExporter, export_schedule, export_standings, 
                          export_knockout, export_groups)

# ========================================
# VERSIONE E METADATI
# ========================================
__version__ = "2.0.0"
__author__ = "FISTF Tournament Manager Team"
__description__ = "Gestione tornei di calcio da tavolo FISTF"

# ========================================
# ESPORTAZIONE TUTTI I SIMBOLI PRINCIPALI
# ========================================
__all__ = [
    # Regole FISTF
    'Category',
    'CompetitionType',
    'get_category_rules',
    'get_competition_type',
    'get_standings_criteria',
    'apply_youth_cap',
    'validate_team_roster',
    'validate_team_match_foreigners',
    'LICENCE_FORMAT',
    'TEAM_ID_FORMAT',
    
    # Generatori individuali
    'TournamentScheduler',
    'generate_tournament_schedule',
    'print_schedule_summary',
    'KnockoutGenerator',
    'get_qualifiers_per_group',
    
    # Generatori squadre
    'TeamTournamentScheduler',
    'generate_team_tournament_schedule',
    'TeamKnockoutGenerator',
    
    # Classifiche
    'StandingsCalculator',
    'TeamStandingsCalculator',
    
    # Marcatori (verranno importati in modo differito)
    'ScorersCalculator',
    'TeamScorersCalculator',
    'calculate_team_scorers',
    'get_top_scorer',
    
    # PDF
    'PDFExporter',
    'export_schedule',
    'export_standings',
    'export_knockout',
    'export_groups',
]

# ========================================
# FUNZIONI DI UTILITÀ CON LAZY IMPORT
# ========================================

# Cache per i moduli importati in modo differito
_scorers_calculator = None
_team_scorers_calculator = None


def _get_scorers_calculator():
    """Importa ScorersCalculator in modo differito per evitare circular import."""
    global _scorers_calculator
    if _scorers_calculator is None:
        from .scorers_calculator import ScorersCalculator
        _scorers_calculator = ScorersCalculator
    return _scorers_calculator


def _get_team_scorers_calculator():
    """Importa TeamScorersCalculator in modo differito per evitare circular import."""
    global _team_scorers_calculator
    if _team_scorers_calculator is None:
        from .team_scorers_calculator import TeamScorersCalculator, calculate_team_scorers, get_top_scorer
        _team_scorers_calculator = (TeamScorersCalculator, calculate_team_scorers, get_top_scorer)
    return _team_scorers_calculator


# Esponiamo i simboli come proprietà per mantenere l'API
@property
def ScorersCalculator():
    return _get_scorers_calculator()


@property
def TeamScorersCalculator():
    return _get_team_scorers_calculator()[0]


@property
def calculate_team_scorers():
    return _get_team_scorers_calculator()[1]


@property
def get_top_scorer():
    return _get_team_scorers_calculator()[2]


def get_core_info():
    """Restituisce informazioni sul modulo core."""
    return {
        "version": __version__,
        "description": __description__,
        "modules": [
            "fistf_rules",
            "scheduler",
            "team_scheduler",
            "knockout_generator",
            "team_knockout_generator",
            "standings_calculator",
            "team_standings_calculator",
            "scorers_calculator",
            "team_scorers_calculator",
            "pdf_exporter"
        ]
    }


def get_available_calculators():
    """Restituisce la lista dei calculator disponibili (con lazy import)."""
    return {
        "individual": {
            "calendar": TournamentScheduler,
            "knockout": KnockoutGenerator,
            "standings": StandingsCalculator,
            "scorers": _get_scorers_calculator(),
        },
        "team": {
            "scheduler": TeamTournamentScheduler,
            "knockout": TeamKnockoutGenerator,
            "standings": TeamStandingsCalculator,
            "scorers": _get_team_scorers_calculator()[0],
        }
    }


# ========================================
# TEST RAPIDO
# ========================================

if __name__ == "__main__":
    print(f"📦 Core module v{__version__}")
    print(f"📝 {__description__}")
    print("\n📋 Moduli disponibili:")
    for module in __all__:
        print(f"   • {module}")
    
    print("\n📊 Calculator disponibili:")
    calcs = get_available_calculators()
    print(f"   Individuale: {list(calcs['individual'].keys())}")
    print(f"   Squadre: {list(calcs['team'].keys())}")