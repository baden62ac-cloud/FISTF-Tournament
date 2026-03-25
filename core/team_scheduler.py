"""
Generazione calendario partite per tornei a squadre secondo regole FISTF.
Gestisce partite con 4 incontri individuali per ogni match.
Ogni incontro occupa 4 campi (uno per ogni partita individuale).

Implementa:
- Tabella ufficiale FISTF 2.3.2 per ordine partite (adattata per squadre)
- Regola 2.3.3 per conflitti club (squadre stesso club in gironi diversi)
- Ottimizzazione avanzata: usa TUTTI i campi disponibili in ogni turno
- RIASSEGNAZIONE DINAMICA DEI CAMPI: quando una categoria finisce, i suoi blocchi di 4 campi
  vengono riassegnati ad altre categorie che hanno ancora partite da giocare
- Anticipazione partite: gioca partite dei turni successivi quando ci sono campi liberi
- Vincoli: una squadra non può giocare più di una partita nello stesso turno
- Massimo matches_per_round per girone per turno
"""
import random
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import defaultdict, deque

# Tabella ufficiale FISTF 2.3.2 - Ordine delle partite (adattata per squadre)
FISTF_TEAM_MATCH_ORDER = {
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
    ]
}


class TeamTournamentScheduler:
    """
    Scheduler per tornei a squadre.
    Ogni incontro occupa 4 campi (uno per ogni partita individuale).
    """
    
    # Mappa prefissi categoria
    CATEGORY_PREFIX = {
        "Team Open": "TO",
        "Team Veterans": "TV",
        "Team Women": "TW",
        "Team U20": "TU20",
        "Team U16": "TU16",
        "Team U12": "TU12",
        "Team Eccellenza": "TE",
        "Team Promozione": "TP",
        "Team MOICAT": "TM"
    }
    
    def __init__(self, total_fields: int, fields_per_category: Dict[str, int]):
        self.total_fields = total_fields
        self.fields_per_category = fields_per_category
        
        # Calcola il numero MASSIMO di incontri contemporanei
        # Ogni incontro occupa 4 campi
        self.max_matches_per_round = total_fields // 4
        print(f"   🏟️ Campi totali: {total_fields}")
        print(f"   📊 Massimo incontri per turno: {self.max_matches_per_round}")
        
        # Per ogni categoria, calcola il massimo incontri per turno
        self.max_matches_per_category = {}
        for category, fields in fields_per_category.items():
            self.max_matches_per_category[category] = fields // 4
            print(f"   🏟️ Categoria {category}: {fields} campi → {fields//4} incontri per turno")
        
        # Calcola i blocchi di campi per categoria
        self.category_blocks = self._calculate_category_blocks()
        
        # Contatori per ID univoci
        self.match_counters = defaultdict(lambda: 1)
    
    def _calculate_category_blocks(self) -> Dict[str, List[List[int]]]:
        """
        Calcola i blocchi di campi per categoria.
        Ogni blocco è un insieme di 4 campi consecutivi.
        Es: 8 campi Open → [[1,2,3,4], [5,6,7,8]]
        """
        result = {}
        current_field = 1
        sorted_categories = sorted(self.fields_per_category.keys())
        
        for category in sorted_categories:
            num_fields = self.fields_per_category[category]
            if num_fields >= 4:
                # Dividi in blocchi da 4 campi
                blocks = []
                for i in range(0, num_fields, 4):
                    block = list(range(current_field + i, current_field + min(i+4, num_fields)))
                    if len(block) == 4:  # Solo blocchi completi
                        blocks.append(block)
                result[category] = blocks
                print(f"   🏟️ Categoria {category}: blocchi {blocks}")
            else:
                print(f"⚠️ Categoria {category} ha solo {num_fields} campi (<4), non può ospitare incontri squadre!")
                result[category] = []
            
            current_field += num_fields
        
        return result
    
    def _get_category_prefix(self, category: str) -> str:
        """Restituisce il prefisso per una categoria."""
        return self.CATEGORY_PREFIX.get(category, "TX")
    
    def _get_category_from_group(self, group_name: str) -> str:
        """Estrae categoria dal nome girone squadre."""
        if group_name.startswith('TO-'):
            return 'Team Open'
        elif group_name.startswith('TV-'):
            return 'Team Veterans'
        elif group_name.startswith('TW-'):
            return 'Team Women'
        elif group_name.startswith('TU20-'):
            return 'Team U20'
        elif group_name.startswith('TU16-'):
            return 'Team U16'
        elif group_name.startswith('TU12-'):
            return 'Team U12'
        elif group_name.startswith('TE-'):
            return 'Team Eccellenza'
        elif group_name.startswith('TP-'):
            return 'Team Promozione'
        elif group_name.startswith('TM-'):
            return 'Team MOICAT'
        else:
            return 'Team Open'
    
    def _get_group_letter(self, group_name: str) -> str:
        """Estrae la lettera del girone dal nome completo (es. 'TO-A' -> 'A')"""
        if '-' in group_name:
            return group_name.split('-')[-1]
        return group_name
    
    def _reorder_for_clash(self, teams: List['Team'], group_name: str) -> List['Team']:
        """
        Riordina le squadre secondo regola FISTF 2.3.3 (adattata per squadre):
        Se ci sono due squadre dello stesso club, devono incontrarsi al primo turno.
        """
        club_counts = defaultdict(list)
        for i, team in enumerate(teams):
            if team.club:
                club_counts[team.club].append((i, team))
        
        conflicting_club = None
        conflicting_teams = []
        
        for club, members in club_counts.items():
            if len(members) >= 2:
                conflicting_club = club
                conflicting_teams = [t for _, t in members]
                break
        
        if not conflicting_teams:
            return teams
        
        print(f"   ⚠️ Conflitto club '{conflicting_club}' nel girone {group_name}: {[t.display_name for t in conflicting_teams]}")
        print(f"   🔄 Applico regola FISTF 2.3.3: le due squadre si affronteranno al primo turno")
        
        conflicting_two = sorted(conflicting_teams, key=lambda t: t.seed if t.seed else 999)[:2]
        other_conflicting = [t for t in conflicting_teams if t not in conflicting_two]
        
        result = conflicting_two.copy()
        remaining = other_conflicting + [t for t in teams if t not in conflicting_teams]
        remaining.sort(key=lambda t: t.seed if t.seed else 999)
        result.extend(remaining)
        
        return result
    
    def _generate_fistf_rounds(self, teams: List['Team'], group_name: str = "") -> List[List[Tuple]]:
        """
        Genera i turni secondo la tabella ufficiale FISTF (adattata per squadre).
        Applica la regola 2.3.3 per conflitti di club.
        """
        reordered_teams = self._reorder_for_clash(teams, group_name)
        n = len(reordered_teams)
        
        if n not in FISTF_TEAM_MATCH_ORDER:
            print(f"⚠️ Dimensione girone {n} non supportata dalla tabella FISTF, uso round-robin classico")
            return self._generate_round_robin_fallback(reordered_teams)
        
        fistf_rounds = FISTF_TEAM_MATCH_ORDER[n]
        rounds = []
        
        for round_num, round_matches in enumerate(fistf_rounds):
            matches = []
            for a, b in round_matches:
                team_a = reordered_teams[a-1] if a <= len(reordered_teams) else None
                team_b = reordered_teams[b-1] if b <= len(reordered_teams) else None
                
                if team_a and team_b:
                    matches.append((team_a, team_b))
            
            rounds.append(matches)
        
        return rounds
    
    def _generate_round_robin_fallback(self, teams: List['Team']) -> List[List[Tuple]]:
        """Genera turni all'italiana classica (fallback per dimensioni non supportate)."""
        n = len(teams)
        
        if n % 2 == 1:
            teams_list = teams + [None]
            n += 1
        else:
            teams_list = teams.copy()
        
        rounds = []
        
        for round_num in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                t1 = teams_list[i]
                t2 = teams_list[n - 1 - i]
                
                if t1 is not None and t2 is not None:
                    round_matches.append((t1, t2))
            
            rounds.append(round_matches)
            teams_list = [teams_list[0]] + [teams_list[-1]] + teams_list[1:-1]
        
        return rounds
    
    def generate_schedule(self, team_groups: Dict[str, List['Team']]) -> List['TeamMatch']:
        """
        Genera calendario OTTIMIZZATO per torneo a squadre.
        Ogni incontro occupa 4 campi.
        """
        from models.team_match import TeamMatch, IndividualMatchResult
        from models.match import MatchStatus
        
        # Step 1: Raggruppa gironi per categoria
        groups_by_category = defaultdict(dict)
        all_teams_by_id = {}
        
        for group_name, teams in team_groups.items():
            category = self._get_category_from_group(group_name)
            groups_by_category[category][group_name] = teams
            for team in teams:
                all_teams_by_id[team.id] = team
        
        # Step 2: Genera turni per ogni girone (FISTF con regola conflitti)
        rounds_by_group = {}
        for category, cat_groups in groups_by_category.items():
            for group_name, teams in cat_groups.items():
                if len(teams) >= 2:
                    sorted_teams = sorted(teams, key=lambda t: (t.seed if t.seed else 999, t.display_name))
                    rounds = self._generate_fistf_rounds(sorted_teams, group_name)
                    rounds_by_group[group_name] = {
                        'rounds': rounds,
                        'category': category,
                        'total_rounds': len(rounds),
                        'matches_per_round': len(rounds[0]) if rounds else 0,
                        'total_matches': sum(len(r) for r in rounds),
                        'group_letter': self._get_group_letter(group_name)
                    }
                    print(f"   📅 Girone {group_name} ({category}): {len(rounds)} turni, {len(rounds[0])} incontri/turno, totale {rounds_by_group[group_name]['total_matches']} incontri")
        
        # Step 3: Prepara code di incontri
        group_queues = {}
        for group_name, group_data in rounds_by_group.items():
            queue = []
            for round_idx, round_matches in enumerate(group_data['rounds']):
                for match_idx, (t1, t2) in enumerate(round_matches):
                    queue.append({
                        'theoretical_round': round_idx,
                        'team1': t1,
                        'team2': t2,
                        'round': round_idx,
                        'match_in_round': match_idx
                    })
            group_queues[group_name] = {
                'queue': queue,
                'category': group_data['category'],
                'matches_per_round': group_data['matches_per_round'],
                'total_matches': group_data['total_matches'],
                'matches_played': 0,
                'group_letter': group_data['group_letter']
            }
        
        # Step 4: Imposta limiti per categoria (in incontri per turno)
        category_limits = {}
        for category, max_matches in self.max_matches_per_category.items():
            if max_matches > 0:
                category_limits[category] = max_matches
                print(f"   🏟️ Categoria {category}: max {max_matches} incontri per turno")
        
        # Step 5: Traccia partite rimaste per categoria
        remaining_matches_per_category = {
            cat: sum(g['total_matches'] for g in group_queues.values() if g['category'] == cat)
            for cat in category_limits.keys()
        }
        
        # Step 6: Mappa blocco -> categoria proprietaria originale
        block_owner = {}
        for category, blocks in self.category_blocks.items():
            for block in blocks:
                block_owner[tuple(block)] = category
        
        all_matches = []
        match_counter = 1
        global_round = 0
        
        total_matches_all = sum(g['total_matches'] for g in group_queues.values())
        total_incontri_max = self.max_matches_per_round
        
        print(f"\n{'='*70}")
        print(f"📊 OTTIMIZZAZIONE CALENDARIO SQUADRE FISTF")
        print(f"   Incontri totali: {total_matches_all}")
        print(f"   Campi totali: {self.total_fields}")
        print(f"   Massimo incontri per turno: {total_incontri_max}")
        print(f"   Turni minimi teorici: {(total_matches_all + total_incontri_max - 1) // total_incontri_max}")
        print(f"\n   Incontri per categoria per turno:")
        for cat, limit in category_limits.items():
            cat_matches = remaining_matches_per_category.get(cat, 0)
            min_turns = (cat_matches + limit - 1) // limit
            print(f"      {cat}: {cat_matches} incontri → {limit} max/turno → {min_turns} turni minimi")
        print(f"{'='*70}\n")
        
        # Statistiche riassegnazione
        reassignment_log = []
        
        while any(len(g['queue']) > 0 for g in group_queues.values()):
            round_time = f"{9 + global_round:02d}:00"
            round_matches = []
            busy_teams = set()
            
            matches_per_category = defaultdict(int)
            matches_per_group = defaultdict(int)
            fields_used_in_round = 0  # Numero di incontri in questo turno
            
            # ========================================
            # FASE 1: CALCOLA BLOCCHI DISPONIBILI DINAMICAMENTE
            # ========================================
            
            # Blocchi disponibili per categoria
            available_blocks_per_category = defaultdict(list)
            freed_blocks = []
            
            # Prima, i blocchi delle categorie che hanno ancora incontri rimangono loro
            for category in category_limits.keys():
                if remaining_matches_per_category.get(category, 0) > 0:
                    for block in self.category_blocks.get(category, []):
                        available_blocks_per_category[category].append(block)
                else:
                    for block in self.category_blocks.get(category, []):
                        if block not in freed_blocks:
                            freed_blocks.append(block)
            
            # Riassegna i blocchi liberi alle categorie che hanno ancora incontri
            if freed_blocks:
                categories_with_matches = [
                    (cat, remaining_matches_per_category[cat])
                    for cat in category_limits.keys()
                    if remaining_matches_per_category.get(cat, 0) > 0
                ]
                categories_with_matches.sort(key=lambda x: x[1], reverse=True)
                
                if categories_with_matches:
                    reassign_msg = f"   🔄 Turno {global_round+1}: blocchi liberi {[list(b) for b in freed_blocks]} "
                    for i, block in enumerate(freed_blocks):
                        target_cat = categories_with_matches[i % len(categories_with_matches)][0]
                        available_blocks_per_category[target_cat].append(block)
                    reassign_msg += f"riassegnati a {[c[0] for c in categories_with_matches]}"
                    reassignment_log.append(reassign_msg)
                    print(reassign_msg)
            
            # ========================================
            # FASE 2: RACCOGLI INCONTRI DISPONIBILI
            # ========================================
            
            all_available_matches = []
            
            for g_name, g_data in group_queues.items():
                category = g_data['category']
                available_blocks = available_blocks_per_category.get(category, [])
                max_incontri = len(available_blocks)
                
                already_scheduled = matches_per_category[category]
                
                if already_scheduled >= max_incontri:
                    continue
                
                max_from_this_group = g_data['matches_per_round']
                already_from_group = matches_per_group[g_name]
                
                if already_from_group >= max_from_this_group:
                    continue
                
                available_slots = max_incontri - already_scheduled
                remaining_slots_in_group = max_from_this_group - already_from_group
                
                queue_matches = []
                for i, match_data in enumerate(g_data['queue']):
                    t1_id = match_data['team1'].id
                    t2_id = match_data['team2'].id
                    
                    if t1_id in busy_teams or t2_id in busy_teams:
                        continue
                    
                    conflict = False
                    for existing in all_available_matches:
                        if existing['group'] == g_name:
                            if (t1_id == existing['team1_id'] or 
                                t1_id == existing['team2_id'] or
                                t2_id == existing['team1_id'] or 
                                t2_id == existing['team2_id']):
                                conflict = True
                                break
                    
                    if conflict:
                        continue
                    
                    queue_matches.append({
                        'index': i,
                        'match_data': match_data,
                        'team1': match_data['team1'],
                        'team2': match_data['team2'],
                        'team1_id': t1_id,
                        'team2_id': t2_id,
                        'theoretical_round': match_data['theoretical_round']
                    })
                
                queue_matches.sort(key=lambda x: x['theoretical_round'])
                
                for qm in queue_matches[:min(available_slots, remaining_slots_in_group)]:
                    all_available_matches.append({
                        'group': g_name,
                        'data': g_data,
                        'match': qm['match_data'],
                        'match_index': qm['index'],
                        'category': category,
                        'team1': qm['team1'],
                        'team2': qm['team2'],
                        'team1_id': qm['team1_id'],
                        'team2_id': qm['team2_id'],
                        'theoretical_round': qm['theoretical_round']
                    })
                    matches_per_group[g_name] += 1
            
            # Ordina per priorità
            all_available_matches.sort(key=lambda x: (x['theoretical_round'], -len(x['data']['queue'])))
            
            # ========================================
            # FASE 3: AGGIUNGI INCONTRI
            # ========================================
            
            # Traccia quali blocchi sono già stati usati in questo turno
            used_blocks = set()
            
            for available in all_available_matches:
                if fields_used_in_round >= self.max_matches_per_round:
                    break
                
                category = available['category']
                available_blocks = available_blocks_per_category.get(category, [])
                
                if matches_per_category[category] >= len(available_blocks):
                    continue
                
                team1_id = available['team1_id']
                team2_id = available['team2_id']
                
                if team1_id in busy_teams or team2_id in busy_teams:
                    continue
                
                g_name = available['group']
                g_data = available['data']
                next_match = available['match']
                
                # Trova un blocco disponibile per questa categoria
                assigned_block = None
                for block in available_blocks:
                    if tuple(block) not in used_blocks:
                        assigned_block = block
                        break
                
                if not assigned_block:
                    continue
                
                used_blocks.add(tuple(assigned_block))
                
                # Crea ID univoco per categoria
                cat_prefix = self._get_category_prefix(category)
                group_letter = self._get_group_letter(g_name)
                match_number = self.match_counters[cat_prefix]
                self.match_counters[cat_prefix] += 1
                
                match_id = f"{cat_prefix}_{group_letter}_{match_number}"
                
                # Crea incontro a squadre con 4 partite individuali
                individual_matches = []
                for i in range(4):
                    field = assigned_block[i] if i < len(assigned_block) else 1
                    individual_matches.append(
                        IndividualMatchResult(
                            player1="", player2="", 
                            table=field, 
                            status=None
                        )
                    )
                
                team_match = TeamMatch(
                    id=match_id,
                    category=category,
                    phase="Groups",
                    group=g_name,
                    team1=team1_id,
                    team2=team2_id,
                    player1=next_match['team1'].display_name,
                    player2=next_match['team2'].display_name,
                    match_number=match_number,
                    scheduled_time=round_time,
                    status=None,
                    individual_matches=individual_matches
                )
                
                round_matches.append(team_match)
                match_counter += 1
                fields_used_in_round += 1
                matches_per_category[category] += 1
                
                # Rimuovi incontro dalla coda
                match_to_remove = next(
                    (m for m in g_data['queue'] 
                     if m['team1'].id == next_match['team1'].id and m['team2'].id == next_match['team2'].id),
                    None
                )
                if match_to_remove:
                    g_data['queue'].remove(match_to_remove)
                    g_data['matches_played'] += 1
                    remaining_matches_per_category[category] -= 1
                
                busy_teams.add(team1_id)
                busy_teams.add(team2_id)
                
                print(f"   📍 Turno {global_round+1}: {match_id} - {next_match['team1'].display_name} vs {next_match['team2'].display_name} ({category}) [campi {assigned_block}]")
            
            # Forza incontro se necessario
            if fields_used_in_round == 0 and any(len(g['queue']) > 0 for g in group_queues.values()):
                for g_name, g_data in group_queues.items():
                    if len(g_data['queue']) > 0:
                        next_match = g_data['queue'][0]
                        category = g_data['category']
                        
                        # Cerca un blocco disponibile
                        available_blocks = available_blocks_per_category.get(category, [])
                        assigned_block = None
                        for block in available_blocks:
                            if tuple(block) not in used_blocks:
                                assigned_block = block
                                break
                        
                        if not assigned_block and available_blocks:
                            assigned_block = available_blocks[0]
                        
                        if not assigned_block:
                            # Crea blocco fittizio
                            assigned_block = [1, 2, 3, 4]
                        
                        used_blocks.add(tuple(assigned_block))
                        
                        cat_prefix = self._get_category_prefix(category)
                        group_letter = self._get_group_letter(g_name)
                        match_number = self.match_counters[cat_prefix]
                        self.match_counters[cat_prefix] += 1
                        
                        match_id = f"{cat_prefix}_{group_letter}_{match_number}"
                        
                        individual_matches = [
                            IndividualMatchResult(player1="", player2="", table=assigned_block[i] if i < len(assigned_block) else 1, status=None)
                            for i in range(4)
                        ]
                        
                        team_match = TeamMatch(
                            id=match_id,
                            category=category,
                            phase="Groups",
                            group=g_name,
                            team1=next_match['team1'].id,
                            team2=next_match['team2'].id,
                            player1=next_match['team1'].display_name,
                            player2=next_match['team2'].display_name,
                            match_number=match_number,
                            scheduled_time=round_time,
                            status=None,
                            individual_matches=individual_matches
                        )
                        
                        round_matches.append(team_match)
                        match_counter += 1
                        fields_used_in_round += 1
                        matches_per_category[category] += 1
                        g_data['queue'].pop(0)
                        g_data['matches_played'] += 1
                        remaining_matches_per_category[category] -= 1
                        busy_teams.add(next_match['team1'].id)
                        busy_teams.add(next_match['team2'].id)
                        
                        print(f"⚠️ Forzata partita {team_match.id} - turno {global_round+1} [campi {assigned_block}]")
                        break
            
            if round_matches:
                all_matches.extend(round_matches)
                
                utilization = (fields_used_in_round / self.max_matches_per_round) * 100
                print(f"✅ Turno {round_time} ({global_round+1:2d}): {fields_used_in_round:2d}/{self.max_matches_per_round} incontri usati ({utilization:5.1f}%)", end="")
                for cat, count in sorted(matches_per_category.items()):
                    max_cat = len(available_blocks_per_category.get(cat, []))
                    print(f" | {cat}: {count}/{max_cat}", end="")
                print()
            
            global_round += 1
            
            if global_round > 200:
                print("❌ Troppi turni, possibile loop")
                break
        
        # Statistiche finali
        total_played = sum(g['matches_played'] for g in group_queues.values())
        actual_turns = global_round
        theoretical_min = (total_played + self.max_matches_per_round - 1) // self.max_matches_per_round
        efficiency = (theoretical_min / actual_turns * 100) if actual_turns > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"📊 RIEPILOGO FINALE OTTIMIZZAZIONE SQUADRE")
        print(f"   Incontri totali: {total_played}")
        print(f"   Turni effettivi: {actual_turns}")
        print(f"   Turni teorici minimi: {theoretical_min}")
        print(f"   Efficienza: {efficiency:.1f}%")
        
        if reassignment_log:
            print(f"\n   Riassegnazioni blocchi effettuate: {len(reassignment_log)}")
        
        print(f"\n   Efficienza per categoria:")
        for category, limit in category_limits.items():
            cat_matches = sum(g['matches_played'] for g in group_queues.values() if g['category'] == category)
            cat_min_turns = (cat_matches + limit - 1) // limit
            cat_actual_turns = actual_turns
            cat_efficiency = (cat_min_turns / cat_actual_turns * 100) if cat_actual_turns > 0 else 0
            print(f"      {category}: {cat_matches} incontri, {limit} max/turno → {cat_min_turns} turni minimi, eff. {cat_efficiency:.1f}%")
        
        print(f"{'='*70}")
        
        return all_matches


def generate_team_tournament_schedule(
    team_groups: Dict[str, List['Team']], 
    total_fields: int = 10,
    fields_per_category: Optional[Dict[str, int]] = None
) -> List['TeamMatch']:
    """
    Genera calendario completo per torneo a squadre.
    
    Args:
        team_groups: Dizionario {nome_girone: lista_squadre}
        total_fields: Numero totale di campi disponibili
        fields_per_category: Assegnazione campi per categoria (deve essere multiplo di 4)
    
    Returns:
        Lista di incontri a squadre
    """
    if fields_per_category is None:
        fields_per_category = {
            "Team Open": 8,
            "Team Veterans": 4,
            "Team Women": 4,
            "Team U20": 4,
            "Team U16": 4,
            "Team U12": 4,
            "Team Eccellenza": 8,
            "Team Promozione": 4,
            "Team MOICAT": 4
        }
    
    scheduler = TeamTournamentScheduler(total_fields, fields_per_category)
    return scheduler.generate_schedule(team_groups)


def print_team_schedule_summary(matches: List['TeamMatch']):
    """Stampa un riassunto del calendario squadre per verifica"""
    from collections import Counter
    
    times = Counter()
    categories = Counter()
    
    for m in matches:
        times[m.scheduled_time] += 1
        categories[m.category] += 1
    
    print("\n=== RIASSUNTO CALENDARIO SQUADRE FISTF ===")
    print(f"Totale incontri: {len(matches)}")
    print("\nIncontri per orario:")
    for time in sorted(times.keys()):
        print(f"  {time}: {times[time]} incontri")
    
    print("\nIncontri per categoria:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")