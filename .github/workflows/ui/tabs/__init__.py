# ui/tabs/__init__.py
"""
Tab dell'interfaccia utente per FISTF Tournament Manager.
Esporta tutte le tab individuali e a squadre.
"""

# ========================================
# TAB TORNEO INDIVIDUALE
# ========================================
from .setup_tab import SetupTab
from .players_tab import PlayersTab
from .groups_tab import GroupsTab
from .calendar_tab import CalendarTab
from .results_tab import ResultsTab          # Nuova tab risultati per turno
from .standings_tab import StandingsTab
from .knockout_tab import KnockoutTab
from .scorers_tab import ScorersTab

# ========================================
# TAB TORNEO A SQUADRE
# ========================================
from .teams_tab import TeamsTab
from .team_groups_tab import TeamGroupsTab
from .team_calendar_tab import TeamCalendarTab
from .team_results_tab import TeamResultsTab
from .team_standings_tab import TeamStandingsTab
from .team_knockout_tab import TeamKnockoutTab
from .team_scorers_tab import TeamScorersTab


# ========================================
# ESPORTAZIONE TUTTE LE TAB
# ========================================
__all__ = [
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
__description__ = "Tab dell'interfaccia utente per FISTF Tournament Manager"


# ========================================
# FUNZIONI DI UTILITÀ PER LE TAB
# ========================================

def get_individual_tabs():
    """Restituisce la lista delle tab individuali."""
    return [
        SetupTab,
        PlayersTab,
        GroupsTab,
        CalendarTab,
        ResultsTab,
        StandingsTab,
        KnockoutTab,
        ScorersTab,
    ]


def get_team_tabs():
    """Restituisce la lista delle tab a squadre."""
    return [
        TeamsTab,
        TeamGroupsTab,
        TeamCalendarTab,
        TeamResultsTab,
        TeamStandingsTab,
        TeamKnockoutTab,
        TeamScorersTab,
    ]


def get_all_tabs():
    """Restituisce la lista di tutte le tab."""
    return get_individual_tabs() + get_team_tabs()


def get_tab_by_class_name(class_name: str):
    """
    Restituisce una classe tab dato il nome della classe.
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
    
    return tabs_map.get(class_name)


def get_tabs_info():
    """Restituisce informazioni sulle tab disponibili."""
    return {
        "version": __version__,
        "description": __description__,
        "individual_tabs": [tab.__name__ for tab in get_individual_tabs()],
        "team_tabs": [tab.__name__ for tab in get_team_tabs()],
        "total_tabs": len(get_all_tabs()),
    }


# ========================================
# TEST RAPIDO (SE ESEGUITO DIRETTAMENTE)
# ========================================

if __name__ == "__main__":
    print(f"📑 UI Tabs module v{__version__}")
    print(f"📝 {__description__}")
    print("\n📋 Tab individuali:")
    for tab in get_individual_tabs():
        print(f"   • {tab.__name__}")
    
    print("\n📋 Tab squadre:")
    for tab in get_team_tabs():
        print(f"   • {tab.__name__}")
    
    print(f"\n✅ Totale: {len(get_all_tabs())} tab")
    print("\n✅ Modulo UI Tabs caricato correttamente")