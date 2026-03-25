"""
Generazione calendario partite per fase a gironi secondo regole FISTF.
Gestisce multiple categorie in contemporanea con distribuzione bilanciata dei turni.
Implementa:
- Tabella ufficiale FISTF 2.3.2 per ordine partite
- Regola 2.3.3 per conflitti club/nazione (prima partita tra stessi club)
- Ottimizzazione avanzata: usa TUTTI i campi disponibili in ogni turno
- RIASSEGNAZIONE DINAMICA DEI CAMPI: quando una categoria finisce, i suoi campi
  vengono riassegnati ad altre categorie che hanno ancora partite da giocare
- Anticipazione partite: gioca partite dei turni successivi quando ci sono campi liberi
- Vincoli: un giocatore NON può giocare più di una partita nello stesso turno
- Massimo matches_per_round per girone per turno
"""
import random
from typing import List, Dict, Tuple, Optional, Set, Any
from itertools import combinations
from collections import defaultdict, deque

# Tabella ufficiale FISTF 2.3.2 - Ordine delle partite
FISTF_MATCH_ORDER = {
    3: [
        [(3, 1)],           # Turno 1: 3 vs 1
        [(2, 3)],           # Turno 2: 2 vs 3
        [(1, 2)]            # Turno 3: 1 vs 2
    ],
    4: [
        [(1, 4), (2, 3)],   # Turno 1: 1vs4, 2vs3
        [(3, 1), (4, 2)],   # Turno 2: 3vs1, 4vs2
        [(1, 2), (3, 4)]    # Turno 3: 1vs2, 3vs4
    ],
    5: [
        [(2, 3), (5, 1)],   # Turno 1: 2vs3, 5vs1
        [(2, 4), (3, 5)],   # Turno 2: 2vs4, 3vs5
        [(4, 1), (5, 2)],   # Turno 3: 4vs1, 5vs2
        [(1, 3), (4, 5)],   # Turno 4: 1vs3, 4vs5
        [(1, 2), (3, 4)]    # Turno 5: 1vs2, 3vs4
    ],
    6: [
        [(1, 5), (2, 3), (4, 6)],  # Turno 1: 1vs5, 2vs3, 4vs6
        [(2, 4), (3, 5), (6, 1)],  # Turno 2: 2vs4, 3vs5, 6vs1
        [(1, 4), (5, 2), (6, 3)],  # Turno 3: 1vs4, 5vs2, 6vs3
        [(2, 6), (3, 1), (4, 5)],  # Turno 4: 2vs6, 3vs1, 4vs5
        [(1, 2), (3, 4), (5, 6)]   # Turno 5: 1vs2, 3vs4, 5vs6
    ],
    7: [
        [(1, 3), (4, 7), (5, 6)],           # Turno 1
        [(1, 5), (2, 4), (6, 7)],           # Turno 2
        [(2, 6), (3, 5), (7, 1)],           # Turno 3
        [(1, 2), (3, 7), (4, 6)],           # Turno 4
        [(2, 3), (4, 1), (7, 5)],           # Turno 5
        [(3, 4), (5, 2), (6, 1)],           # Turno 6
        [(5, 4), (6, 3), (7, 2)]            # Turno 7
    ],
    8: [
        [(1, 3), (2, 8), (4, 7), (5, 6)],   # Turno 1
        [(1, 5), (2, 4), (3, 8), (6, 7)],   # Turno 2
        [(3, 5), (6, 2), (7, 1), (8, 4)],   # Turno 3
        [(1, 2), (4, 6), (5, 8), (7, 3)],   # Turno 4
        [(1, 4), (2, 3), (5, 7), (8, 6)],   # Turno 5
        [(3, 4), (5, 2), (6, 1), (7, 8)],   # Turno 6
        [(2, 7), (3, 6), (4, 5), (8, 1)]    # Turno 7
    ],
    9: [
        [(1, 3), (4, 9), (5, 8), (6, 7)],           # Turno 1
        [(1, 5), (2, 4), (7, 8), (9, 6)],           # Turno 2
        [(2, 6), (3, 5), (7, 1), (8, 9)],           # Turno 3
        [(1, 9), (6, 4), (7, 3), (8, 2)],           # Turno 4
        [(2, 1), (4, 8), (5, 7), (9, 3)],           # Turno 5
        [(1, 4), (3, 2), (5, 9), (8, 6)],           # Turno 6
        [(2, 5), (4, 3), (6, 1), (9, 7)],           # Turno 7
        [(3, 6), (5, 4), (7, 2), (8, 1)],           # Turno 8
        [(3, 8), (4, 7), (6, 5), (9, 2)]            # Turno 9
    ],
    10: [
        [(1, 3), (2, 10), (4, 9), (5, 8), (6, 7)],  # Turno 1
        [(2, 4), (3, 10), (5, 1), (7, 8), (9, 6)],  # Turno 2
        [(3, 5), (4, 10), (6, 2), (7, 1), (8, 9)],  # Turno 3
        [(1, 9), (2, 8), (3, 7), (4, 6), (10, 5)],  # Turno 4
        [(1, 2), (5, 7), (8, 4), (9, 3), (10, 6)],  # Turno 5
        [(1, 4), (2, 3), (5, 9), (6, 8), (7, 10)],  # Turno 6
        [(1, 6), (2, 5), (3, 4), (8, 10), (9, 7)],  # Turno 7
        [(4, 5), (6, 3), (7, 2), (8, 1), (10, 9)],  # Turno 8
        [(3, 8), (4, 7), (5, 6), (9, 2), (10, 1)]   # Turno 9
    ]
}


class TournamentScheduler:
    """
    Scheduler principale con riassegnazione dinamica dei campi.
    Quando una categoria finisce le sue partite, i suoi campi vengono
    riassegnati ad altre categorie che hanno ancora partite da giocare.
    """
    
    def __init__(self, total_fields: int, fields_per_category: Dict[str, int]):
        self.total_fields = total_fields
        self.fields_per_category = fields_per_category
        self.category_fields = self._calculate_category_fields()
    
    def _get_group_letter(self, group_name: str) -> str:
        if '-' in group_name:
            return group_name.split('-')[-1]
        return group_name
    
    def _get_category_from_group(self, group_name: str) -> str:
        if group_name.startswith('O-'):
            return 'Open'
        elif group_name.startswith('V-'):
            return 'Veterans'
        elif group_name.startswith('W-'):
            return 'Women'
        elif group_name.startswith('U20-'):
            return 'U20'
        elif group_name.startswith('U16-'):
            return 'U16'
        elif group_name.startswith('U12-'):
            return 'U12'
        elif group_name.startswith('E-'):
            return 'Eccellenza'
        elif group_name.startswith('P-'):
            return 'Promozione'
        elif group_name.startswith('M-'):
            return 'MOICAT'
        else:
            return 'Open'
    
    def _calculate_category_fields(self) -> Dict[str, List[int]]:
        """Calcola i numeri di campo assegnati a ciascuna categoria."""
        result = {}
        current_field = 1
        sorted_categories = sorted(self.fields_per_category.keys())
        
        for category in sorted_categories:
            num_fields = self.fields_per_category[category]
            if num_fields > 0:
                fields = list(range(current_field, current_field + num_fields))
                result[category] = fields
                current_field += num_fields
        
        return result
    
    def _reorder_for_clash(self, players: List['Player'], group_name: str) -> List['Player']:
        """Riordina i giocatori secondo regola FISTF 2.3.3."""
        club_counts = defaultdict(list)
        for i, player in enumerate(players):
            if player.club:
                club_counts[player.club].append((i, player))
        
        conflicting_club = None
        conflicting_players = []
        
        for club, members in club_counts.items():
            if len(members) >= 2:
                conflicting_club = club
                conflicting_players = [p for _, p in members]
                break
        
        if not conflicting_players:
            return players
        
        print(f"   ⚠️ Conflitto club '{conflicting_club}' nel girone {group_name}: {[p.display_name for p in conflicting_players]}")
        print(f"   🔄 Applico regola FISTF 2.3.3: i due giocatori si affronteranno al primo turno")
        
        conflicting_two = sorted(conflicting_players, key=lambda p: p.seed if p.seed else 999)[:2]
        other_conflicting = [p for p in conflicting_players if p not in conflicting_two]
        
        result = conflicting_two.copy()
        remaining = other_conflicting + [p for p in players if p not in conflicting_players]
        remaining.sort(key=lambda p: p.seed if p.seed else 999)
        result.extend(remaining)
        
        return result
    
    def _generate_fistf_rounds(self, players: List['Player'], group_name: str = "") -> List[List[Tuple]]:
        """Genera i turni secondo la tabella ufficiale FISTF."""
        reordered_players = self._reorder_for_clash(players, group_name)
        n = len(reordered_players)
        
        if n not in FISTF_MATCH_ORDER:
            print(f"⚠️ Dimensione girone {n} non supportata dalla tabella FISTF, uso round-robin classico")
            return self._generate_round_robin_fallback(reordered_players)
        
        fistf_rounds = FISTF_MATCH_ORDER[n]
        rounds = []
        
        for round_num, round_matches in enumerate(fistf_rounds):
            matches = []
            for a, b in round_matches:
                player_a = reordered_players[a-1] if a <= len(reordered_players) else None
                player_b = reordered_players[b-1] if b <= len(reordered_players) else None
                
                if player_a and player_b:
                    matches.append((player_a, player_b))
            
            rounds.append(matches)
        
        return rounds
    
    def _generate_round_robin_fallback(self, players: List['Player']) -> List[List[Tuple]]:
        """Genera turni all'italiana classica."""
        n = len(players)
        
        if n % 2 == 1:
            players_list = players + [None]
            n += 1
        else:
            players_list = players.copy()
        
        rounds = []
        
        for round_num in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                p1 = players_list[i]
                p2 = players_list[n - 1 - i]
                
                if p1 is not None and p2 is not None:
                    round_matches.append((p1, p2))
            
            rounds.append(round_matches)
            players_list = [players_list[0]] + [players_list[-1]] + players_list[1:-1]
        
        return rounds
    
    def generate_schedule(self, groups: Dict[str, List['Player']]) -> List['Match']:
        """
        Genera calendario ottimizzato con RIASSEGNAZIONE DINAMICA DEI CAMPI.
        Quando una categoria finisce le sue partite, i suoi campi vengono
        riassegnati ad altre categorie che hanno ancora partite.
        """
        from models.match import Match, MatchStatus
        
        # Step 1: Raggruppa gironi per categoria
        groups_by_category = defaultdict(dict)
        all_players_by_name = {}
        
        for group_name, players in groups.items():
            category = self._get_category_from_group(group_name)
            groups_by_category[category][group_name] = players
            for player in players:
                all_players_by_name[player.display_name] = player
        
        # Step 2: Genera turni per ogni girone
        rounds_by_group = {}
        for category, cat_groups in groups_by_category.items():
            for group_name, players in cat_groups.items():
                if len(players) >= 2:
                    sorted_players = sorted(players, key=lambda p: (p.seed if p.seed else 999, p.display_name))
                    rounds = self._generate_fistf_rounds(sorted_players, group_name)
                    rounds_by_group[group_name] = {
                        'rounds': rounds,
                        'category': category,
                        'total_rounds': len(rounds),
                        'matches_per_round': len(rounds[0]) if rounds else 0,
                        'total_matches': sum(len(r) for r in rounds),
                        'group_letter': self._get_group_letter(group_name)
                    }
                    print(f"   📅 Girone {group_name} ({category}): {len(rounds)} turni, {len(rounds[0])} partite/turno, totale {rounds_by_group[group_name]['total_matches']} partite")
        
        # Step 3: Prepara le code
        group_queues = {}
        for group_name, group_data in rounds_by_group.items():
            queue = []
            for round_idx, round_matches in enumerate(group_data['rounds']):
                for match_idx, (p1, p2) in enumerate(round_matches):
                    queue.append({
                        'round': round_idx,
                        'match_in_round': match_idx,
                        'p1': p1,
                        'p2': p2,
                        'theoretical_round': round_idx
                    })
            group_queues[group_name] = {
                'queue': queue,
                'category': group_data['category'],
                'matches_per_round': group_data['matches_per_round'],
                'total_matches': group_data['total_matches'],
                'matches_played': 0,
                'group_letter': group_data['group_letter']
            }
        
        # Step 4: Imposta limiti per categoria
        category_limits = {}
        for category, fields in self.fields_per_category.items():
            if fields > 0:
                category_limits[category] = fields
                print(f"   🏟️ Categoria {category}: {fields} campi disponibili")
        
        # Step 5: Riassegnazione dinamica dei campi
        # Traccia partite rimaste per categoria
        remaining_matches_per_category = {
            cat: sum(g['total_matches'] for g in group_queues.values() if g['category'] == cat)
            for cat in category_limits.keys()
        }
        
        # Mappa campo -> categoria proprietaria originale
        field_owner = {}
        for category, fields in self.category_fields.items():
            for field in fields:
                field_owner[field] = category
        
        all_matches = []
        match_counter = 1
        global_round = 0
        
        total_matches_all = sum(g['total_matches'] for g in group_queues.values())
        total_fields = self.total_fields
        
        print(f"\n{'='*70}")
        print(f"📊 OTTIMIZZAZIONE CALENDARIO FISTF con RIASSEGNAZIONE DINAMICA")
        print(f"   Partite totali: {total_matches_all}")
        print(f"   Campi totali: {total_fields}")
        print(f"   Turni minimi teorici: {(total_matches_all + total_fields - 1) // total_fields}")
        print(f"\n   Campi iniziali per categoria:")
        for cat, limit in category_limits.items():
            cat_matches = remaining_matches_per_category.get(cat, 0)
            min_turns = (cat_matches + limit - 1) // limit
            print(f"      {cat}: {cat_matches} partite → {limit} campi → {min_turns} turni minimi")
        print(f"{'='*70}\n")
        
        # Statistiche riassegnazione
        reassignment_log = []
        
        while any(len(g['queue']) > 0 for g in group_queues.values()):
            round_time = f"{9 + global_round:02d}:00"
            round_matches = []
            busy_players = set()
            
            matches_per_category = defaultdict(int)
            matches_per_group = defaultdict(int)
            fields_used_in_round = 0
            
            # ========================================
            # FASE 1: CALCOLA CAMPI DISPONIBILI DINAMICAMENTE
            # ========================================
            
            # Campi disponibili per categoria (inizialmente quelli dedicati)
            available_fields_per_category = defaultdict(list)
            freed_fields = []
            
            # Prima, i campi delle categorie che hanno ancora partite rimangono loro
            for category in category_limits.keys():
                if remaining_matches_per_category.get(category, 0) > 0:
                    # La categoria ha ancora partite, i suoi campi sono suoi
                    for field in self.category_fields.get(category, []):
                        available_fields_per_category[category].append(field)
                else:
                    # La categoria ha finito, libera i suoi campi
                    for field in self.category_fields.get(category, []):
                        if field not in freed_fields:
                            freed_fields.append(field)
            
            # Riassegna i campi liberi alle categorie che hanno ancora partite
            if freed_fields:
                # Trova le categorie con più partite rimaste
                categories_with_matches = [
                    (cat, remaining_matches_per_category[cat])
                    for cat in category_limits.keys()
                    if remaining_matches_per_category.get(cat, 0) > 0
                ]
                categories_with_matches.sort(key=lambda x: x[1], reverse=True)
                
                # Distribuisci i campi liberi equamente
                if categories_with_matches:
                    reassign_msg = f"   🔄 Turno {global_round+1}: campi liberi {freed_fields} "
                    for i, field in enumerate(freed_fields):
                        target_cat = categories_with_matches[i % len(categories_with_matches)][0]
                        available_fields_per_category[target_cat].append(field)
                    reassign_msg += f"riassegnati a {[c[0] for c in categories_with_matches]}"
                    reassignment_log.append(reassign_msg)
                    print(reassign_msg)
            
            # ========================================
            # FASE 2: RACCOGLI PARTITE DISPONIBILI
            # ========================================
            
            all_available_matches = []
            
            for g_name, g_data in group_queues.items():
                category = g_data['category']
                available_fields = available_fields_per_category.get(category, [])
                max_fields = len(available_fields)
                
                already_scheduled = matches_per_category[category]
                
                if already_scheduled >= max_fields:
                    continue
                
                max_from_this_group = g_data['matches_per_round']
                already_from_group = matches_per_group[g_name]
                
                if already_from_group >= max_from_this_group:
                    continue
                
                available_slots = max_fields - already_scheduled
                remaining_slots_in_group = max_from_this_group - already_from_group
                
                queue_matches = []
                for i, match_data in enumerate(g_data['queue']):
                    p1_name = match_data['p1'].display_name
                    p2_name = match_data['p2'].display_name
                    
                    if p1_name in busy_players or p2_name in busy_players:
                        continue
                    
                    conflict = False
                    for existing in all_available_matches:
                        if existing['group'] == g_name:
                            if (p1_name == existing['p1_name'] or 
                                p1_name == existing['p2_name'] or
                                p2_name == existing['p1_name'] or 
                                p2_name == existing['p2_name']):
                                conflict = True
                                break
                    
                    if conflict:
                        continue
                    
                    queue_matches.append({
                        'match_data': match_data,
                        'p1_name': p1_name,
                        'p2_name': p2_name,
                        'theoretical_round': match_data['theoretical_round']
                    })
                
                queue_matches.sort(key=lambda x: x['theoretical_round'])
                
                for qm in queue_matches[:min(available_slots, remaining_slots_in_group)]:
                    all_available_matches.append({
                        'group': g_name,
                        'data': g_data,
                        'match': qm['match_data'],
                        'category': category,
                        'p1_name': qm['p1_name'],
                        'p2_name': qm['p2_name'],
                        'theoretical_round': qm['theoretical_round']
                    })
                    matches_per_group[g_name] += 1
            
            # Ordina per priorità
            all_available_matches.sort(key=lambda x: (x['theoretical_round'], -len(x['data']['queue'])))
            
            # ========================================
            # FASE 3: AGGIUNGI PARTITE
            # ========================================
            
            for available in all_available_matches:
                if fields_used_in_round >= self.total_fields:
                    break
                
                category = available['category']
                available_fields = available_fields_per_category.get(category, [])
                if matches_per_category[category] >= len(available_fields):
                    continue
                
                p1_name = available['p1_name']
                p2_name = available['p2_name']
                
                if p1_name in busy_players or p2_name in busy_players:
                    continue
                
                g_name = available['group']
                g_data = available['data']
                next_match = available['match']
                
                match = Match(
                    id=f"{g_name}-M{match_counter}",
                    category=category,
                    phase="Groups",
                    group=g_name,
                    player1=p1_name,
                    player2=p2_name,
                    match_number=match_counter,
                    scheduled_time=round_time,
                    status=MatchStatus.SCHEDULED
                )
                
                round_matches.append(match)
                match_counter += 1
                fields_used_in_round += 1
                matches_per_category[category] += 1
                
                # Rimuovi la partita dalla coda
                match_to_remove = next(
                    (m for m in g_data['queue'] 
                     if m['p1'] == next_match['p1'] and m['p2'] == next_match['p2']),
                    None
                )
                if match_to_remove:
                    g_data['queue'].remove(match_to_remove)
                    g_data['matches_played'] += 1
                    remaining_matches_per_category[category] -= 1
                
                busy_players.add(p1_name)
                busy_players.add(p2_name)
            
            # Forza partita se necessario
            if fields_used_in_round == 0 and any(len(g['queue']) > 0 for g in group_queues.values()):
                for g_name, g_data in group_queues.items():
                    if len(g_data['queue']) > 0:
                        next_match = g_data['queue'][0]
                        p1_name = next_match['p1'].display_name
                        p2_name = next_match['p2'].display_name
                        
                        match = Match(
                            id=f"{g_name}-M{match_counter}",
                            category=g_data['category'],
                            phase="Groups",
                            group=g_name,
                            player1=p1_name,
                            player2=p2_name,
                            match_number=match_counter,
                            scheduled_time=round_time,
                            status=MatchStatus.SCHEDULED
                        )
                        
                        round_matches.append(match)
                        match_counter += 1
                        fields_used_in_round += 1
                        matches_per_category[g_data['category']] += 1
                        g_data['queue'].pop(0)
                        g_data['matches_played'] += 1
                        remaining_matches_per_category[g_data['category']] -= 1
                        busy_players.add(p1_name)
                        busy_players.add(p2_name)
                        
                        print(f"⚠️ Forzata partita {match.id} - turno {global_round+1}")
                        break
            
            # Assegna arbitri e campi
            if round_matches:
                self._assign_fields_dynamic(round_matches, available_fields_per_category)
                self._assign_referees_to_round(round_matches, busy_players, all_players_by_name, groups_by_category)
                all_matches.extend(round_matches)
                
                utilization = (fields_used_in_round / total_fields) * 100
                print(f"✅ Turno {round_time} ({global_round+1:2d}): {fields_used_in_round:2d}/{total_fields} campi usati ({utilization:5.1f}%)", end="")
                for cat, count in sorted(matches_per_category.items()):
                    max_cat = len(available_fields_per_category.get(cat, []))
                    print(f" | {cat}: {count}/{max_cat}", end="")
                print()
            
            global_round += 1
            
            if global_round > 200:
                print("❌ Troppi turni, possibile loop")
                break
        
        # Statistiche finali
        total_played = sum(g['matches_played'] for g in group_queues.values())
        actual_turns = global_round
        theoretical_min = (total_played + total_fields - 1) // total_fields
        efficiency = (theoretical_min / actual_turns * 100) if actual_turns > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"📊 RIEPILOGO FINALE OTTIMIZZAZIONE")
        print(f"   Partite totali: {total_played}")
        print(f"   Turni effettivi: {actual_turns}")
        print(f"   Turni teorici minimi: {theoretical_min}")
        print(f"   Efficienza: {efficiency:.1f}%")
        
        if reassignment_log:
            print(f"\n   Riassegnazioni campi effettuate: {len(reassignment_log)}")
        
        print(f"\n   Efficienza per categoria:")
        for category, limit in category_limits.items():
            cat_matches = sum(g['matches_played'] for g in group_queues.values() if g['category'] == category)
            cat_min_turns = (cat_matches + limit - 1) // limit
            cat_actual_turns = actual_turns
            cat_efficiency = (cat_min_turns / cat_actual_turns * 100) if cat_actual_turns > 0 else 0
            print(f"      {category}: {cat_matches} partite, {limit} campi iniziali → {cat_min_turns} turni minimi, eff. {cat_efficiency:.1f}%")
        
        print(f"{'='*70}")
        
        return all_matches
    
    def _assign_fields_dynamic(self, round_matches: List['Match'], 
                               available_fields_per_category: Dict[str, List[int]]):
        """
        Assegna i campi dinamicamente in base alla disponibilità.
        Ogni partita viene assegnata a un campo disponibile della sua categoria.
        """
        # Raggruppa per categoria
        matches_by_category = defaultdict(list)
        for match in round_matches:
            matches_by_category[match.category].append(match)
        
        used_fields = set()
        
        for category, matches in matches_by_category.items():
            available_fields = available_fields_per_category.get(category, [])
            available_in_category = [f for f in available_fields if f not in used_fields]
            
            for i, match in enumerate(matches):
                if i < len(available_in_category):
                    match.field = available_in_category[i]
                    used_fields.add(available_in_category[i])
                else:
                    # Cerca un campo libero qualsiasi (fallback)
                    field = 1
                    while field in used_fields:
                        field += 1
                    match.field = field
                    used_fields.add(field)
    
    def _assign_referees_to_round(self, round_matches: List['Match'], 
                                  busy_players: Set[str],
                                  all_players_by_name: Dict[str, 'Player'],
                                  groups_by_category: Dict[str, Dict[str, List['Player']]]):
        """Assegna gli arbitri alle partite di un turno seguendo le regole FISTF."""
        available_referees = []
        
        for category, cat_groups in groups_by_category.items():
            for group_name, players in cat_groups.items():
                for player in players:
                    if player.display_name not in busy_players:
                        available_referees.append({
                            'name': player.display_name,
                            'player': player,
                            'category': category,
                            'group': group_name
                        })
        
        if not available_referees:
            return
        
        for match in round_matches:
            p1 = all_players_by_name.get(match.player1)
            p2 = all_players_by_name.get(match.player2)
            
            if not p1 or not p2:
                continue
            
            suitable_referees = []
            
            for ref in available_referees:
                if ref['player'].club == p1.club or ref['player'].club == p2.club:
                    continue
                
                if p1.country != p2.country:
                    if ref['player'].country == p1.country or ref['player'].country == p2.country:
                        continue
                
                if ref['group'] == match.group:
                    continue
                
                suitable_referees.append(ref)
            
            if suitable_referees:
                chosen = random.choice(suitable_referees)
                match.referee = chosen['name']
                available_referees = [r for r in available_referees if r['name'] != chosen['name']]
            else:
                if available_referees:
                    chosen = available_referees[0]
                    match.referee = chosen['name']
                    print(f"⚠️ Nessun arbitro ideale per {match.id}, uso {chosen['name']}")
                    available_referees = available_referees[1:]


def generate_tournament_schedule(groups: Dict[str, List['Player']], 
                                total_fields: int = 10,
                                fields_per_category: Optional[Dict[str, int]] = None) -> List['Match']:
    """Genera calendario completo per tutte le categorie in contemporanea."""
    if fields_per_category is None:
        fields_per_category = {
            "Open": 6,
            "Veterans": 4,
            "Women": 2,
            "U20": 2,
            "U16": 2,
            "U12": 2,
            "Eccellenza": 6,
            "Promozione": 4,
            "MOICAT": 2
        }
    
    scheduler = TournamentScheduler(total_fields, fields_per_category)
    return scheduler.generate_schedule(groups)


def print_schedule_summary(matches: List['Match']):
    """Stampa un riassunto del calendario per verifica"""
    from collections import Counter
    
    times = Counter()
    categories = Counter()
    referees_by_time = defaultdict(set)
    
    for m in matches:
        times[m.scheduled_time] += 1
        categories[m.category] += 1
        if m.referee:
            referees_by_time[m.scheduled_time].add(m.referee)
    
    print("\n=== RIASSUNTO CALENDARIO FISTF ===")
    print(f"Totale partite: {len(matches)}")
    print("\nPartite per orario:")
    for time in sorted(times.keys()):
        print(f"  {time}: {times[time]} partite, arbitri: {len(referees_by_time[time])}")
    
    print("\nPartite per categoria:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")