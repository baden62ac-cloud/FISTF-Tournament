# config/__init__.py
"""
Modulo config - Configurazioni e formule per FISTF Tournament Manager.
Fornisce le formule per la fase finale e i criteri di spareggio.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# ========================================
# CARICAMENTO FORMULE
# ========================================

def load_bracket_formulas() -> Dict[str, Any]:
    """
    Carica le formule per la fase finale dal file JSON.
    
    Returns:
        Dizionario con le formule per numero di gironi
    """
    formulas_path = Path(__file__).parent / "bracket_formulas.json"
    if formulas_path.exists():
        with open(formulas_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_tiebreakers() -> Dict[str, List[str]]:
    """
    Carica i criteri di spareggio dal file JSON.
    
    Returns:
        Dizionario con i criteri per tipo torneo
    """
    tiebreakers_path = Path(__file__).parent / "tiebreakers.json"
    if tiebreakers_path.exists():
        with open(tiebreakers_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ========================================
# FORMULE PREDEFINITE (FALLBACK)
# ========================================

# Formule di fallback se il file JSON non è disponibile
FALLBACK_BRACKET_FORMULAS: Dict[str, List[str]] = {
    "2": ["SF", "F"],
    "3": ["QF", "SF", "F"],
    "4": ["QF", "SF", "F"],
    "5": ["BARRAGE", "QF", "SF", "F"],
    "6": ["BARRAGE", "QF", "SF", "F"],
    "7": ["R16", "QF", "SF", "F"],
    "8": ["R16", "QF", "SF", "F"],
}

# Criteri di fallback
FALLBACK_TIEBREAKERS: Dict[str, List[str]] = {
    "individual": [
        "Punti",
        "Punti scontri diretti",
        "Differenza reti scontri diretti",
        "Gol segnati scontri diretti",
        "Differenza reti totale",
        "Gol segnati totali",
        "Shoot-out"
    ],
    "team": [
        "Punti squadra",
        "Punti scontri diretti",
        "Differenza vittorie individuali H2H",
        "Vittorie individuali H2H",
        "Differenza vittorie individuali totale",
        "Vittorie individuali totali",
        "Differenza reti H2H",
        "Gol segnati H2H",
        "Differenza reti totale",
        "Gol segnati totali",
        "Shoot-out"
    ]
}


# ========================================
# FUNZIONI DI ACCESSO
# ========================================

def get_bracket_formula(num_groups: int) -> Optional[List[str]]:
    """
    Restituisce la formula per la fase finale dato il numero di gironi.
    
    Args:
        num_groups: Numero di gironi
    
    Returns:
        Lista delle fasi da generare, o None se non trovata
    """
    formulas = load_bracket_formulas()
    key = str(num_groups)
    
    if key in formulas:
        return formulas[key]
    
    # Fallback alle formule predefinite
    return FALLBACK_BRACKET_FORMULAS.get(key)


def get_tiebreakers(tournament_type: str = "individual") -> List[str]:
    """
    Restituisce i criteri di spareggio per il tipo di torneo.
    
    Args:
        tournament_type: "individual" o "team"
    
    Returns:
        Lista dei criteri in ordine di applicazione
    """
    tiebreakers = load_tiebreakers()
    
    if tournament_type in tiebreakers:
        return tiebreakers[tournament_type]
    
    # Fallback ai criteri predefiniti
    return FALLBACK_TIEBREAKERS.get(tournament_type, FALLBACK_TIEBREAKERS["individual"])


# ========================================
# ESPORTAZIONE PRINCIPALE
# ========================================

__all__ = [
    # Caricamento
    'load_bracket_formulas',
    'load_tiebreakers',
    
    # Accesso formule
    'get_bracket_formula',
    'get_tiebreakers',
    
    # Fallback
    'FALLBACK_BRACKET_FORMULAS',
    'FALLBACK_TIEBREAKERS',
]

__version__ = "1.0.0"
__author__ = "FISTF Tournament Manager Team"
__description__ = "Configurazioni e formule per FISTF Tournament Manager"


# ========================================
# FUNZIONI DI UTILITÀ
# ========================================

def get_config_info() -> Dict[str, Any]:
    """Restituisce informazioni sul modulo config."""
    formulas = load_bracket_formulas()
    tiebreakers = load_tiebreakers()
    
    return {
        "version": __version__,
        "description": __description__,
        "formulas_loaded": len(formulas) > 0,
        "formulas_count": len(formulas),
        "tiebreakers_loaded": len(tiebreakers) > 0,
        "available_formulas": list(formulas.keys()),
        "available_tiebreakers": list(tiebreakers.keys()),
    }


def reload_config():
    """Ricarica le configurazioni dai file JSON."""
    global _formulas_cache, _tiebreakers_cache
    _formulas_cache = None
    _tiebreakers_cache = None
    return load_bracket_formulas(), load_tiebreakers()


# Cache per evitare ricariche continue
_formulas_cache = None
_tiebreakers_cache = None


def get_cached_bracket_formulas() -> Dict[str, Any]:
    """Restituisce le formule in cache."""
    global _formulas_cache
    if _formulas_cache is None:
        _formulas_cache = load_bracket_formulas()
    return _formulas_cache


def get_cached_tiebreakers() -> Dict[str, List[str]]:
    """Restituisce i tiebreakers in cache."""
    global _tiebreakers_cache
    if _tiebreakers_cache is None:
        _tiebreakers_cache = load_tiebreakers()
    return _tiebreakers_cache


# ========================================
# TEST RAPIDO (SE ESEGUITO DIRETTAMENTE)
# ========================================

if __name__ == "__main__":
    print(f"📦 Config module v{__version__}")
    print(f"📝 {__description__}")
    
    formulas = load_bracket_formulas()
    print(f"\n📋 Formule caricate: {len(formulas)}")
    if formulas:
        for k, v in list(formulas.items())[:5]:
            print(f"   • {k} gironi: {v}")
    
    tiebreakers = load_tiebreakers()
    print(f"\n📋 Tiebreakers caricati: {len(tiebreakers)}")
    for k, v in tiebreakers.items():
        print(f"   • {k}: {len(v)} criteri")
    
    print("\n✅ Modulo config caricato correttamente")