# ui/tabs/results_tab.py
"""
Tab per l'inserimento dei risultati delle partite per turno.
Interfaccia ottimizzata con maschera per turno e spinbox personalizzati.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QComboBox, QSpinBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QDialogButtonBox,
                               QFrame, QScrollArea, QCheckBox, QGridLayout,
                               QLineEdit, QFormLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Set
from datetime import datetime

from ui.base_tab import BaseTab
from models.match import MatchStatus


class MatchRowWidget(QWidget):
    """Widget per una singola partita con spinbox personalizzati (+/-)."""
    
    result_changed = Signal(object, int, int)  # match, goals1, goals2
    
    def __init__(self, match, category: str, group: str, field: int, parent=None):
        super().__init__(parent)
        self.match = match
        self.category = category
        self.group = group
        self.field = field
        
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Campo (stile badge)
        field_label = QLabel(f"🏟️ {self.field}")
        field_label.setFixedWidth(60)
        field_label.setAlignment(Qt.AlignCenter)
        field_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 12px;
                padding: 4px 0px;
            }
        """)
        layout.addWidget(field_label)
        
        # ID partita (monospace piccolo)
        id_label = QLabel(self.match.id)
        id_label.setFixedWidth(75)
        id_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(id_label)
        
        # Giocatore 1
        p1_label = QLabel(self.match.player1)
        p1_label.setMinimumWidth(180)
        p1_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        layout.addWidget(p1_label)
        
        # Container per gol 1 con stile
        g1_container = QWidget()
        g1_container.setFixedWidth(70)
        g1_layout = QHBoxLayout(g1_container)
        g1_layout.setContentsMargins(0, 0, 0, 0)
        g1_layout.setSpacing(0)
        
        # Pulsante meno
        self.btn_minus1 = QPushButton("-")
        self.btn_minus1.setFixedSize(24, 28)
        self.btn_minus1.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #a82313;
            }
        """)
        self.btn_minus1.clicked.connect(self._decrement1)
        g1_layout.addWidget(self.btn_minus1)
        
        # Spinbox gol
        self.goals1_spin = QSpinBox()
        self.goals1_spin.setMinimum(0)
        self.goals1_spin.setMaximum(20)
        self.goals1_spin.setFixedSize(40, 28)
        self.goals1_spin.setAlignment(Qt.AlignCenter)
        self.goals1_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.goals1_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-left: none;
                border-right: none;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        if self.match.goals1 is not None:
            self.goals1_spin.setValue(self.match.goals1)
        self.goals1_spin.valueChanged.connect(self._on_value_changed)
        g1_layout.addWidget(self.goals1_spin)
        
        # Pulsante più
        self.btn_plus1 = QPushButton("+")
        self.btn_plus1.setFixedSize(24, 28)
        self.btn_plus1.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.btn_plus1.clicked.connect(self._increment1)
        g1_layout.addWidget(self.btn_plus1)
        
        layout.addWidget(g1_container)
        
        # Trattino (separatore)
        dash_label = QLabel("—")
        dash_label.setFixedWidth(20)
        dash_label.setAlignment(Qt.AlignCenter)
        dash_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #95a5a6;")
        layout.addWidget(dash_label)
        
        # Container per gol 2
        g2_container = QWidget()
        g2_container.setFixedWidth(70)
        g2_layout = QHBoxLayout(g2_container)
        g2_layout.setContentsMargins(0, 0, 0, 0)
        g2_layout.setSpacing(0)
        
        self.btn_minus2 = QPushButton("-")
        self.btn_minus2.setFixedSize(24, 28)
        self.btn_minus2.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #a82313;
            }
        """)
        self.btn_minus2.clicked.connect(self._decrement2)
        g2_layout.addWidget(self.btn_minus2)
        
        self.goals2_spin = QSpinBox()
        self.goals2_spin.setMinimum(0)
        self.goals2_spin.setMaximum(20)
        self.goals2_spin.setFixedSize(40, 28)
        self.goals2_spin.setAlignment(Qt.AlignCenter)
        self.goals2_spin.setButtonSymbols(QSpinBox.NoButtons)
        self.goals2_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-left: none;
                border-right: none;
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        if self.match.goals2 is not None:
            self.goals2_spin.setValue(self.match.goals2)
        self.goals2_spin.valueChanged.connect(self._on_value_changed)
        g2_layout.addWidget(self.goals2_spin)
        
        self.btn_plus2 = QPushButton("+")
        self.btn_plus2.setFixedSize(24, 28)
        self.btn_plus2.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.btn_plus2.clicked.connect(self._increment2)
        g2_layout.addWidget(self.btn_plus2)
        
        layout.addWidget(g2_container)
        
        # Giocatore 2
        p2_label = QLabel(self.match.player2)
        p2_label.setMinimumWidth(180)
        p2_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        layout.addWidget(p2_label)
        
        # Stato (badge)
        self.status_label = QLabel()
        self.status_label.setFixedWidth(90)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def _increment1(self):
        """Incrementa gol 1."""
        self.goals1_spin.setValue(self.goals1_spin.value() + 1)
    
    def _decrement1(self):
        """Decrementa gol 1."""
        self.goals1_spin.setValue(max(0, self.goals1_spin.value() - 1))
    
    def _increment2(self):
        """Incrementa gol 2."""
        self.goals2_spin.setValue(self.goals2_spin.value() + 1)
    
    def _decrement2(self):
        """Decrementa gol 2."""
        self.goals2_spin.setValue(max(0, self.goals2_spin.value() - 1))
    
    def _on_value_changed(self):
        """Emit quando i valori cambiano."""
        g1 = self.goals1_spin.value()
        g2 = self.goals2_spin.value()
        self.result_changed.emit(self.match, g1, g2)
        self._update_display()
    
    def _update_display(self):
        """Aggiorna lo stato visivo."""
        g1 = self.goals1_spin.value()
        g2 = self.goals2_spin.value()
        
        # Determina se la partita è giocata (risultato inserito)
        # Una partita è considerata giocata se ha un risultato (anche 0-0)
        is_played = self.match.status == MatchStatus.COMPLETED or (self.match.goals1 is not None or self.match.goals2 is not None)
        
        if is_played:
            self.status_label.setText("✅ Giocata")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #2ecc71;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 12px;
                    padding: 4px 8px;
                }
            """)
            self.setStyleSheet("""
                MatchRowWidget {
                    background-color: #e8f8f5;
                    border-radius: 8px;
                    margin: 2px;
                    border: 1px solid #2ecc71;
                }
            """)
        else:
            self.status_label.setText("⏳ Da giocare")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    color: #7f8c8d;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 12px;
                    padding: 4px 8px;
                }
            """)
            self.setStyleSheet("""
                MatchRowWidget {
                    background-color: #ffffff;
                    border-radius: 8px;
                    margin: 2px;
                    border: 1px solid #ecf0f1;
                }
            """)
    
    def get_result(self) -> Tuple[int, int]:
        """Restituisce il risultato corrente."""
        return self.goals1_spin.value(), self.goals2_spin.value()
    
    def set_result(self, g1: int, g2: int):
        """Imposta il risultato."""
        self.goals1_spin.setValue(g1)
        self.goals2_spin.setValue(g2)
    
    def is_played(self) -> bool:
        """Verifica se la partita è stata giocata (risultato inserito)."""
        # Una partita è giocata se ha un risultato (anche 0-0)
        return self.match.status == MatchStatus.COMPLETED or (self.match.goals1 is not None or self.match.goals2 is not None)


class GroupMatchesWidget(QWidget):
    """Widget per un girone con le sue partite."""
    
    def __init__(self, group_name: str, matches: List, category: str, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.matches = matches
        self.category = category
        self.match_widgets = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Header girone
        header = QLabel(f"📌 GIRONE {self.group_name}")
        header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(header)
        
        # Contenitore partite
        matches_container = QWidget()
        matches_layout = QVBoxLayout(matches_container)
        matches_layout.setContentsMargins(20, 0, 0, 0)
        matches_layout.setSpacing(2)
        
        for match in self.matches:
            # Estrai campo
            field = match.field if match.field else 0
            
            row_widget = MatchRowWidget(match, self.category, self.group_name, field)
            row_widget.result_changed.connect(self._on_match_result_changed)
            self.match_widgets.append(row_widget)
            matches_layout.addWidget(row_widget)
        
        layout.addWidget(matches_container)
    
    def _on_match_result_changed(self, match, g1, g2):
        """Propaga il cambiamento."""
        # Aggiorna il match
        match.goals1 = g1
        match.goals2 = g2
        
        # Anche 0-0 è un risultato valido
        match.status = MatchStatus.COMPLETED
    
    def get_matches_status(self) -> Tuple[int, int]:
        """Restituisce (giocate, totali) per questo girone."""
        played = sum(1 for w in self.match_widgets if w.is_played())
        return played, len(self.match_widgets)
    
    def save_all(self):
        """Salva tutte le partite del girone."""
        for widget in self.match_widgets:
            g1, g2 = widget.get_result()
            match = widget.match
            match.goals1 = g1
            match.goals2 = g2
            # Anche 0-0 è un risultato valido
            match.status = MatchStatus.COMPLETED


class CategoryMatchesWidget(QWidget):
    """Widget per una categoria con i suoi gironi."""
    
    def __init__(self, category: str, groups: Dict[str, List], parent=None):
        super().__init__(parent)
        self.category = category
        self.groups = groups
        self.group_widgets = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(10)
        
        # Header categoria
        header = QLabel(f"🏆 {self.category}")
        header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #e67e22;
                padding: 8px;
                background-color: #fef5e8;
                border-radius: 6px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Gironi
        for group_name, matches in self.groups.items():
            group_widget = GroupMatchesWidget(group_name, matches, self.category)
            self.group_widgets.append(group_widget)
            layout.addWidget(group_widget)
        
        layout.addSpacing(10)
    
    def get_stats(self) -> Tuple[int, int]:
        """Restituisce (giocate, totali) per questa categoria."""
        total_played = 0
        total_matches = 0
        for gw in self.group_widgets:
            played, total = gw.get_matches_status()
            total_played += played
            total_matches += total
        return total_played, total_matches
    
    def save_all(self):
        """Salva tutte le partite della categoria."""
        for gw in self.group_widgets:
            gw.save_all()


class ResultsTab(BaseTab):
    """Tab per l'inserimento dei risultati per turno."""
    
    def __init__(self, parent):
        super().__init__(parent, "⚽ Risultati per Turno")
        
        # Riferimenti
        self.lbl_turn_info = None
        self.btn_prev = None
        self.btn_next = None
        self.btn_save = None
        self.progress_bar = None
        self.lbl_progress = None
        self.scroll_area = None
        self.content_widget = None
        self.content_layout_inner = None
        
        # Dati
        self.unique_times = []
        self.current_turn_index = 0
        self.turn_matches = {}  # time -> lista match
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        # Usa content_layout che è già definito nel BaseTab
        if self.content_layout is None:
            self.content_layout = QVBoxLayout(self)
        
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
        
        # ========================================
        # PANNELLO NAVIGAZIONE TURNI
        # ========================================
        nav_frame = QFrame()
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        nav_layout = QHBoxLayout(nav_frame)
        
        # Turno precedente
        self.btn_prev = QPushButton("◀ Turno precedente")
        self.btn_prev.clicked.connect(self.prev_turn)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        nav_layout.addWidget(self.btn_prev)
        
        # Info turno corrente
        turn_info_layout = QVBoxLayout()
        
        self.lbl_turn_info = QLabel("Turno 1/1 - 09:00")
        self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.lbl_turn_info.setAlignment(Qt.AlignCenter)
        turn_info_layout.addWidget(self.lbl_turn_info)
        
        nav_layout.addLayout(turn_info_layout)
        
        # Turno successivo
        self.btn_next = QPushButton("Turno successivo ▶")
        self.btn_next.clicked.connect(self.next_turn)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        nav_layout.addWidget(self.btn_next)
        
        nav_layout.addStretch()
        
        # Pulsante salva
        self.btn_save = QPushButton("💾 Salva Tutto")
        self.btn_save.clicked.connect(self.save_current_turn)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        nav_layout.addWidget(self.btn_save)
        
        self.content_layout.addWidget(nav_frame)
        
        # ========================================
        # PROGRESSO TURNO
        # ========================================
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border-radius: 6px;
                padding: 8px;
                margin-top: 10px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 10px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.lbl_progress = QLabel("0/0 partite completate")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet("color: #2c3e50; font-weight: bold;")
        progress_layout.addWidget(self.lbl_progress)
        
        self.content_layout.addWidget(progress_frame)
        
        # ========================================
        # SCROLL AREA PER LE PARTITE DEL TURNO
        # ========================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout_inner = QVBoxLayout(self.content_widget)
        self.content_layout_inner.setSpacing(15)
        self.content_layout_inner.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout.addWidget(self.scroll_area)
    
    def refresh(self):
        """Aggiorna la visualizzazione."""
        if not self.parent.current_tournament or not hasattr(self.parent, 'matches'):
            return
        
        # Raccogli solo partite individuali
        individual_matches = [m for m in self.parent.matches if not hasattr(m, 'individual_matches')]
        
        if not individual_matches:
            self.lbl_turn_info.setText("Nessuna partita generata")
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
            self.btn_save.setEnabled(False)
            return
        
        # Raggruppa per orario
        self.turn_matches = defaultdict(list)
        for match in individual_matches:
            time = match.scheduled_time
            if time:
                self.turn_matches[time].append(match)
        
        # Ordina gli orari
        self.unique_times = sorted(self.turn_matches.keys())
        
        if not self.unique_times:
            self.lbl_turn_info.setText("Nessun orario definito")
            return
        
        # Imposta turno corrente
        self.current_turn_index = 0
        self._update_turn_display()
    
    def _update_turn_display(self):
        """Aggiorna la visualizzazione del turno corrente."""
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        matches = self.turn_matches[current_time]
        
        # Aggiorna info turno
        self.lbl_turn_info.setText(f"📅 TURNO {self.current_turn_index + 1}/{len(self.unique_times)} - {current_time}")
        
        # Aggiorna pulsanti
        self.btn_prev.setEnabled(self.current_turn_index > 0)
        self.btn_next.setEnabled(self.current_turn_index < len(self.unique_times) - 1)
        
        # Pulisci e ricostruisci il contenuto
        self._clear_content()
        
        # Raggruppa partite per categoria e girone
        matches_by_category = defaultdict(lambda: defaultdict(list))
        
        for match in matches:
            category = match.category
            group = match.group or "?"
            matches_by_category[category][group].append(match)
        
        # Crea widget per ogni categoria
        for category, groups in sorted(matches_by_category.items()):
            category_widget = CategoryMatchesWidget(category, groups)
            self.content_layout_inner.addWidget(category_widget)
        
        self.content_layout_inner.addStretch()
        
        # Aggiorna progresso
        self._update_progress()
    
    def _clear_content(self):
        """Pulisce il contenuto dello scroll area."""
        while self.content_layout_inner.count():
            item = self.content_layout_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _update_progress(self):
        """Aggiorna la barra di progresso del turno corrente."""
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        matches = self.turn_matches[current_time]
        
        total = len(matches)
        played = sum(1 for m in matches if m.status == MatchStatus.COMPLETED or (m.goals1 is not None or m.goals2 is not None))
        
        percent = (played / total * 100) if total > 0 else 0
        
        # Aggiorna testo
        self.lbl_progress.setText(f"📊 {played}/{total} partite completate ({percent:.0f}%)")
        
        # Aggiorna barra progresso
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
        
        # Se il turno è completo, evidenzia
        if played == total and total > 0:
            self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
            self.lbl_progress.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.lbl_turn_info.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
            self.lbl_progress.setStyleSheet("color: #2c3e50; font-weight: bold;")
    
    def prev_turn(self):
        """Vai al turno precedente."""
        if self.current_turn_index > 0:
            self.current_turn_index -= 1
            self._update_turn_display()
    
    def next_turn(self):
        """Vai al turno successivo."""
        if self.current_turn_index < len(self.unique_times) - 1:
            self.current_turn_index += 1
            self._update_turn_display()
    
    def save_current_turn(self):
        """Salva tutte le partite del turno corrente."""
        if not self.unique_times:
            return
        
        current_time = self.unique_times[self.current_turn_index]
        
        # Salva modifiche
        self.parent.statusBar().showMessage(f"💾 Salvataggio risultati turno {current_time}...")
        
        # Aggiorna le classifiche
        if hasattr(self.parent, 'refresh_standings'):
            self.parent.refresh_standings()
        if hasattr(self.parent, 'refresh_scorers'):
            self.parent.refresh_scorers()
        if hasattr(self.parent, 'update_knockout_button_state'):
            self.parent.update_knockout_button_state()
        
        # Aggiorna il progresso
        self._update_progress()
        
        self.parent.statusBar().showMessage(f"✅ Risultati turno {current_time} salvati", 3000)
        
        # Verifica completamento
        played, total = self._get_turn_stats(current_time)
        if played == total:
            QMessageBox.information(self, "Turno Completato", 
                                   f"✅ Tutte le {total} partite del turno {current_time} sono state completate!")
    
    def _get_turn_stats(self, time: str) -> Tuple[int, int]:
        """Restituisce (giocate, totali) per un turno."""
        matches = self.turn_matches.get(time, [])
        total = len(matches)
        played = sum(1 for m in matches if m.status == MatchStatus.COMPLETED or (m.goals1 is not None or m.goals2 is not None))
        return played, total
    
    def check_all_turns_completed(self):
        """Verifica se tutti i turni sono completati."""
        if not self.unique_times:
            return False
        
        for time in self.unique_times:
            played, total = self._get_turn_stats(time)
            if played < total:
                return False
        return True
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()