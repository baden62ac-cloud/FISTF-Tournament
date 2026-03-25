# ui/tabs/teams_tab.py
"""
Tab per la gestione delle iscrizioni squadre.
Layout ottimizzato per occupare tutto lo spazio disponibile.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFileDialog,
                               QDialog, QFormLayout, QLineEdit, QComboBox,
                               QSpinBox, QDialogButtonBox, QGroupBox, QCheckBox,
                               QSplitter, QScrollArea, QSizePolicy, QFrame)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from collections import Counter

from ui.base_tab import BaseTab
from models.team import Team, TeamType
from models.player import Player, Category
from models.match import MatchStatus


class TeamsTab(BaseTab):
    """Tab per le iscrizioni squadre."""
    
    def __init__(self, parent):
        super().__init__(parent, "👥 Iscrizioni Squadre")
        
        # Riferimenti UI
        self.teams_table = None
        self.team_roster_table = None
        self.selected_team_label = None
        self.roster_stats = None
        self.lbl_teams_stats = None
        self.selected_team = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        # Assicurati che content_layout esista
        if self.content_layout is None:
            self.content_layout = QVBoxLayout(self)
            self.setLayout(self.content_layout)
        
        # Imposta il layout principale per riempire tutto lo spazio
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        
        # ========================================
        # TOOLBAR
        # ========================================
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        btn_add_team = QPushButton("➕ Nuova Squadra")
        btn_add_team.clicked.connect(self.add_team_dialog)
        btn_add_team.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 15px; border-radius: 4px;")
        toolbar.addWidget(btn_add_team)
        
        btn_import_teams = QPushButton("📤 Importa Squadre")
        btn_import_teams.clicked.connect(self.import_teams_dialog)
        btn_import_teams.setStyleSheet("background-color: #FF9800; color: white; padding: 6px 15px; border-radius: 4px;")
        toolbar.addWidget(btn_import_teams)
        
        btn_export_teams = QPushButton("📥 Esporta Squadre")
        btn_export_teams.clicked.connect(self.export_teams)
        btn_export_teams.setStyleSheet("background-color: #2196F3; color: white; padding: 6px 15px; border-radius: 4px;")
        toolbar.addWidget(btn_export_teams)
        
        #btn_test_teams = QPushButton("🧪 Aggiungi Test")
        #btn_test_teams.clicked.connect(self.add_test_teams)
        #btn_test_teams.setStyleSheet("background-color: #9C27B0; color: white; padding: 6px 15px; border-radius: 4px;")
        #toolbar.addWidget(btn_test_teams)
        
        btn_delete_team = QPushButton("🗑️ Elimina Squadra")
        btn_delete_team.clicked.connect(self.delete_team)
        btn_delete_team.setStyleSheet("background-color: #f44336; color: white; padding: 6px 15px; border-radius: 4px;")
        toolbar.addWidget(btn_delete_team)
        
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)
        
        # ========================================
        # SPLITTER ORIZZONTALE (occupa tutto lo spazio)
        # ========================================
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        
        # ========================================
        # PANNELLO SINISTRO: LISTA SQUADRE
        # ========================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        left_layout.setSpacing(5)
        
        # Titolo
        title_left = QLabel("📋 SQUADRE ISCRITTE")
        title_left.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50; padding: 5px; background-color: #ecf0f1; border-radius: 4px;")
        left_layout.addWidget(title_left)
        
        # Tabella squadre con scroll
        self.teams_table = QTableWidget()
        self.teams_table.setColumnCount(6)
        self.teams_table.setHorizontalHeaderLabels([
            "ID", "Squadra", "Categoria", "Club", "Nazione", "Seed"
        ])
        
        header = self.teams_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.teams_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.teams_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.teams_table.setAlternatingRowColors(True)
        self.teams_table.itemSelectionChanged.connect(self.on_team_selected)
        
        # Imposta altezza minima
        self.teams_table.setMinimumHeight(300)
        
        left_layout.addWidget(self.teams_table)
        
        # Statistiche squadre
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px; padding: 5px;")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(5, 2, 5, 2)
        
        self.lbl_teams_stats = QLabel("Totale squadre: 0")
        self.lbl_teams_stats.setStyleSheet("font-weight: bold;")
        stats_layout.addWidget(self.lbl_teams_stats)
        stats_layout.addStretch()
        
        left_layout.addWidget(stats_frame)
        
        # ========================================
        # PANNELLO DESTRO: ROSTER SQUADRA SELEZIONATA
        # ========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        right_layout.setSpacing(5)
        
        # Titolo
        title_right = QLabel("👥 ROSTER SQUADRA")
        title_right.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50; padding: 5px; background-color: #ecf0f1; border-radius: 4px;")
        right_layout.addWidget(title_right)
        
        # Squadra selezionata
        self.selected_team_label = QLabel("Nessuna squadra selezionata")
        self.selected_team_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px; padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        self.selected_team_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.selected_team_label)
        
        # Tabella roster
        self.team_roster_table = QTableWidget()
        self.team_roster_table.setColumnCount(5)
        self.team_roster_table.setHorizontalHeaderLabels([
            "Licenza", "Cognome", "Nome", "Nazione", "Ruolo"
        ])
        
        roster_header = self.team_roster_table.horizontalHeader()
        roster_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        roster_header.setSectionResizeMode(1, QHeaderView.Stretch)
        roster_header.setSectionResizeMode(2, QHeaderView.Stretch)
        roster_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        roster_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.team_roster_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.team_roster_table.setAlternatingRowColors(True)
        self.team_roster_table.setMinimumHeight(200)
        
        right_layout.addWidget(self.team_roster_table)
        
        # Pulsanti gestione roster
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 5, 0, 5)
        buttons_layout.setSpacing(8)
        
        btn_add_to_team = QPushButton("➕ Aggiungi Giocatore")
        btn_add_to_team.clicked.connect(self.add_player_to_team)
        btn_add_to_team.setStyleSheet("background-color: #4CAF50; color: white; padding: 6px 12px; border-radius: 4px;")
        buttons_layout.addWidget(btn_add_to_team)
        
        btn_remove_from_team = QPushButton("🗑️ Rimuovi Giocatore")
        btn_remove_from_team.clicked.connect(self.remove_player_from_team)
        btn_remove_from_team.setStyleSheet("background-color: #f44336; color: white; padding: 6px 12px; border-radius: 4px;")
        buttons_layout.addWidget(btn_remove_from_team)
        
        buttons_layout.addStretch()
        
        btn_edit_team = QPushButton("✏️ Modifica Squadra")
        btn_edit_team.clicked.connect(self.edit_team)
        btn_edit_team.setStyleSheet("background-color: #FF9800; color: white; padding: 6px 12px; border-radius: 4px;")
        buttons_layout.addWidget(btn_edit_team)
        
        right_layout.addWidget(buttons_container)
        
        # Statistiche roster
        self.roster_stats = QLabel("Giocatori: 0/8 (min 3 richiesti)")
        self.roster_stats.setStyleSheet("padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
        self.roster_stats.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.roster_stats)
        
        right_layout.addStretch()
        
        # Aggiungi widget allo splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Imposta proporzioni (60% sinistra, 40% destra)
        splitter.setSizes([600, 400])
        
        # Aggiungi splitter al layout principale (occupa tutto lo spazio)
        self.content_layout.addWidget(splitter, 1)  # stretch factor = 1 per occupare lo spazio
        
        # Aggiungi info aggiuntive in fondo
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #fef9e6; border-radius: 4px; padding: 5px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 4, 8, 4)
        
        info_label = QLabel("ℹ️ Le squadre devono avere almeno 3 giocatori (max 8) per essere valide.")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        
        self.content_layout.addWidget(info_frame)
    
    def refresh(self):
        """Aggiorna la tabella squadre."""
        if not hasattr(self.parent, 'teams'):
            return
        
        self.teams_table.setRowCount(0)
        
        # Salva la selezione corrente
        current_selection = None
        if self.selected_team and hasattr(self.selected_team, 'id'):
            current_selection = self.selected_team.id
        
        for row, team in enumerate(self.parent.teams):
            self.teams_table.insertRow(row)
            self.teams_table.setItem(row, 0, QTableWidgetItem(team.id))
            self.teams_table.setItem(row, 1, QTableWidgetItem(team.display_name))
            self.teams_table.setItem(row, 2, QTableWidgetItem(team.category))
            self.teams_table.setItem(row, 3, QTableWidgetItem(team.club or ""))
            self.teams_table.setItem(row, 4, QTableWidgetItem(team.country))
            seed_text = str(team.seed) if team.seed else ""
            self.teams_table.setItem(row, 5, QTableWidgetItem(seed_text))
        
        self.lbl_teams_stats.setText(f"Totale squadre: {len(self.parent.teams)}")
        
        # Ripristina la selezione se possibile
        if current_selection:
            for row in range(self.teams_table.rowCount()):
                if self.teams_table.item(row, 0).text() == current_selection:
                    self.teams_table.selectRow(row)
                    break
        else:
            self.teams_table.clearSelection()
    
    def on_team_selected(self):
        """Gestisce la selezione di una squadra."""
        if hasattr(self.parent, '_loading_tournament') and self.parent._loading_tournament:
            return
        
        current_row = self.teams_table.currentRow()
        
        if current_row < 0:
            self.selected_team_label.setText("Nessuna squadra selezionata")
            self.team_roster_table.setRowCount(0)
            self.roster_stats.setText("Giocatori: 0/8 (min 3 richiesti)")
            self.roster_stats.setStyleSheet("padding: 5px; background-color: #f8f9fa; border-radius: 4px;")
            self.selected_team = None
            return
        
        team_id = self.teams_table.item(current_row, 0).text()
        
        # Evita ricorsione
        if (self.selected_team is not None and 
            hasattr(self.selected_team, 'id') and
            self.selected_team.id == team_id):
            return
        
        team = next((t for t in self.parent.teams if t.id == team_id), None)
        
        if not team:
            return
        
        self.selected_team = team
        self.selected_team_label.setText(f"📌 {team.display_name} - {team.category}")
        self.selected_team_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px; padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        
        self.team_roster_table.setRowCount(0)
        
        for row, player in enumerate(team.players):
            self.team_roster_table.insertRow(row)
            self.team_roster_table.setItem(row, 0, QTableWidgetItem(player.licence))
            self.team_roster_table.setItem(row, 1, QTableWidgetItem(player.last_name))
            self.team_roster_table.setItem(row, 2, QTableWidgetItem(player.first_name))
            self.team_roster_table.setItem(row, 3, QTableWidgetItem(player.country))
            self.team_roster_table.setItem(row, 4, QTableWidgetItem("Titolare"))
        
        player_count = len(team.players)
        self.roster_stats.setText(f"Giocatori: {player_count}/8 (min 3 richiesti)")
        
        if player_count < 3:
            self.roster_stats.setStyleSheet("padding: 5px; background-color: #ffebee; border-radius: 4px; color: #c62828; font-weight: bold;")
        else:
            self.roster_stats.setStyleSheet("padding: 5px; background-color: #e8f5e9; border-radius: 4px; color: #2e7d32; font-weight: bold;")
    
    def add_team_dialog(self):
        """Dialog per aggiungere una nuova squadra."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo nella tab Setup")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuova Squadra")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        layout = QFormLayout(dialog)
        
        team_name = QLineEdit()
        team_name.setPlaceholderText("Es: ASD Subbuteo Messina A")
        layout.addRow("Nome Squadra *:", team_name)
        
        team_id = QLineEdit()
        team_id.setPlaceholderText("ID automatico se lasciato vuoto")
        layout.addRow("ID Squadra (opzionale):", team_id)
        
        category = QComboBox()
        for cat in self.parent.current_tournament.categories:
            if "Team" in cat.value:
                category.addItem(cat.value)
        layout.addRow("Categoria *:", category)
        
        club = QLineEdit()
        club.setPlaceholderText("Es: ASD Subbuteo Messina")
        layout.addRow("Club:", club)
        
        country = QLineEdit()
        country.setText("ITA")
        country.setMaxLength(3)
        layout.addRow("Nazione *:", country)
        
        seed = QSpinBox()
        seed.setMinimum(1)
        seed.setMaximum(999)
        seed.setSpecialValueText("Nessuno")
        seed.setValue(0)
        layout.addRow("Seed:", seed)
        
        team_type = QComboBox()
        team_type.addItems(["Club", "National", "Barbarians"])
        layout.addRow("Tipo:", team_type)
        
        barbarians_note = QLabel("Le squadre Barbarians non possono qualificarsi per la fase finale")
        barbarians_note.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        barbarians_note.setVisible(False)
        layout.addRow("", barbarians_note)
        
        def on_team_type_changed():
            is_barbarians = team_type.currentText() == "Barbarians"
            barbarians_note.setVisible(is_barbarians)
        
        team_type.currentTextChanged.connect(on_team_type_changed)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            if not team_name.text():
                QMessageBox.warning(self, "Errore", "Inserisci il nome della squadra")
                return
            
            if category.currentText() == "":
                QMessageBox.warning(self, "Errore", "Seleziona una categoria")
                return
            
            # Genera ID se vuoto
            safe_id = team_id.text().strip().upper()
            if not safe_id:
                safe_id = team_name.text().upper().replace(' ', '_').replace("'", "")[:20]
            
            selected_category = category.currentText()
            
            team = Team(
                id=safe_id,
                name=team_name.text(),
                club=club.text() if club.text() else None,
                country=country.text().upper(),
                team_type=team_type.currentText(),
                category=selected_category,
                players=[],
                seed=seed.value() if seed.value() > 0 else None
            )
            
            if any(t.id == team.id for t in self.parent.teams):
                QMessageBox.warning(self, "Errore", f"Squadra con ID {team.id} già esistente!")
                return
            
            self.parent.teams.append(team)
            self.refresh()
            self.parent.statusBar().showMessage(f"✅ Squadra {team.display_name} creata")
    
    def delete_team(self):
        """Elimina la squadra selezionata."""
        current_row = self.teams_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona una squadra da eliminare")
            return
        
        team_id = self.teams_table.item(current_row, 0).text()
        team = next((t for t in self.parent.teams if t.id == team_id), None)
        
        if not team:
            return
        
        reply = QMessageBox.question(self, "Conferma Eliminazione",
                                    f"Sei sicuro di voler eliminare la squadra '{team.display_name}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        self.parent.teams.remove(team)
        self.refresh()
        self.team_roster_table.setRowCount(0)
        self.selected_team_label.setText("Nessuna squadra selezionata")
        self.roster_stats.setText("Giocatori: 0/8 (min 3 richiesti)")
        
        self.parent.statusBar().showMessage(f"✅ Squadra {team.display_name} eliminata")
    
    def edit_team(self):
        """Modifica i dati della squadra selezionata."""
        if not self.selected_team:
            QMessageBox.warning(self, "Attenzione", "Seleziona una squadra da modificare")
            return
        
        team = self.selected_team
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifica Squadra - {team.display_name}")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        layout = QFormLayout(dialog)
        
        team_name = QLineEdit()
        team_name.setText(team.name)
        layout.addRow("Nome Squadra *:", team_name)
        
        team_id_edit = QLineEdit()
        team_id_edit.setText(team.id)
        team_id_edit.setEnabled(False)
        layout.addRow("ID Squadra:", team_id_edit)
        
        category = QComboBox()
        for cat in self.parent.current_tournament.categories:
            if "Team" in cat.value:
                category.addItem(cat.value)
        category.setCurrentText(team.category)
        layout.addRow("Categoria *:", category)
        
        club = QLineEdit()
        club.setText(team.club or "")
        layout.addRow("Club:", club)
        
        country = QLineEdit()
        country.setText(team.country)
        country.setMaxLength(3)
        layout.addRow("Nazione *:", country)
        
        seed = QSpinBox()
        seed.setMinimum(1)
        seed.setMaximum(999)
        seed.setSpecialValueText("Nessuno")
        seed.setValue(team.seed if team.seed else 0)
        layout.addRow("Seed:", seed)
        
        team_type = QComboBox()
        team_type.addItems(["Club", "National", "Barbarians"])
        team_type.setCurrentText(team.team_type.value if hasattr(team.team_type, 'value') else str(team.team_type))
        layout.addRow("Tipo:", team_type)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            if not team_name.text():
                QMessageBox.warning(self, "Errore", "Inserisci il nome della squadra")
                return
            
            team.name = team_name.text()
            team.category = category.currentText()
            team.club = club.text() if club.text() else None
            team.country = country.text().upper()
            team.seed = seed.value() if seed.value() > 0 else None
            team.team_type = team_type.currentText()
            
            self.refresh()
            self.on_team_selected()
            self.parent.statusBar().showMessage(f"✅ Squadra {team.display_name} aggiornata")
    
    def add_player_to_team(self):
        """Aggiunge un giocatore alla squadra selezionata."""
        if not self.selected_team:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una squadra")
            return
        
        team = self.selected_team
        
        if len(team.players) >= 8:
            QMessageBox.warning(self, "Attenzione", "La squadra ha già il massimo di 8 giocatori")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Aggiungi Giocatore a {team.display_name}")
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Seleziona un giocatore da aggiungere al roster:"))
        
        available_players = [p for p in self.parent.players if p not in team.players]
        
        if not available_players:
            QMessageBox.information(self, "Info", "Nessun giocatore disponibile. Aggiungi prima dei giocatori nella tab Iscrizioni.")
            dialog.reject()
            return
        
        player_table = QTableWidget()
        player_table.setColumnCount(4)
        player_table.setHorizontalHeaderLabels(["Licenza", "Cognome", "Nome", "Categoria"])
        
        for row, player in enumerate(available_players):
            player_table.insertRow(row)
            player_table.setItem(row, 0, QTableWidgetItem(player.licence))
            player_table.setItem(row, 1, QTableWidgetItem(player.last_name))
            player_table.setItem(row, 2, QTableWidgetItem(player.first_name))
            player_table.setItem(row, 3, QTableWidgetItem(player.category.value))
        
        player_table.setSelectionBehavior(QTableWidget.SelectRows)
        player_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(player_table)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            current_row = player_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore")
                return
            
            player_licence = player_table.item(current_row, 0).text()
            player = next((p for p in available_players if p.licence == player_licence), None)
            
            if player:
                team.players.append(player)
                self.on_team_selected()
                self.parent.statusBar().showMessage(f"✅ Giocatore {player.display_name} aggiunto alla squadra")
    
    def remove_player_from_team(self):
        """Rimuove un giocatore dalla squadra selezionata."""
        if not self.selected_team:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una squadra")
            return
        
        team = self.selected_team
        
        current_row = self.team_roster_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore dal roster")
            return
        
        player_licence = self.team_roster_table.item(current_row, 0).text()
        player = next((p for p in team.players if p.licence == player_licence), None)
        
        if not player:
            return
        
        if len(team.players) <= 3:
            reply = QMessageBox.question(self, "Conferma",
                                        f"La squadra ha solo {len(team.players)} giocatori. Rimuovendo questo giocatore scenderà a {len(team.players)-1} (minimo 3 richiesti).\n\nContinuare?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        team.players.remove(player)
        self.on_team_selected()
        self.parent.statusBar().showMessage(f"✅ Giocatore {player.display_name} rimosso dalla squadra")
    
    def import_teams_dialog(self):
        """Dialog per importare squadre da CSV."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo nella tab Setup")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file CSV squadre",
            str(Path(".").absolute()),
            "File CSV (*.csv);;Tutti i file (*.*)"
        )
        
        if not file_path:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Opzioni Import Squadre")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Formato CSV richiesto:\n"
                      "team_id,team_name,category,club,country,seed,player1_licence,player2_licence,player3_licence,...\n"
                      "MESSINA_A,ASD Messina A,Team Open,ASD Messina,ITA,1,ITA12345,ITA12346,ITA12347\n\n"
                      "Minimo 3 giocatori, massimo 8")
        label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(label)
        
        options_group = QGroupBox("Opzioni")
        options_layout = QVBoxLayout(options_group)
        
        import_skip_errors = QCheckBox("Salta righe con errori")
        import_skip_errors.setChecked(True)
        options_layout.addWidget(import_skip_errors)
        
        import_preview = QCheckBox("Solo anteprima (non importare)")
        import_preview.setChecked(False)
        options_layout.addWidget(import_preview)
        
        layout.addWidget(options_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        self.import_teams_from_csv(file_path, import_skip_errors.isChecked(), import_preview.isChecked())
    
    def import_teams_from_csv(self, file_path, skip_errors=True, preview_only=False):
        """Importa squadre da file CSV completo con dettagli giocatori."""
        import pandas as pd
        import os
        
        try:
            # Leggi il file con encoding UTF-8
            df = pd.read_csv(file_path, encoding='utf-8')
            
            print(f"📂 File caricato: {file_path}")
            print(f"📊 Colonne trovate: {list(df.columns)}")
            print(f"📊 Righe: {len(df)}")
            
            if preview_only:
                QMessageBox.information(self, "Info", "Modalità anteprima - nessuna squadra importata")
                return
            
            # Colonne richieste base
            required_cols = ['team_id', 'team_name', 'category', 'country']
            missing = [c for c in required_cols if c not in df.columns]
            
            if missing:
                QMessageBox.critical(self, "Errore", 
                                f"Colonne mancanti nel file CSV:\n{', '.join(missing)}\n\n"
                                f"Colonne trovate: {', '.join(list(df.columns))}")
                return
            
            success = 0
            errors = []
            duplicates = 0
            players_created = 0
            players_updated = 0
            
            existing_team_ids = [t.id for t in self.parent.teams]
            existing_licences = [p.licence for p in self.parent.players]
            
            for idx, row in df.iterrows():
                try:
                    team_id = str(row['team_id']).strip().upper()
                    print(f"\n🔍 Riga {idx+2}: importazione squadra {team_id}")
                    
                    # Verifica duplicati
                    if team_id in existing_team_ids:
                        duplicates += 1
                        errors.append(f"Riga {idx+2}: Squadra ID '{team_id}' già esistente")
                        continue
                    
                    team_name = str(row['team_name']).strip()
                    category_value = str(row['category']).strip()
                    club = str(row['club']).strip() if pd.notna(row.get('club')) else None
                    country = str(row['country']).strip().upper()[:3]
                    
                    # Verifica categoria
                    if not category_value.startswith("Team "):
                        errors.append(f"Riga {idx+2}: Categoria '{category_value}' non valida. Deve iniziare con 'Team '")
                        continue
                    
                    seed = None
                    if pd.notna(row.get('seed')):
                        try:
                            seed = int(row['seed'])
                        except:
                            pass
                    
                    # Raccogli giocatori
                    team_players = []
                    
                    for player_num in range(1, 9):
                        first_col = f'player{player_num}_first'
                        last_col = f'player{player_num}_last'
                        licence_col = f'player{player_num}_licence'
                        country_col = f'player{player_num}_country'
                        
                        # Verifica se la colonna licenza esiste
                        if licence_col not in df.columns:
                            if player_num <= 3:
                                errors.append(f"Riga {idx+2}: Colonna {licence_col} mancante")
                            break
                        
                        licence = str(row[licence_col]).strip().upper() if pd.notna(row[licence_col]) else ""
                        
                        if not licence:
                            if player_num <= 3:
                                errors.append(f"Riga {idx+2}: Giocatore {player_num} obbligatorio")
                            break
                        
                        # Estrai dati giocatore
                        first_name = str(row[first_col]).strip().upper() if first_col in df.columns and pd.notna(row[first_col]) else ""
                        last_name = str(row[last_col]).strip().upper() if last_col in df.columns and pd.notna(row[last_col]) else ""
                        player_country = str(row[country_col]).strip().upper()[:3] if country_col in df.columns and pd.notna(row[country_col]) else country
                        
                        # Cerca giocatore esistente
                        player = next((p for p in self.parent.players if p.licence == licence), None)
                        
                        if not player:
                            # Crea nuovo giocatore con i dati completi
                            # Determina categoria individuale dalla categoria squadra
                            individual_category = Category.OPEN
                            if "Veterans" in category_value:
                                individual_category = Category.VETERANS
                            elif "Women" in category_value:
                                individual_category = Category.WOMEN
                            elif "U20" in category_value:
                                individual_category = Category.U20
                            elif "U16" in category_value:
                                individual_category = Category.U16
                            elif "U12" in category_value:
                                individual_category = Category.U12
                            
                            player = Player(
                                first_name=first_name,
                                last_name=last_name,
                                licence=licence,
                                category=individual_category,
                                club=club or "Da definire",
                                country=player_country,
                                seed=None
                            )
                            self.parent.players.append(player)
                            existing_licences.append(licence)
                            players_created += 1
                            print(f"   ✅ Creato nuovo giocatore: {licence} - {first_name} {last_name}")
                        else:
                            # Aggiorna i dati del giocatore se mancanti
                            updated = False
                            if not player.first_name and first_name:
                                player.first_name = first_name
                                updated = True
                            if not player.last_name and last_name:
                                player.last_name = last_name
                                updated = True
                            if not player.club and club:
                                player.club = club
                                updated = True
                            if updated:
                                players_updated += 1
                                print(f"   ✅ Aggiornato giocatore: {licence} - {first_name} {last_name}")
                        
                        team_players.append(player)
                    
                    # Verifica minimo 3 giocatori
                    if len(team_players) < 3:
                        errors.append(f"Riga {idx+2}: Servono almeno 3 giocatori (trovati {len(team_players)})")
                        continue
                    
                    # Crea squadra
                    team = Team(
                        id=team_id,
                        name=team_name,
                        club=club,
                        country=country,
                        team_type="Club",
                        category=category_value,
                        players=team_players,
                        seed=seed
                    )
                    
                    self.parent.teams.append(team)
                    existing_team_ids.append(team_id)
                    success += 1
                    print(f"   ✅ Squadra creata: {team_id} con {len(team_players)} giocatori")
                    
                except Exception as e:
                    errors.append(f"Riga {idx+2}: {str(e)}")
                    print(f"   ❌ Errore: {e}")
                    import traceback
                    traceback.print_exc()
                    if not skip_errors:
                        break
            
            # Mostra report
            report = f"✅ Importate {success} squadre con successo!\n"
            if players_created > 0:
                report += f"✅ Creati {players_created} nuovi giocatori\n"
            if players_updated > 0:
                report += f"✅ Aggiornati {players_updated} giocatori esistenti\n"
            if duplicates > 0:
                report += f"⚠️ Saltate {duplicates} squadre duplicate\n"
            if errors:
                report += f"\n❌ {len(errors)} errori riscontrati"
            
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Risultato Import Squadre")
            msg_box.setText(report)
            
            if errors:
                msg_box.setDetailedText("\n".join(errors[:20]))
            
            msg_box.exec()
            
            if success > 0 or players_created > 0 or players_updated > 0:
                self.refresh()
                # Aggiorna anche la tab giocatori se aperta
                if hasattr(self.parent, 'refresh_players_table'):
                    self.parent.refresh_players_table()
                self.parent.statusBar().showMessage(f"✅ Importate {success} squadre, creati {players_created} giocatori")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la lettura del file:\n{str(e)}")
            import traceback
            traceback.print_exc()
            
    def export_teams(self):
        """Esporta squadre in Excel con dettaglio giocatori."""
        if not self.parent.teams:
            QMessageBox.warning(self, "Attenzione", "Nessuna squadra da esportare")
            return
        
        import pandas as pd
        
        data = []
        for team in self.parent.teams:
            row_data = {
                'team_id': team.id,
                'team_name': team.name,
                'category': team.category,
                'club': team.club or '',
                'country': team.country,
                'seed': team.seed if team.seed else '',
                'team_type': team.team_type.value if hasattr(team.team_type, 'value') else str(team.team_type),
                'num_players': len(team.players)
            }
            
            # Esporta i giocatori con tutti i dati
            for i, player in enumerate(team.players, 1):
                row_data[f'player{i}_licence'] = player.licence
                row_data[f'player{i}_first_name'] = player.first_name
                row_data[f'player{i}_last_name'] = player.last_name
                row_data[f'player{i}_country'] = player.country
                row_data[f'player{i}_category'] = player.category.value if hasattr(player.category, 'value') else str(player.category)
            
            data.append(row_data)
        
        df = pd.DataFrame(data)
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f"squadre_{timestamp}.xlsx"
        
        try:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Successo", f"File salvato:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()