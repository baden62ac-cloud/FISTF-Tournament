# utils/__init__.py
"""
Modulo utility - Funzioni di utilità e costanti per FISTF Tournament Manager.
Espone tutte le funzionalità di supporto dell'applicazione.
"""

# ========================================
# ESPORTAZIONE COSTANTI
# ========================================
from .constants import (
    # Mapping categorie
    CATEGORY_PREFIX,
    PREFIX_TO_CATEGORY,
    
    # Criteri classifica
    INDIVIDUAL_STANDINGS_CRITERIA,
    TEAM_STANDINGS_CRITERIA,
    
    # Fasi knockout
    KNOCKOUT_PHASES,
    KNOCKOUT_PHASE_ORDER,
    KNOCKOUT_PHASE_PREFIX,
    KNOCKOUT_PHASE_DISPLAY,
    
    # Tipi evento
    EVENT_TYPES,
    
    # Limiti e valori default
    MIN_PLAYERS_PER_TEAM,
    MAX_PLAYERS_PER_TEAM,
    MIN_PLAYERS_PER_GROUP,
    MAX_PLAYERS_PER_GROUP,
    MAX_FOREIGN_PLAYERS_PER_MATCH,
    DEFAULT_FIELDS,
    MAX_FIELDS,
    QUALIFIERS_PER_GROUP,
    
    # Stili UI
    STYLE_BUTTON_PRIMARY,
    STYLE_BUTTON_DANGER,
    STYLE_BUTTON_WARNING,
    STYLE_BUTTON_INFO,
    STYLE_BUTTON_SECONDARY,
    STYLE_BUTTON_PDF,
    
    # Colori stati partita
    MATCH_STATUS_COLORS,
    
    # Tipo competizione
    CompetitionType,
    
    # Funzioni di utilità
    get_category_prefix,
    get_phase_number_from_id,
    get_phase_display,
)

# ========================================
# ESPORTAZIONE FUNZIONI DI UTILITÀ
# ========================================
from .helpers import (
    # Validazione
    validate_licence,
    validate_country,
    validate_team_id,
    
    # Conversione
    safe_int,
    safe_float,
    parse_result,
    
    # File system
    ensure_directory,
    get_data_dir,
    get_pdf_dir,
    get_saves_dir,
    get_backup_dir,
    get_timestamp,
    sanitize_filename,
    
    # Data e ora
    format_date,
    format_datetime,
    parse_date,
    
    # Statistiche
    calculate_win_percentage,
    calculate_average,
    format_average,
    
    # Distribuzione gironi
    calculate_group_sizes,
    get_qualifiers_from_group_size,
    snake_distribution,
    
    # Esportazione
    prepare_export_dataframe,
    save_dataframe_excel,
    save_dataframe_csv,
    
    # Debug
    print_dict_structure,
    log_function_call,
)


# ========================================
# METADATI
# ========================================
__version__ = "1.0.0"
__author__ = "FISTF Tournament Manager Team"
__description__ = "Utility e costanti per FISTF Tournament Manager"


# ========================================
# FUNZIONI DI UTILITÀ AGGIUNTIVE
# ========================================

def get_utils_info():
    """Restituisce informazioni sul modulo utility."""
    return {
        "version": __version__,
        "description": __description__,
        "modules": ["constants", "helpers"],
        "categories": list(CATEGORY_PREFIX.keys()),
        "event_types": EVENT_TYPES,
        "knockout_phases": KNOCKOUT_PHASES,
    }


def get_all_constants():
    """Restituisce tutte le costanti in un unico dizionario."""
    return {
        "category_prefix": CATEGORY_PREFIX,
        "individual_standings_criteria": INDIVIDUAL_STANDINGS_CRITERIA,
        "team_standings_criteria": TEAM_STANDINGS_CRITERIA,
        "knockout_phases": KNOCKOUT_PHASES,
        "event_types": EVENT_TYPES,
        "min_players_per_team": MIN_PLAYERS_PER_TEAM,
        "max_players_per_team": MAX_PLAYERS_PER_TEAM,
        "min_players_per_group": MIN_PLAYERS_PER_GROUP,
        "max_players_per_group": MAX_PLAYERS_PER_GROUP,
        "default_fields": DEFAULT_FIELDS,
        "max_fields": MAX_FIELDS,
        "qualifiers_per_group": QUALIFIERS_PER_GROUP,
    }


# ========================================
# ESPORTAZIONE TUTTI I SIMBOLI PRINCIPALI
# ========================================
__all__ = [
    # Constants
    'CATEGORY_PREFIX',
    'PREFIX_TO_CATEGORY',
    'INDIVIDUAL_STANDINGS_CRITERIA',
    'TEAM_STANDINGS_CRITERIA',
    'KNOCKOUT_PHASES',
    'KNOCKOUT_PHASE_ORDER',
    'KNOCKOUT_PHASE_PREFIX',
    'KNOCKOUT_PHASE_DISPLAY',
    'EVENT_TYPES',
    'MIN_PLAYERS_PER_TEAM',
    'MAX_PLAYERS_PER_TEAM',
    'MIN_PLAYERS_PER_GROUP',
    'MAX_PLAYERS_PER_GROUP',
    'MAX_FOREIGN_PLAYERS_PER_MATCH',
    'DEFAULT_FIELDS',
    'MAX_FIELDS',
    'QUALIFIERS_PER_GROUP',
    'STYLE_BUTTON_PRIMARY',
    'STYLE_BUTTON_DANGER',
    'STYLE_BUTTON_WARNING',
    'STYLE_BUTTON_INFO',
    'STYLE_BUTTON_SECONDARY',
    'STYLE_BUTTON_PDF',
    'MATCH_STATUS_COLORS',
    'CompetitionType',
    'get_category_prefix',
    'get_phase_number_from_id',
    'get_phase_display',
    
    # Helpers
    'validate_licence',
    'validate_country',
    'validate_team_id',
    'safe_int',
    'safe_float',
    'parse_result',
    'ensure_directory',
    'get_data_dir',
    'get_pdf_dir',
    'get_saves_dir',
    'get_backup_dir',
    'get_timestamp',
    'sanitize_filename',
    'format_date',
    'format_datetime',
    'parse_date',
    'calculate_win_percentage',
    'calculate_average',
    'format_average',
    'calculate_group_sizes',
    'get_qualifiers_from_group_size',
    'snake_distribution',
    'prepare_export_dataframe',
    'save_dataframe_excel',
    'save_dataframe_csv',
    'print_dict_structure',
    'log_function_call',
    
    # Metadata
    'get_utils_info',
    'get_all_constants',
]


# ========================================
# TEST RAPIDO (SE ESEGUITO DIRETTAMENTE)
# ========================================

if __name__ == "__main__":
    print(f"📦 Utility module v{__version__}")
    print(f"📝 {__description__}")
    print("\n📋 Costanti disponibili:")
    print(f"   • Categorie: {len(CATEGORY_PREFIX)}")
    print(f"   • Event types: {len(EVENT_TYPES)}")
    print(f"   • Knockout phases: {len(KNOCKOUT_PHASES)}")
    
    print("\n📋 Funzioni disponibili:")
    from .helpers import __all__ as helpers_all
    print(f"   • Helpers: {len(helpers_all)}")
    
    print("\n✅ Modulo utility caricato correttamente")