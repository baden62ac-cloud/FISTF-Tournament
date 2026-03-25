"""
Modello configurazione torneo.
"""
import sys
#print(f"🔵 tournament.py caricato, QApplication esiste? {QApplication.instance() is not None if 'QApplication' in dir() else 'QApplication non importato'}")
print("🟢 CARICAMENTO models/tournament.py")
from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from core.fistf_rules import Category

class TournamentConfig(BaseModel):
    """Configurazione di un torneo FISTF."""
    
    # Dati identificativi
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    name: str
    start_date: date
    end_date: date
    venue: str
    organizer: str
    organizer_email: str
    event_type: str  # "Major Grand Prix", "Satellite", etc.
    
    # Categorie attive
    categories: List[Category]

    tournament_type: str = "individual"  # "individual" o "team"
    
    # Opzioni
    allow_double_categories: bool = False  # Giocatore in due categorie
    apply_youth_cap: bool = True
    
    # Dati per report FISTF
    fistf_tournament_id: Optional[str] = None
    total_players: int = 0
    fees_paid: float = 0.0
    
    @property
    def duration_days(self) -> int:
        """Durata torneo in giorni."""
        return (self.end_date - self.start_date).days + 1
    
    def calculate_fistf_fees(self, players_by_category: Dict[Category, int]) -> float:
        """
        Calcola le tasse da pagare alla FISTF.
        """
        # Tariffe dal Tournament Organisers' Handbook
        rates = {
            Category.OPEN: 5.0,
            Category.VETERANS: 5.0,
            Category.WOMEN: 5.0,
            Category.U20: 2.0,
            Category.U16: 2.0,
            Category.U12: 2.0
        }
        
        total = 0
        for category, count in players_by_category.items():
            if category in rates:
                total += count * rates[category]
        
        return total
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Messina Open 2026",
                "start_date": "2026-03-05",
                "end_date": "2026-03-06",
                "venue": "Palazzo dello Sport, Messina",
                "organizer": "ASD Subbuteo Messina",
                "organizer_email": "info@subbuteomessina.it",
                "event_type": "International Open",
                "categories": ["Open", "Veterans", "U20"]
            }
        }