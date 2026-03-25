"""
Regole ufficiali FISTF (dal Tournament Organisers' Handbook 2025-26).
Aggiornato con supporto per competizioni a squadre.
"""
from enum import Enum
from typing import Dict, List, Optional, Any

# ========================================
# ENUM PER CATEGORIE E TIPI COMPETIZIONE
# ========================================

class Category(str, Enum):
    """Categorie FISTF e regionali (individuali e squadre)."""
    
    # Categorie FISTF individuali
    OPEN = "Open"
    VETERANS = "Veterans"  # Over 40
    WOMEN = "Women"
    U20 = "U20"  # Under 20
    U16 = "U16"  # Under 16
    U12 = "U12"  # Under 12
    
    # Categorie regionali individuali
    ECCELLENZA = "Eccellenza"
    PROMOZIONE = "Promozione"
    MOICAT = "MOICAT"
    
    # Categorie FISTF a squadre
    TEAM_OPEN = "Team Open"
    TEAM_VETERANS = "Team Veterans"
    TEAM_WOMEN = "Team Women"
    TEAM_U20 = "Team U20"
    TEAM_U16 = "Team U16"
    TEAM_U12 = "Team U12"
    
    # Categorie regionali a squadre
    TEAM_ECCELLENZA = "Team Eccellenza"
    TEAM_PROMOZIONE = "Team Promozione"
    TEAM_MOICAT = "Team MOICAT"


class CompetitionType(str, Enum):
    """Tipo di competizione."""
    INDIVIDUAL = "individual"
    TEAM = "team"


# ========================================
# CONFIGURAZIONE REGOLE PER CATEGORIA
# ========================================

# Mappa delle categorie individuali alle corrispondenti categorie squadre
INDIVIDUAL_TO_TEAM_MAP = {
    Category.OPEN: Category.TEAM_OPEN,
    Category.VETERANS: Category.TEAM_VETERANS,
    Category.WOMEN: Category.TEAM_WOMEN,
    Category.U20: Category.TEAM_U20,
    Category.U16: Category.TEAM_U16,
    Category.U12: Category.TEAM_U12,
    Category.ECCELLENZA: Category.TEAM_ECCELLENZA,
    Category.PROMOZIONE: Category.TEAM_PROMOZIONE,
    Category.MOICAT: Category.TEAM_MOICAT,
}

# Mappa delle categorie squadre alle corrispondenti individuali
TEAM_TO_INDIVIDUAL_MAP = {v: k for k, v in INDIVIDUAL_TO_TEAM_MAP.items()}


def is_team_category(category: Category) -> bool:
    """Verifica se una categoria è di tipo squadre."""
    return category.value.startswith("Team ")


def get_individual_category(team_category: Category) -> Optional[Category]:
    """Restituisce la categoria individuale corrispondente."""
    return TEAM_TO_INDIVIDUAL_MAP.get(team_category)


def get_team_category(individual_category: Category) -> Optional[Category]:
    """Restituisce la categoria squadre corrispondente."""
    return INDIVIDUAL_TO_TEAM_MAP.get(individual_category)


# ========================================
# REGOLE BASE PER TUTTE LE CATEGORIE
# ========================================

# Punteggi (FISTF 2.1.2.a e 2.2.2.a)
POINTS = {
    "win": 3,
    "draw": 1,
    "loss": 0
}

# Limiti gironi (FISTF 2.3.1)
GROUP_RULES = {
    "min_players_per_group": 3,
    "max_players_per_group": 10,
    "prefer_group_size": 4,  # Gironi da 4 preferiti
    "allow_groups_of_3": True,  # Consentiti solo all'inizio
    "allow_groups_of_5": True,  # Consentiti solo alla fine
}

# Regole per il sorteggio (FISTF 1.1.2.7.d - NUOVE 2025-26)
DRAW_RULES = {
    "use_seed_pots": True,
    "mandatory_second_pot": True,  # Secondo piatto obbligatorio (nuovo 2025-26)
    "separate_club_members": True,
    "separate_country_members": True,
}

# ========================================
# REGOLE PER CATEGORIA (INDIVIDUALI)
# ========================================

INDIVIDUAL_CATEGORY_RULES = {
    # Categorie FISTF
    Category.OPEN: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": False,  # No limite 5-0
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {  # Quanti si qualificano in base alla dimensione
            3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4
        },
    },
    Category.VETERANS: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": False,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.WOMEN: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": True,  # Applica limite 5-0
        "cap_margin": 5,  # Massimo 5 gol di scarto in classifica
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.U20: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": True,
        "cap_margin": 5,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.U16: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": True,
        "cap_margin": 5,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.U12: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": True,
        "cap_margin": 5,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    
    # Categorie regionali (stesse regole di OPEN)
    Category.ECCELLENZA: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": False,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.PROMOZIONE: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": False,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.MOICAT: {
        "competition_type": CompetitionType.INDIVIDUAL,
        "apply_cap": False,
        "max_players_per_group": 10,
        "min_players_per_group": 3,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
}


# ========================================
# REGOLE PER CATEGORIA (SQUADRE)
# ========================================

TEAM_CATEGORY_RULES = {
    Category.TEAM_OPEN: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": False,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},  # Regola 2.2.1.a
        "players_per_match": 4,  # 4 giocatori per partita
        "max_foreigners_per_match": 2,  # Regola 2.2.1.d (max 2 stranieri)
        "allow_substitutions": True,  # Sostituzioni a metà tempo
        "max_substitutions": 2,  # Max 2 sostituzioni (regola 2.2.4)
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_VETERANS: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": False,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_WOMEN: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": True,  # Anche le squadre femminili hanno limite 5-0?
        "cap_margin": 5,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_U20: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": True,
        "cap_margin": 5,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_U16: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": True,
        "cap_margin": 5,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_U12: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": True,
        "cap_margin": 5,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    
    # Categorie regionali a squadre
    Category.TEAM_ECCELLENZA: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": False,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_PROMOZIONE: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": False,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
    Category.TEAM_MOICAT: {
        "competition_type": CompetitionType.TEAM,
        "apply_cap": False,
        "max_teams_per_group": 10,
        "min_teams_per_group": 3,
        "players_per_team": {"min": 3, "max": 8},
        "players_per_match": 4,
        "max_foreigners_per_match": 2,
        "allow_substitutions": True,
        "max_substitutions": 2,
        "qualifiers_per_group": {3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4, 10: 4},
    },
}

# Unisco tutte le regole
CATEGORY_RULES = {**INDIVIDUAL_CATEGORY_RULES, **TEAM_CATEGORY_RULES}


# ========================================
# CRITERI DI CLASSIFICA
# ========================================

# Criteri di classificazione INDIVIDUALI in ordine (FISTF 2.1.2.b)
INDIVIDUAL_STANDINGS_CRITERIA = [
    "points",                          # 1. Punti
    "head_to_head_points",             # 2. Punti scontri diretti
    "head_to_head_goal_difference",    # 3. Differenza reti scontri diretti
    "head_to_head_goals_scored",       # 4. Gol segnati scontri diretti
    "goal_difference",                  # 5. Differenza reti totale
    "goals_scored",                      # 6. Gol segnati totali
    "shootout"                           # 7. Shoot-out (se necessario)
]

# Criteri di classificazione per SQUADRE (FISTF 2.2.2.b)
TEAM_STANDINGS_CRITERIA = [
    "points",                          # 1. Punti squadra
    "head_to_head_points",             # 2. Punti scontri diretti
    "head_to_head_individual_wins_diff", # 3. Differenza vittorie individuali H2H
    "head_to_head_individual_wins",     # 4. Vittorie individuali H2H
    "individual_wins_diff",             # 5. Differenza vittorie individuali totale
    "individual_wins",                   # 6. Vittorie individuali totali
    "head_to_head_goal_difference",      # 7. Differenza reti H2H
    "head_to_head_goals_scored",         # 8. Gol segnati H2H
    "goal_difference",                    # 9. Differenza reti totale
    "goals_scored",                        # 10. Gol segnati totali
    "shootout"                              # 11. Shoot-out
]


# ========================================
# REGOLE FORFAIT E SANZIONI
# ========================================

# Regole forfait (FISTF 2.1.2.d e 2.2.2.c - AGGIORNATE 2025-26)
FORFEIT_RULES = {
    "grace_period_minutes": 0,  # NUOVO: nessun periodo di grazia (abolito 15 minuti)
    "individual_score": "0-3",  # Risultato a tavolino
    "team_score": "0-4",  # Per squadre (0-4 partita, 0-3 ogni incontro)
    "team_individual_scores": ["0-3", "0-3", "0-3", "0-3"],
}

# Penalità per assenze (FISTF 2.1.2.d.iv)
PENALTIES = {
    "first_offense": {"fine": 50, "ranking_points": -50},
    "second_offense": {"fine": 100, "ranking_points": -100},
    "third_offense": {"fine": 150, "ranking_points": -200, "suspension_months": 6},
}


# ========================================
# REGOLE ARBITRI
# ========================================

REFFREE_RULES = {
    "cannot_referee_own_club": True,
    "cannot_referee_own_country": True,
    "u12_cannot_referee": True,  # Regola 1.1.2.8.d
    "head_referee_must_be_nominated": True,
    "head_referee_cannot_play_alone": True,  # Se gioca, serve più di un head referee
    "player_appeals_per_match": 2,  # Regola 1.1.2.8.l
}


# ========================================
# REGOLE COMPETIZIONI A SQUADRE SPECIFICHE
# ========================================

TEAM_SPECIFIC_RULES = {
    "barbarians_team": {
        "allowed": True,
        "always_in_group_1": True,  # Sempre nel primo girone
        "cannot_qualify": True,  # Non possono passare il turno
        "results_recorded_as_forfeit": True,  # Risultati registrati come forfait
    },
    "pairing_procedure": {  # Regola 2.2.3
        "time_limit_minutes": 5,  # 5 minuti per compilare match sheet
        "selection_order": [
            "A_selects_game1",
            "B_selects_game1",
            "B_selects_game2",
            "A_selects_game2",
            "A_selects_game3",
            "B_selects_game3",
            "B_selects_game4",
            "A_selects_game4",
        ],
    },
    "three_player_team": {  # Regola 2.2.3.f
        "must_forfeit_fourth_match": True,
        "cannot_win_on_goal_difference": True,  # In caso di pareggio
    },
    "substitution_rules": {  # Regola 2.2.4
        "allowed_at_half_time": True,
        "allowed_before_sudden_death": True,
        "allowed_before_shootout": True,
        "max_substitutions_per_team": 2,
        "winner_of_toss_substitutes_first": True,
        "time_limit_minutes": 2,
    },
    "sudden_death": {  # Regola 2.2.5
        "duration_minutes": 10,
        "all_4_tables_continue": True,
        "shootout_if_still_draw": True,
    },
}


# ========================================
# FORMATI LICENZA
# ========================================

# Formato licenza FISTF
LICENCE_FORMAT = r'^[A-Z]{3}\d{5}$'  # Es: ITA12345

# Formato ID squadra (opzionale)
TEAM_ID_FORMAT = r'^[A-Z0-9_]{3,20}$'  # Es: MESSINA_A, ITALIA_1


# ========================================
# FUNZIONI DI UTILITÀ
# ========================================

def get_category_rules(category: Category) -> Dict[str, Any]:
    """Restituisce le regole per una categoria."""
    return CATEGORY_RULES.get(category, {})


def get_competition_type(category: Category) -> CompetitionType:
    """Restituisce il tipo di competizione per una categoria."""
    rules = get_category_rules(category)
    return rules.get("competition_type", CompetitionType.INDIVIDUAL)


def get_standings_criteria(category: Category) -> List[str]:
    """Restituisce i criteri di classifica appropriati per la categoria."""
    if get_competition_type(category) == CompetitionType.TEAM:
        return TEAM_STANDINGS_CRITERIA
    return INDIVIDUAL_STANDINGS_CRITERIA


def apply_youth_cap(category: Category, goals_for: int, goals_against: int) -> tuple[int, int]:
    """
    Applica il limite 5-0 per le categorie giovanili/femminili se richiesto.
    Restituisce (capped_goals_for, capped_goals_against).
    """
    rules = get_category_rules(category)
    if rules.get("apply_cap", False):
        margin = rules.get("cap_margin", 5)
        diff = goals_for - goals_against
        
        if diff > margin:
            return (goals_against + margin, goals_against)
        elif diff < -margin:
            return (goals_for, goals_for + margin)
    
    return (goals_for, goals_against)


def validate_team_roster(players: List, category: Category) -> tuple[bool, List[str]]:
    """
    Valida che un roster squadra rispetti le regole.
    Restituisce (is_valid, list_of_errors).
    """
    errors = []
    rules = get_category_rules(category)
    
    if get_competition_type(category) != CompetitionType.TEAM:
        return False, ["Categoria non valida per squadre"]
    
    min_players = rules.get("players_per_team", {}).get("min", 3)
    max_players = rules.get("players_per_team", {}).get("max", 8)
    
    if len(players) < min_players:
        errors.append(f"Numero giocatori insufficiente: {len(players)} (min {min_players})")
    
    if len(players) > max_players:
        errors.append(f"Numero giocatori eccedente: {len(players)} (max {max_players})")
    
    # Verifica duplicati licenze
    licences = [p.licence for p in players]
    duplicates = [l for l in licences if licences.count(l) > 1]
    if duplicates:
        errors.append(f"Licenze duplicate: {', '.join(set(duplicates))}")
    
    return len(errors) == 0, errors


def validate_team_match_foreigners(individual_matches: List, team_country: str) -> tuple[bool, List[str]]:
    """
    Valida che in una partita a squadre non ci siano più di 2 stranieri.
    Restituisce (is_valid, list_of_errors).
    """
    foreigners_count = 0
    errors = []
    
    for match in individual_matches:
        if hasattr(match, 'player1_country') and match.player1_country != team_country:
            foreigners_count += 1
        if hasattr(match, 'player2_country') and match.player2_country != team_country:
            foreigners_count += 1
    
    if foreigners_count > 2:
        errors.append(f"Troppi stranieri: {foreigners_count} (max 2)")
        return False, errors
    
    return True, errors