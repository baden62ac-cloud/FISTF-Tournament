"""
Modelli dati per FISTF Tournament Manager.
"""
from .player import Player, Category
from .tournament import TournamentConfig
from .match import Match, MatchStatus
from .tournament_save import TournamentSave
from .team import Team, TeamType
from .team_match import TeamMatch, IndividualMatchResult  # <-- AGGIUNTO

__all__ = [
    'Player', 'Category',
    'TournamentConfig',
    'Match', 'MatchStatus',
    'TournamentSave',
    'Team', 'TeamType',
    'TeamMatch', 'IndividualMatchResult',  # <-- AGGIUNTO
]