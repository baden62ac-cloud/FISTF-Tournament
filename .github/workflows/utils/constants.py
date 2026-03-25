# utils/constants.py
"""
Costanti e mapping per FISTF Tournament Manager.
Centralizza tutte le costanti utilizzate nell'applicazione.
"""

from enum import Enum
from typing import Dict, List, Optional

# ========================================
# MAPPING CATEGORIE PREFISSI
# ========================================
CATEGORY_PREFIX: Dict[str, str] = {
    # Individuali
    "Open": "O",
    "Veterans": "V",
    "Women": "W",
    "U20": "U20",
    "U16": "U16",
    "U12": "U12",
    "Eccellenza": "E",
    "Promozione": "P",
    "MOICAT": "M",
    
    # Squadre
    "Team Open": "TO",
    "Team Veterans": "TV",
    "Team Women": "TW",
    "Team U20": "TU20",
    "Team U16": "TU16",
    "Team U12": "TU12",
    "Team Eccellenza": "TE",
    "Team Promozione": "TP",
    "Team MOICAT": "TM",
}

# Mappa inversa (prefisso -> categoria)
PREFIX_TO_CATEGORY: Dict[str, str] = {v: k for k, v in CATEGORY_PREFIX.items()}


# ========================================
# CRITERI CLASSIFICA FISTF
# ========================================

# Criteri individuali (FISTF 2.1.2.b)
INDIVIDUAL_STANDINGS_CRITERIA: List[str] = [
    "1. Punti",
    "2. Punti scontri diretti",
    "3. Differenza reti scontri diretti",
    "4. Gol segnati scontri diretti",
    "5. Differenza reti totale",
    "6. Gol segnati totali",
    "7. Shoot-out (se necessario)"
]

# Criteri squadre (FISTF 2.2.2.b)
TEAM_STANDINGS_CRITERIA: List[str] = [
    "1. Punti squadra",
    "2. Punti scontri diretti",
    "3. Differenza vittorie individuali H2H",
    "4. Vittorie individuali H2H",
    "5. Differenza vittorie individuali totale",
    "6. Vittorie individuali totali",
    "7. Differenza reti H2H",
    "8. Gol segnati H2H",
    "9. Differenza reti totale",
    "10. Gol segnati totali",
    "11. Shoot-out (se necessario)"
]


# ========================================
# ORDINE FASI ELIMINAZIONE
# ========================================
KNOCKOUT_PHASES: List[str] = ["BARRAGE", "R64", "R32", "R16", "QF", "SF", "F"]

KNOCKOUT_PHASE_ORDER: Dict[str, int] = {
    "BARRAGE": 0,
    "R64": 1,
    "R32": 2,
    "R16": 3,
    "QF": 4,
    "SF": 5,
    "F": 6
}

KNOCKOUT_PHASE_PREFIX: Dict[str, str] = {
    "BARRAGE": "B",
    "QF": "QF",
    "SF": "SF",
    "F": "F"
}

KNOCKOUT_PHASE_DISPLAY: Dict[str, str] = {
    "BARRAGE": "Spareggio",
    "R64": "64° di Finale",
    "R32": "32° di Finale",
    "R16": "16° di Finale",
    "QF": "Quarti di Finale",
    "SF": "Semifinale",
    "F": "Finale"
}


# ========================================
# TIPI EVENTO FISTF
# ========================================
EVENT_TYPES: List[str] = [
    "Major Grand Prix",
    "International Grand Prix",
    "Golden Grand Prix",
    "International Open",
    "Satellite",
    "Regionale",
    "Provinciale"
]


# ========================================
# LIMITI E VALORI DEFAULT
# ========================================
MIN_PLAYERS_PER_TEAM: int = 3
MAX_PLAYERS_PER_TEAM: int = 8
MIN_PLAYERS_PER_GROUP: int = 3
MAX_PLAYERS_PER_GROUP: int = 10
MAX_FOREIGN_PLAYERS_PER_MATCH: int = 2
DEFAULT_FIELDS: int = 4
MAX_FIELDS: int = 20

# Limiti per fase finale
MAX_GROUPS_FOR_QUALIFIERS: int = 32
QUALIFIERS_PER_GROUP: Dict[int, int] = {
    3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4
}


# ========================================
# STILI UI
# ========================================
STYLE_BUTTON_PRIMARY: str = """
    QPushButton {
        background-color: #4CAF50;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""

STYLE_BUTTON_DANGER: str = """
    QPushButton {
        background-color: #f44336;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #d32f2f;
    }
"""

STYLE_BUTTON_WARNING: str = """
    QPushButton {
        background-color: #FF9800;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #F57C00;
    }
"""

STYLE_BUTTON_INFO: str = """
    QPushButton {
        background-color: #2196F3;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1976D2;
    }
"""

STYLE_BUTTON_SECONDARY: str = """
    QPushButton {
        background-color: #6c757d;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5a6268;
    }
"""

STYLE_BUTTON_PDF: str = """
    QPushButton {
        background-color: #dc3545;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #c82333;
    }
"""


# ========================================
# COLORI PER STATI PARTITA
# ========================================
MATCH_STATUS_COLORS: Dict[str, str] = {
    "Giocata": "#90EE90",      # Verde chiaro
    "COMPLETED": "#90EE90",
    "Programmata": "#D3D3D3",  # Grigio
    "SCHEDULED": "#D3D3D3",
    "In corso": "#FFF3CD",     # Giallo chiaro
    "IN_PROGRESS": "#FFF3CD",
    "Forfait": "#FFB6C1",      # Rosa
    "FORFEIT": "#FFB6C1",
}


# ========================================
# TIPO COMPETIZIONE
# ========================================
class CompetitionType(str, Enum):
    """Tipo di competizione."""
    INDIVIDUAL = "individual"
    TEAM = "team"


# ========================================
# FUNZIONI DI UTILITÀ
# ========================================

def get_category_prefix(category: str) -> str:
    """Restituisce il prefisso per una categoria."""
    return CATEGORY_PREFIX.get(category, "X")


def get_phase_number_from_id(match_id: str) -> int:
    """Estrae il numero della partita dalla fase dall'ID."""
    parts = match_id.split('_')
    if len(parts) >= 3:
        try:
            return int(parts[-1])
        except ValueError:
            return 1
    elif len(parts) == 2:
        try:
            return int(parts[1])
        except ValueError:
            return 1
    return 1


def get_phase_display(phase: str) -> str:
    """Restituisce il nome visualizzato per una fase."""
    return KNOCKOUT_PHASE_DISPLAY.get(phase, phase)