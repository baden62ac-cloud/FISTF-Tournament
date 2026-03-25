"""
Generazione fase finale per tornei a squadre secondo formule FISTF.
Basato sul Tournament Organisers' Handbook 2025-26.

Convenzione FISTF per i token:
- Qualificati: "1A" = Girone 1 primo classificato, "1B" = Girone 1 secondo classificato, ecc.
- Vincitori: "WIN B1", "WIN QF1", "WIN SF1", "WIN F1"
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict


class TeamKnockoutGenerator:
    """Genera il tabellone della fase finale per squadre."""
    
    # Mappa prefissi categoria (coerente con team_scheduler.py)
    CATEGORY_PREFIX = {
        "Team Open": "O",
        "Team Veterans": "V",
        "Team Women": "W",
        "Team U20": "U20",
        "Team U16": "U16",
        "Team U12": "U12",
        "Team Eccellenza": "E",
        "Team Promozione": "P",
        "Team MOICAT": "M"
    }
    
    def __init__(self):
        json_path = Path(__file__).parent.parent / "config" / "bracket_formulas.json"
        with open(json_path, 'r', encoding='utf-8') as f:
            self.formulas = json.load(f)
    
    def _get_category_prefix(self, category: str) -> str:
        """Restituisce il prefisso per una categoria."""
        return self.CATEGORY_PREFIX.get(category, "X")
    
    def get_qualifiers_per_group(self, group_sizes: List[int]) -> Dict[str, int]:
        """
        Determina quanti si qualificano per girone in base alle dimensioni.
        Regole FISTF per tornei a squadre.
        """
        num_groups = len(group_sizes)
        result = {}
        
        print(f"\n📊 Calcolo qualificati per {num_groups} gironi:")
        
        for i, size in enumerate(group_sizes):
            group_num = str(i + 1)
            
            # CASO SPECIALE: 2 GIRONI - servono 2 qualificati ciascuno per semifinali
            if num_groups == 2:
                result[group_num] = 2
                print(f"   Girone {group_num} ({size} squadre): {result[group_num]} qualificate (per semifinali)")
            
            # Per 3-4 gironi: 2 qualificati per girone
            elif num_groups <= 4:
                result[group_num] = 2
                print(f"   Girone {group_num} ({size} squadre): {result[group_num]} qualificate")
            
            # Per 5-6 gironi: 2 qualificati + eventuali terzi
            elif num_groups <= 6:
                if size <= 3:
                    result[group_num] = 1
                elif size <= 5:
                    result[group_num] = 2
                else:
                    result[group_num] = 3
                print(f"   Girone {group_num} ({size} squadre): {result[group_num]} qualificate")
            
            # Per 7-8 gironi: 1 qualificato + migliori secondi
            else:
                if size <= 3:
                    result[group_num] = 1
                elif size <= 5:
                    result[group_num] = 1
                else:
                    result[group_num] = 2
                print(f"   Girone {group_num} ({size} squadre): {result[group_num]} qualificate")
        
        return result
    
    def generate_bracket(self, num_groups: int, group_standings: Dict[str, List['Team']], 
                        category: str = "", category_prefix: str = "") -> List['TeamMatch']:
        """
        Genera il tabellone completo per squadre secondo le formule FISTF.
        
        Args:
            num_groups: Numero di gironi (2, 3, 4, 5, 6, 7, 8, ...)
            group_standings: Dict con gruppo -> lista squadre in ordine
            category: Nome categoria (es. "Team Open")
            category_prefix: Prefisso per ID (es. "O" per Open)
        
        Returns:
            Lista di partite di fase finale
        """
        formula_key = str(num_groups)
        if formula_key not in self.formulas:
            raise ValueError(f"Nessuna formula per {num_groups} gironi")
        
        formula = self.formulas[formula_key]
        print(f"\n📋 Formula per {num_groups} gironi (squadre): {formula}")
        
        # Se non è stato fornito un prefisso, ricavalo dalla categoria
        if not category_prefix and category:
            category_prefix = self._get_category_prefix(category)
        
        # ========================================
        # CASO 2 GIRONI: GESTIONE COMPLETA
        # ========================================
        if num_groups == 2:
            print("\n🏆 CASO: 2 GIRONI -> Generazione fase finale")
            return self._generate_two_groups_bracket(
                group_standings, category, category_prefix
            )
        
        # Per gli altri casi, usa le formule dal JSON
        return self._generate_from_formula(formula, group_standings, category, category_prefix)
    
    def _generate_from_formula(self, formula: Dict, group_standings: Dict[str, List['Team']],
                              category: str, category_prefix: str) -> List['TeamMatch']:
        """
        Genera il tabellone a partire dalla formula JSON.
        """
        from models.team_match import TeamMatch, IndividualMatchResult, MatchStatus
        
        # Crea mappa qualificati: "1A" -> Team
        qualified = {}
        print("\n📊 Mappa qualificati squadre:")
        for group_num, teams in group_standings.items():
            for pos_idx, team in enumerate(teams):
                if pos_idx < 6:
                    letter = chr(65 + pos_idx)
                    token = f"{group_num}{letter}"
                    qualified[token] = team
                    team_name = team.display_name if hasattr(team, 'display_name') else str(team)
                    print(f"   {token} -> {team_name}")
        
        # Genera partite con ID specifici per categoria
        all_matches = []
        phase_order = ["BARRAGE", "QF", "SF", "F"]
        
        # Dizionario per tenere traccia dei contatori per fase
        phase_counters = {phase: 1 for phase in phase_order}
        
        for phase in phase_order:
            if phase in formula:
                print(f"\n🔨 Generazione fase {phase} per {category}...")
                phase_matches, phase_counters = self._create_phase_matches(
                    formula[phase], 
                    qualified, 
                    phase, 
                    phase_counters,
                    category, 
                    category_prefix
                )
                all_matches.extend(phase_matches)
                
                for m in phase_matches:
                    team1_name = m.player1 if m.player1 else m.token1
                    team2_name = m.player2 if m.player2 else m.token2
                    print(f"   {m.id}: {team1_name} vs {team2_name}")
        
        print(f"\n✅ Totale partite fase finale generate per {category}: {len(all_matches)}")
        return all_matches
    
    def _generate_two_groups_bracket(self, group_standings: Dict[str, List['Team']],
                                    category: str, category_prefix: str) -> List['TeamMatch']:
        """
        Genera tabellone per 2 gironi gestendo tutti i casi:
        - Se entrambi i gironi hanno >=2 squadre: semifinali + finale
        - Se un girone ha 1 squadra: finale diretta
        """
        from models.team_match import TeamMatch, IndividualMatchResult, MatchStatus
        
        matches = []
        
        # Estrai i due gironi
        groups = list(group_standings.items())
        if len(groups) != 2:
            print(f"⚠️ Attenzione: {len(groups)} gironi, attesi 2")
            return []
        
        group1_num, group1_teams = groups[0]  # Girone 1
        group2_num, group2_teams = groups[1]  # Girone 2
        
        print(f"\n🏆 Generazione FASE FINALE per {category} (2 GIRONI):")
        print(f"   Girone {group1_num}: {len(group1_teams)} squadre")
        for i, team in enumerate(group1_teams):
            print(f"      {i+1}°: {team.display_name}")
        print(f"   Girone {group2_num}: {len(group2_teams)} squadre")
        for i, team in enumerate(group2_teams):
            print(f"      {i+1}°: {team.display_name}")
        
        # ========================================
        # CASO 1: Entrambi i gironi hanno 1 squadra -> FINALE DIRETTA
        # ========================================
        if len(group1_teams) == 1 and len(group2_teams) == 1:
            print("\n✅ Entrambi i gironi hanno 1 squadra - Finale diretta")
            
            match_id_f = f"{category_prefix}_F_1"
            
            match_f = TeamMatch(
                id=match_id_f,
                category=category,
                phase="F",
                team1=group1_teams[0].id if hasattr(group1_teams[0], 'id') else str(group1_teams[0]),
                team2=group2_teams[0].id if hasattr(group2_teams[0], 'id') else str(group2_teams[0]),
                player1=group1_teams[0].display_name if hasattr(group1_teams[0], 'display_name') else str(group1_teams[0]),
                player2=group2_teams[0].display_name if hasattr(group2_teams[0], 'display_name') else str(group2_teams[0]),
                match_number=1,
                status=None,
                token1=f"{group1_num}A",
                token2=f"{group2_num}A",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_f)
            print(f"\n   🏆 FINALE DIRETTA:")
            print(f"      {group1_teams[0].display_name} vs {group2_teams[0].display_name}")
            print(f"      ID: {match_id_f}")
            
            return matches
        
        # ========================================
        # CASO 2: Un girone ha 1 squadra, l'altro ne ha 2+ -> SEMIFINALE + FINALE
        # ========================================
        elif len(group1_teams) == 1 and len(group2_teams) >= 2:
            print("\n⚠️ Girone 1 ha 1 squadra, Girone 2 ne ha 2+ - Semifinale speciale")
            
            # La squadra del girone 1 va direttamente in finale
            team_final1 = group1_teams[0]
            
            # Semifinale tra 1° e 2° del girone 2
            team1_sf = group2_teams[0]  # 1° Girone 2
            team2_sf = group2_teams[1]  # 2° Girone 2
            
            match_id_sf = f"{category_prefix}_SF_1"
            
            match_sf = TeamMatch(
                id=match_id_sf,
                category=category,
                phase="SF",
                team1=team1_sf.id if hasattr(team1_sf, 'id') else str(team1_sf),
                team2=team2_sf.id if hasattr(team2_sf, 'id') else str(team2_sf),
                player1=team1_sf.display_name if hasattr(team1_sf, 'display_name') else str(team1_sf),
                player2=team2_sf.display_name if hasattr(team2_sf, 'display_name') else str(team2_sf),
                match_number=1,
                status=None,
                token1=f"{group2_num}A",
                token2=f"{group2_num}B",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_sf)
            print(f"\n   ⚽ SEMIFINALE:")
            print(f"      {team1_sf.display_name} (1° G{group2_num}) vs {team2_sf.display_name} (2° G{group2_num})")
            
            # Finale
            match_id_f = f"{category_prefix}_F_1"
            
            match_f = TeamMatch(
                id=match_id_f,
                category=category,
                phase="F",
                team1=team_final1.id if hasattr(team_final1, 'id') else str(team_final1),
                team2=None,
                player1=team_final1.display_name if hasattr(team_final1, 'display_name') else str(team_final1),
                player2="WIN SF1",
                match_number=1,
                status=None,
                token1=f"{group1_num}A",
                token2="WIN SF1",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_f)
            print(f"\n   🏆 FINALE:")
            print(f"      {team_final1.display_name} (1° G{group1_num}) vs WIN SF1")
            
            return matches
        
        # ========================================
        # CASO 3: Viceversa, girone 2 ha 1 squadra, girone 1 ne ha 2+
        # ========================================
        elif len(group1_teams) >= 2 and len(group2_teams) == 1:
            print("\n⚠️ Girone 2 ha 1 squadra, Girone 1 ne ha 2+ - Semifinale speciale")
            
            # La squadra del girone 2 va direttamente in finale
            team_final2 = group2_teams[0]
            
            # Semifinale tra 1° e 2° del girone 1
            team1_sf = group1_teams[0]  # 1° Girone 1
            team2_sf = group1_teams[1]  # 2° Girone 1
            
            match_id_sf = f"{category_prefix}_SF_1"
            
            match_sf = TeamMatch(
                id=match_id_sf,
                category=category,
                phase="SF",
                team1=team1_sf.id if hasattr(team1_sf, 'id') else str(team1_sf),
                team2=team2_sf.id if hasattr(team2_sf, 'id') else str(team2_sf),
                player1=team1_sf.display_name if hasattr(team1_sf, 'display_name') else str(team1_sf),
                player2=team2_sf.display_name if hasattr(team2_sf, 'display_name') else str(team2_sf),
                match_number=1,
                status=None,
                token1=f"{group1_num}A",
                token2=f"{group1_num}B",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_sf)
            print(f"\n   ⚽ SEMIFINALE:")
            print(f"      {team1_sf.display_name} (1° G{group1_num}) vs {team2_sf.display_name} (2° G{group1_num})")
            
            # Finale
            match_id_f = f"{category_prefix}_F_1"
            
            match_f = TeamMatch(
                id=match_id_f,
                category=category,
                phase="F",
                team1=None,
                team2=team_final2.id if hasattr(team_final2, 'id') else str(team_final2),
                player1="WIN SF1",
                player2=team_final2.display_name if hasattr(team_final2, 'display_name') else str(team_final2),
                match_number=1,
                status=None,
                token1="WIN SF1",
                token2=f"{group2_num}A",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_f)
            print(f"\n   🏆 FINALE:")
            print(f"      WIN SF1 vs {team_final2.display_name} (1° G{group2_num})")
            
            return matches
        
        # ========================================
        # CASO 4: Entrambi i gironi hanno 2+ squadre -> SEMIFINALI REGOLARI
        # ========================================
        else:
            print("\n✅ Entrambi i gironi hanno almeno 2 squadre - Semifinali regolari")
            
            # SEMIFINALE 1: 1° Gruppo 1 vs 2° Gruppo 2
            team1_sf1 = group1_teams[0]  # 1° Girone 1
            team2_sf1 = group2_teams[1]  # 2° Girone 2
            
            match_id_sf1 = f"{category_prefix}_SF_1"
            
            match_sf1 = TeamMatch(
                id=match_id_sf1,
                category=category,
                phase="SF",
                team1=team1_sf1.id if hasattr(team1_sf1, 'id') else str(team1_sf1),
                team2=team2_sf1.id if hasattr(team2_sf1, 'id') else str(team2_sf1),
                player1=team1_sf1.display_name if hasattr(team1_sf1, 'display_name') else str(team1_sf1),
                player2=team2_sf1.display_name if hasattr(team2_sf1, 'display_name') else str(team2_sf1),
                match_number=1,
                status=None,
                token1=f"{group1_num}A",
                token2=f"{group2_num}B",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_sf1)
            print(f"\n   🔵 SEMIFINALE 1:")
            print(f"      {team1_sf1.display_name} (1° G{group1_num}) vs {team2_sf1.display_name} (2° G{group2_num})")
            
            # SEMIFINALE 2: 1° Gruppo 2 vs 2° Gruppo 1
            team1_sf2 = group2_teams[0]  # 1° Girone 2
            team2_sf2 = group1_teams[1]  # 2° Girone 1
            
            match_id_sf2 = f"{category_prefix}_SF_2"
            
            match_sf2 = TeamMatch(
                id=match_id_sf2,
                category=category,
                phase="SF",
                team1=team1_sf2.id if hasattr(team1_sf2, 'id') else str(team1_sf2),
                team2=team2_sf2.id if hasattr(team2_sf2, 'id') else str(team2_sf2),
                player1=team1_sf2.display_name if hasattr(team1_sf2, 'display_name') else str(team1_sf2),
                player2=team2_sf2.display_name if hasattr(team2_sf2, 'display_name') else str(team2_sf2),
                match_number=2,
                status=None,
                token1=f"{group2_num}A",
                token2=f"{group1_num}B",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_sf2)
            print(f"\n   🔴 SEMIFINALE 2:")
            print(f"      {team1_sf2.display_name} (1° G{group2_num}) vs {team2_sf2.display_name} (2° G{group1_num})")
            
            # FINALE
            match_id_f = f"{category_prefix}_F_1"
            
            match_f = TeamMatch(
                id=match_id_f,
                category=category,
                phase="F",
                team1=None,
                team2=None,
                player1="WIN SF1",
                player2="WIN SF2",
                match_number=1,
                status=None,
                token1="WIN SF1",
                token2="WIN SF2",
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            matches.append(match_f)
            print(f"\n   🏆 FINALE:")
            print(f"      WIN SF1 vs WIN SF2")
            
            return matches
    
    def _create_phase_matches(self, match_list: List[str], qualified: Dict, 
                            phase: str, phase_counters: Dict[str, int],
                            category: str = "", category_prefix: str = "") -> Tuple[List['TeamMatch'], Dict[str, int]]:
        """
        Crea le partite per una fase specifica con ID univoci per categoria.
        
        Returns:
            Tuple: (lista partite, contatori aggiornati)
        """
        from models.team_match import TeamMatch, IndividualMatchResult, MatchStatus
        
        matches = []
        
        for i in range(0, len(match_list), 2):
            if i + 1 >= len(match_list):
                break
            
            token1 = match_list[i]
            token2 = match_list[i + 1]
            
            team1 = self._resolve_token(token1, qualified)
            team2 = self._resolve_token(token2, qualified)
            
            match_number = phase_counters[phase]
            phase_counters[phase] += 1
            
            # ===== ID UNIVOCO PER CATEGORIA =====
            # Formato: PREFIX_PHASE_NUMBER  (es. O_QF_1, V_SF_2)
            if category_prefix:
                match_id = f"{category_prefix}_{phase}_{match_number}"
            else:
                match_id = f"{phase}_{match_number}"
            
            # Prepara nomi per visualizzazione
            player1 = team1.display_name if isinstance(team1, object) and hasattr(team1, 'display_name') else str(team1)
            player2 = team2.display_name if isinstance(team2, object) and hasattr(team2, 'display_name') else str(team2)
            
            # Se sono token, usa il token come nome
            if token1.startswith("WIN "):
                player1 = token1
            if token2.startswith("WIN "):
                player2 = token2
            
            # Crea partita con 4 incontri vuoti
            match = TeamMatch(
                id=match_id,
                category=category,
                phase=phase,
                team1=team1.id if isinstance(team1, object) and hasattr(team1, 'id') else str(team1),
                team2=team2.id if isinstance(team2, object) and hasattr(team2, 'id') else str(team2),
                player1=player1,
                player2=player2,
                match_number=match_number,
                status=None,
                token1=token1,
                token2=token2,
                individual_matches=[
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None
                    )
                    for i in range(4)
                ]
            )
            
            matches.append(match)
        
        return matches, phase_counters
    
    def _resolve_token(self, token: str, qualified: Dict) -> Any:
        """Risolve un token nel team corrispondente."""
        if token.startswith("WIN "):
            return token
        
        if token in qualified:
            return qualified[token]
        
        print(f"⚠️ Token non trovato: {token}")
        return token
    
    # ========================================
    # METODI DI PROPAGAZIONE VINCITORI (CORRETTI CON FILTRO PER CATEGORIA)
    # ========================================
    
    def propagate_winners(self, matches: List, teams_list: List = None) -> int:
        """
        Propaga i vincitori alle partite successive della STESSA categoria.
        Gestisce token nel formato "WIN SF1", "WIN QF2", "WIN B3", ecc.
        
        IMPORTANTE: La propagazione avviene solo tra partite della stessa categoria
        per evitare conflitti tra Open, Veterans, U20, ecc.
        """
        print("\n" + "="*70)
        print("🔄 PROPAGAZIONE VINCITORI FASE FINALE SQUADRE")
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
        
        # Dizionario per tenere traccia dei vincitori, organizzato per categoria
        winners_by_category = defaultdict(dict)  # category -> {token: winner_info}
        
        # Mappa per conversione fase -> prefisso token
        phase_token_map = {
            "BARRAGE": "B",
            "QF": "QF",
            "SF": "SF",
            "F": "F",
            "R16": "R16",
            "R32": "R32",
            "R64": "R64"
        }
        
        # Passo 1: Trova tutte le partite completate e registra i vincitori per categoria
        for match in knockout_matches:
            if not self._is_match_completed(match):
                continue
            
            winner_id = self._get_winner_id(match)
            if not winner_id:
                continue
            
            winner_name = self._get_team_name(winner_id, teams_list)
            category = match.category
            
            # Estrai il numero della partita dall'ID
            match_num = 1
            num_match = re.search(r'_(\d+)$', match.id)
            if num_match:
                match_num = int(num_match.group(1))
            
            token_prefix = phase_token_map.get(match.phase, match.phase)
            winner_token = f"WIN {token_prefix}{match_num}"
            
            # Registra il vincitore nella sua categoria
            winners_by_category[category][winner_token] = {
                'id': winner_id,
                'name': winner_name
            }
            
            print(f"\n   🏆 Partita {match.id} completata (categoria: {category}):")
            print(f"      Vincitore: {winner_name}")
            print(f"      Token generato: {winner_token}")
        
        # Passo 2: Applica i vincitori alle partite successive della STESSA categoria
        resolved = 0
        
        # Ordina le partite per fase (dalle più piccole alle più grandi)
        knockout_matches.sort(key=lambda m: phase_order.get(m.phase, 99))
        
        for match in knockout_matches:
            # Salta partite già completate
            if self._is_match_completed(match):
                continue
            
            category = match.category
            
            # Ottieni i vincitori di questa categoria
            winners = winners_by_category.get(category, {})
            
            if not winners:
                continue
            
            updated = False
            
            # Controlla se il player1 è un token da risolvere
            if match.player1 and match.player1 in winners:
                winner = winners[match.player1]
                old_player1 = match.player1
                match.player1 = winner['name']
                if hasattr(match, 'team1'):
                    match.team1 = winner['id']
                if hasattr(match, 'token1') and match.token1 == old_player1:
                    match.token1 = winner['name']
                print(f"      ✅ {match.id} ({category}): player1 aggiornato")
                print(f"         da '{old_player1}' a '{winner['name']}'")
                updated = True
                resolved += 1
            
            # Controlla anche token1 (se esiste)
            if hasattr(match, 'token1') and match.token1 and match.token1 in winners:
                winner = winners[match.token1]
                old_token1 = match.token1
                match.token1 = winner['name']
                if hasattr(match, 'team1') and not match.team1:
                    match.team1 = winner['id']
                if not match.player1 or match.player1 == old_token1:
                    match.player1 = winner['name']
                print(f"      ✅ {match.id} ({category}): token1 aggiornato")
                print(f"         da '{old_token1}' a '{winner['name']}'")
                updated = True
                resolved += 1
            
            # Controlla se il player2 è un token da risolvere
            if match.player2 and match.player2 in winners:
                winner = winners[match.player2]
                old_player2 = match.player2
                match.player2 = winner['name']
                if hasattr(match, 'team2'):
                    match.team2 = winner['id']
                if hasattr(match, 'token2') and match.token2 == old_player2:
                    match.token2 = winner['name']
                print(f"      ✅ {match.id} ({category}): player2 aggiornato")
                print(f"         da '{old_player2}' a '{winner['name']}'")
                updated = True
                resolved += 1
            
            # Controlla anche token2 (se esiste)
            if hasattr(match, 'token2') and match.token2 and match.token2 in winners:
                winner = winners[match.token2]
                old_token2 = match.token2
                match.token2 = winner['name']
                if hasattr(match, 'team2') and not match.team2:
                    match.team2 = winner['id']
                if not match.player2 or match.player2 == old_token2:
                    match.player2 = winner['name']
                print(f"      ✅ {match.id} ({category}): token2 aggiornato")
                print(f"         da '{old_token2}' a '{winner['name']}'")
                updated = True
                resolved += 1
            
            if updated:
                print(f"      📍 {match.id} ora: {match.player1} vs {match.player2}")
        
        print(f"\n✅ Propagazione completata: {resolved} token risolti")
        return resolved
    
    def _is_match_completed(self, match) -> bool:
        """Verifica se una partita a squadre è completata."""
        # Controlla lo status
        if hasattr(match, 'status'):
            status_text = str(match.status)
            if hasattr(match.status, 'value'):
                status_text = match.status.value
            
            if "COMPLETED" in status_text or "Giocata" in status_text:
                return True
        
        # Controlla gli incontri individuali
        if hasattr(match, 'individual_matches') and match.individual_matches:
            all_played = True
            for im in match.individual_matches:
                if hasattr(im, 'goals1') and hasattr(im, 'goals2'):
                    if im.goals1 is None or im.goals2 is None:
                        all_played = False
                        break
                else:
                    all_played = False
                    break
            return all_played
        
        return False
    
    def _get_winner_id(self, match) -> Optional[str]:
        """Restituisce l'ID della squadra vincente."""
        # Se c'è un campo winner esplicito
        if hasattr(match, 'winner') and match.winner:
            return match.winner
        
        # Altrimenti calcola dagli incontri individuali
        if hasattr(match, 'individual_matches') and match.individual_matches:
            wins1 = 0
            wins2 = 0
            
            for im in match.individual_matches:
                if hasattr(im, 'goals1') and hasattr(im, 'goals2') and im.goals1 is not None and im.goals2 is not None:
                    if im.goals1 > im.goals2:
                        wins1 += 1
                    elif im.goals2 > im.goals1:
                        wins2 += 1
            
            if wins1 > wins2 and hasattr(match, 'team1'):
                return match.team1
            elif wins2 > wins1 and hasattr(match, 'team2'):
                return match.team2
        
        return None
    
    def _get_team_name(self, team_id: str, teams_list: List = None) -> str:
        """Restituisce il nome visualizzato della squadra."""
        if not team_id or team_id.startswith("WIN "):
            return team_id
        
        if teams_list:
            for team in teams_list:
                if hasattr(team, 'id') and team.id == team_id:
                    return team.display_name
                if hasattr(team, 'display_name') and team.display_name == team_id:
                    return team.display_name
        
        return team_id
    
    def get_qualified_teams(self, group_standings: Dict[str, List['Team']], 
                           num_qualifiers: Dict[str, int]) -> Dict[str, List['Team']]:
        """Estrae i qualificati da ogni girone."""
        qualified = {}
        for group_num, teams in group_standings.items():
            n = num_qualifiers.get(group_num, 2)
            qualified[group_num] = teams[:n]
            team_names = ', '.join([t.display_name for t in teams[:n]])
            print(f"   Girone {group_num}: {n} qualificati ({team_names})")
        return qualified