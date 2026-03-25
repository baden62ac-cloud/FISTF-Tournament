# ui/__init__.py
"""
Modulo UI - Interfaccia utente per FISTF Tournament Manager.
Espone le classi base e le tab dell'applicazione.
"""

# ========================================
# CLASSE BASE
# ========================================
from .base_tab import BaseTab

# ========================================
# TAB TORNEO INDIVIDUALE
# ========================================
from .tabs.setup_tab import SetupTab
from .tabs.players_tab import PlayersTab
from .tabs.groups_tab import GroupsTab
from .tabs.calendar_tab import CalendarTab
from .tabs.results_tab import ResultsTab          # Nuova tab risultati per turno
from .tabs.standings_tab import StandingsTab
from .tabs.knockout_tab import KnockoutTab
from .tabs.scorers_tab import ScorersTab

# ========================================
# TAB TORNEO A SQUADRE
# ========================================
from .tabs.teams_tab import TeamsTab
from .tabs.team_groups_tab import TeamGroupsTab
from .tabs.team_calendar_tab import TeamCalendarTab
from .tabs.team_results_tab import TeamResultsTab
from .tabs.team_standings_tab import TeamStandingsTab
from .tabs.team_knockout_tab import TeamKnockoutTab
from .tabs.team_scorers_tab import TeamScorersTab


# ========================================
# ESPORTAZIONE TUTTE LE CLASSI
# ========================================
__all__ = [
    # Classe base
    'BaseTab',
    
    # Tab individuali
    'SetupTab',
    'PlayersTab',
    'GroupsTab',
    'CalendarTab',
    'ResultsTab',
    'StandingsTab',
    'KnockoutTab',
    'ScorersTab',
    
    # Tab squadre
    'TeamsTab',
    'TeamGroupsTab',
    'TeamCalendarTab',
    'TeamResultsTab',
    'TeamStandingsTab',
    'TeamKnockoutTab',
    'TeamScorersTab',
]


# ========================================
# METADATI
# ========================================
__version__ = "2.0.0"
__author__ = "FISTF Tournament Manager Team"
__description__ = "Interfaccia utente per FISTF Tournament Manager"


# ========================================
# FUNZIONI DI UTILITÀ UI
# ========================================

def get_tabs_info():
    """Restituisce informazioni sulle tab disponibili."""
    return {
        "version": __version__,
        "description": __description__,
        "individual_tabs": [
            "SetupTab",
            "PlayersTab", 
            "GroupsTab",
            "CalendarTab",
            "ResultsTab",
            "StandingsTab",
            "KnockoutTab",
            "ScorersTab",
        ],
        "team_tabs": [
            "TeamsTab",
            "TeamGroupsTab",
            "TeamCalendarTab",
            "TeamResultsTab",
            "TeamStandingsTab",
            "TeamKnockoutTab",
            "TeamScorersTab",
        ],
        "total_tabs": 15,  # 8 individuali + 7 squadre
    }


def get_tab_by_name(name: str):
    """
    Restituisce una classe tab dato il nome.
    Utile per caricamento dinamico.
    """
    tabs_map = {
        # Individuali
        "SetupTab": SetupTab,
        "PlayersTab": PlayersTab,
        "GroupsTab": GroupsTab,
        "CalendarTab": CalendarTab,
        "ResultsTab": ResultsTab,
        "StandingsTab": StandingsTab,
        "KnockoutTab": KnockoutTab,
        "ScorersTab": ScorersTab,
        
        # Squadre
        "TeamsTab": TeamsTab,
        "TeamGroupsTab": TeamGroupsTab,
        "TeamCalendarTab": TeamCalendarTab,
        "TeamResultsTab": TeamResultsTab,
        "TeamStandingsTab": TeamStandingsTab,
        "TeamKnockoutTab": TeamKnockoutTab,
        "TeamScorersTab": TeamScorersTab,
    }
    
    return tabs_map.get(name)


# ========================================
# TEST RAPIDO (SE ESEGUITO DIRETTAMENTE)
# ========================================

if __name__ == "__main__":
    print(f"🎨 UI module v{__version__}")
    print(f"📝 {__description__}")
    print("\n📋 Tab individuali:")
    for tab in get_tabs_info()["individual_tabs"]:
        print(f"   • {tab}")
    
    print("\n📋 Tab squadre:")
    for tab in get_tabs_info()["team_tabs"]:
        print(f"   • {tab}")
    
    print(f"\n✅ Totale: {get_tabs_info()['total_tabs']} tab")
    print("\n✅ Modulo UI caricato correttamente")