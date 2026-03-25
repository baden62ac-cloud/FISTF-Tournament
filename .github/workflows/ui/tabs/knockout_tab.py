# ui/tabs/knockout_tab.py
"""
Tab per la fase finale (eliminazione diretta) - Torneo individuale.
FISTF: Nelle partite a eliminazione diretta non sono ammessi pareggi.
In caso di pareggio → Sudden Death (10 min, primo gol vince) → Shoot-out

REGOLA FISTF PER I TOKEN:
- I qualificati dai gironi sono identificati come: "1A" (girone 1, primo), "1B" (girone 1, secondo)
- I vincitori delle partite di fase finale sono identificati come:
  - "WIN B1", "WIN B2", ... per gli spareggi (BARRAGE)
  - "WIN QF1", "WIN QF2", ... per i quarti di finale
  - "WIN SF1", "WIN SF2", ... per le semifinali
  - "WIN F1" per la finale
"""
import re
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QComboBox, QSpinBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QDialogButtonBox,
                               QFrame, QScrollArea, QCheckBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from datetime import datetime
from collections import defaultdict

from ui.base_tab import BaseTab
from models.match import MatchStatus
from core.knockout_generator import KnockoutGenerator, get_qualifiers_per_group
from core.standings_calculator import StandingsCalculator


class KnockoutTab(BaseTab):
    """Tab per la fase finale individuale."""
    
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
    
    def __init__(self, parent):
        super().__init__(parent, "🏆 Fase Finale")
        
        # Riferimenti UI
        self.knockout_category = None
        self.knockout_filter = None
        self.knockout_table = None
        self.knockout_phase = None
        self.knockout_match = None
        self.knockout_goals1 = None
        self.knockout_goals2 = None
        self.lbl_stats = None
        self.btn_generate_knockout = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        if not self.parent.current_tournament:
            label = QLabel("⚠️ Nessun torneo attivo")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; color: #f39c12; margin: 50px;")
            self.content_layout.addWidget(label)
            return
        
        # ========================================
        # PANNELLO GENERAZIONE
        # ========================================
        controls_group = QGroupBox("Generazione Tabellone")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #3498db;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Categoria:"))
        self.knockout_category = QComboBox()
        self.knockout_category.setMinimumWidth(150)
        for cat in self.parent.current_tournament.categories:
            if "Team" not in cat.value:
                self.knockout_category.addItem(cat.value)
        self.knockout_category.currentTextChanged.connect(self.update_button_state)
        controls_layout.addWidget(self.knockout_category)
        
        self.btn_generate_knockout = QPushButton("🎲 Genera Fase Finale")
        self.btn_generate_knockout.clicked.connect(self.generate_knockout_stage)
        self.btn_generate_knockout.setMinimumWidth(200)
        self.btn_generate_knockout.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        controls_layout.addWidget(self.btn_generate_knockout)
        
        controls_layout.addStretch()
        self.content_layout.addWidget(controls_group)
        
        # ========================================
        # PANNELLO FILTRO
        # ========================================
        filter_group = QGroupBox("Filtra Visualizzazione")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Mostra categoria:"))
        self.knockout_filter = QComboBox()
        self.knockout_filter.addItem("Tutte")
        for cat in self.parent.current_tournament.categories:
            if "Team" not in cat.value:
                self.knockout_filter.addItem(cat.value)
        self.knockout_filter.currentTextChanged.connect(self.refresh)
        filter_layout.addWidget(self.knockout_filter)
        
        filter_layout.addStretch()
        
        btn_debug = QPushButton("🔍 Debug Token")
        btn_debug.clicked.connect(self.debug_tokens)
        btn_debug.setStyleSheet("background-color: #607D8B; color: white; padding: 5px 15px;")
        filter_layout.addWidget(btn_debug)
        
        self.content_layout.addWidget(filter_group)
        
        # ========================================
        # TABELLA FASE FINALE
        # ========================================
        self.knockout_table = QTableWidget()
        self.knockout_table.setColumnCount(6)
        self.knockout_table.setHorizontalHeaderLabels([
            "Fase", "Partita", "Giocatore 1", "Risultato", "Giocatore 2", "Stato"
        ])
        
        self.knockout_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.knockout_table.cellDoubleClicked.connect(self.on_match_double_clicked)
        
        header = self.knockout_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.knockout_table)
        
        # ========================================
        # PANNELLO INSERIMENTO RAPIDO
        # ========================================
        quick_group = QGroupBox("Inserimento Risultati")
        quick_layout = QHBoxLayout(quick_group)
        
        quick_layout.addWidget(QLabel("Fase:"))
        self.knockout_phase = QComboBox()
        self.knockout_phase.addItems(["BARRAGE", "QF", "SF", "F"])
        self.knockout_phase.currentTextChanged.connect(self.update_match_list)
        quick_layout.addWidget(self.knockout_phase)
        
        quick_layout.addWidget(QLabel("Partita:"))
        self.knockout_match = QComboBox()
        self.knockout_match.setMinimumWidth(300)
        quick_layout.addWidget(self.knockout_match)
        
        quick_layout.addWidget(QLabel("Risultato:"))
        
        self.knockout_goals1 = QSpinBox()
        self.knockout_goals1.setMinimum(0)
        self.knockout_goals1.setMaximum(20)
        self.knockout_goals1.setFixedWidth(90)
        self.knockout_goals1.setAlignment(Qt.AlignCenter)
        self.knockout_goals1.setStyleSheet("""
            QSpinBox {
                font-size: 12px;
                font-weight: bold;
                background-color: white;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        quick_layout.addWidget(self.knockout_goals1)
        
        quick_layout.addWidget(QLabel("-"))
        
        self.knockout_goals2 = QSpinBox()
        self.knockout_goals2.setMinimum(0)
        self.knockout_goals2.setMaximum(20)
        self.knockout_goals2.setFixedWidth(90)
        self.knockout_goals2.setAlignment(Qt.AlignCenter)
        self.knockout_goals2.setStyleSheet("""
            QSpinBox {
                font-size: 12px;
                font-weight: bold;
                background-color: white;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        quick_layout.addWidget(self.knockout_goals2)
        
        btn_save = QPushButton("💾 Salva")
        btn_save.clicked.connect(self.save_knockout_result)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        quick_layout.addWidget(btn_save)
        
        btn_clear = QPushButton("🗑️ Cancella")
        btn_clear.clicked.connect(self.clear_knockout_result)
        btn_clear.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        quick_layout.addWidget(btn_clear)
        
        quick_layout.addStretch()
        self.content_layout.addWidget(quick_group)
        
        # ========================================
        # STATISTICHE
        # ========================================
        stats_layout = QHBoxLayout()
        
        self.lbl_stats = QLabel("Partite fase finale: 0 | Giocate: 0")
        self.lbl_stats.setStyleSheet("font-size: 11pt; padding: 5px;")
        stats_layout.addWidget(self.lbl_stats)
        
        stats_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self.refresh)
        btn_refresh.setStyleSheet("background-color: #6c757d; color: white; padding: 5px 15px;")
        stats_layout.addWidget(btn_refresh)
        
        self.content_layout.addLayout(stats_layout)
        
        # Aggiorna stato iniziale
        self.update_button_state()
    
    def refresh(self):
        """Aggiorna la tabella della fase finale."""
        self.knockout_table.setRowCount(0)
        
        # Filtra partite knockout individuali
        filter_cat = self.knockout_filter.currentText()
        
        knockout_matches = [m for m in self.parent.matches 
                           if not hasattr(m, 'individual_matches')
                           and m.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]]
        
        if filter_cat != "Tutte":
            knockout_matches = [m for m in knockout_matches if m.category == filter_cat]
        
        # Ordina per fase
        phase_order = {"BARRAGE": 0, "R64": 1, "R32": 2, "R16": 3, "QF": 4, "SF": 5, "F": 6}
        knockout_matches.sort(key=lambda m: (phase_order.get(m.phase, 99), m.id))
        
        # Contatori
        played_count = 0
        
        phase_display = {
            "BARRAGE": "Spareggio",
            "QF": "Quarti",
            "SF": "Semifinale",
            "F": "Finale",
            "R16": "16° di Finale",
            "R32": "32° di Finale",
            "R64": "64° di Finale"
        }
        
        for row, match in enumerate(knockout_matches):
            self.knockout_table.insertRow(row)
            
            # Fase
            phase_item = QTableWidgetItem(phase_display.get(match.phase, match.phase))
            phase_item.setTextAlignment(Qt.AlignCenter)
            self.knockout_table.setItem(row, 0, phase_item)
            
            # ID partita
            display_id = match.id.split('_', 1)[1] if '_' in match.id else match.id
            id_item = QTableWidgetItem(display_id)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.knockout_table.setItem(row, 1, id_item)
            
            # Giocatore 1
            player1_display = match.player1
            if match.player1 and match.player1.startswith("WIN "):
                player1_display = f"⚡ {match.player1}"
            self.knockout_table.setItem(row, 2, QTableWidgetItem(player1_display))
            
            # Risultato
            result_text = match.result if match.is_played else "vs"
            result_item = QTableWidgetItem(result_text)
            result_item.setFlags(result_item.flags() | Qt.ItemIsEditable)
            self.knockout_table.setItem(row, 3, result_item)
            
            # Giocatore 2
            player2_display = match.player2
            if match.player2 and match.player2.startswith("WIN "):
                player2_display = f"⚡ {match.player2}"
            self.knockout_table.setItem(row, 4, QTableWidgetItem(player2_display))
            
            # Stato
            status_text = match.status.value if hasattr(match.status, 'value') else str(match.status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            if match.is_played:
                status_item.setBackground(QColor(144, 238, 144))
                played_count += 1
            elif "SCHEDULED" in status_text:
                status_item.setBackground(QColor(211, 211, 211))
            
            self.knockout_table.setItem(row, 5, status_item)
        
        # Aggiorna statistiche
        total = len(knockout_matches)
        self.lbl_stats.setText(f"Partite fase finale: {total} | Giocate: {played_count}")
        
        self.update_match_list()
    
    def update_button_state(self):
        """Aggiorna lo stato del pulsante Genera Fase Finale."""
        if not hasattr(self, 'btn_generate_knockout'):
            return
        
        category = self.knockout_category.currentText()
        
        if not category:
            self.btn_generate_knockout.setEnabled(False)
            return
        
        # Trova partite dei gironi per questa categoria
        group_matches = [m for m in self.parent.matches 
                        if not hasattr(m, 'individual_matches')
                        and m.phase == "Groups" 
                        and m.category == category]
        
        if not group_matches:
            self.btn_generate_knockout.setEnabled(False)
            self.btn_generate_knockout.setToolTip("❌ Nessuna partita nei gironi")
            return
        
        total = len(group_matches)
        played = sum(1 for m in group_matches if m.is_played)
        
        if played == total:
            self.btn_generate_knockout.setEnabled(True)
            self.btn_generate_knockout.setToolTip("✅ Tutti i gironi completati")
        else:
            self.btn_generate_knockout.setEnabled(False)
            self.btn_generate_knockout.setToolTip(f"⏳ Completate {played}/{total} partite")
    
    def update_match_list(self):
        """Aggiorna la lista delle partite per fase."""
        self.knockout_match.clear()
        
        phase = self.knockout_phase.currentText()
        filter_cat = self.knockout_filter.currentText()
        
        count = 0
        for match in self.parent.matches:
            if (not hasattr(match, 'individual_matches') and
                match.phase == phase and 
                not match.is_played):
                
                if filter_cat == "Tutte" or match.category == filter_cat:
                    display_text = f"{match.id} - {match.player1} vs {match.player2}"
                    self.knockout_match.addItem(display_text, match.id)
                    count += 1
        
        if count == 0:
            self.knockout_match.addItem("Nessuna partita disponibile")
    
    def on_match_double_clicked(self, row, col):
        """Gestisce doppio clic sulla partita per inserire risultato dettagliato."""
        match_id_item = self.knockout_table.item(row, 1)
        if not match_id_item:
            return
        
        match_id = match_id_item.text()
        
        # Trova la partita
        match = None
        for m in self.parent.matches:
            if m.id == match_id and not hasattr(m, 'individual_matches'):
                match = m
                break
        
        if match:
            self.show_match_editor(match)
    
    def show_match_editor(self, match):
        """Mostra editor per la partita (con gestione pareggio)."""
        if match.is_played:
            QMessageBox.information(self, "Info", "Questa partita è già stata giocata!")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Inserisci Risultato - {match.id}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Info
        info = QLabel(f"<b>{match.player1}</b> vs <b>{match.player2}</b>")
        info.setStyleSheet("font-size: 16px; padding: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # Input risultati
        result_layout = QHBoxLayout()
        result_layout.addStretch()
        
        g1_spin = QSpinBox()
        g1_spin.setMinimum(0)
        g1_spin.setMaximum(20)
        g1_spin.setFixedWidth(80)
        g1_spin.setAlignment(Qt.AlignCenter)
        g1_spin.setStyleSheet("font-size: 18px; font-weight: bold;")
        result_layout.addWidget(g1_spin)
        
        dash = QLabel("-")
        dash.setStyleSheet("font-size: 18px; font-weight: bold;")
        result_layout.addWidget(dash)
        
        g2_spin = QSpinBox()
        g2_spin.setMinimum(0)
        g2_spin.setMaximum(20)
        g2_spin.setFixedWidth(80)
        g2_spin.setAlignment(Qt.AlignCenter)
        g2_spin.setStyleSheet("font-size: 18px; font-weight: bold;")
        result_layout.addWidget(g2_spin)
        
        result_layout.addStretch()
        layout.addLayout(result_layout)
        
        # Avviso pareggio
        warning_label = QLabel("⚠️ In caso di pareggio si procederà con Sudden Death e Shoot-out")
        warning_label.setStyleSheet("color: #f39c12; font-size: 11px; padding: 5px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        # Bottoni
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        g1 = g1_spin.value()
        g2 = g2_spin.value()
        
        if g1 == g2:
            # PAREGGIO → Avvia Sudden Death
            reply = QMessageBox.question(self, "Pareggio",
                f"La partita è finita in parità {g1}-{g2}.\n\n"
                "⚡ Si procede con SUDDEN DEATH (10 minuti, primo gol vince).\n\n"
                "Procedere?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.No:
                return
            
            self.show_sudden_death(match)
        else:
            # Risultato normale
            match.goals1 = g1
            match.goals2 = g2
            match.winner = match.player1 if g1 > g2 else match.player2
            match.status = MatchStatus.COMPLETED
            
            # Propaga vincitore (solo nella stessa categoria)
            self.propagate_winner(match)
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Risultato salvato: {g1}-{g2}\nVincitore: {match.winner}")
        
        self.refresh()
    
    def show_sudden_death(self, match):
        """
        Gestisce sudden death per partite individuali.
        Primo gol vince.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sudden Death - {match.id}")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"⚽ SUDDEN DEATH - 10 MINUTI ⚽")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            background-color: #ff9800;
            color: white;
            padding: 15px;
            border-radius: 10px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Giocatori
        players_frame = QFrame()
        players_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 15px;")
        players_layout = QHBoxLayout(players_frame)
        
        # Giocatore 1
        p1_box = QFrame()
        p1_box.setStyleSheet("background-color: #e3f2fd; border-radius: 8px; padding: 10px;")
        p1_layout = QVBoxLayout(p1_box)
        p1_name = QLabel(match.player1)
        p1_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        p1_name.setAlignment(Qt.AlignCenter)
        p1_gol = QLabel("0")
        p1_gol.setStyleSheet("font-size: 48px; font-weight: bold; color: #1976D2;")
        p1_gol.setAlignment(Qt.AlignCenter)
        p1_layout.addWidget(p1_name)
        p1_layout.addWidget(p1_gol)
        
        # VS
        vs_label = QLabel("VS")
        vs_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 0 20px;")
        
        # Giocatore 2
        p2_box = QFrame()
        p2_box.setStyleSheet("background-color: #ffebee; border-radius: 8px; padding: 10px;")
        p2_layout = QVBoxLayout(p2_box)
        p2_name = QLabel(match.player2)
        p2_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
        p2_name.setAlignment(Qt.AlignCenter)
        p2_gol = QLabel("0")
        p2_gol.setStyleSheet("font-size: 48px; font-weight: bold; color: #d32f2f;")
        p2_gol.setAlignment(Qt.AlignCenter)
        p2_layout.addWidget(p2_name)
        p2_layout.addWidget(p2_gol)
        
        players_layout.addWidget(p1_box)
        players_layout.addWidget(vs_label)
        players_layout.addWidget(p2_box)
        layout.addWidget(players_frame)
        
        # Timer
        timer_frame = QFrame()
        timer_frame.setStyleSheet("background-color: #2c3e50; border-radius: 12px; padding: 10px;")
        timer_layout = QVBoxLayout(timer_frame)
        
        timer_label = QLabel("10:00")
        timer_label.setStyleSheet("""
            font-size: 72px;
            font-weight: bold;
            font-family: monospace;
            color: white;
            background-color: #1a2632;
            border-radius: 12px;
            padding: 20px;
        """)
        timer_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(timer_label)
        
        rule_label = QLabel("⚡ Il primo gol vince la partita! ⚡")
        rule_label.setStyleSheet("font-size: 14px; color: #ffaa66;")
        rule_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(rule_label)
        
        layout.addWidget(timer_frame)
        
        # Pulsanti gol
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(30)
        
        btn_p1 = QPushButton(f"⚽ GOAL\n{match.player1[:20]}")
        btn_p1.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        btn_p2 = QPushButton(f"⚽ GOAL\n{match.player2[:20]}")
        btn_p2.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        buttons_layout.addWidget(btn_p1)
        buttons_layout.addWidget(btn_p2)
        layout.addWidget(buttons_frame)
        
        # Log
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 6px; border: 1px solid #dee2e6;")
        log_layout = QVBoxLayout(log_frame)
        
        log_title = QLabel("📋 Cronologia:")
        log_title.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_title)
        
        log_text = QLabel("In attesa del primo gol...")
        log_text.setStyleSheet("font-family: monospace; font-size: 11px; color: #6c757d;")
        log_text.setWordWrap(True)
        log_layout.addWidget(log_text)
        
        layout.addWidget(log_frame)
        
        # Bottone forzatura shoot-out
        btn_force = QPushButton("🎯 Forza Shoot-out")
        btn_force.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                padding: 10px;
                border-radius: 6px;
            }
        """)
        layout.addWidget(btn_force)
        
        # Variabili di stato
        remaining = 600  # 10 minuti in secondi
        match_ended = False
        events = []
        
        def update_timer():
            nonlocal remaining, match_ended
            
            if match_ended:
                return
            
            if remaining <= 0:
                timer.stop()
                dialog.accept()
                self.show_penalty_shootout(match)
                return
            
            remaining -= 1
            mins = remaining // 60
            secs = remaining % 60
            timer_label.setText(f"{mins:02d}:{secs:02d}")
        
        def add_goal(player):
            nonlocal match_ended, events
            
            if match_ended:
                return
            
            now = datetime.now().strftime("%H:%M:%S")
            match_ended = True
            timer.stop()
            
            if player == 1:
                p1_gol.setText("1")
                match.winner = match.player1
                events.append(f"[{now}] ⚽ GOL! {match.player1} segna e vince!")
                p1_box.setStyleSheet("background-color: #c8e6c9; border-radius: 8px; padding: 10px;")
            else:
                p2_gol.setText("1")
                match.winner = match.player2
                events.append(f"[{now}] ⚽ GOL! {match.player2} segna e vince!")
                p2_box.setStyleSheet("background-color: #c8e6c9; border-radius: 8px; padding: 10px;")
            
            log_text.setText("\n".join(events[-5:]))
            
            match.goals1 = 1 if player == 1 else 0
            match.goals2 = 1 if player == 2 else 0
            match.status = MatchStatus.COMPLETED
            
            QMessageBox.information(dialog, "PARTITA TERMINATA",
                                   f"🏆 GOL! {match.winner} vince il sudden death!")
            
            dialog.accept()
        
        def force_shootout():
            nonlocal match_ended
            match_ended = True
            timer.stop()
            dialog.accept()
            self.show_penalty_shootout(match)
        
        btn_p1.clicked.connect(lambda: add_goal(1))
        btn_p2.clicked.connect(lambda: add_goal(2))
        btn_force.clicked.connect(force_shootout)
        
        # Avvia timer
        timer = QTimer()
        timer.timeout.connect(update_timer)
        timer.start(1000)
        
        dialog.exec()
        
        if timer.isActive():
            timer.stop()
        
        # Propaga vincitore (solo nella stessa categoria)
        if match.winner:
            self.propagate_winner(match)
        
        self.refresh()
    
    def show_penalty_shootout(self, match):
        """
        Gestisce lo shoot-out per partite individuali.
        Tiri di rigore alternati.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Shoot-out - {match.id}")
        dialog.setModal(True)
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"⚽ SHOOT-OUT ⚽")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            background-color: #9c27b0;
            color: white;
            padding: 15px;
            border-radius: 10px;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Giocatori
        players_frame = QFrame()
        players_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 15px;")
        players_layout = QHBoxLayout(players_frame)
        
        # Giocatore 1
        p1_box = QFrame()
        p1_box.setStyleSheet("background-color: #e3f2fd; border-radius: 8px; padding: 10px;")
        p1_layout = QVBoxLayout(p1_box)
        p1_name = QLabel(match.player1)
        p1_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        p1_name.setAlignment(Qt.AlignCenter)
        p1_score = QLabel("0")
        p1_score.setStyleSheet("font-size: 36px; font-weight: bold; color: #1976D2;")
        p1_score.setAlignment(Qt.AlignCenter)
        p1_layout.addWidget(p1_name)
        p1_layout.addWidget(p1_score)
        
        # VS
        vs_label = QLabel("VS")
        vs_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 0 20px;")
        
        # Giocatore 2
        p2_box = QFrame()
        p2_box.setStyleSheet("background-color: #ffebee; border-radius: 8px; padding: 10px;")
        p2_layout = QVBoxLayout(p2_box)
        p2_name = QLabel(match.player2)
        p2_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
        p2_name.setAlignment(Qt.AlignCenter)
        p2_score = QLabel("0")
        p2_score.setStyleSheet("font-size: 36px; font-weight: bold; color: #d32f2f;")
        p2_score.setAlignment(Qt.AlignCenter)
        p2_layout.addWidget(p2_name)
        p2_layout.addWidget(p2_score)
        
        players_layout.addWidget(p1_box)
        players_layout.addWidget(vs_label)
        players_layout.addWidget(p2_box)
        layout.addWidget(players_frame)
        
        # Info
        info_label = QLabel("Tiri di rigore alternati.\nSegna chi fa più gol. Se necessario, si procede a morte improvvisa.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        layout.addWidget(info_label)
        
        # Tabella tiri
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Tiro", "Giocatore", "Risultato", ""])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        for i in range(20):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            table.setItem(i, 1, QTableWidgetItem(""))
            table.setItem(i, 2, QTableWidgetItem("⬜"))
            table.setItem(i, 3, QTableWidgetItem(""))
            table.item(i, 0).setTextAlignment(Qt.AlignCenter)
            table.item(i, 2).setTextAlignment(Qt.AlignCenter)
        
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 200)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(3, 0)  # colonna nascosta
        layout.addWidget(table)
        
        # Stato corrente
        current_label = QLabel("🎯 Inizio shoot-out")
        current_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            background-color: #fff3e0;
            border-radius: 6px;
            color: #ff9800;
        """)
        current_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_label)
        
        # Pulsanti
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(20)
        
        btn_goal = QPushButton("⚽ GOAL")
        btn_goal.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_goal.setEnabled(False)
        
        btn_miss = QPushButton("❌ SBAGLIA")
        btn_miss.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        btn_miss.setEnabled(False)
        
        buttons_layout.addWidget(btn_goal)
        buttons_layout.addWidget(btn_miss)
        layout.addWidget(buttons_frame)
        
        # Bottone inizio
        btn_start = QPushButton("▶ Inizia Shoot-out")
        btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(btn_start)
        
        # Logica
        kicks1 = []  # Lista di bool per gol giocatore 1
        kicks2 = []  # Lista di bool per gol giocatore 2
        current_kick = 0
        game_over = False
        
        def update_display():
            """Aggiorna tabella e punteggi"""
            total1 = sum(kicks1)
            total2 = sum(kicks2)
            p1_score.setText(str(total1))
            p2_score.setText(str(total2))
            
            for i in range(len(kicks1)):
                table.setItem(i, 1, QTableWidgetItem(match.player1))
                table.setItem(i, 2, QTableWidgetItem("✓" if kicks1[i] else "✗"))
                table.item(i, 2).setForeground(Qt.darkGreen if kicks1[i] else Qt.darkRed)
            
            for i in range(len(kicks2)):
                table.setItem(i, 1, QTableWidgetItem(match.player2))
                table.setItem(i, 2, QTableWidgetItem("✓" if kicks2[i] else "✗"))
                table.item(i, 2).setForeground(Qt.darkGreen if kicks2[i] else Qt.darkRed)
            
            # Evidenzia riga corrente
            for i in range(table.rowCount()):
                item = table.item(i, 1)
                if item:
                    if i == current_kick and not game_over:
                        item.setBackground(QColor(255, 255, 200))
                    else:
                        item.setBackground(QColor(255, 255, 255))
        
        def process_kick(goal):
            nonlocal current_kick, game_over
            
            if game_over:
                return
            
            # Determina chi tira
            if len(kicks1) <= len(kicks2):
                kicks1.append(goal)
                current_label.setText(f"🎯 {match.player1} - {'GOAL!' if goal else 'SBAGLIA!'}")
            else:
                kicks2.append(goal)
                current_label.setText(f"🎯 {match.player2} - {'GOAL!' if goal else 'SBAGLIA!'}")
            
            update_display()
            current_kick = len(kicks1) + len(kicks2)
            
            # Verifica vincitore (morte improvvisa)
            if len(kicks1) > 0 and len(kicks2) > 0:
                last1 = kicks1[-1] if kicks1 else False
                last2 = kicks2[-1] if kicks2 else False
                
                if last1 and not last2:
                    game_over = True
                    match.winner = match.player1
                elif not last1 and last2:
                    game_over = True
                    match.winner = match.player2
            
            if game_over:
                # Calcola risultato
                total1 = sum(kicks1)
                total2 = sum(kicks2)
                match.goals1 = total1
                match.goals2 = total2
                match.status = MatchStatus.COMPLETED
                
                QMessageBox.information(dialog, "PARTITA TERMINATA",
                                       f"🏆 {match.winner} vince lo shoot-out!\n\n"
                                       f"Risultato: {total1}-{total2}")
                
                dialog.accept()
                return
            
            # Prossimo tiro
            next_player = match.player1 if len(kicks1) <= len(kicks2) else match.player2
            current_label.setText(f"🎯 Prossimo tiro: {next_player}")
        
        def start_shootout():
            btn_start.setEnabled(False)
            btn_goal.setEnabled(True)
            btn_miss.setEnabled(True)
            current_label.setText(f"🎯 Primo tiro: {match.player1}")
        
        btn_start.clicked.connect(start_shootout)
        btn_goal.clicked.connect(lambda: process_kick(True))
        btn_miss.clicked.connect(lambda: process_kick(False))
        
        dialog.exec()
        
        # Propaga vincitore (solo nella stessa categoria)
        if match.winner:
            self.propagate_winner(match)
        
        self.refresh()
    
    def propagate_winner(self, match):
        """
        Propaga il vincitore alle partite successive della STESSA categoria.
        Formato token: "WIN B1", "WIN QF1", "WIN SF1", "WIN F1"
        """
        # Estrai il numero della partita dall'ID
        match_id = match.id
        
        # Cerca il numero alla fine (es. "QF_1" -> 1, "SF_2" -> 2)
        match_num = 1
        num_match = re.search(r'_(\d+)$', match_id)
        if num_match:
            match_num = int(num_match.group(1))
        
        # Ottieni il prefisso per questa fase
        phase_prefix = self.PHASE_TOKEN_PREFIX.get(match.phase, match.phase)
        
        # Genera token nel formato esatto del generator
        token = f"WIN {phase_prefix}{match_num}"
        
        print(f"\n   🔄 PROPAGAZIONE VINCITORE:")
        print(f"      Partita: {match.id} (fase: {match.phase}, numero: {match_num})")
        print(f"      Vincitore: {match.winner}")
        print(f"      Token generato: {token}")
        
        # Propaga solo alle partite della stessa categoria
        updated = 0
        for m in self.parent.matches:
            if (not hasattr(m, 'individual_matches') and 
                m.category == match.category):
                
                # Controlla player1
                if m.player1 == token:
                    old = m.player1
                    m.player1 = match.winner
                    if hasattr(m, 'token1'):
                        m.token1 = match.winner
                    updated += 1
                    print(f"      ✅ {m.id}: player1 aggiornato da '{old}' a '{match.winner}'")
                
                # Controlla player2
                if m.player2 == token:
                    old = m.player2
                    m.player2 = match.winner
                    if hasattr(m, 'token2'):
                        m.token2 = match.winner
                    updated += 1
                    print(f"      ✅ {m.id}: player2 aggiornato da '{old}' a '{match.winner}'")
        
        if updated == 0:
            print(f"      ⚠️ NESSUN MATCH TROVATO con token '{token}'")
            print(f"      Partite nella categoria {match.category} che contengono token:")
            for m in self.parent.matches:
                if (not hasattr(m, 'individual_matches') and 
                    m.category == match.category):
                    if "WIN" in str(m.player1) or "WIN" in str(m.player2):
                        print(f"         {m.id}: player1='{m.player1}', player2='{m.player2}'")
    
    def generate_knockout_stage(self):
        """Genera il tabellone della fase finale."""
        cat = self.knockout_category.currentText()
        
        groups_key = f"groups_{cat}"
        if groups_key not in self.parent.groups:
            QMessageBox.warning(self, "Attenzione", f"Nessun girone per la categoria {cat}")
            return
        
        # Verifica partite giocate
        group_matches = [m for m in self.parent.matches 
                        if not hasattr(m, 'individual_matches')
                        and m.category == cat 
                        and m.phase == "Groups"]
        
        played = sum(1 for m in group_matches if m.is_played)
        total = len(group_matches)
        
        if played < total:
            reply = QMessageBox.question(self, "Conferma",
                f"Solo {played}/{total} partite giocate nei gironi.\nGenerare comunque la fase finale?",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Calcola classifiche
        calculator = StandingsCalculator()
        group_standings = {}
        
        group_number = 1
        for group_name in sorted(self.parent.groups[groups_key].keys()):
            players = self.parent.groups[groups_key][group_name]
            df = calculator.calculate_group_standings(group_name, players, self.parent.matches)
            
            if not df.empty:
                group_players = []
                for _, row in df.iterrows():
                    player = next((p for p in players if p.display_name == row["Giocatore"]), None)
                    if player:
                        group_players.append(player)
                
                if group_players:
                    group_standings[str(group_number)] = group_players
                    group_number += 1
        
        if not group_standings:
            QMessageBox.warning(self, "Errore", "Impossibile calcolare classifiche")
            return
        
        # Determina qualificati
        group_sizes = [len(players) for players in self.parent.groups[groups_key].values()]
        qualifiers_per_group = get_qualifiers_per_group(group_sizes)
        
        generator = KnockoutGenerator()
        qualified = generator.get_qualified_teams(group_standings, qualifiers_per_group)
        
        try:
            category_prefix = self._get_category_prefix(cat)
            
            knockout_matches = generator.generate_bracket(
                len(group_standings),
                qualified,
                category=cat,
                category_prefix=category_prefix
            )
            
            # Rimuovi vecchie partite di fase finale per questa categoria
            self.parent.matches = [m for m in self.parent.matches 
                                  if not (m.category == cat and m.phase in 
                                         ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"])]
            
            # Aggiungi nuove partite
            self.parent.matches.extend(knockout_matches)
            
            self.refresh()
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Fase finale per {cat} generata!\n{len(knockout_matches)} partite")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def _get_category_prefix(self, category: str) -> str:
        """Restituisce il prefisso per una categoria."""
        prefix_map = {
            "Open": "O",
            "Veterans": "V",
            "Women": "W",
            "U20": "U20",
            "U16": "U16",
            "U12": "U12",
            "Eccellenza": "E",
            "Promozione": "P",
            "MOICAT": "M"
        }
        return prefix_map.get(category, "X")
    
    def get_phase_number_from_id(self, match_id: str) -> int:
        """Estrae il numero della partita dall'ID."""
        parts = match_id.split('_')
        if len(parts) >= 3:
            try:
                return int(parts[-1])
            except ValueError:
                return 1
        elif len(parts) == 2:
            try:
                return int(parts[1])
            except ValueError:
                return 1
        return 1
    
    def save_knockout_result(self):
        """Salva il risultato di una partita della fase finale."""
        if self.knockout_match.count() == 0 or self.knockout_match.currentText() == "Nessuna partita disponibile":
            QMessageBox.warning(self, "Attenzione", "Seleziona una partita")
            return
        
        match_id = self.knockout_match.currentData()
        if not match_id:
            return
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and not hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            QMessageBox.warning(self, "Errore", f"Partita {match_id} non trovata")
            return
        
        g1 = self.knockout_goals1.value()
        g2 = self.knockout_goals2.value()
        
        if g1 == g2:
            # PAREGGIO → avvia gestione
            reply = QMessageBox.question(self, "Pareggio",
                f"La partita è finita in parità {g1}-{g2}.\n\n"
                "⚡ Si procede con SUDDEN DEATH (10 minuti, primo gol vince).\n\n"
                "Procedere?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.No:
                return
            
            self.show_sudden_death(match)
            
            # Aggiorna UI
            self.refresh()
            self.update_match_list()
            
            # Rimuovi dalla lista rapida
            if match.winner:
                current_index = self.knockout_match.currentIndex()
                self.knockout_match.removeItem(current_index)
            
            self.knockout_goals1.setValue(0)
            self.knockout_goals2.setValue(0)
            
            if self.knockout_match.count() == 0:
                self.knockout_match.addItem("Nessuna partita disponibile")
            
            return
        
        # Risultato normale
        match.goals1 = g1
        match.goals2 = g2
        match.winner = match.player1 if g1 > g2 else match.player2
        match.status = MatchStatus.COMPLETED
        
        self.propagate_winner(match)
        
        # Rimuovi dalla lista rapida
        current_index = self.knockout_match.currentIndex()
        self.knockout_match.removeItem(current_index)
        
        self.knockout_goals1.setValue(0)
        self.knockout_goals2.setValue(0)
        
        self.refresh()
        
        self.parent.statusBar().showMessage(f"✅ Risultato {match_id}: {g1}-{g2} - Vincitore: {match.winner}")
        
        if self.knockout_match.count() == 0:
            self.knockout_match.addItem("Nessuna partita disponibile")
    
    def clear_knockout_result(self):
        """Cancella il risultato di una partita della fase finale."""
        current_row = self.knockout_table.currentRow()
        match_id = None
        
        if current_row >= 0:
            match_id_item = self.knockout_table.item(current_row, 1)
            if match_id_item:
                match_id = match_id_item.text()
        else:
            if self.knockout_match.count() > 0:
                match_id = self.knockout_match.currentData()
        
        if not match_id:
            QMessageBox.warning(self, "Attenzione", "Seleziona una partita")
            return
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and not hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            QMessageBox.warning(self, "Errore", f"Partita {match_id} non trovata")
            return
        
        reply = QMessageBox.question(self, "Conferma Cancellazione",
                                    f"Sei sicuro di voler cancellare il risultato della partita?\n\n"
                                    f"{match_id}: {match.player1} vs {match.player2}",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        match.goals1 = None
        match.goals2 = None
        match.winner = None
        match.status = MatchStatus.SCHEDULED
        
        # Genera il token per trovare le partite successive
        match_num = 1
        num_match = re.search(r'_(\d+)$', match.id)
        if num_match:
            match_num = int(num_match.group(1))
        
        phase_prefix = self.PHASE_TOKEN_PREFIX.get(match.phase, match.phase)
        token = f"WIN {phase_prefix}{match_num}"
        
        print(f"   🔄 Reset: cancellato risultato per {match.id}, token: {token}")
        
        # Reset delle partite successive della STESSA categoria
        for m in self.parent.matches:
            if (not hasattr(m, 'individual_matches') and 
                m.category == match.category):
                if m.player1 == token:
                    m.player1 = m.token1 if m.token1 else token
                    print(f"      ✅ Reset partita {m.id}: player1 = {m.player1}")
                if m.player2 == token:
                    m.player2 = m.token2 if m.token2 else token
                    print(f"      ✅ Reset partita {m.id}: player2 = {m.player2}")
        
        self.refresh()
        self.parent.statusBar().showMessage(f"✅ Risultato cancellato per {match_id}")
    
    def on_result_changed(self, row, col):
        """Gestisce la modifica diretta nella tabella."""
        if col != 3:
            return
        
        try:
            self.knockout_table.cellChanged.disconnect()
        except:
            pass
        
        try:
            match_id_item = self.knockout_table.item(row, 1)
            if not match_id_item:
                return
            
            match_id = match_id_item.text()
            
            match = None
            for m in self.parent.matches:
                if m.id == match_id and not hasattr(m, 'individual_matches'):
                    match = m
                    break
            
            if not match:
                return
            
            result_item = self.knockout_table.item(row, 3)
            if not result_item:
                return
            
            result_text = result_item.text().strip()
            
            if '-' in result_text:
                parts = result_text.split('-')
                if len(parts) == 2:
                    try:
                        g1 = int(parts[0].strip())
                        g2 = int(parts[1].strip())
                        
                        if g1 == g2:
                            QMessageBox.warning(self, "Attenzione", 
                                              "Nella fase finale non sono ammessi pareggi!")
                            self.refresh()
                            return
                        
                        match.goals1 = g1
                        match.goals2 = g2
                        match.winner = match.player1 if g1 > g2 else match.player2
                        match.status = MatchStatus.COMPLETED
                        
                        self.propagate_winner(match)
                        
                        self.refresh()
                        self.parent.statusBar().showMessage(f"✅ Risultato {match_id}: {g1}-{g2}")
                        
                    except ValueError:
                        self.refresh()
            else:
                self.refresh()
                
        finally:
            self.knockout_table.cellChanged.connect(self.on_result_changed)
    
    def debug_tokens(self):
        """Stampa i token per debug."""
        print("\n" + "="*70)
        print("🔍 DEBUG TOKEN FASE FINALE")
        print("="*70)
        
        knockout_matches = [m for m in self.parent.matches 
                           if not hasattr(m, 'individual_matches')
                           and m.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]]
        
        # Raggruppa per categoria
        matches_by_category = defaultdict(list)
        for match in knockout_matches:
            matches_by_category[match.category].append(match)
        
        for category, matches in matches_by_category.items():
            print(f"\n📌 Categoria: {category}")
            print("-" * 40)
            for match in sorted(matches, key=lambda x: x.id):
                print(f"  {match.id}:")
                print(f"    player1: '{match.player1}'")
                print(f"    player2: '{match.player2}'")
                if hasattr(match, 'token1'):
                    print(f"    token1: '{match.token1}'")
                if hasattr(match, 'token2'):
                    print(f"    token2: '{match.token2}'")
                if match.is_played:
                    print(f"    RISULTATO: {match.goals1}-{match.goals2}")
                    print(f"    VINCITORE: '{match.winner}'")
        
        print("\n" + "="*70)
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.update_button_state()
        self.refresh()