# models/team_match.py
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MatchStatus(str, Enum):
    """Stati possibili di una partita."""
    COMPLETED = "Giocata"
    FORFEIT = "Forfait"


class IndividualMatchResult(BaseModel):
    """
    Risultato di un singolo incontro individuale
    all'interno di una partita a squadre.
    """
    player1: str = ""
    player2: str = ""
    goals1: Optional[int] = None
    goals2: Optional[int] = None
    table: int = 1
    status: Optional[MatchStatus] = None  # Solo COMPLETED o FORFEIT, None = non giocata
    notes: str = ""
    referee: Optional[str] = None
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def is_played(self) -> bool:
        """Verifica se l'incontro è stato giocato."""
        return self.goals1 is not None and self.goals2 is not None
    
    @property
    def result(self) -> str:
        """Restituisce il risultato formattato."""
        if self.is_played:
            return f"{self.goals1}-{self.goals2}"
        return "vs"


class TeamMatch(BaseModel):
    """Modello per partita a squadre (4 incontri individuali)."""
    
    id: str
    category: str
    phase: str
    group: Optional[str] = None
    
    # Squadre - sono opzionali per gestire i token WIN
    team1: Optional[str] = None
    team2: Optional[str] = None
    
    # Nomi visualizzati (possono essere token WIN)
    player1: str
    player2: str
    
    match_number: int
    scheduled_time: Optional[str] = None
    field: Optional[int] = None
    status: Optional[MatchStatus] = None  # Solo COMPLETED o FORFEIT, None = non giocata
    
    # Token per la propagazione
    token1: Optional[str] = None
    token2: Optional[str] = None
    
    # Vincitore
    winner: Optional[str] = None
    
    # Arbitro della partita (squadra)
    referee: Optional[str] = None
    referee_id: Optional[str] = None
    
    # 4 incontri individuali
    individual_matches: List[IndividualMatchResult] = Field(default_factory=list)
    
    # Flag forfait
    has_forfait_match: bool = False
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def is_played(self) -> bool:
        """Verifica se la partita è stata giocata."""
        if self.status == MatchStatus.COMPLETED:
            return True
        
        if self.individual_matches:
            all_played = True
            for im in self.individual_matches:
                if im.goals1 is None or im.goals2 is None:
                    all_played = False
                    break
            return all_played
        
        return False
    
    @property
    def is_forfeit(self) -> bool:
        """Verifica se la partita è stata persa per forfait."""
        return self.status == MatchStatus.FORFEIT or self.has_forfait_match
    
    @property
    def team_result(self) -> str:
        """Restituisce il risultato della squadra (es. '3-1')."""
        if self.is_forfeit:
            return "0-4"
        
        if not self.is_played:
            return "vs"
        
        wins1 = 0
        wins2 = 0
        
        for im in self.individual_matches:
            if im.goals1 is not None and im.goals2 is not None:
                if im.goals1 > im.goals2:
                    wins1 += 1
                elif im.goals2 > im.goals1:
                    wins2 += 1
        
        return f"{wins1}-{wins2}"
    
    def is_match_played(self) -> bool:
        """Alias per compatibilità."""
        return self.is_played
    
    @property
    def display_time(self) -> str:
        """Orario formattato per display."""
        if self.scheduled_time:
            return self.scheduled_time
        return "Orario da definire"
    
    @property
    def display_field(self) -> str:
        """Campo formattato per display."""
        if self.field:
            return f"Campo {self.field}"
        return "Campo da definire"