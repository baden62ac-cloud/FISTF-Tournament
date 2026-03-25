"""
Calcolo classifiche secondo regole FISTF.
Criteri (FISTF 2.1.2.b):
1. Punti
2. Scontri diretti (punti H2H)
3. Differenza reti H2H
4. Gol segnati H2H
5. Differenza reti totale
6. Gol segnati totali
7. Shoot-out (se necessario)

Regola 2.1.2.c: Limite 5-0 per categorie giovanili (U12, U16, U20, Women)
"""
print("🟢 CARICAMENTO core/standings_calculator.py")
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import pandas as pd


class StandingsCalculator:
    """Calcolatore classifiche con regole FISTF."""
    
    def __init__(self):
        self.points_win = 3
        self.points_draw = 1
        self.points_loss = 0
    
    def normalize_result(self, category: str, goals1: int, goals2: int) -> Tuple[int, int]:
        """
        Normalizza il risultato secondo regola FISTF 2.1.2.c.
        Per U12, U16, U20, Women: massimo 5-0 per la classifica.
        """
        limited_categories = ["U12", "U16", "U20", "Women"]
        
        if category in limited_categories:
            if goals1 > 5:
                goals1 = 5
            if goals2 > 5:
                goals2 = 5
        
        return goals1, goals2
    
    def calculate_group_standings(self, group_name: str, players: List['Player'], matches: List['Match']) -> pd.DataFrame:
        """
        Calcola classifica per un gruppo di giocatori secondo criteri FISTF.
        """
        from models.match import MatchStatus
        
        if not players:
            return pd.DataFrame()
        
        # Inizializza statistiche
        stats = {}
        for player in players:
            stats[player.display_name] = {
                "player": player,
                "giocate": 0,
                "vinte": 0,
                "perse": 0,
                "pareggiate": 0,
                "gf": 0,
                "gs": 0,
                "punti": 0,
                "matches": []  # Per tracciare gli scontri diretti
            }
        
        # Elabora partite del girone
        for match in matches:
            if match.status != MatchStatus.COMPLETED or not match.is_played:
                continue
            
            # Verifica che la partita appartenga a questo girone
            if not match.group or not match.group.endswith(f"-{group_name}"):
                continue
            
            p1 = match.player1
            p2 = match.player2
            
            if p1 not in stats or p2 not in stats:
                continue
            
            # Normalizza risultato
            g1, g2 = self.normalize_result(match.category, match.goals1, match.goals2)
            
            # Aggiorna statistiche base
            stats[p1]["giocate"] += 1
            stats[p2]["giocate"] += 1
            stats[p1]["gf"] += g1
            stats[p1]["gs"] += g2
            stats[p2]["gf"] += g2
            stats[p2]["gs"] += g1
            
            # Aggiorna punti e vittorie/sconfitte
            if g1 > g2:
                stats[p1]["vinte"] += 1
                stats[p1]["punti"] += self.points_win
                stats[p2]["perse"] += 1
                # Traccia scontro diretto
                stats[p1]["matches"].append({"opponent": p2, "gf": g1, "ga": g2, "points": 3})
                stats[p2]["matches"].append({"opponent": p1, "gf": g2, "ga": g1, "points": 0})
            elif g2 > g1:
                stats[p2]["vinte"] += 1
                stats[p2]["punti"] += self.points_win
                stats[p1]["perse"] += 1
                stats[p1]["matches"].append({"opponent": p2, "gf": g1, "ga": g2, "points": 0})
                stats[p2]["matches"].append({"opponent": p1, "gf": g2, "ga": g1, "points": 3})
            else:
                stats[p1]["pareggiate"] += 1
                stats[p2]["pareggiate"] += 1
                stats[p1]["punti"] += self.points_draw
                stats[p2]["punti"] += self.points_draw
                stats[p1]["matches"].append({"opponent": p2, "gf": g1, "ga": g2, "points": 1})
                stats[p2]["matches"].append({"opponent": p1, "gf": g2, "ga": g1, "points": 1})
        
        # Calcola HTH per ogni giocatore
        for player_name in stats:
            hth_stats = self._calculate_hth_for_player(player_name, stats)
            stats[player_name].update(hth_stats)
        
        # Prepara dati per DataFrame
        data = []
        for player_name, s in stats.items():
            data.append({
                "Giocatore": player_name,
                "Club": s["player"].club,
                "Punti": s["punti"],
                "Giocate": s["giocate"],
                "Vinte": s["vinte"],
                "Pareggiate": s["pareggiate"],
                "Perse": s["perse"],
                "GF": s["gf"],
                "GS": s["gs"],
                "DG": s["gf"] - s["gs"],
                "HTH_P": s.get("hth_punti", 0),
                "HTH_DG": s.get("hth_diff", 0),
                "HTH_GF": s.get("hth_gf", 0)
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        # Ordina secondo criteri FISTF
        df = df.sort_values(
            by=["Punti", "HTH_P", "HTH_DG", "HTH_GF", "DG", "GF"],
            ascending=[False, False, False, False, False, False]
        ).reset_index(drop=True)
        
        # Aggiungi posizione
        df.insert(0, "Pos", df.index + 1)
        
        return df
    
    def _calculate_hth_for_player(self, player_name: str, stats: Dict) -> Dict:
        """
        Calcola le statistiche HTH per un giocatore considerando solo i giocatori
        con gli stessi punti.
        """
        player_points = stats[player_name]["punti"]
        
        # Trova tutti i giocatori con gli stessi punti
        same_points = []
        for other_name, other_stats in stats.items():
            if other_name != player_name and other_stats["punti"] == player_points:
                same_points.append(other_name)
        
        if not same_points:
            return {"hth_punti": 0, "hth_diff": 0, "hth_gf": 0}
        
        # Filtra partite solo contro giocatori con stessi punti
        hth_punti = 0
        hth_gf = 0
        hth_ga = 0
        
        for match in stats[player_name]["matches"]:
            if match["opponent"] in same_points:
                hth_punti += match["points"]
                hth_gf += match["gf"]
                hth_ga += match["ga"]
        
        hth_diff = hth_gf - hth_ga
        
        return {
            "hth_punti": hth_punti,
            "hth_diff": hth_diff,
            "hth_gf": hth_gf
        }
    
    def calculate_knockout_progression(self, group_standings: Dict[str, pd.DataFrame]) -> List:
        """
        Calcola la progressione dalla fase a gironi alla fase finale.
        Restituisce lista di qualificati per girone.
        """
        qualified = []
        
        for group_name, df in group_standings.items():
            if not df.empty:
                # Primo classificato
                first = df.iloc[0]
                qualified.append({
                    "group": group_name,
                    "position": 1,
                    "player": first["Giocatore"],
                    "club": first["Club"],
                    "points": first["Punti"]
                })
                
                # Secondo classificato (se presente)
                if len(df) >= 2:
                    second = df.iloc[1]
                    qualified.append({
                        "group": group_name,
                        "position": 2,
                        "player": second["Giocatore"],
                        "club": second["Club"],
                        "points": second["Punti"]
                    })
        
        return qualified