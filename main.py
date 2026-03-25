# main.py
"""
FISTF Tournament Manager - Entry Point
Gestione tornei di calcio da tavolo secondo regole FISTF.
"""
import sys
from pathlib import Path

# Aggiungi il percorso per importare i moduli
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QTabWidget, QLabel,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt

from models.tournament import TournamentConfig
from models.player import Player
from storage.tournament_storage import TournamentStorage

# Import delle tab
from ui.tabs.setup_tab import SetupTab
from ui.tabs.players_tab import PlayersTab
from ui.tabs.groups_tab import GroupsTab
from ui.tabs.calendar_tab import CalendarTab
from ui.tabs.results_tab import ResultsTab

from ui.tabs.standings_tab import StandingsTab
from ui.tabs.knockout_tab import KnockoutTab
from ui.tabs.scorers_tab import ScorersTab

# Import tab squadre
from ui.tabs.teams_tab import TeamsTab
from ui.tabs.team_groups_tab import TeamGroupsTab
from ui.tabs.team_calendar_tab import TeamCalendarTab
from ui.tabs.team_results_tab import TeamResultsTab
from ui.tabs.team_standings_tab import TeamStandingsTab
from ui.tabs.team_knockout_tab import TeamKnockoutTab
from ui.tabs.team_scorers_tab import TeamScorersTab


class TournamentManager(QMainWindow):
    """Finestra principale dell'applicazione."""
    
    def __init__(self):
        super().__init__()
        
        # Impostazioni finestra
        self.setWindowTitle("FISTF Tournament Manager")
        self.setGeometry(100, 100, 1300, 900)
        
        # Flag di sicurezza
        self._loading_tournament = False
        self._updating_ui = False
        self._creating_tournament = False
        
        # Dati del torneo
        self.current_tournament = None
        self.players = []
        self.teams = []
        self.groups = {}
        self.matches = []
        self.tournament_type = "individual"
        
        # Storage
        self.storage = TournamentStorage()
        
        # Riferimenti UI
        self.tabs = None
        
        # Setup UI
        self.setup_ui()
        
        print("✅ TournamentManager inizializzato")
    
    def setup_ui(self):
        """Crea l'interfaccia principale."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ========================================
        # TOOLBAR
        # ========================================
        toolbar = QHBoxLayout()
        
        btn_save = QPushButton("💾 Salva Torneo")
        btn_save.clicked.connect(self.save_tournament)
        btn_save.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 10px; border-radius: 4px;")
        toolbar.addWidget(btn_save)
        
        btn_load = QPushButton("📂 Carica Torneo")
        btn_load.clicked.connect(self.load_tournament)
        btn_load.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 10px; border-radius: 4px;")
        toolbar.addWidget(btn_load)
        
        btn_close = QPushButton("🔒 Chiudi Torneo")
        btn_close.clicked.connect(self.close_tournament)
        btn_close.setStyleSheet("background-color: #9C27B0; color: white; padding: 5px 10px; border-radius: 4px;")
        toolbar.addWidget(btn_close)
        
        toolbar.addStretch()
        
        btn_exit = QPushButton("🚪 Esci")
        btn_exit.clicked.connect(self.exit_application)
        btn_exit.setStyleSheet("background-color: #f44336; color: white; padding: 5px 10px; border-radius: 4px;")
        toolbar.addWidget(btn_exit)
        
        main_layout.addLayout(toolbar)
        
        # ========================================
        # TAB WIDGET
        # ========================================
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)
        
        # Crea la tab Setup (sempre presente)
        self.tabs.addTab(SetupTab(self), "Setup")
        
        # Barra di stato
        self.statusBar().showMessage("Pronto")
    
    def rebuild_tabs_after_creation(self):
        """Ricostruisce le tab dopo la creazione del torneo."""
        if not self.current_tournament:
            return
        
        self._creating_tournament = True
        
        # Rimuovi tutte le tab tranne Setup
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        
        # Crea le tab in base al tipo di torneo
        if self.tournament_type == "team":
            self._create_team_tabs()
        else:
            self._create_individual_tabs()
        
        # Imposta la prima tab dopo Setup come attiva
        if self.tabs.count() > 1:
            self.tabs.setCurrentIndex(1)
        
        self._creating_tournament = False
    
    def _create_individual_tabs(self):
        """Crea le tab per torneo individuale."""
        print("🏆 Creazione tab torneo INDIVIDUALE")
        
        from ui.tabs.players_tab import PlayersTab
        from ui.tabs.groups_tab import GroupsTab
        from ui.tabs.calendar_tab import CalendarTab
        from ui.tabs.results_tab import ResultsTab
        # from ui.tabs.round_results_tab import RoundResultsTab
        from ui.tabs.standings_tab import StandingsTab
        from ui.tabs.knockout_tab import KnockoutTab
        from ui.tabs.scorers_tab import ScorersTab
        
        self.tabs.addTab(PlayersTab(self), "Iscrizioni")
        self.tabs.addTab(GroupsTab(self), "Gironi")
        self.tabs.addTab(CalendarTab(self), "Calendario")
        self.tabs.addTab(ResultsTab(self), "Risultati")
        #self.tabs.addTab(RoundResultsTab(self), "Risultati per Turno")
        self.tabs.addTab(StandingsTab(self), "Classifiche")
        self.tabs.addTab(KnockoutTab(self), "Fase Finale")
        self.tabs.addTab(ScorersTab(self), "Cannonieri")  # SOLO Cannonieri Individuali
        
        print(f"   ✅ Create {self.tabs.count() - 1} tab individuali")
    def _create_team_tabs(self):
        """Crea le tab per torneo a squadre."""
        print("🏆 Creazione tab torneo a SQUADRE")
        
        from ui.tabs.teams_tab import TeamsTab
        from ui.tabs.team_groups_tab import TeamGroupsTab
        from ui.tabs.team_calendar_tab import TeamCalendarTab
        from ui.tabs.team_results_tab import TeamResultsTab
        from ui.tabs.team_standings_tab import TeamStandingsTab
        from ui.tabs.team_knockout_tab import TeamKnockoutTab
        from ui.tabs.team_scorers_tab import TeamScorersTab
        
        self.tabs.addTab(TeamsTab(self), "Squadre")
        self.tabs.addTab(TeamGroupsTab(self), "Gironi Squadre")
        self.tabs.addTab(TeamCalendarTab(self), "Calendario Squadre")
        self.tabs.addTab(TeamResultsTab(self), "Risultati Squadre")
        self.tabs.addTab(TeamStandingsTab(self), "Classifiche Squadre")
        self.tabs.addTab(TeamKnockoutTab(self), "Fase Finale Squadre")
        self.tabs.addTab(TeamScorersTab(self), "Cannonieri Squadre")  # SOLO questa, non Cannonieri Individuali
        
        print(f"   ✅ Create {self.tabs.count() - 1} tab squadre")
        
    # ========================================
    # METODI DI SALVATAGGIO E CARICAMENTO
    # ========================================
    
    def save_tournament(self):
        """Salva il torneo su file."""
        if not self.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Nessun torneo attivo da salvare")
            return
        
        try:
            filename = self.storage.save_tournament(
                tournament=self.current_tournament,
                players=self.players,
                teams=self.teams,
                groups=self.groups,
                matches=self.matches
            )
            
            QMessageBox.information(self, "Successo", f"✅ Torneo salvato in:\n{filename}")
            self.statusBar().showMessage(f"Torneo salvato: {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_tournament(self):
        """Carica un torneo da file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file torneo",
            str(Path("saves").absolute()),
            "File torneo (*.pkl)"
        )
        
        if not file_path:
            return
        
        try:
            self._loading_tournament = True
            
            tournament_save = self.storage.load_tournament(file_path)
            
            if not tournament_save:
                QMessageBox.critical(self, "Errore", "Impossibile caricare il file")
                return
            
            # Carica dati
            self.current_tournament = tournament_save.tournament
            self.players = tournament_save.players
            self.teams = getattr(tournament_save, 'teams', [])
            self.groups = tournament_save.groups
            self.matches = tournament_save.matches
            self.tournament_type = getattr(tournament_save, 'tournament_type', 'individual')
            
            # Fix stati partita
            self._fix_match_status()
            
            # Ricostruisci tab
            self.rebuild_tabs_after_creation()
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Torneo '{self.current_tournament.name}' caricato!\n"
                                   f"Tipo: {'SQUADRE' if self.tournament_type == 'team' else 'INDIVIDUALE'}\n"
                                   f"{len(self.players)} giocatori, {len(self.teams)} squadre, {len(self.matches)} partite")
            
            self.statusBar().showMessage(f"Torneo caricato: {self.current_tournament.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento:\n{str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            self._loading_tournament = False
    
    def _fix_match_status(self):
        """Converte gli stati delle partite da stringhe a enum."""
        from models.match import MatchStatus
        
        fixed_count = 0
        status_map = {
            "SCHEDULED": MatchStatus.SCHEDULED,
            "Programmata": MatchStatus.SCHEDULED,
            "IN_PROGRESS": MatchStatus.IN_PROGRESS,
            "In corso": MatchStatus.IN_PROGRESS,
            "COMPLETED": MatchStatus.COMPLETED,
            "Giocata": MatchStatus.COMPLETED,
            "FORFEIT": MatchStatus.FORFEIT,
            "Forfait": MatchStatus.FORFEIT,
        }
        
        for match in self.matches:
            if hasattr(match, 'status') and isinstance(match.status, str):
                if match.status in status_map:
                    match.status = status_map[match.status]
                    fixed_count += 1
        
        if fixed_count > 0:
            print(f"✅ Corretti {fixed_count} stati partita")
    
    def close_tournament(self):
        """Chiude il torneo corrente."""
        if not self.current_tournament:
            QMessageBox.information(self, "Info", "Nessun torneo attivo da chiudere")
            return
        
        reply = QMessageBox.question(self, "Conferma Chiusura",
                                    f"Sei sicuro di voler chiudere il torneo '{self.current_tournament.name}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        reply_save = QMessageBox.question(self, "Salvare prima di chiudere?",
                                        "Vuoi salvare il torneo prima di chiuderlo?",
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        
        if reply_save == QMessageBox.Cancel:
            return
        
        if reply_save == QMessageBox.Yes:
            self.save_tournament()
        
        # Reset dati
        self.current_tournament = None
        self.players = []
        self.teams = []
        self.groups = {}
        self.matches = []
        self.tournament_type = "individual"
        
        # Ricostruisci tab (solo Setup)
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        
        self.statusBar().showMessage("Torneo chiuso. Crea o carica un nuovo torneo.")
        QMessageBox.information(self, "Torneo Chiuso", "Torneo chiuso con successo.")
    
    def exit_application(self):
        """Esce dall'applicazione."""
        reply = QMessageBox.question(self, "Conferma Uscita",
                                    "Sei sicuro di voler uscire dall'applicazione?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            sys.exit(0)
    
    def closeEvent(self, event):
        """Gestisce la chiusura della finestra."""
        reply = QMessageBox.question(self, "Conferma Uscita",
                                    "Sei sicuro di voler uscire dall'applicazione?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    
    def on_tab_changed(self, index):
        """Chiamato quando si cambia tab."""
        if self._loading_tournament or self._creating_tournament:
            return
        
        if index >= 0 and index < self.tabs.count():
            tab = self.tabs.widget(index)
            if hasattr(tab, 'on_tab_selected'):
                try:
                    tab.on_tab_selected()
                except Exception as e:
                    print(f"⚠️ Errore in on_tab_selected per {tab.__class__.__name__}: {e}")
    
    # ========================================
    # METODI DI UTILITÀ PER LE TAB
    # ========================================
    
    def refresh_standings(self):
        """Aggiorna la classifica se la tab è attiva."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, StandingsTab):
                tab.refresh()
                break
    
    def refresh_scorers(self):
        """Aggiorna la classifica marcatori se la tab è attiva."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, ScorersTab):
                tab.refresh()
                break
    
    def update_knockout_button_state(self):
        """Aggiorna lo stato del pulsante fase finale."""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, KnockoutTab):
                tab.update_button_state()
                break


def main():
    """Entry point dell'applicazione."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = TournamentManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()