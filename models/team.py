# models/team.py
"""
Modello squadra per competizioni a squadre FISTF.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
from models.player import Player

class TeamType(str, Enum):
    """Tipo di squadra."""
    CLUB = "Club"
    NATIONAL = "National"
    BARBARIANS = "Barbarians"  # Regola speciale FISTF

class Team(BaseModel):
    """Squadra per competizioni a squadre."""
    
    # Identificativi
    id: str  # Es: "MESSINA_A", "ITALIA"
    name: str
    club: Optional[str] = None  # Per squadre di club
    country: str = Field(..., min_length=3, max_length=3)
    team_type: TeamType = TeamType.CLUB
    category: str  # Categoria della squadra (es. "Team Open")
    
    # Roster giocatori (min 3, max 8)
    players: List[Player] = Field(..., min_length=3, max_length=8)
    
    # Dati torneo
    seed: Optional[int] = Field(None, ge=1)
    group: Optional[str] = None
    
    @field_validator('players')
    @classmethod
    def validate_players(cls, v: List[Player]) -> List[Player]:
        """Validazione base del roster."""
        if len(v) < 3:
            raise ValueError('Una squadra deve avere almeno 3 giocatori')
        if len(v) > 8:
            raise ValueError('Una squadra può avere al massimo 8 giocatori')
        
        # Verifica licenze duplicate
        licences = [p.licence for p in v]
        duplicates = [l for l in licences if licences.count(l) > 1]
        if duplicates:
            raise ValueError(f'Licenze duplicate nel roster: {", ".join(set(duplicates))}')
        
        return v
    
    @property
    def display_name(self) -> str:
        """Nome per UI."""
        if self.team_type == TeamType.CLUB:
            return f"{self.name} ({self.country})"
        return self.name
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    @property
    def player_names(self) -> str:
        """Elenco giocatori per display."""
        return ", ".join([p.display_name for p in self.players])
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "MESSINA_A",
                "name": "ASD Subbuteo Messina A",
                "club": "ASD Subbuteo Messina",
                "country": "ITA",
                "team_type": "Club",
                "category": "Team Open",
                "players": [],
                "seed": 1
            }
        }