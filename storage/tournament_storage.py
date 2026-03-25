"""
Gestione salvataggio e caricamento dei tornei.
"""
import pickle
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Union

from models.tournament_save import TournamentSave
from models.match import Match
from models.team_match import TeamMatch

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TournamentStorage:
    """Gestisce il salvataggio e caricamento dei tornei."""
    
    def __init__(self):
        self.saves_dir = Path("saves")
        self.saves_dir.mkdir(exist_ok=True)
        self.backup_dir = self.saves_dir / "backup"
        self.backup_dir.mkdir(exist_ok=True)
    
    def save_tournament(self, tournament, players, teams=None, groups=None, matches=None) -> str:
        """
        Salva il torneo completo.
        """
        # Determina il tipo di torneo
        tournament_type = getattr(tournament, 'tournament_type', 'individual')
        
        # Filtra le partite in base al tipo
        if tournament_type == "team":
            # Per tornei a squadre, assicurati che matches contenga TeamMatch
            valid_matches = []
            for m in (matches or []):
                if hasattr(m, 'individual_matches'):
                    valid_matches.append(m)
                else:
                    logger.warning(f"Partita {m.id} non è una TeamMatch, ignorata")
            matches = valid_matches
        else:
            # Per tornei individuali, assicurati che matches contenga Match
            valid_matches = []
            for m in (matches or []):
                if not hasattr(m, 'individual_matches'):
                    valid_matches.append(m)
                else:
                    logger.warning(f"Partita {m.id} non è una Match, ignorata")
            matches = valid_matches
        
        tournament_save = TournamentSave(
            tournament=tournament,
            players=players,
            teams=teams or [],
            groups=groups or {},
            matches=matches or [],
            tournament_type=tournament_type
        )
        
        # Crea nome file sicuro
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = tournament.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = self.saves_dir / f"{safe_name}_{timestamp}.pkl"
        
        # Salva con pickle
        with open(filename, 'wb') as f:
            pickle.dump(tournament_save, f)
        
        logger.info(f"✅ Torneo salvato: {filename}")
        return str(filename)
    
    def save_with_backup(self, tournament, players, teams=None, groups=None, matches=None) -> str:
        """
        Salva con backup del file precedente se esiste già.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = tournament.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = self.saves_dir / f"{safe_name}_{timestamp}.pkl"
        
        # Se esiste già un file con lo stesso nome (raro per via del timestamp)
        if filename.exists():
            backup_name = self.backup_dir / f"{safe_name}_{timestamp}_backup.pkl"
            filename.rename(backup_name)
            logger.info(f"📦 Backup creato: {backup_name}")
        
        return self.save_tournament(tournament, players, teams, groups, matches)
    
    def load_tournament(self, filename: str) -> Optional[TournamentSave]:
        """
        Carica un torneo da file con gestione versioni.
        """
        filepath = Path(filename)
        if not filepath.exists():
            logger.error(f"File non trovato: {filename}")
            return None
        
        try:
            with open(filepath, 'rb') as f:
                tournament_save = pickle.load(f)
            
            if not isinstance(tournament_save, TournamentSave):
                logger.error(f"File {filename} non contiene un TournamentSave valido")
                return None
            
            # LOG VERSIONE
            version = getattr(tournament_save, 'version', '1.0')
            logger.info(f"📦 Caricato torneo versione: {version}")
            
            # GESTIONE RETROCOMPATIBILITÀ
            if not hasattr(tournament_save, 'teams'):
                tournament_save.teams = []
                logger.info("   Aggiunto campo teams mancante")
            
            if not hasattr(tournament_save, 'tournament_type'):
                # Determina il tipo dalle partite
                if tournament_save.matches and any(hasattr(m, 'individual_matches') for m in tournament_save.matches):
                    tournament_save.tournament_type = 'team'
                else:
                    tournament_save.tournament_type = 'individual'
                logger.info(f"   Determinato tournament_type: {tournament_save.tournament_type}")
            
            if not hasattr(tournament_save, 'version'):
                tournament_save.version = '1.0'
            
            # VALIDAZIONE CONSISTENZA
            warnings = self._validate_loaded_tournament(tournament_save)
            if warnings:
                logger.warning("⚠️ Trovati avvisi di validazione:")
                for w in warnings:
                    logger.warning(f"   • {w}")
            
            return tournament_save
            
        except Exception as e:
            logger.error(f"❌ Errore caricamento {filename}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_loaded_tournament(self, tournament_save: TournamentSave) -> List[str]:
        """
        Valida l'integrità del torneo caricato.
        Restituisce una lista di avvisi.
        """
        warnings = []
        
        # Verifica che tutti i giocatori delle squadre esistano
        for team in tournament_save.teams:
            for player in team.players:
                if player not in tournament_save.players:
                    warnings.append(f"Giocatore {player.display_name} nella squadra {team.id} non trovato in players")
        
        # Verifica che tutte le partite abbiano giocatori/squadre validi
        player_names = {p.display_name for p in tournament_save.players}
        team_ids = {t.id for t in tournament_save.teams}
        
        for i, match in enumerate(tournament_save.matches):
            if hasattr(match, 'individual_matches'):  # TeamMatch
                if match.team1 and match.team1 not in team_ids:
                    warnings.append(f"Partita {match.id}: squadra {match.team1} non trovata")
                if match.team2 and match.team2 not in team_ids:
                    warnings.append(f"Partita {match.id}: squadra {match.team2} non trovata")
            else:  # Match individuale
                if match.player1 and match.player1 not in player_names and not match.player1.startswith("WIN "):
                    warnings.append(f"Partita {match.id}: giocatore {match.player1} non trovato")
                if match.player2 and match.player2 not in player_names and not match.player2.startswith("WIN "):
                    warnings.append(f"Partita {match.id}: giocatore {match.player2} non trovato")
        
        # Verifica consistenza tipo torneo
        has_team_matches = any(hasattr(m, 'individual_matches') for m in tournament_save.matches)
        has_individual_matches = any(not hasattr(m, 'individual_matches') for m in tournament_save.matches)
        
        if tournament_save.tournament_type == "team" and has_individual_matches:
            warnings.append("Torneo a squadre ma contiene partite individuali")
        
        if tournament_save.tournament_type == "individual" and has_team_matches:
            warnings.append("Torneo individuale ma contiene partite a squadre")
        
        return warnings
    
    def list_saved_tournaments(self) -> List[Dict]:
        """
        Restituisce la lista dei tornei salvati con metadati.
        Utile per mostrare una finestra di caricamento.
        """
        tournaments = []
        
        for filepath in sorted(self.saves_dir.glob("*.pkl"), reverse=True):
            try:
                # Prova a leggere solo i metadati senza caricare tutto
                # Nota: con pickle non possiamo fare peek, dobbiamo caricare
                with open(filepath, 'rb') as f:
                    tournament_save = pickle.load(f)
                
                tournaments.append({
                    'filename': str(filepath),
                    'name': tournament_save.tournament.name,
                    'date': tournament_save.save_date.strftime('%d/%m/%Y %H:%M'),
                    'type': 'Squadre' if tournament_save.tournament_type == 'team' else 'Individuale',
                    'players': len(tournament_save.players),
                    'teams': len(tournament_save.teams),
                    'matches': len(tournament_save.matches),
                    'version': getattr(tournament_save, 'version', '1.0')
                })
            except Exception as e:
                tournaments.append({
                    'filename': str(filepath),
                    'name': f"❌ ERRORE: {filepath.name}",
                    'date': '?',
                    'type': '?',
                    'players': 0,
                    'teams': 0,
                    'matches': 0,
                    'version': '?',
                    'error': str(e)
                })
        
        return tournaments
    
    def delete_tournament(self, filename: str) -> bool:
        """
        Elimina un file di salvataggio (con conferma).
        """
        filepath = Path(filename)
        if not filepath.exists():
            logger.error(f"File {filename} non trovato")
            return False
        
        try:
            # Sposta in backup invece di eliminare
            backup_path = self.backup_dir / f"deleted_{filepath.name}"
            filepath.rename(backup_path)
            logger.info(f"🗑️ Torneo spostato in backup: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Errore eliminazione {filename}: {e}")
            return False
    
    def export_as_json(self, tournament, players, teams=None, groups=None, matches=None) -> str:
        """
        Esporta in formato JSON (per debug/backup leggibile).
        """
        import json
        from datetime import date
        
        tournament_type = getattr(tournament, 'tournament_type', 'individual')
        
        tournament_save = TournamentSave(
            tournament=tournament,
            players=players,
            teams=teams or [],
            groups=groups or {},
            matches=matches or [],
            tournament_type=tournament_type
        )
        
        # Funzione per serializzare oggetti non JSON
        def json_serializer(obj):
            if isinstance(obj, date):
                return obj.isoformat()
            if hasattr(obj, 'dict'):  # Pydantic model
                return obj.dict()
            if hasattr(obj, '__dict__'):
                return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = tournament.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = self.saves_dir / f"{safe_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(tournament_save.dict(), f, default=json_serializer, indent=2)
        
        logger.info(f"📄 JSON esportato: {filename}")
        return str(filename)


# ========================================
# FUNZIONI DI UTILITÀ PER USO RAPIDO
# ========================================

def save_tournament(tournament, players, teams=None, groups=None, matches=None):
    """Funzione rapida per salvare."""
    storage = TournamentStorage()
    return storage.save_tournament(tournament, players, teams, groups, matches)

def load_tournament(filename):
    """Funzione rapida per caricare."""
    storage = TournamentStorage()
    return storage.load_tournament(filename)

def list_tournaments():
    """Funzione rapida per listare."""
    storage = TournamentStorage()
    return storage.list_saved_tournaments()