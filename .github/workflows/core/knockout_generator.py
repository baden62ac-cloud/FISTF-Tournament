"""
Generazione fase finale secondo formule FISTF.
La notazione usa: numero = girone, lettera = posizione (A=1°, B=2°, C=3°, ...)
Esempio: "1A" = Girone 1, primo classificato
         "3B" = Girone 3, secondo classificato
         "WIN B1" = Vincitore barrage 1
         "WIN QF1" = Vincitore quarto di finale 1
         "WIN SF1" = Vincitore semifinale 1
         "WIN F1" = Vincitore finale
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict


class KnockoutGenerator:
    """Genera il tabellone della fase finale in base alle formule FISTF."""
    
    # Mappa per la conversione fase -> prefisso token
    PHASE_TOKEN_PREFIX = {
        "BARRAGE": "B",
        "QF": "QF",
        "SF": "SF",
        "F": "F",
        "R16": "R16",
        "R32": "R32",
        "R64": "R64"
    }
    
    def __init__(self):
        json_path = Path(__file__).parent.parent / "config" / "bracket_formulas.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            self.formulas = json.load(f)
    
    def generate_bracket(self, num_groups: int, group_standings: Dict[str, List['Player']], 
                    category: str = "", category_prefix: str = "") -> List['Match']:
        """
        Genera il tabellone completo.
        
        Args:
            num_groups: Numero di gironi (es. 6)
            group_standings: Classifiche per girone con chiavi numeriche
            category: Nome della categoria (es. "Eccellenza")
            category_prefix: Prefisso per gli ID (es. "ECC")
        
        Returns:
            Lista di partite in ordine di fase
        """
        # Importa qui i modelli necessari
        from models.match import Match, MatchStatus
        from models.player import Player
        
        formula_key = str(num_groups)
        if formula_key not in self.formulas:
            raise ValueError(f"Nessuna formula per {num_groups} gironi")
        
        formula = self.formulas[formula_key]
        print(f"\n📋 Formula per {num_groups} gironi: {formula}")
        
        # Crea mappa dei qualificati: "1A" -> Player (girone 1, 1° classificato)
        qualified = {}
        print("\n📊 Mappa qualificati:")
        for group_num, standings in group_standings.items():
            for pos_idx, player in enumerate(standings):
                # Limita alle prime 6 posizioni (A-F)
                if pos_idx < 6:
                    letter = chr(65 + pos_idx)  # 0->A, 1->B, 2->C, 3->D, 4->E, 5->F
                    token = f"{group_num}{letter}"
                    qualified[token] = player
                    print(f"   {token} -> {player.display_name} ({player.club})")
        
        # Genera tutte le partite in ordine
        all_matches = []
        match_counter = 1
        
        # Gestisci le fasi nell'ordine corretto
        phase_order = ["BARRAGE", "R64", "R32", "R16", "QF", "SF", "F"]
        
        for phase in phase_order:
            if phase in formula:
                print(f"\n🔨 Generazione fase {phase}...")
                phase_matches, match_counter = self._create_phase_matches(
                    formula[phase], qualified, phase, match_counter, category, category_prefix
                )
                all_matches.extend(phase_matches)
                
                # Stampa le partite generate
                for m in phase_matches:
                    print(f"   {m.id}: {m.token1} vs {m.token2} -> {m.player1} vs {m.player2}")
        
        print(f"\n✅ Totale partite generate: {len(all_matches)}")
        return all_matches
    
    def _create_phase_matches(self, match_list: List[str], qualified: Dict, 
                          phase: str, start_counter: int, 
                          category: str = "", category_prefix: str = "") -> tuple[List['Match'], int]:
        """Crea le partite per una fase specifica."""
        from models.match import Match, MatchStatus
        
        matches = []
        counter = start_counter
        
        for i in range(0, len(match_list), 2):
            if i + 1 >= len(match_list):
                break
            
            token1 = match_list[i]
            token2 = match_list[i + 1]
            
            player1 = self._resolve_token(token1, qualified)
            player2 = self._resolve_token(token2, qualified)
            
            match_number = (i // 2) + 1
            
            # ID univoco con prefisso categoria (se fornito)
            if category_prefix:
                match_id = f"{category_prefix}_{phase}_{match_number}"
            else:
                match_id = f"{phase}_{match_number}"
            
            match = Match(
                id=match_id,
                category=category,
                phase=phase,
                player1=player1 if isinstance(player1, str) else player1.display_name,
                player2=player2 if isinstance(player2, str) else player2.display_name,
                match_number=match_number,
                status=MatchStatus.SCHEDULED,
                token1=token1,
                token2=token2
            )
            
            matches.append(match)
            counter += 1
        
        return matches, counter

    def _resolve_token(self, token: str, qualified: Dict) -> Any:
        """
        Risolve un token nel giocatore corrispondente.
        
        Token possono essere:
        - "1A" = Girone 1, primo classificato
        - "2B" = Girone 2, secondo classificato
        - "WIN B1" = Vincitore del barrage 1 (da risolvere dopo)
        - "WIN QF1" = Vincitore quarto di finale 1
        - "WIN SF1" = Vincitore semifinale 1
        - "WIN F1" = Vincitore finale
        """
        if token.startswith("WIN "):
            # I token WIN saranno risolti dopo quando le partite saranno giocate
            return token
        
        # Token come "1A", "2B", "3C", ecc.
        if token in qualified:
            return qualified[token]
        
        # Se non trovato, ritorna il token stesso (es. se il girone non esiste)
        print(f"⚠️ Token non trovato: {token}")
        return token
    
    def get_qualified_teams(self, group_standings: Dict[str, List['Player']], 
                           num_qualifiers: Dict[str, int]) -> Dict[str, List['Player']]:
        """
        Estrae i qualificati da ogni girone in base al numero di qualificati.
        
        Args:
            group_standings: Classifiche complete per girone (con chiavi numeriche)
            num_qualifiers: Quanti si qualificano per girone (es. {"1": 2, "2": 2, ...})
        
        Returns:
            Dizionario con i soli qualificati (sempre con chiavi numeriche)
        """
        qualified = {}
        for group_num, players in group_standings.items():
            n = num_qualifiers.get(group_num, 2)  # Default 2
            qualified[group_num] = players[:n]
            print(f"   Girone {group_num}: {n} qualificati ({', '.join([p.display_name for p in players[:n]])})")
        return qualified
    
    # ========================================
    # METODI DI PROPAGAZIONE VINCITORI
    # ========================================
    
    def get_winner_token(self, match) -> Optional[str]:
        """
        Genera il token del vincitore per una partita completata.
        Formato: "WIN {phase_prefix}{match_num}"
        
        Esempi:
        - Partita BARRAGE_1 -> "WIN B1"
        - Partita QF_1 -> "WIN QF1"
        - Partita SF_2 -> "WIN SF2"
        - Partita F_1 -> "WIN F1"
        """
        if not self._is_match_completed(match):
            return None
        
        # Estrai il numero della partita dall'ID
        match_id = match.id
        match_num = 1
        num_match = re.search(r'_(\d+)$', match_id)
        if num_match:
            match_num = int(num_match.group(1))
        
        # Ottieni il prefisso per questa fase
        phase_prefix = self.PHASE_TOKEN_PREFIX.get(match.phase, match.phase)
        
        return f"WIN {phase_prefix}{match_num}"
    
    def propagate_winners(self, matches: List, players_list: List = None) -> int:
        """
        Propaga SOLO i vincitori delle partite completate alle partite successive.
        
        Args:
            matches: Lista di tutte le partite del torneo
            players_list: Lista di tutti i giocatori (per risolvere i nomi)
        
        Returns:
            Numero di token risolti
        """
        print("\n" + "="*70)
        print("🔄 PROPAGAZIONE VINCITORI FASE FINALE")
        print("="*70)
        
        # Filtra solo partite di fase finale
        knockout_matches = [m for m in matches 
                           if hasattr(m, 'phase') and m.phase in 
                           ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]]
        
        if not knockout_matches:
            print("   ⚠️ Nessuna partita di fase finale trovata")
            return 0
        
        # Ordine delle fasi (dalle prime alle ultime)
        phase_order = {"BARRAGE": 0, "R64": 1, "R32": 2, "R16": 3, "QF": 4, "SF": 5, "F": 6}
        
        # Dizionario per tenere traccia dei vincitori
        winners = {}  # token -> player_name
        
        # Passo 1: Trova tutte le partite completate e registra i vincitori
        for match in knockout_matches:
            if not self._is_match_completed(match):
                continue
            
            winner = self._get_winner(match)
            if not winner:
                continue
            
            winner_token = self.get_winner_token(match)
            if winner_token:
                winners[winner_token] = winner
                print(f"\n   🏆 Partita {match.id} completata:")
                print(f"      Vincitore: {winner}")
                print(f"      Token generato: {winner_token}")
        
        # Passo 2: Applica i vincitori alle partite successive
        resolved = 0
        
        # Ordina le partite per fase (dalle più piccole alle più grandi)
        knockout_matches.sort(key=lambda m: phase_order.get(m.phase, 99))
        
        for match in knockout_matches:
            # Salta partite già completate
            if self._is_match_completed(match):
                continue
            
            updated = False
            
            # Controlla se il player1 è un token da risolvere
            if match.player1 and match.player1 in winners:
                old_player1 = match.player1
                match.player1 = winners[match.player1]
                if hasattr(match, 'token1') and match.token1 == old_player1:
                    match.token1 = winners[match.player1]
                print(f"      ✅ {match.id}: player1 aggiornato da '{old_player1}' a '{match.player1}'")
                updated = True
                resolved += 1
            
            # Controlla anche token1 (se esiste)
            if hasattr(match, 'token1') and match.token1 and match.token1 in winners:
                old_token1 = match.token1
                match.token1 = winners[match.token1]
                if not match.player1 or match.player1 == old_token1:
                    match.player1 = winners[match.token1]
                print(f"      ✅ {match.id}: token1 aggiornato da '{old_token1}' a '{match.token1}'")
                updated = True
                resolved += 1
            
            # Controlla se il player2 è un token da risolvere
            if match.player2 and match.player2 in winners:
                old_player2 = match.player2
                match.player2 = winners[match.player2]
                if hasattr(match, 'token2') and match.token2 == old_player2:
                    match.token2 = winners[match.player2]
                print(f"      ✅ {match.id}: player2 aggiornato da '{old_player2}' a '{match.player2}'")
                updated = True
                resolved += 1
            
            # Controlla anche token2 (se esiste)
            if hasattr(match, 'token2') and match.token2 and match.token2 in winners:
                old_token2 = match.token2
                match.token2 = winners[match.token2]
                if not match.player2 or match.player2 == old_token2:
                    match.player2 = winners[match.token2]
                print(f"      ✅ {match.id}: token2 aggiornato da '{old_token2}' a '{match.token2}'")
                updated = True
                resolved += 1
            
            if updated:
                print(f"      📍 {match.id} ora: {match.player1} vs {match.player2}")
        
        print(f"\n✅ Propagazione completata: {resolved} token risolti")
        return resolved
    
    def _is_match_completed(self, match) -> bool:
        """Verifica se una partita individuale è completata."""
        # Controlla lo status
        if hasattr(match, 'status'):
            status_text = str(match.status)
            if hasattr(match.status, 'value'):
                status_text = match.status.value
            
            if "COMPLETED" in status_text or "Giocata" in status_text:
                return True
        
        # Controlla se ci sono gol
        if hasattr(match, 'goals1') and hasattr(match, 'goals2'):
            if match.goals1 is not None and match.goals2 is not None:
                return True
        
        return False
    
    def _get_winner(self, match) -> Optional[str]:
        """Restituisce il nome del vincitore."""
        if hasattr(match, 'winner') and match.winner:
            return match.winner
        
        if hasattr(match, 'goals1') and hasattr(match, 'goals2'):
            if match.goals1 is not None and match.goals2 is not None:
                if match.goals1 > match.goals2:
                    return match.player1
                elif match.goals2 > match.goals1:
                    return match.player2
        
        return None


def get_qualifiers_per_group(group_sizes: List[int]) -> Dict[str, int]:
    """
    Determina quanti giocatori si qualificano per girone in base alle dimensioni.
    
    Regole tipiche FISTF:
    - Gironi da 3-4: qualificano i primi 2
    - Gironi da 5-6: qualificano i primi 3
    - Gironi da 7+: qualificano i primi 4 (raro)
    
    Returns:
        Dizionario con chiavi numeriche "1", "2", "3", ...
    """
    result = {}
    
    for i, size in enumerate(group_sizes):
        group_num = str(i + 1)  # 1, 2, 3, ...
        if size <= 4:
            result[group_num] = 2
        elif size <= 6:
            result[group_num] = 3
        else:
            result[group_num] = 4
        print(f"   Girone {group_num} ({size} giocatori): {result[group_num]} qualificati")
    
    return result