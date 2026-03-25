"""
Modello giocatore conforme alle specifiche FISTF.
"""
import sys
#print(f"🔵 player.py caricato, QApplication esiste? {QApplication.instance() is not None if 'QApplication' in dir() else 'QApplication non importato'}")

print("🟢 CARICAMENTO models/player.py")
import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from core.fistf_rules import Category, LICENCE_FORMAT

class Player(BaseModel):
    """Giocatore con tutti i dati richiesti dalla FISTF."""
    
    # Dati anagrafici
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    
    # Dati FISTF
    licence: str = Field(..., description="Formato: 3 lettere nazione + 5 numeri")
    category: Category
    club: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=3, max_length=3)
    
    # Dati torneo (opzionali, popolati dopo)
    seed: Optional[int] = Field(None, ge=1)
    group: Optional[str] = None
    
    @field_validator('licence')
    @classmethod
    def validate_licence(cls, v: str) -> str:
        """Valida formato licenza FISTF."""
        if not re.match(LICENCE_FORMAT, v):
            raise ValueError(f'Licenza {v} non valida. Formato: 3 lettere + 5 numeri')
        return v.upper()
    
    @field_validator('country')
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Converte in maiuscolo e tronca a 3 lettere."""
        return v.upper()[:3]
    
    @property
    def full_name(self) -> str:
        """Nome completo per visualizzazione."""
        return f"{self.first_name} {self.last_name}".upper()
    
    @property
    def display_name(self) -> str:
        """Nome per UI (Cognome Nome)."""
        return f"{self.last_name} {self.first_name}"
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "RICCARDO",
                "last_name": "NATOLI",
                "licence": "ITA12345",
                "category": "Open",
                "club": "Messina",
                "country": "ITA",
                "seed": 1
            }
        }