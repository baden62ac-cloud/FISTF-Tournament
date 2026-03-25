# models/match.py
"""
Modello partita con supporto per turni e campi.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class MatchStatus(str, Enum):
    """Stato della partita."""
    SCHEDULED = "Programmata"
    IN_PROGRESS = "In corso"
    COMPLETED = "Giocata"
    FORFEIT = "Forfait"
    POSTPONED = "Rinviata"

class Match(BaseModel):
    """Partita del torneo con supporto turni."""
    
    # Identificativi
    id: str  # Es: "O-M1", "V-M2", "U20-M3"
    category: str
    phase: str  # "Groups", "BARRAGE", "QF", "SF", "F"
    
    # Giocatori
    player1: str  # Nome completo giocatore o "WIN M1"
    player2: str
    
    # Dati organizzativi
    group: Optional[str] = None  # Solo per fase a gironi
    match_day: Optional[int] = None  # Numero del turno/giornata
    match_number: Optional[int] = None  # Numero progressivo match (senza prefisso)
    phase_number: Optional[int] = None
    field: Optional[int] = None  # Numero campo
    slot: Optional[int] = None  # Slot nel turno
    scheduled_time: Optional[str] = None  # Orario programmato (es. "09:00")
    referee: Optional[str] = None
    # round_number: Optional[int] = None  # Numero del turno/giornata
    
    # Token per fase finale (per tracciare provenienza)
    token1: Optional[str] = None  # Es. "1A", "WIN QF_1"
    token2: Optional[str] = None  # Es. "2B", "WIN B1"
    
    # Risultato
    goals1: Optional[int] = Field(None, ge=0)
    goals2: Optional[int] = Field(None, ge=0)
    status: MatchStatus = MatchStatus.SCHEDULED
    winner: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def is_played(self) -> bool:
        """Verifica se partita giocata."""
        return self.goals1 is not None and self.goals2 is not None
    
    @property
    def result(self) -> str:
        """Risultato formattato."""
        if not self.is_played:
            return "vs"
        return f"{self.goals1}-{self.goals2}"
    
    @property
    def is_knockout(self) -> bool:
        """Verifica se partita a eliminazione diretta."""
        return self.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32"]
    
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
    
    @property
    def display_id(self) -> str:
        """ID formattato per display."""
        return self.id