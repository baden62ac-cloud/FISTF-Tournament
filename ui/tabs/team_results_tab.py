# ui/tabs/team_results_tab.py
"""
Tab per l'inserimento dei risultati delle partite a squadre per turno.
Interfaccia ottimizzata con maschera per turno, selezione giocatori e sostituzioni.
Regole FISTF per sostituzioni (Sezione 2.2.4):
- Max 2 sostituzioni per squadra
- A metà tempo, prima del sudden death, prima dello shoot-out
- Il subentrato eredita le sanzioni
- Le sostituzioni vengono tracciate con timestamp
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QComboBox, QSpinBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QDialogButtonBox,
                               QFrame, QScrollArea, QCheckBox, QGridLayout,
                               QLineEdit, QFormLayout, QSizePolicy, QTextEdit,
                               QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from collections import defaultdict
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path

from ui.base_tab import BaseTab
from models.match import MatchStatus


class IndividualMatchWidget(QWidget):
    """Widget per un singolo incontro individuale con selezione giocatori e sostituzioni."""
    
    result_changed = Signal(object, int, int, str, str)
    
    def __init__(self, match, individual_match, table_num: int, 
                 team1_players: List, team2_players: List,
                 team1_subs: List = None, team2_subs: List = None,
                 substitutions_used: Dict = None, parent=None):
        super().__init__(parent)
        self.match = match
        self.individual_match = individual_match
        self.table_num = table_num
        self.team1_players = team1_players.copy() if team1_players else []
        self.team2_players = team2_players.copy() if team2_players else []
        self.team1_subs = team1_subs.copy() if team1_subs else []
        self.team2_subs = team2_subs.copy() if team2_subs else []
        self.substitutions_used = substitutions_used or {"team1": 0, "team2": 0}
        self.substitution_log = []
        
        self.g1_spin = None
        self.g2_spin = None
        self.player1_combo = None
        self.player2_combo = None
        self.btn_sub1 = None
        self.btn_sub2 = None
        self.btn_notes = None
        
        if not hasattr(self.individual_match, 'notes'):
            self.individual_match.notes = ""
        
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(3)
        
        # Tavolo
        table_label = QLabel(f"🏓 T{self.table_num}")
        table_label.setFixedWidth(45)
        table_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(table_label)
        
        # Giocatore 1 (dropdown)
        self.player1_combo = QComboBox()
        self.player1_combo.setMinimumWidth(130)
        self._populate_player_combo(self.player1_combo, self.team1_players, self.team1_subs, "team1")
        if self.individual_match.player1 and self.individual_match.player1 != "":
            idx = self.player1_combo.findText(self.individual_match.player1)
            if idx >= 0:
                self.player1_combo.setCurrentIndex(idx)
        self.player1_combo.currentTextChanged.connect(self._on_player_changed)
        self.player1_combo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 3px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                min-width: 120px;
            }
        """)
        layout.addWidget(self.player1_combo)
        
        # Pulsante sostituzione squadra 1
        self.btn_sub1 = QPushButton("🔄")
        self.btn_sub1.setFixedSize(32, 32)
        self.btn_sub1.setToolTip("Sostituisci giocatore (max 2 per squadra)")
        self.btn_sub1.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_sub1.clicked.connect(lambda: self._request_substitution("team1"))
        layout.addWidget(self.btn_sub1)
        
        # Gol 1 con pulsanti +/-
        g1_container = self._create_score_widget("g1")
        layout.addWidget(g1_container)
        
        # Trattino
        dash_label = QLabel("-")
        dash_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(dash_label)
        
        # Gol 2 con pulsanti +/-
        g2_container = self._create_score_widget("g2")
        layout.addWidget(g2_container)
        
        # Pulsante sostituzione squadra 2
        self.btn_sub2 = QPushButton("🔄")
        self.btn_sub2.setFixedSize(32, 32)
        self.btn_sub2.setToolTip("Sostituisci giocatore (max 2 per squadra)")
        self.btn_sub2.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.btn_sub2.clicked.connect(lambda: self._request_substitution("team2"))
        layout.addWidget(self.btn_sub2)
        
        # Giocatore 2 (dropdown)
        self.player2_combo = QComboBox()
        self.player2_combo.setMinimumWidth(130)
        self._populate_player_combo(self.player2_combo, self.team2_players, self.team2_subs, "team2")
        if self.individual_match.player2 and self.individual_match.player2 != "":
            idx = self.player2_combo.findText(self.individual_match.player2)
            if idx >= 0:
                self.player2_combo.setCurrentIndex(idx)
        self.player2_combo.currentTextChanged.connect(self._on_player_changed)
        self.player2_combo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 3px;
                border: 2px solid #f44336;
                border-radius: 4px;
                min-width: 120px;
            }
        """)
        layout.addWidget(self.player2_combo)
        
        # Pulsante note
        self.btn_notes = QPushButton("📝")
        self.btn_notes.setFixedSize(32, 32)
        self.btn_notes.setToolTip("Visualizza/Modifica note")
        self.btn_notes.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        self.btn_notes.clicked.connect(self._show_notes_dialog)
        layout.addWidget(self.btn_notes)
        
        layout.addStretch()
        
        self._update_substitution_buttons()
    
    def _populate_player_combo(self, combo, starters, subs, team):
        combo.clear()
        combo.addItem("-- Seleziona --")
        
        for player in starters:
            combo.addItem(player.display_name, ("starter", player))
        
        for player in subs:
            combo.addItem(f"🔄 {player.display_name}", ("sub", player))
    
    def _show_notes_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Note - Tavolo {self.table_num}")
        dialog.setModal(True)
        dialog.resize(550, 400)
        
        layout = QVBoxLayout(dialog)
        
        info = QLabel(f"<b>{self.match.player1}</b> vs <b>{self.match.player2}</b><br>"
                      f"<b>Tavolo {self.table_num}</b>")
        info.setStyleSheet("padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
        layout.addWidget(info)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(self.individual_match.notes or "")
        text_edit.setPlaceholderText("Inserisci note per questo tavolo (sostituzioni, incidenti, ecc.)")
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Salva")
        btn_save.clicked.connect(lambda: self._save_notes(text_edit.toPlainText(), dialog))
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("✖ Annulla")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _save_notes(self, notes, dialog):
        self.individual_match.notes = notes
        dialog.accept()
        QMessageBox.information(self, "Successo", "✅ Note salvate!")
    
    def _request_substitution(self, team):
        current_player = ""
        available_subs = []
        
        if team == "team1":
            current_player = self.player1_combo.currentText()
            if current_player.startswith("🔄 "):
                current_player = current_player[2:]
            available_subs = [p for p in self.team1_subs if p.display_name != current_player]
            max_subs = 2
            subs_used = self.substitutions_used.get("team1", 0)
            team_name = "Squadra 1"
        else:
            current_player = self.player2_combo.currentText()
            if current_player.startswith("🔄 "):
                current_player = current_player[2:]
            available_subs = [p for p in self.team2_subs if p.display_name != current_player]
            max_subs = 2
            subs_used = self.substitutions_used.get("team2", 0)
            team_name = "Squadra 2"
        
        if current_player == "-- Seleziona --":
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un giocatore da sostituire")
            return
        
        if subs_used >= max_subs:
            QMessageBox.warning(self, "Sostituzioni esaurite", 
                               f"{team_name} ha già effettuato il massimo di {max_subs} sostituzioni.")
            return
        
        if not available_subs:
            QMessageBox.warning(self, "Nessun sostituto", 
                               "Non ci sono giocatori in panchina disponibili.\n"
                               "Aggiungi più giocatori alla squadra per avere sostituti.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sostituisci giocatore - Tavolo {self.table_num}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"🔄 SOSTITUZIONE - {team_name.upper()}"))
        layout.addWidget(QLabel(f"Tavolo: {self.table_num}"))
        layout.addWidget(QLabel(f"Giocatore uscente: {current_player}"))
        layout.addWidget(QLabel(f"Sostituzioni rimaste: {max_subs - subs_used}"))
        layout.addWidget(QLabel(" "))
        
        layout.addWidget(QLabel("Seleziona il giocatore entrante:"))
        
        sub_combo = QComboBox()
        for player in available_subs:
            sub_combo.addItem(player.display_name, player)
        layout.addWidget(sub_combo)
        
        layout.addWidget(QLabel("Motivo sostituzione (opzionale):"))
        note_edit = QLineEdit()
        note_edit.setPlaceholderText("Es: infortunio, tattica, ecc.")
        layout.addWidget(note_edit)
        
        note = QLabel("ℹ️ Il giocatore subentrato eredita le eventuali sanzioni del sostituito.")
        note.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(note)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            new_player = sub_combo.currentData()
            motivo = note_edit.text().strip()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if team == "team1":
                old_player = next((p for p in self.team1_players if p.display_name == current_player), None)
                if old_player and old_player in self.team1_players:
                    self.team1_players.remove(old_player)
                    self.team1_subs.append(old_player)
                
                if new_player in self.team1_subs:
                    self.team1_subs.remove(new_player)
                self.team1_players.append(new_player)
                
                self._populate_player_combo(self.player1_combo, self.team1_players, self.team1_subs, "team1")
                self.player1_combo.setCurrentText(new_player.display_name)
                
                self.substitutions_used["team1"] = subs_used + 1
                
                note_text = f"[{timestamp}] SOSTITUZIONE Squadra 1 - Tavolo {self.table_num}: {current_player} → {new_player.display_name}"
                if motivo:
                    note_text += f" ({motivo})"
                note_text += "\n"
                self.individual_match.notes = (self.individual_match.notes or "") + note_text
                
            else:
                old_player = next((p for p in self.team2_players if p.display_name == current_player), None)
                if old_player and old_player in self.team2_players:
                    self.team2_players.remove(old_player)
                    self.team2_subs.append(old_player)
                
                if new_player in self.team2_subs:
                    self.team2_subs.remove(new_player)
                self.team2_players.append(new_player)
                
                self._populate_player_combo(self.player2_combo, self.team2_players, self.team2_subs, "team2")
                self.player2_combo.setCurrentText(new_player.display_name)
                
                self.substitutions_used["team2"] = subs_used + 1
                
                note_text = f"[{timestamp}] SOSTITUZIONE Squadra 2 - Tavolo {self.table_num}: {current_player} → {new_player.display_name}"
                if motivo:
                    note_text += f" ({motivo})"
                note_text += "\n"
                self.individual_match.notes = (self.individual_match.notes or "") + note_text
            
            self._update_substitution_buttons()
            self._emit_result(
                self.g1_spin.value() if self.g1_spin else 0,
                self.g2_spin.value() if self.g2_spin else 0
            )
            
            QMessageBox.information(self, "Sostituzione effettuata", 
                                   f"✅ {current_player} sostituito da {new_player.display_name}\n"
                                   f"⏰ {timestamp}\n"
                                   f"{'Motivo: ' + motivo if motivo else ''}")
    
    def _update_substitution_buttons(self):
        if self.btn_sub1:
            subs_used = self.substitutions_used.get("team1", 0)
            self.btn_sub1.setEnabled(subs_used < 2 and len(self.team1_subs) > 0)
        if self.btn_sub2:
            subs_used = self.substitutions_used.get("team2", 0)
            self.btn_sub2.setEnabled(subs_used < 2 and len(self.team2_subs) > 0)
    
    def _create_score_widget(self, side: str) -> QWidget:
        container = QWidget()
        container.setFixedWidth(70)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(24, 28)
        btn_minus.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 4px 0 0 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        spin = QSpinBox()
        spin.setMinimum(0)
        spin.setMaximum(20)
        spin.setFixedSize(40, 28)
        spin.setAlignment(Qt.AlignCenter)
        spin.setButtonSymbols(QSpinBox.NoButtons)
        spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-left: none;
                border-right: none;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(24, 28)
        btn_plus.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 0 4px 4px 0;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        if side == "g1":
            btn_minus.clicked.connect(lambda: spin.setValue(max(0, spin.value() - 1)))
            btn_plus.clicked.connect(lambda: spin.setValue(spin.value() + 1))
            self.g1_spin = spin
        else:
            btn_minus.clicked.connect(lambda: spin.setValue(max(0, spin.value() - 1)))
            btn_plus.clicked.connect(lambda: spin.setValue(spin.value() + 1))
            self.g2_spin = spin
        
        if side == "g1" and self.individual_match.goals1 is not None:
            spin.setValue(self.individual_match.goals1)
        elif side == "g2" and self.individual_match.goals2 is not None:
            spin.setValue(self.individual_match.goals2)
        
        spin.valueChanged.connect(self._on_score_changed)
        
        layout.addWidget(btn_minus)
        layout.addWidget(spin)
        layout.addWidget(btn_plus)
        
        return container
    
    def _on_score_changed(self, value):
        g1 = self.g1_spin.value() if self.g1_spin else 0
        g2 = self.g2_spin.value() if self.g2_spin else 0
        self._emit_result(g1, g2)
    
    def _on_player_changed(self):
        g1 = self.g1_spin.value() if self.g1_spin else 0
        g2 = self.g2_spin.value() if self.g2_spin else 0
        self._emit_result(g1, g2)
    
    def _emit_result(self, g1, g2):
        player1 = self.player1_combo.currentText() if self.player1_combo else ""
        player2 = self.player2_combo.currentText() if self.player2_combo else ""
        
        if player1.startswith("🔄 "):
            player1 = player1[2:]
        if player2.startswith("🔄 "):
            player2 = player2[2:]
        
        if player1 == "-- Seleziona --" or player2 == "-- Seleziona --":
            self._update_display()
            return
        
        self.result_changed.emit(self.individual_match, g1, g2, player1, player2)
        self._update_display()
    
    def _update_display(self):
        g1 = self.g1_spin.value() if self.g1_spin else 0
        g2 = self.g2_spin.value() if self.g2_spin else 0
        player1 = self.player1_combo.currentText() if self.player1_combo else ""
        player2 = self.player2_combo.currentText() if self.player2_combo else ""
        
        if player1 == "-- Seleziona --" or player2 == "-- Seleziona --":
            self.setStyleSheet("background-color: #fff3e0; border-radius: 4px;")
        elif g1 == 0 and g2 == 0 and not self.individual_match.is_played:
            self.setStyleSheet("background-color: #f9f9f9; border-radius: 4px;")
        else:
            self.setStyleSheet("background-color: #e8f5e9; border-radius: 4px;")
    
    def get_result(self) -> Tuple[int, int, str, str]:
        g1 = self.g1_spin.value() if self.g1_spin else 0
        g2 = self.g2_spin.value() if self.g2_spin else 0
        player1 = self.player1_combo.currentText() if self.player1_combo else ""
        player2 = self.player2_combo.currentText() if self.player2_combo else ""
        if player1.startswith("🔄 "):
            player1 = player1[2:]
        if player2.startswith("🔄 "):
            player2 = player2[2:]
        return g1, g2, player1, player2
    
    def is_played(self) -> bool:
        g1, g2, p1, p2 = self.get_result()
        return (p1 != "-- Seleziona --" and p2 != "-- Seleziona --" and 
                (g1 > 0 or g2 > 0 or self.individual_match.status == MatchStatus.COMPLETED))
    
    def is_valid(self) -> bool:
        p1 = self.player1_combo.currentText() if self.player1_combo else ""
        p2 = self.player2_combo.currentText() if self.player2_combo else ""
        return p1 != "-- Seleziona --" and p2 != "-- Seleziona --"
    
    def get_substitutions_used(self) -> Dict:
        return self.substitutions_used


class TeamMatchWidget(QWidget):
    result_changed = Signal(object)
    
    def __init__(self, team_match, category: str, group: str, field_block: int,
                 team1_players: List, team2_players: List,
                 team1_subs: List = None, team2_subs: List = None, parent=None):
        super().__init__(parent)
        self.team_match = team_match
        self.category = category
        self.group = group
        self.field_block = field_block
        self.team1_players = team1_players.copy() if team1_players else []
        self.team2_players = team2_players.copy() if team2_players else []
        self.team1_subs = team1_subs.copy() if team1_subs else []
        self.team2_subs = team2_subs.copy() if team2_subs else []
        self.substitutions_used = {"team1": 0, "team2": 0}
        self.individual_widgets = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        header = QLabel(f"🏆 {self.team_match.player1} vs {self.team_match.player2}")
        header.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50; background-color: #ecf0f1; padding: 5px; border-radius: 4px;")
        header_layout.addWidget(header, 1)
        
        btn_notes = QPushButton("📝 Note Partita")
        btn_notes.setFixedSize(100, 32)
        btn_notes.setStyleSheet("background-color: #607D8B; color: white; font-size: 11px; border-radius: 6px;")
        btn_notes.clicked.connect(self._show_match_notes)
        header_layout.addWidget(btn_notes)
        layout.addLayout(header_layout)
        
        fields = [str(im.table) for im in self.team_match.individual_matches if im.table]
        fields_info = QLabel(f"🏟️ Campi: {', '.join(fields)}")
        fields_info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(fields_info)
        
        subs_info = QLabel(f"🔄 Sostituzioni: Squadra 1: 0/2 | Squadra 2: 0/2")
        subs_info.setStyleSheet("color: #FF9800; font-size: 9px;")
        layout.addWidget(subs_info)
        self.subs_info_label = subs_info
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #bdc3c7; max-height: 1px;")
        layout.addWidget(line)
        
        for i, im in enumerate(self.team_match.individual_matches):
            widget = IndividualMatchWidget(
                self.team_match, im, i+1, 
                self.team1_players, self.team2_players,
                self.team1_subs, self.team2_subs,
                self.substitutions_used
            )
            widget.result_changed.connect(self._on_individual_result_changed)
            self.individual_widgets.append(widget)
            layout.addWidget(widget)
        
        summary_layout = QHBoxLayout()
        self.result_label = QLabel("Risultato: vs")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px; background-color: #f8f9fa; border-radius: 4px;")
        self.result_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.result_label, 1)
        self.valid_label = QLabel("")
        self.valid_label.setStyleSheet("font-size: 10px;")
        summary_layout.addWidget(self.valid_label)
        layout.addLayout(summary_layout)
        
        self._update_result()
        self._update_subs_info()
    
    def _update_subs_info(self):
        subs1 = self.substitutions_used.get("team1", 0)
        subs2 = self.substitutions_used.get("team2", 0)
        self.subs_info_label.setText(f"🔄 Sostituzioni: Squadra 1: {subs1}/2 | Squadra 2: {subs2}/2")
    
    def _show_match_notes(self):
        all_notes = []
        all_notes.append(f"{'='*60}")
        all_notes.append(f"PARTITA: {self.team_match.player1} vs {self.team_match.player2}")
        all_notes.append(f"ID: {self.team_match.id}")
        all_notes.append(f"{'='*60}\n")
        
        wins1 = 0
        wins2 = 0
        for im in self.team_match.individual_matches:
            if im.goals1 is not None and im.goals2 is not None:
                if im.goals1 > im.goals2:
                    wins1 += 1
                elif im.goals2 > im.goals1:
                    wins2 += 1
        all_notes.append(f"📊 RISULTATO FINALE: {wins1} - {wins2}")
        all_notes.append("")
        
        for i, widget in enumerate(self.individual_widgets):
            all_notes.append(f"\n{'─'*50}")
            all_notes.append(f"🏓 TAVOLO {i+1}")
            all_notes.append(f"{'─'*50}")
            g1, g2, p1, p2 = widget.get_result()
            all_notes.append(f"Risultato: {g1} - {g2}")
            all_notes.append(f"Giocatori: {p1} vs {p2}")
            if hasattr(widget.individual_match, 'notes') and widget.individual_match.notes:
                all_notes.append("\n📝 NOTE:")
                all_notes.append(widget.individual_match.notes.strip())
            else:
                all_notes.append("(nessuna nota)")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Note Partita - {self.team_match.id}")
        dialog.setModal(True)
        dialog.resize(650, 500)
        
        layout = QVBoxLayout(dialog)
        
        header = QLabel(f"<b>📋 NOTE PARTITA</b><br>{self.team_match.player1} vs {self.team_match.player2}")
        header.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 6px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        text_edit = QTextEdit()
        text_edit.setPlainText("\n".join(all_notes))
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("📄 Esporta")
        btn_export.clicked.connect(lambda: self._export_notes("\n".join(all_notes)))
        btn_export.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_export)
        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _export_notes(self, notes_text):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"note_partita_{self.team_match.id}_{timestamp}.txt"
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Note",
            str(data_dir / default_filename),
            "File di testo (*.txt);;Tutti i file (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(notes_text)
                QMessageBox.information(self, "Successo", f"✅ Note esportate in:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione:\n{str(e)}")
    
    def _on_individual_result_changed(self, individual_match, g1, g2, p1, p2):
        individual_match.goals1 = g1
        individual_match.goals2 = g2
        individual_match.player1 = p1
        individual_match.player2 = p2
        
        if g1 == 0 and g2 == 0:
            individual_match.status = None
        else:
            individual_match.status = MatchStatus.COMPLETED
        
        self._update_result()
        self._update_subs_info()
        self.result_changed.emit(self.team_match)
    
    def _update_result(self):
        wins1 = 0
        wins2 = 0
        all_valid = True
        
        for widget in self.individual_widgets:
            if not widget.is_valid():
                all_valid = False
            g1, g2, p1, p2 = widget.get_result()
            if g1 > g2:
                wins1 += 1
            elif g2 > g1:
                wins2 += 1
        
        if all_valid:
            self.result_label.setText(f"Risultato: {wins1} - {wins2}")
            self.valid_label.setText("✅")
            self.valid_label.setStyleSheet("color: green; font-size: 10px;")
        else:
            self.result_label.setText("Risultato: --")
            self.valid_label.setText("⚠️ Seleziona tutti i giocatori")
            self.valid_label.setStyleSheet("color: orange; font-size: 10px;")
        
        if wins1 > wins2:
            self.result_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px; background-color: #e8f5e9; border-radius: 4px; color: #2e7d32;")
        elif wins2 > wins1:
            self.result_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px; background-color: #ffebee; border-radius: 4px; color: #c62828;")
        elif wins1 == wins2 and wins1 > 0:
            self.result_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px; background-color: #fff3e0; border-radius: 4px; color: #f57c00;")
        else:
            self.result_label.setStyleSheet("font-weight: bold; font-size: 11px; padding: 3px; background-color: #f8f9fa; border-radius: 4px;")
    
    def is_complete(self) -> bool:
        for widget in self.individual_widgets:
            if not widget.is_valid():
                return False
            g1, g2, _, _ = widget.get_result()
            if g1 == 0 and g2 == 0:
                return False
        return True
    
    def is_valid(self) -> bool:
        for widget in self.individual_widgets:
            if not widget.is_valid():
                return False
        return True
    
    def save(self):
        for widget in self.individual_widgets:
            g1, g2, p1, p2 = widget.get_result()
            im = widget.individual_match
            im.goals1 = g1
            im.goals2 = g2
            im.player1 = p1
            im.player2 = p2
            if g1 == 0 and g2 == 0:
                im.status = None
            else:
                im.status = MatchStatus.COMPLETED
        
        wins1 = 0
        wins2 = 0
        for im in self.team_match.individual_matches:
            if im.goals1 is not None and im.goals2 is not None:
                if im.goals1 > im.goals2:
                    wins1 += 1
                elif im.goals2 > im.goals1:
                    wins2 += 1
        
        if wins1 > wins2:
            self.team_match.winner = self.team_match.team1
        elif wins2 > wins1:
            self.team_match.winner = self.team_match.team2
        else:
            self.team_match.winner = None
        
        self.team_match.status = MatchStatus.COMPLETED if self.is_complete() else None


class GroupMatchesWidget(QWidget):
    def __init__(self, group_name: str, matches: List, category: str,
                 team_players_map: Dict, team_subs_map: Dict, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.matches = matches
        self.category = category
        self.team_players_map = team_players_map
        self.team_subs_map = team_subs_map
        self.match_widgets = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        header = QLabel(f"📌 GIRONE {self.group_name}")
        header.setStyleSheet("font-weight: bold; font-size: 12px; color: #2c3e50; background-color: #ecf0f1; padding: 5px 10px; border-radius: 4px;")
        layout.addWidget(header)
        
        matches_container = QWidget()
        matches_layout = QVBoxLayout(matches_container)
        matches_layout.setContentsMargins(20, 0, 0, 0)
        matches_layout.setSpacing(8)
        
        for match in self.matches:
            team1_players = self.team_players_map.get(match.team1, [])
            team2_players = self.team_players_map.get(match.team2, [])
            team1_subs = self.team_subs_map.get(match.team1, [])
            team2_subs = self.team_subs_map.get(match.team2, [])
            
            if hasattr(match, 'individual_matches') and match.individual_matches:
                first_field = match.individual_matches[0].table if match.individual_matches else 1
            else:
                first_field = match.field if match.field else 1
            
            widget = TeamMatchWidget(match, self.category, self.group_name, first_field,
                                     team1_players, team2_players,
                                     team1_subs, team2_subs)
            widget.result_changed.connect(self._on_match_result_changed)
            self.match_widgets.append(widget)
            matches_layout.addWidget(widget)
        
        layout.addWidget(matches_container)
    
    def _on_match_result_changed(self, team_match):
        pass
    
    def get_matches_status(self) -> Tuple[int, int]:
        complete = sum(1 for w in self.match_widgets if w.is_complete())
        return complete, len(self.match_widgets)
    
    def save_all(self):
        for widget in self.match_widgets:
            widget.save()


class CategoryMatchesWidget(QWidget):
    def __init__(self, category: str, groups: Dict[str, List], 
                 team_players_map: Dict, team_subs_map: Dict, parent=None):
        super().__init__(parent)
        self.category = category
        self.groups = groups
        self.team_players_map = team_players_map
        self.team_subs_map = team_subs_map
        self.group_widgets = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(12)
        
        display_name = self.category.replace("Team ", "")
        header = QLabel(f"🏆 {display_name.upper()}")
        header.setStyleSheet("font-weight: bold; font-size: 16px; color: #e67e22; padding: 8px; background-color: #fef5e8; border-radius: 6px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        for group_name, matches in self.groups.items():
            group_widget = GroupMatchesWidget(group_name, matches, self.category, 
                                              self.team_players_map, self.team_subs_map)
            self.group_widgets.append(group_widget)
            layout.addWidget(group_widget)
        
        layout.addSpacing(10)
    
    def get_stats(self) -> Tuple[int, int]:
        total_complete = 0
        total_matches = 0
        for gw in self.group_widgets:
            complete, total = gw.get_matches_status()
            total_complete += complete
            total_matches += total
        return total_complete, total_matches
    
    def save_all(self):
        for gw in self.group_widgets:
            gw.save_all()


class TeamResultsTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent, "⚽ Risultati Squadre per Turno")
        
        self.lbl_turn_info = None
        self.btn_prev = None
        self.btn_next = None
        self.btn_save = None
        self.progress_bar = None
        self.lbl_progress = None
        self.scroll_area = None
        self.content_widget = None
        self.content_layout_inner = None
        
        self.unique_times = []
        self.current_turn_index = 0
        self.turn_matches = {}
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        if self.content_layout is None:
            self.content_layout = QVBoxLayout(self)
            self.setLayout(self.content_layout)
        
        if not self.parent.current_tournament:
            label = QLabel("⚠️ Nessun torneo attivo. Vai nella tab Setup e crea un torneo.")
            label.setStyleSheet("color: orange; font-size: 16px; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(label)
            btn_setup = QPushButton("➡️ Vai a Setup")
            btn_setup.clicked.connect(lambda: self.parent.tabs.setCurrentIndex(0))
            btn_setup.setMaximumWidth(200)
            self.content_layout.addWidget(btn_setup, alignment=Qt.AlignCenter)
            self.content_layout.addStretch()
            return
        
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 10px;")
        nav_layout = QHBoxLayout(nav_frame)
        
        self.btn_prev = QPushButton("◀ Turno precedente")
        self.btn_prev.clicked.connect(self.prev_turn)
        self.btn_prev.setStyleSheet("background-color: #3498db; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        nav_layout.addWidget(self.btn_prev)
        
        turn_info_layout = QVBoxLayout()
        self.lbl_turn_info = QLabel("Turno 1/1 - 09:00")
        self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.lbl_turn_info.setAlignment(Qt.AlignCenter)
        turn_info_layout.addWidget(self.lbl_turn_info)
        nav_layout.addLayout(turn_info_layout)
        
        self.btn_next = QPushButton("Turno successivo ▶")
        self.btn_next.clicked.connect(self.next_turn)
        self.btn_next.setStyleSheet("background-color: #3498db; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        nav_layout.addWidget(self.btn_next)
        
        nav_layout.addStretch()
        self.btn_save = QPushButton("💾 Salva Tutto")
        self.btn_save.clicked.connect(self.save_current_turn)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        nav_layout.addWidget(self.btn_save)
        self.content_layout.addWidget(nav_frame)
        
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: #f9f9f9; border-radius: 6px; padding: 8px; margin-top: 10px;")
        progress_layout = QVBoxLayout(progress_frame)
        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("background-color: #ecf0f1; border-radius: 10px;")
        progress_layout.addWidget(self.progress_bar)
        self.lbl_progress = QLabel("0/0 incontri completati")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet("color: #2c3e50; font-weight: bold;")
        progress_layout.addWidget(self.lbl_progress)
        self.content_layout.addWidget(progress_frame)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background-color: white; border: none;")
        self.content_widget = QWidget()
        self.content_layout_inner = QVBoxLayout(self.content_widget)
        self.content_layout_inner.setSpacing(15)
        self.content_layout_inner.setContentsMargins(10, 10, 10, 10)
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout.addWidget(self.scroll_area)
    
    def _get_team_players_map(self) -> Dict:
        team_players = {}
        if hasattr(self.parent, 'teams'):
            for team in self.parent.teams:
                team_players[team.id] = team.players.copy()
        return team_players
    
    def _get_team_subs_map(self) -> Dict:
        team_subs = {}
        if hasattr(self.parent, 'teams'):
            for team in self.parent.teams:
                team_subs[team.id] = team.players.copy()
        return team_subs
    
    def refresh(self):
        if not self.parent.current_tournament or not hasattr(self.parent, 'matches'):
            return
        
        team_matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
        
        if not team_matches:
            self.lbl_turn_info.setText("Nessun incontro generato")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_save.setEnabled(False)
            return
        
        self.turn_matches = defaultdict(list)
        for match in team_matches:
            time = match.scheduled_time
            if time:
                self.turn_matches[time].append(match)
        
        self.unique_times = sorted(self.turn_matches.keys())
        
        if not self.unique_times:
            self.lbl_turn_info.setText("Nessun orario definito")
            return
        
        self.current_turn_index = 0
        self._update_turn_display()
    
    def _update_turn_display(self):
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        matches = self.turn_matches[current_time]
        
        self.lbl_turn_info.setText(f"📅 TURNO {self.current_turn_index + 1}/{len(self.unique_times)} - {current_time}")
        self.btn_prev.setEnabled(self.current_turn_index > 0)
        self.btn_next.setEnabled(self.current_turn_index < len(self.unique_times) - 1)
        
        self._clear_content()
        
        matches_by_category = defaultdict(lambda: defaultdict(list))
        for match in matches:
            category = match.category
            group = match.group or "?"
            matches_by_category[category][group].append(match)
        
        team_players_map = self._get_team_players_map()
        team_subs_map = self._get_team_subs_map()
        
        for category, groups in sorted(matches_by_category.items()):
            category_widget = CategoryMatchesWidget(category, groups, team_players_map, team_subs_map)
            self.content_layout_inner.addWidget(category_widget)
        
        self.content_layout_inner.addStretch()
        self._update_progress()
    
    def _clear_content(self):
        while self.content_layout_inner.count():
            item = self.content_layout_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _update_progress(self):
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        matches = self.turn_matches[current_time]
        
        total = len(matches)
        complete = 0
        for m in matches:
            all_played = True
            for im in m.individual_matches:
                if im.goals1 is None or im.goals2 is None:
                    all_played = False
                    break
            if all_played:
                complete += 1
        
        percent = (complete / total * 100) if total > 0 else 0
        self.lbl_progress.setText(f"📊 {complete}/{total} incontri completati ({percent:.0f}%)")
        
        bar_color = "#27ae60" if percent == 100 else "#f39c12" if percent > 0 else "#bdc3c7"
        self.progress_bar.setStyleSheet(f"""
            QFrame {{
                background-color: #ecf0f1;
                border-radius: 10px;
            }}
            QFrame::after {{
                content: "";
                display: block;
                width: {percent}%;
                height: 100%;
                background-color: {bar_color};
                border-radius: 10px;
            }}
        """)
        
        if complete == total and total > 0:
            self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
            self.lbl_progress.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
            self.lbl_progress.setStyleSheet("color: #2c3e50; font-weight: bold;")
    
    def prev_turn(self):
        if self.current_turn_index > 0:
            self.current_turn_index -= 1
            self._update_turn_display()
    
    def next_turn(self):
        if self.current_turn_index < len(self.unique_times) - 1:
            self.current_turn_index += 1
            self._update_turn_display()
    
    def save_current_turn(self):
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        self.parent.statusBar().showMessage(f"💾 Salvataggio risultati turno {current_time}...")
        
        if hasattr(self.parent, 'refresh_team_standings'):
            self.parent.refresh_team_standings()
        
        self._update_progress()
        self.parent.statusBar().showMessage(f"✅ Risultati turno {current_time} salvati", 3000)
        
        matches = self.turn_matches[current_time]
        complete = 0
        for m in matches:
            all_played = True
            for im in m.individual_matches:
                if im.goals1 is None or im.goals2 is None:
                    all_played = False
                    break
            if all_played:
                complete += 1
        
        if complete == len(matches):
            QMessageBox.information(self, "Turno Completato", 
                                   f"✅ Tutti i {len(matches)} incontri del turno {current_time} sono stati completati!")
    
    def on_tab_selected(self):
        self.refresh()