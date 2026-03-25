# core/team_standings_calculator.py
"""
Calcolatore classifiche per tornei a squadre secondo criteri FISTF.
Include tutti i criteri HTH per squadre.
Considera solo le partite effettivamente giocate.
"""
import pandas as pd
from typing import List, Dict, Optional
from collections import defaultdict


class TeamStandingsCalculator:
    """Calcola classifiche per gironi a squadre."""
    
    def calculate_group_standings(self, group_name: str, teams: List, matches: List) -> pd.DataFrame:
        """
        Calcola la classifica di un girone secondo criteri FISTF con HTH.
        Considera solo le partite effettivamente giocate.
        
        Args:
            group_name: Nome del girone
            teams: Lista squadre nel girone
            matches: Lista partite del girone
        
        Returns:
            DataFrame con classifica ordinata e colonne HTH
        """
        print(f"\n🔍 Calcolo classifica squadre per girone '{group_name}'")
        
        # Inizializza statistiche
        stats = {}
        for team in teams:
            stats[team.id] = {
                'team': team,
                'Punti': 0,
                'Giocate': 0,
                'Vinte': 0,
                'Pareggiate': 0,
                'Perse': 0,
                'V': 0,  # Vittorie individuali totali
                'DIFF_V': 0,  # Differenza vittorie individuali
                'GF': 0,  # Gol fatti totali
                'GS': 0,  # Gol subiti totali
                'DG': 0,  # Differenza reti totale
                'HTH_Punti': defaultdict(int),  # Punti scontri diretti
                'HTH_V': defaultdict(int),  # Vittorie ind. scontri diretti
                'HTH_DIFF_V': defaultdict(int),  # Diff. vittorie ind. scontri diretti
                'HTH_GF': defaultdict(int),  # Gol fatti scontri diretti
                'HTH_GS': defaultdict(int),  # Gol subiti scontri diretti
                'match_results': {}  # Risultati per scontri diretti
            }
        
        # Processa ogni partita (solo quelle giocate)
        print(f"\n   Partite totali nel girone: {len(matches)}")
        processed = 0
        skipped = 0
        
        for match in matches:
            # Verifica se la partita è stata giocata
            is_played = match.is_played
            
            if not is_played:
                print(f"   ⏳ Partita {match.id} non ancora giocata - saltata")
                skipped += 1
                continue
            
            if not match.individual_matches:
                print(f"   ⚠️ Partita {match.id} senza incontri individuali - saltata")
                skipped += 1
                continue
            
            # Identifica squadre
            team1_id = match.team1
            team2_id = match.team2
            
            if team1_id not in stats or team2_id not in stats:
                print(f"   ⚠️ Squadre non trovate: {team1_id} vs {team2_id}")
                continue
            
            # Calcola risultati squadra
            wins1 = 0
            wins2 = 0
            goals1 = 0
            goals2 = 0
            
            for im in match.individual_matches:
                if im.goals1 is not None and im.goals2 is not None:
                    if im.goals1 > im.goals2:
                        wins1 += 1
                    elif im.goals2 > im.goals1:
                        wins2 += 1
                    goals1 += im.goals1
                    goals2 += im.goals2
            
            # Determina risultato squadra
            if wins1 > wins2:
                team_result = f"{wins1}-{wins2} (vittoria)"
            elif wins2 > wins1:
                team_result = f"{wins1}-{wins2} (sconfitta)"
            else:
                team_result = f"{wins1}-{wins2} (pareggio)"
            
            print(f"   ✅ Partita {match.id}: {match.player1} vs {match.player2} - {team_result}")
            processed += 1
            
            # Aggiorna statistiche squadra 1
            stats[team1_id]['Giocate'] += 1
            stats[team1_id]['V'] += wins1
            stats[team1_id]['DIFF_V'] += (wins1 - wins2)
            stats[team1_id]['GF'] += goals1
            stats[team1_id]['GS'] += goals2
            stats[team1_id]['DG'] += (goals1 - goals2)
            
            # Aggiorna statistiche squadra 2
            stats[team2_id]['Giocate'] += 1
            stats[team2_id]['V'] += wins2
            stats[team2_id]['DIFF_V'] += (wins2 - wins1)
            stats[team2_id]['GF'] += goals2
            stats[team2_id]['GS'] += goals1
            stats[team2_id]['DG'] += (goals2 - goals1)
            
            # Punti squadra (vittoria squadra = 3 punti, pareggio = 1)
            if wins1 > wins2:
                stats[team1_id]['Vinte'] += 1
                stats[team1_id]['Punti'] += 3
                stats[team2_id]['Perse'] += 1
            elif wins2 > wins1:
                stats[team2_id]['Vinte'] += 1
                stats[team2_id]['Punti'] += 3
                stats[team1_id]['Perse'] += 1
            else:
                stats[team1_id]['Pareggiate'] += 1
                stats[team2_id]['Pareggiate'] += 1
                stats[team1_id]['Punti'] += 1
                stats[team2_id]['Punti'] += 1
            
            # Salva risultato per scontri diretti
            stats[team1_id]['match_results'][team2_id] = {
                'punti': 3 if wins1 > wins2 else (1 if wins1 == wins2 else 0),
                'v': wins1,
                'v_opp': wins2,
                'diff_v': wins1 - wins2,
                'gf': goals1,
                'gs': goals2,
                'diff_g': goals1 - goals2
            }
            
            stats[team2_id]['match_results'][team1_id] = {
                'punti': 3 if wins2 > wins1 else (1 if wins1 == wins2 else 0),
                'v': wins2,
                'v_opp': wins1,
                'diff_v': wins2 - wins1,
                'gf': goals2,
                'gs': goals1,
                'diff_g': goals2 - goals1
            }
        
        print(f"\n   📊 Riepilogo: {processed} partite processate, {skipped} saltate (non giocate)")
        
        # Calcola scontri diretti per ogni coppia
        for team_id, team_stats in stats.items():
            for opp_id, result in team_stats['match_results'].items():
                team_stats['HTH_Punti'][opp_id] = result['punti']
                team_stats['HTH_V'][opp_id] = result['v']
                team_stats['HTH_DIFF_V'][opp_id] = result['diff_v']
                team_stats['HTH_GF'][opp_id] = result['gf']
                team_stats['HTH_GS'][opp_id] = result['gs']
        
        # Crea DataFrame
        data = []
        for team_id, team_stats in stats.items():
            team = team_stats['team']
            
            # Calcola HTH aggregati per la classifica generale
            hth_punti = sum(team_stats['HTH_Punti'].values())
            hth_v = sum(team_stats['HTH_V'].values())
            hth_diff_v = sum(team_stats['HTH_DIFF_V'].values())
            hth_gf = sum(team_stats['HTH_GF'].values())
            hth_gs = sum(team_stats['HTH_GS'].values())
            hth_dg = hth_gf - hth_gs
            
            data.append({
                'Squadra': team.display_name,
                'Squadra ID': team.id,
                'Club': team.club or team.display_name,
                'Punti': team_stats['Punti'],
                'Giocate': team_stats['Giocate'],
                'Vinte': team_stats['Vinte'],
                'Pareggiate': team_stats['Pareggiate'],
                'Perse': team_stats['Perse'],
                'V': team_stats['V'],
                'DIFF_V': team_stats['DIFF_V'],
                'GF': team_stats['GF'],
                'GS': team_stats['GS'],
                'DG': team_stats['DG'],
                'HTH_Punti': hth_punti,
                'HTH_V': hth_v,
                'HTH_DIFF_V': hth_diff_v,
                'HTH_DG': hth_dg,
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            print("   ⚠️ Nessun dato disponibile per la classifica")
            return df
        
        # Ordina secondo criteri FISTF
        df_sorted = df.sort_values(
            by=['Punti', 'HTH_Punti', 'HTH_DIFF_V', 'HTH_V', 'DIFF_V', 'V', 'HTH_DG', 'DG', 'GF'],
            ascending=[False, False, False, False, False, False, False, False, False]
        ).reset_index(drop=True)
        
        # Aggiungi colonna posizione
        df_sorted.insert(0, 'Pos', range(1, len(df_sorted) + 1))
        
        print("\n   📋 Statistiche calcolate con HTH:")
        for _, row in df_sorted.iterrows():
            print(f"      {row['Squadra']}:")
            print(f"         Punti: {row['Punti']} ({row['Vinte']}V, {row['Pareggiate']}P, {row['Perse']}S)")
            print(f"         Vittorie Ind.: {row['V']} (Diff: {row['DIFF_V']})")
            print(f"         Reti: {row['GF']}-{row['GS']} (Diff: {row['DG']})")
            print(f"         HTH-P: {row['HTH_Punti']}, HTH-V: {row['HTH_V']}, HTH-DiffV: {row['HTH_DIFF_V']}, HTH-DG: {row['HTH_DG']}")
        
        return df_sorted