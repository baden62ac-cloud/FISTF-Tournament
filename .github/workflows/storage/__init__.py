# storage/__init__.py
"""
Modulo storage - Gestione persistenza dei tornei.
Fornisce funzionalità di salvataggio e caricamento per FISTF Tournament Manager.
"""

from .tournament_storage import TournamentStorage

# ========================================
# ESPORTAZIONE PRINCIPALE
# ========================================

__all__ = [
    'TournamentStorage',
]

__version__ = "1.0.0"
__author__ = "FISTF Tournament Manager Team"
__description__ = "Gestione persistenza tornei FISTF"


# ========================================
# FUNZIONI DI UTILITÀ
# ========================================

def get_storage_info():
    """Restituisce informazioni sul modulo storage."""
    return {
        "version": __version__,
        "description": __description__,
        "classes": ["TournamentStorage"],
    }


def create_storage():
    """Crea e restituisce un'istanza di TournamentStorage."""
    return TournamentStorage()


# ========================================
# TEST RAPIDO (SE ESEGUITO DIRETTAMENTE)
# ========================================

if __name__ == "__main__":
    print(f"📦 Storage module v{__version__}")
    print(f"📝 {__description__}")
    print("\n📋 Classi disponibili:")
    print("   • TournamentStorage - Gestione salvataggio/caricamento")
    print("\n✅ Modulo storage caricato correttamente")