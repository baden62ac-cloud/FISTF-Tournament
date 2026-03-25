# models/tournament_save.py
"""
Modello per il salvataggio completo del torneo.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union  # <-- AGGIUNGI Union
from datetime import datetime
from models.player import Player
from models.tournament import TournamentConfig
from models.match import Match
from models.team_match import TeamMatch  # <-- AGGIUNGI TeamMatch


class TournamentSave(BaseModel):
    """Rappresenta un salvataggio completo del torneo."""
    
    # Metadati
    version: str = "2.0"  # AUMENTA LA VERSIONE!
    save_date: datetime = datetime.now()
    
    # Dati torneo - SOLO I DATI, NON L'UI!
    tournament: TournamentConfig
    players: List[Player]
    teams: List[Any] = []  # Già ok
    groups: Dict[str, Any] = {}
    matches: List[Union[Match, TeamMatch]] = []  # <-- MODIFICATO: accetta entrambi!
    tournament_type: str = "individual"  # Già ok
    
    # Statistiche (calcolate, non salvate)
    total_players: int = 0
    total_teams: int = 0
    total_groups: int = 0
    total_matches: int = 0
    players_by_category: dict = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calcola statistiche dopo il caricamento
        self.total_players = len(self.players)
        self.total_teams = len(self.teams)
        self.total_matches = len(self.matches)
        
        # Calcola gironi
        self.total_groups = 0
        for cat_groups in self.groups.values():
            if isinstance(cat_groups, dict):
                self.total_groups += len(cat_groups)
        
        # Calcola giocatori per categoria
        self.players_by_category = {}
        for p in self.players:
            cat = p.category.value
            self.players_by_category[cat] = self.players_by_category.get(cat, 0) + 1