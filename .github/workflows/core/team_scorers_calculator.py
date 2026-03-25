"""
Calcolo classifica marcatori per tornei a squadre.
Considera i gol segnati negli incontri individuali delle partite a squadre.
"""
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import pandas as pd
import logging
from pathlib import Path

from models.team import Team
from models.team_match import TeamMatch, IndividualMatchResult
from models.match import MatchStatus

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TeamScorersCalculator:
    """
    Calcolatore classifica marcatori per tornei a squadre.
    """
    
    def __init__(self, teams: List[Team]):
        """
        Args:
            teams: Lista di tutte le squadre del torneo
        """
        self.teams = teams
        self._build_player_to_team_map()
    
    def _build_player_to_team_map(self):
        """Costruisce mappa giocatore -> (squadra, club) per lookup veloce."""
        self.player_to_team = {}
        self.player_to_club = {}
        
        for team in self.teams:
            for player in team.players:
                self.player_to_team[player.display_name] = team.display_name
                self.player_to_club[player.display_name] = player.club
        
        logger.debug(f"Mappa giocatori costruita: {len(self.player_to_team)} giocatori")
    
    def _get_player_team(self, player_name: str) -> str:
        """Restituisce il nome della squadra per un giocatore."""
        return self.player_to_team.get(player_name, "Sconosciuta")
    
    def _get_player_club(self, player_name: str) -> str:
        """Restituisce il club per un giocatore."""
        return self.player_to_club.get(player_name, "Sconosciuto")
    
    def calculate_category_scorers(
        self, 
        category: str, 
        team_matches: List[TeamMatch],
        include_knockout: bool = True
    ) -> pd.DataFrame:
        """
        Calcola classifica marcatori per una categoria.
        
        Args:
            category: Categoria (es. "Team Open") - stringa vuota per tutte
            team_matches: Lista di partite a squadre
            include_knockout: Se True include fase finale, altrimenti solo gironi
        
        Returns:
            DataFrame con classifica marcatori
        """
        # Filtra partite della categoria e giocate
        if category:
            filtered_matches = [
                m for m in team_matches 
                if m.category == category and m.is_match_played()
            ]
        else:
            filtered_matches = [
                m for m in team_matches 
                if m.is_match_played()
            ]
        
        # Filtra per fase se richiesto
        if not include_knockout:
            filtered_matches = [m for m in filtered_matches if m.phase == "Groups"]
        
        logger.info(f" Calcolo marcatori per '{category or 'TUTTE'}': {len(filtered_matches)} partite")
        
        # Dizionario dei marcatori con statistiche dettagliate
        scorers = defaultdict(lambda: {
            "goals": 0,
            "matches": 0,
            "team": "",
            "club": "",
            "group_goals": 0,
            "knockout_goals": 0,
            "hattricks": 0,
            "penalties": 0,  # Se avremo questi dati
            "own_goals": 0    # Se avremo questi dati
        })
        
        # Dizionario per tracciare le partite giocate da ogni giocatore
        player_matches = defaultdict(set)
        
        for team_match in filtered_matches:
            match_id = team_match.id
            phase = "group" if team_match.phase == "Groups" else "knockout"
            
            for ind_match in team_match.individual_matches:
                if not ind_match.is_played:
                    continue
                
                # ===== GIOCATORE 1 =====
                if ind_match.goals1 and ind_match.goals1 > 0:
                    player_name = ind_match.player1
                    goals = ind_match.goals1
                    
                    scorers[player_name]["goals"] += goals
                    scorers[player_name][f"{phase}_goals"] += goals
                    scorers[player_name]["team"] = self._get_player_team(player_name)
                    scorers[player_name]["club"] = self._get_player_club(player_name)
                    
                    # Traccia partita giocata
                    player_matches[player_name].add(match_id)
                    
                    # Verifica tripletta (hat-trick)
                    if goals >= 3:
                        scorers[player_name]["hattricks"] += 1
                
                # ===== GIOCATORE 2 =====
                if ind_match.goals2 and ind_match.goals2 > 0:
                    player_name = ind_match.player2
                    goals = ind_match.goals2
                    
                    scorers[player_name]["goals"] += goals
                    scorers[player_name][f"{phase}_goals"] += goals
                    scorers[player_name]["team"] = self._get_player_team(player_name)
                    scorers[player_name]["club"] = self._get_player_club(player_name)
                    
                    player_matches[player_name].add(match_id)
                    
                    if goals >= 3:
                        scorers[player_name]["hattricks"] += 1
        
        # Correggi il conteggio partite (un giocatore gioca UN SOLO incontro per partita)
        for player_name in scorers:
            scorers[player_name]["matches"] = len(player_matches[player_name])
        
        # Prepara DataFrame
        data = []
        for player_name, stats in scorers.items():
            matches = stats["matches"]
            data.append({
                "Giocatore": player_name,
                "Squadra": stats["team"],
                "Club": stats["club"],
                "Gol": stats["goals"],
                "Gol Gironi": stats["group_goals"],
                "Gol Finale": stats["knockout_goals"],
                "Partite": matches,
                "Media": round(stats["goals"] / matches, 2) if matches > 0 else 0,
                "Triplette": stats["hattricks"]
            })
        
        # Crea DataFrame e ordina
        df = pd.DataFrame(data)
        if not df.empty:
            # Ordina per Gol (decrescente), poi Media, poi Gol Gironi
            df = df.sort_values(
                by=["Gol", "Media", "Gol Gironi"], 
                ascending=[False, False, False]
            ).reset_index(drop=True)
            df.insert(0, "Pos", df.index + 1)
        
        logger.info(f" Trovati {len(df)} marcatori")
        return df
    
    def calculate_tournament_top_scorer(
        self, 
        team_matches: List[TeamMatch]
    ) -> Optional[Dict]:
        """
        Calcola il capocannoniere assoluto del torneo (tutte le categorie).
        
        Returns:
            Dizionario con giocatore, gol, squadra, categoria o None
        """
        # Raccogli tutti i gol
        all_scorers = defaultdict(lambda: {"goals": 0, "category": "", "team": ""})
        
        for team_match in team_matches:
            if not team_match.is_match_played():
                continue
            
            for ind_match in team_match.individual_matches:
                if not ind_match.is_played:
                    continue
                
                # Giocatore 1
                if ind_match.goals1 and ind_match.goals1 > 0:
                    player = ind_match.player1
                    all_scorers[player]["goals"] += ind_match.goals1
                    all_scorers[player]["category"] = team_match.category
                    all_scorers[player]["team"] = self._get_player_team(player)
                
                # Giocatore 2
                if ind_match.goals2 and ind_match.goals2 > 0:
                    player = ind_match.player2
                    all_scorers[player]["goals"] += ind_match.goals2
                    all_scorers[player]["category"] = team_match.category
                    all_scorers[player]["team"] = self._get_player_team(player)
        
        if not all_scorers:
            return None
        
        # Trova il massimo
        top_scorer = max(all_scorers.items(), key=lambda x: x[1]["goals"])
        
        return {
            "giocatore": top_scorer[0],
            "gol": top_scorer[1]["goals"],
            "squadra": top_scorer[1]["team"],
            "categoria": top_scorer[1]["category"]
        }
    
    def get_top_scorer_by_category(
        self, 
        category: str, 
        team_matches: List[TeamMatch]
    ) -> Optional[Dict]:
        """
        Calcola il capocannoniere di una specifica categoria.
        """
        category_matches = [
            m for m in team_matches 
            if m.category == category and m.is_match_played()
        ]
        
        scorers = defaultdict(lambda: {"goals": 0, "team": ""})
        
        for team_match in category_matches:
            for ind_match in team_match.individual_matches:
                if not ind_match.is_played:
                    continue
                
                if ind_match.goals1:
                    scorers[ind_match.player1]["goals"] += ind_match.goals1
                    scorers[ind_match.player1]["team"] = self._get_player_team(ind_match.player1)
                
                if ind_match.goals2:
                    scorers[ind_match.player2]["goals"] += ind_match.goals2
                    scorers[ind_match.player2]["team"] = self._get_player_team(ind_match.player2)
        
        if not scorers:
            return None
        
        top_scorer = max(scorers.items(), key=lambda x: x[1]["goals"])
        
        return {
            "giocatore": top_scorer[0],
            "gol": top_scorer[1]["goals"],
            "squadra": top_scorer[1]["team"]
        }
    
    def get_scorers_by_team(self, team_matches: List[TeamMatch]) -> Dict[str, List[Dict]]:
        """
        Raggruppa marcatori per squadra.
        
        Returns:
            Dizionario {nome_squadra: lista_marcatori}
        """
        result = defaultdict(list)
        
        for team_match in team_matches:
            if not team_match.is_match_played():
                continue
            
            for ind_match in team_match.individual_matches:
                if not ind_match.is_played:
                    continue
                
                # Giocatore 1
                if ind_match.goals1 and ind_match.goals1 > 0:
                    player = ind_match.player1
                    team_name = self._get_player_team(player)
                    result[team_name].append({
                        "giocatore": player,
                        "gol": ind_match.goals1,
                        "partita": team_match.id
                    })
                
                # Giocatore 2
                if ind_match.goals2 and ind_match.goals2 > 0:
                    player = ind_match.player2
                    team_name = self._get_player_team(player)
                    result[team_name].append({
                        "giocatore": player,
                        "gol": ind_match.goals2,
                        "partita": team_match.id
                    })
        
        return dict(result)
    
    def export_to_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """
        Esporta classifica marcatori in CSV.
        
        Args:
            df: DataFrame con classifica
            filename: Nome file (opzionale)
        
        Returns:
            Path del file creato
        """
        # Crea directory data se non esiste
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"marcatori_squadre_{timestamp}.csv"
        
        filepath = data_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f" Esportato: {filepath}")
        return str(filepath)
    
    def export_to_excel(self, df: pd.DataFrame, filename: str = None) -> str:
        """
        Esporta classifica marcatori in Excel.
        """
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"marcatori_squadre_{timestamp}.xlsx"
        
        filepath = data_dir / filename
        df.to_excel(filepath, index=False)
        logger.info(f" Esportato: {filepath}")
        return str(filepath)
    
    def get_statistics_summary(self, team_matches: List[TeamMatch]) -> Dict:
        """
        Restituisce statistiche riassuntive sui marcatori.
        """
        stats = {
            "total_goals": 0,
            "total_scorers": 0,
            "avg_goals_per_match": 0,
            "most_goals_in_match": 0,
            "matches_with_goals": 0,
            "most_goals_by_player": 0,
            "top_scorer": None
        }
        
        all_goals = []
        scorers_set = set()
        match_goals = []
        player_goals = defaultdict(int)
        
        for team_match in team_matches:
            if not team_match.is_match_played():
                continue
            
            match_total = 0
            for ind_match in team_match.individual_matches:
                if not ind_match.is_played:
                    continue
                
                if ind_match.goals1:
                    all_goals.append(ind_match.goals1)
                    scorers_set.add(ind_match.player1)
                    player_goals[ind_match.player1] += ind_match.goals1
                    match_total += ind_match.goals1
                
                if ind_match.goals2:
                    all_goals.append(ind_match.goals2)
                    scorers_set.add(ind_match.player2)
                    player_goals[ind_match.player2] += ind_match.goals2
                    match_total += ind_match.goals2
            
            if match_total > 0:
                match_goals.append(match_total)
                if match_total > stats["most_goals_in_match"]:
                    stats["most_goals_in_match"] = match_total
        
        stats["total_goals"] = sum(all_goals)
        stats["total_scorers"] = len(scorers_set)
        stats["matches_with_goals"] = len(match_goals)
        
        if player_goals:
            stats["most_goals_by_player"] = max(player_goals.values())
            top_player = max(player_goals.items(), key=lambda x: x[1])
            stats["top_scorer"] = f"{top_player[0]} ({top_player[1]} gol)"
        
        if match_goals:
            stats["avg_goals_per_match"] = round(sum(match_goals) / len(match_goals), 2)
        
        return stats


# ========================================
# FUNZIONI DI UTILITÀ PER USO RAPIDO
# ========================================

def calculate_team_scorers(
    teams: List[Team],
    team_matches: List[TeamMatch],
    category: str = "",
    include_knockout: bool = True
) -> pd.DataFrame:
    """
    Funzione rapida per calcolare classifica marcatori squadre.
    """
    calculator = TeamScorersCalculator(teams)
    return calculator.calculate_category_scorers(category, team_matches, include_knockout)


def get_top_scorer(
    teams: List[Team],
    team_matches: List[TeamMatch],
    category: str = ""
) -> Optional[Dict]:
    """
    Funzione rapida per ottenere il capocannoniere.
    """
    calculator = TeamScorersCalculator(teams)
    
    if category:
        return calculator.get_top_scorer_by_category(category, team_matches)
    else:
        return calculator.calculate_tournament_top_scorer(team_matches)


# ========================================
# ESEMPIO DI UTILIZZO (TEST)
# ========================================

if __name__ == "__main__":
    # Questo blocco viene eseguito solo se lanciato direttamente
    print(" Test TeamScorersCalculator")
    
    from models.player import Player, Category
    from models.team import Team, TeamType
    
    # Crea giocatori fittizi
    players = [
        Player(first_name="MARCO", last_name="ROSSI", licence="ITA001", 
               category=Category.OPEN, club="Messina", country="ITA"),
        Player(first_name="LUCA", last_name="BIANCHI", licence="ITA002",
               category=Category.OPEN, club="Messina", country="ITA"),
        Player(first_name="GIUSEPPE", last_name="VERDI", licence="ITA003",
               category=Category.OPEN, club="Palermo", country="ITA"),
    ]
    
    # Crea squadre fittizie
    team1 = Team(id="MESSINA", name="Messina", country="ITA", 
                 category="Team Open", players=players[:2])
    team2 = Team(id="PALERMO", name="Palermo", country="ITA",
                 category="Team Open", players=[players[2]])
    
    # Test
    calculator = TeamScorersCalculator([team1, team2])
    print(f" Calculator inizializzato con {len(calculator.teams)} squadre")
    print(f" Mappa giocatori: {list(calculator.player_to_team.keys())}")