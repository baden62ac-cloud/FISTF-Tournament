# core/scorers_calculator.py
"""
Calcolo classifica marcatori per categoria.
"""
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import pandas as pd

from models.player import Player
from models.match import Match, MatchStatus


class ScorersCalculator:
    """Calcolatore classifica marcatori."""
    
    def calculate_category_scorers(self, category: str, players: List[Player], matches: List[Match]) -> pd.DataFrame:
        """
        Calcola classifica marcatori per una categoria.
        Se category è stringa vuota, considera tutte le categorie.
        """
        # Filtra partite della categoria (o tutte) e giocate
        if category:
            category_matches = [m for m in matches 
                               if m.category == category 
                               and m.status == MatchStatus.COMPLETED
                               and m.is_played]
        else:
            category_matches = [m for m in matches 
                               if m.status == MatchStatus.COMPLETED
                               and m.is_played]
        
        # Dizionario dei gol: {giocatore: gol_totali}
        scorers = defaultdict(int)
        matches_played = defaultdict(int)  # Partite giocate da ogni giocatore
        
        for match in category_matches:
            # Gol del giocatore 1
            if match.goals1:
                scorers[match.player1] += match.goals1
                matches_played[match.player1] += 1
            
            # Gol del giocatore 2
            if match.goals2:
                scorers[match.player2] += match.goals2
                matches_played[match.player2] += 1
        
        # Prepara DataFrame
        data = []
        for player_name, goals in scorers.items():
            # Cerca il giocatore per avere club e categoria
            player = next((p for p in players if p.display_name == player_name), None)
            
            data.append({
                "Giocatore": player_name,
                "Club": player.club if player else "",
                "Categoria": player.category.value if player else "",
                "Gol": goals,
                "Partite": matches_played[player_name],
                "Media": round(goals / matches_played[player_name], 2) if matches_played[player_name] > 0 else 0
            })
        
        # Ordina per gol (decrescente) e poi per media
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(by=["Gol", "Media"], ascending=[False, False]).reset_index(drop=True)
            df.insert(0, "Pos", df.index + 1)
        
        return df
    
    def calculate_tournament_top_scorer(self, matches: List[Match]) -> Optional[Dict]:
        """
        Calcola il capocannoniere assoluto del torneo.
        """
        all_scorers = defaultdict(int)
        
        for match in matches:
            if match.status == MatchStatus.COMPLETED and match.is_played:
                if match.goals1:
                    all_scorers[match.player1] += match.goals1
                if match.goals2:
                    all_scorers[match.player2] += match.goals2
        
        if not all_scorers:
            return None
        
        # Trova il massimo
        top_scorer = max(all_scorers.items(), key=lambda x: x[1])
        
        return {
            "giocatore": top_scorer[0],
            "gol": top_scorer[1]
        }
    
    def get_top_scorer_by_category(self, category: str, matches: List[Match]) -> Optional[Dict]:
        """
        Calcola il capocannoniere di una specifica categoria.
        """
        category_matches = [m for m in matches 
                           if m.category == category 
                           and m.status == MatchStatus.COMPLETED
                           and m.is_played]
        
        scorers = defaultdict(int)
        
        for match in category_matches:
            if match.goals1:
                scorers[match.player1] += match.goals1
            if match.goals2:
                scorers[match.player2] += match.goals2
        
        if not scorers:
            return None
        
        top_scorer = max(scorers.items(), key=lambda x: x[1])
        
        return {
            "giocatore": top_scorer[0],
            "gol": top_scorer[1]
        }