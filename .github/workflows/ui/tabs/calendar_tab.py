# ui/tabs/calendar_tab.py
"""
Tab per la gestione del calendario partite (torneo individuale) con modifica manuale.
Rispetta le regole FISTF per l'ordine delle partite e i conflitti.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QSpinBox, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QDialogButtonBox,
                               QFrame, QScrollArea, QCheckBox, QFileDialog,
                               QInputDialog, QFormLayout, QLineEdit)
from PySide6.QtCore import Qt
from collections import defaultdict
import random

from ui.base_tab import BaseTab
from core.scheduler import generate_tournament_schedule
from models.match import MatchStatus


class CalendarTab(BaseTab):
    """Tab per la gestione del calendario partite con modifica manuale."""
    
    def __init__(self, parent):
        super().__init__(parent, "📅 Calendario Partite")
        
        # Riferimenti UI
        self.spin_fields = None
        self.calendar_category = None
        self.calendar_table = None
        self.lbl_calendar_stats = None
        self.btn_manual_edit = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
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
        # PANNELLO CONTROLLI
        # ========================================
        controls_group = QGroupBox("Opzioni Calendario")
        controls_layout = QHBoxLayout(controls_group)
        
        # Campi disponibili
        controls_layout.addWidget(QLabel("Campi totali:"))
        self.spin_fields = QSpinBox()
        self.spin_fields.setMinimum(1)
        self.spin_fields.setMaximum(50)
        self.spin_fields.setValue(12)
        self.spin_fields.setFixedWidth(90)
        self.spin_fields.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.spin_fields)
        
        # Filtro categoria
        controls_layout.addWidget(QLabel("Categoria:"))
        self.calendar_category = QComboBox()
        for cat in self.parent.current_tournament.categories:
            if "Team" not in cat.value:
                self.calendar_category.addItem(cat.value)
        self.calendar_category.currentTextChanged.connect(self.filter_calendar)
        controls_layout.addWidget(self.calendar_category)
        
        controls_layout.addStretch()
        
        # Pulsante configura campi
        btn_configure_fields = QPushButton("⚙️ Configura Campi")
        btn_configure_fields.clicked.connect(self.configure_fields)
        btn_configure_fields.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        controls_layout.addWidget(btn_configure_fields)
        
        # Pulsante genera
        btn_generate = QPushButton("⚙️ Genera Calendario")
        btn_generate.clicked.connect(self.generate_schedule)
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        controls_layout.addWidget(btn_generate)
        
        # Pulsante modifica manuale
        self.btn_manual_edit = QPushButton("✏️ Modifica Manuale")
        self.btn_manual_edit.clicked.connect(self.manual_edit_schedule)
        self.btn_manual_edit.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        controls_layout.addWidget(self.btn_manual_edit)
        
        # Pulsante PDF
        btn_pdf = QPushButton("📄 PDF")
        btn_pdf.clicked.connect(self.export_calendar_pdf)
        btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        controls_layout.addWidget(btn_pdf)
        
        btn_export_csv = QPushButton("📊 Esporta CSV")
        btn_export_csv.clicked.connect(self.export_calendar_csv)
        btn_export_csv.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        controls_layout.addWidget(btn_export_csv)

        btn_import_csv = QPushButton("📂 Importa CSV")
        btn_import_csv.clicked.connect(self.import_calendar_csv)
        btn_import_csv.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        controls_layout.addWidget(btn_import_csv)

        btn_template = QPushButton("📋 Template CSV")
        btn_template.clicked.connect(self.export_calendar_template)
        btn_template.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        controls_layout.addWidget(btn_template)

        self.content_layout.addWidget(controls_group)
        
        # ========================================
        # TABELLA CALENDARIO
        # ========================================
        self.calendar_table = QTableWidget()
        self.calendar_table.setColumnCount(8)
        self.calendar_table.setHorizontalHeaderLabels([
            "ID", "Girone", "Campo", "Orario", "Giocatore 1", "Giocatore 2", "Arbitro", "Stato"
        ])
        
        header = self.calendar_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.calendar_table)
        
        # ========================================
        # STATISTICHE
        # ========================================
        stats_layout = QHBoxLayout()
        self.lbl_calendar_stats = QLabel("Partite totali: 0")
        stats_layout.addWidget(self.lbl_calendar_stats)
        stats_layout.addStretch()
        self.content_layout.addLayout(stats_layout)
        
        # ========================================
        # LEGENDA
        # ========================================
        legend_frame = QFrame()
        legend_frame.setFrameStyle(QFrame.Box)
        legend_layout = QHBoxLayout(legend_frame)
        
        legend_layout.addWidget(QLabel("🎨 Legenda:"))
        
        completed_label = QLabel("⬜ Giocata")
        completed_label.setStyleSheet("background-color: #90EE90; padding: 2px 8px; border-radius: 3px;")
        legend_layout.addWidget(completed_label)
        
        scheduled_label = QLabel("⬜ Programmata")
        scheduled_label.setStyleSheet("background-color: #D3D3D3; padding: 2px 8px; border-radius: 3px;")
        legend_layout.addWidget(scheduled_label)
        
        in_progress_label = QLabel("⬜ In corso")
        in_progress_label.setStyleSheet("background-color: #FFF3CD; padding: 2px 8px; border-radius: 3px;")
        legend_layout.addWidget(in_progress_label)
        
        legend_layout.addStretch()
        self.content_layout.addWidget(legend_frame)
    
    def refresh(self):
        """Aggiorna la visualizzazione del calendario."""
        if not hasattr(self.parent, 'matches'):
            return
        
        # Fix stati partita
        from models.match import MatchStatus
        
        for match in self.parent.matches:
            if hasattr(match, 'status') and isinstance(match.status, str):
                status_map = {
                    "SCHEDULED": MatchStatus.SCHEDULED,
                    "Programmata": MatchStatus.SCHEDULED,
                    "IN_PROGRESS": MatchStatus.IN_PROGRESS,
                    "In corso": MatchStatus.IN_PROGRESS,
                    "COMPLETED": MatchStatus.COMPLETED,
                    "Giocata": MatchStatus.COMPLETED,
                }
                if match.status in status_map:
                    match.status = status_map[match.status]
        
        self.calendar_table.setRowCount(0)
        
        # Filtra solo partite individuali (non TeamMatch)
        individual_matches = [m for m in self.parent.matches 
                              if not hasattr(m, 'individual_matches')]
        
        if not individual_matches:
            self.lbl_calendar_stats.setText("Nessuna partita generata")
            self.calendar_table.insertRow(0)
            msg_item = QTableWidgetItem("👉 Nessuna partita generata - Clicca 'Genera Calendario'")
            msg_item.setForeground(Qt.blue)
            msg_item.setTextAlignment(Qt.AlignCenter)
            self.calendar_table.setSpan(0, 0, 1, 8)
            self.calendar_table.setItem(0, 0, msg_item)
            return
        
        # Filtra per categoria
        cat = self.calendar_category.currentText()
        filtered_matches = individual_matches
        if cat:
            filtered_matches = [m for m in individual_matches if m.category == cat]
        
        for row, match in enumerate(filtered_matches):
            self.calendar_table.insertRow(row)
            
            # ID
            self.calendar_table.setItem(row, 0, QTableWidgetItem(match.id))
            
            # Girone
            self.calendar_table.setItem(row, 1, QTableWidgetItem(match.group or ""))
            
            # Campo
            self.calendar_table.setItem(row, 2, QTableWidgetItem(str(match.field) if match.field else ""))
            
            # Orario
            self.calendar_table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
            
            # Giocatore 1
            self.calendar_table.setItem(row, 4, QTableWidgetItem(match.player1))
            
            # Giocatore 2
            self.calendar_table.setItem(row, 5, QTableWidgetItem(match.player2))
            
            # Arbitro
            referee_text = match.referee if match.referee else "Da assegnare"
            referee_item = QTableWidgetItem(referee_text)
            if not match.referee:
                referee_item.setForeground(Qt.red)
            self.calendar_table.setItem(row, 6, referee_item)
            
            # Stato
            status_value = match.status
            if hasattr(status_value, 'value'):
                status_text = status_value.value
            else:
                status_text = str(status_value)
            
            status_item = QTableWidgetItem(status_text)
            
            if "COMPLETED" in status_text or "Giocata" in status_text:
                status_item.setBackground(Qt.green)
            elif "IN_PROGRESS" in status_text or "In corso" in status_text:
                status_item.setBackground(Qt.yellow)
            elif "SCHEDULED" in status_text or "Programmata" in status_text:
                status_item.setBackground(Qt.lightGray)
            
            self.calendar_table.setItem(row, 7, status_item)
        
        # Statistiche
        total = len(individual_matches)
        filtered = len(filtered_matches)
        with_referee = sum(1 for m in filtered_matches if m.referee)
        
        # Calcola turni
        unique_times = sorted(set(m.scheduled_time for m in filtered_matches if m.scheduled_time))
        turns = len(unique_times)
        
        if cat:
            self.lbl_calendar_stats.setText(f"Partite: {filtered}/{total} (filtro: {cat}) | Arbitri: {with_referee}/{filtered} | Turni: {turns}")
        else:
            self.lbl_calendar_stats.setText(f"Partite totali: {total} | Arbitri: {with_referee}/{total} | Turni: {turns}")
    
    def filter_calendar(self):
        """Filtra calendario per categoria."""
        self.refresh()
    
    def get_category_prefix(self, category_value):
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
        return prefix_map.get(category_value, "X")
    
    def configure_fields(self):
        """Dialog per configurare i campi per categoria."""
        if not self.parent.current_tournament:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurazione Campi per Categoria")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Assegna i campi disponibili per categoria:"))
        layout.addWidget(QLabel("(1 campo = 1 partita per turno per quella categoria)"))
        
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Campi totali disponibili:"))
        spin_total = QSpinBox()
        spin_total.setMinimum(1)
        spin_total.setMaximum(50)
        spin_total.setValue(self.spin_fields.value())
        total_layout.addWidget(spin_total)
        total_layout.addStretch()
        layout.addLayout(total_layout)
        
        layout.addWidget(QLabel(" "))
        
        category_spins = {}
        for cat in self.parent.current_tournament.categories:
            if "Team" in cat.value:
                continue
            cat_layout = QHBoxLayout()
            cat_layout.addWidget(QLabel(f"  {cat.value}:"))
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(20)
            if cat.value == "Open":
                spin.setValue(6)
            elif cat.value == "Veterans":
                spin.setValue(4)
            elif cat.value == "Women":
                spin.setValue(2)
            elif cat.value == "U20":
                spin.setValue(2)
            elif cat.value == "U16":
                spin.setValue(2)
            elif cat.value == "U12":
                spin.setValue(2)
            else:
                spin.setValue(2)
            cat_layout.addWidget(spin)
            cat_layout.addStretch()
            layout.addLayout(cat_layout)
            category_spins[cat.value] = spin
        
        layout.addWidget(QLabel(" "))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        total_fields = spin_total.value()
        self.spin_fields.setValue(total_fields)
        
        # Salva la configurazione per l'uso in generate_schedule
        self.fields_per_category = {}
        for cat, spin in category_spins.items():
            if spin.value() > 0:
                self.fields_per_category[cat] = spin.value()
        
        QMessageBox.information(self, "Configurazione Salvata", 
                               f"✅ Configurazione campi salvata:\n"
                               f"Campi totali: {total_fields}\n"
                               f"Categorie con campi: {len(self.fields_per_category)}")
    
    def generate_schedule(self):
        """Genera il calendario partite per tutte le categorie."""
        if not self.parent.current_tournament:
            return
        
        if self.parent.matches:
            reply = QMessageBox.question(self, "Conferma",
                                        "Esistono già partite generate. Sovrascrivere?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # Verifica se esiste configurazione campi
        if not hasattr(self, 'fields_per_category') or not self.fields_per_category:
            reply = QMessageBox.question(self, "Configurazione Campi",
                                        "Prima di generare il calendario, devi configurare i campi per categoria.\n\n"
                                        "Vuoi configurarli ora?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.configure_fields()
            else:
                return
        
        total_fields = self.spin_fields.value()
        
        # Raccogli tutti i gironi
        all_groups = {}
        for cat in self.parent.current_tournament.categories:
            if "Team" in cat.value:
                continue
            groups_key = f"groups_{cat.value}"
            if groups_key in self.parent.groups:
                for group_name, players in self.parent.groups[groups_key].items():
                    prefix = self.get_category_prefix(cat.value)
                    full_group_name = f"{prefix}-{group_name}"
                    all_groups[full_group_name] = players
        
        if not all_groups:
            QMessageBox.warning(self, "Attenzione", "Nessun girone trovato!")
            return
        
        # Genera calendario con scheduler ottimizzato
        self.parent.matches = generate_tournament_schedule(
            all_groups,
            total_fields=total_fields,
            fields_per_category=self.fields_per_category
        )
        
        # Fix stati partita
        from models.match import MatchStatus
        for match in self.parent.matches:
            if hasattr(match, 'status') and isinstance(match.status, str):
                if match.status in ["SCHEDULED", "Programmata"]:
                    match.status = MatchStatus.SCHEDULED
        
        self.refresh()
        
        # Aggiorna tab Risultati per Turno se esiste
        if hasattr(self.parent, '_update_round_visibility'):
            self.parent._update_round_visibility()
        
        # Statistiche
        matches_by_category = defaultdict(int)
        matches_with_ref = 0
        
        for m in self.parent.matches:
            matches_by_category[m.category] += 1
            if m.referee:
                matches_with_ref += 1
        
        unique_times = sorted(set(m.scheduled_time for m in self.parent.matches if m.scheduled_time))
        turni_info = f"{len(unique_times)} turni: {unique_times[0]} - {unique_times[-1]}" if unique_times else "0 turni"
        
        stats = "\n".join([f"  {cat}: {count} partite" for cat, count in sorted(matches_by_category.items())])
        
        QMessageBox.information(self, "Successo", 
                               f"✅ Calendario generato con ottimizzazione FISTF!\n"
                               f"📊 Totale: {len(self.parent.matches)} partite\n"
                               f"⏰ {turni_info}\n"
                               f"👤 Arbitri: {matches_with_ref}/{len(self.parent.matches)}\n\n"
                               f"📈 Distribuzione per categoria:\n{stats}")
    
    # ========================================
    # MODIFICA MANUALE DEL CALENDARIO (senza drag & drop)
    # ========================================
    
    def manual_edit_schedule(self):
        """Apre il dialog per la modifica manuale del calendario."""
        if not self.parent.matches:
            QMessageBox.warning(self, "Attenzione", "Nessun calendario da modificare. Genera prima il calendario.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifica Manuale Calendario")
        dialog.setModal(True)
        dialog.resize(1100, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Istruzioni
        instructions = QLabel(
            "📋 **Istruzioni:**\n"
            "• Seleziona una o più partite (clicca sulle righe)\n"
            "• Usa i pulsanti per modificare campo, orario o arbitro\n"
            "• Le modifiche vengono applicate immediatamente\n\n"
            "⚠️ Le modifiche devono rispettare le regole FISTF:\n"
            "   - Un giocatore non può giocare due partite nello stesso turno\n"
            "   - L'arbitro non può essere dello stesso club/nazione dei giocatori"
        )
        instructions.setStyleSheet("color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Filtri
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Turno:"))
        turn_combo = QComboBox()
        times = sorted(set(m.scheduled_time for m in self.parent.matches if m.scheduled_time))
        turn_combo.addItem("Tutti i turni")
        for t in times:
            turn_combo.addItem(t)
        filter_layout.addWidget(turn_combo)
        
        filter_layout.addWidget(QLabel("Categoria:"))
        cat_combo = QComboBox()
        cat_combo.addItem("Tutte")
        for cat in self.parent.current_tournament.categories:
            if "Team" not in cat.value:
                cat_combo.addItem(cat.value)
        filter_layout.addWidget(cat_combo)
        
        filter_layout.addStretch()
        
        btn_refresh = QPushButton("🔄 Aggiorna")
        filter_layout.addWidget(btn_refresh)
        
        layout.addWidget(filter_frame)
        
        # Tabella con selezione
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID", "Girone", "Campo", "Orario", "Giocatore 1", "Giocatore 2", "Arbitro", "Stato"
        ])
        
        # Imposta selezione per righe intere
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.ExtendedSelection)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        layout.addWidget(table)
        
        # Pannello azioni
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        actions_layout = QHBoxLayout(actions_frame)
        
        # Pulsante modifica campo
        btn_edit_field = QPushButton("🏟️ Modifica Campo")
        btn_edit_field.clicked.connect(lambda: self._edit_field(table))
        btn_edit_field.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_edit_field)
        
        # Pulsante modifica orario
        btn_edit_time = QPushButton("⏰ Modifica Orario")
        btn_edit_time.clicked.connect(lambda: self._edit_time(table))
        btn_edit_time.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_edit_time)
        
        # Pulsante modifica arbitro
        btn_edit_referee = QPushButton("👤 Modifica Arbitro")
        btn_edit_referee.clicked.connect(lambda: self._edit_referee(table))
        btn_edit_referee.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_edit_referee)

        # Pulsante riordina (solo per questo turno/categoria)
        btn_sort_dialog = QPushButton("🔄 Riordina (questo turno)")
        btn_sort_dialog.clicked.connect(lambda: self._sort_visible_matches(table, turn_combo.currentText(), cat_combo.currentText()))
        btn_sort_dialog.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_sort_dialog)

        
        # Separatore
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #ccc;")
        actions_layout.addWidget(separator)
        
        # Pulsante scambia campi
        btn_swap = QPushButton("🔄 Scambia Campi")
        btn_swap.clicked.connect(lambda: self._swap_fields(table))
        btn_swap.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_swap)
        
        # Pulsante assegna arbitri
        btn_auto_referee = QPushButton("🎲 Assegna Arbitri")
        btn_auto_referee.clicked.connect(lambda: self._auto_assign_referees(table))
        btn_auto_referee.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        actions_layout.addWidget(btn_auto_referee)
        
        actions_layout.addStretch()
        
        # Pulsante chiudi
        btn_close = QPushButton("✖ Chiudi")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
        """)
        actions_layout.addWidget(btn_close)
        
        layout.addWidget(actions_frame)
        
        # Funzione per aggiornare la tabella
        def update_table():
            table.setRowCount(0)
            table.clearSelection()
            
            cat = cat_combo.currentText()
            turn = turn_combo.currentText()
            
            matches = self.parent.matches
            if cat != "Tutte":
                matches = [m for m in matches if hasattr(m, 'category') and m.category == cat]
            if turn != "Tutti i turni":
                matches = [m for m in matches if m.scheduled_time == turn]
            
            # Filtra solo partite individuali
            matches = [m for m in matches if not hasattr(m, 'individual_matches')]
            
            for row, match in enumerate(matches):
                table.insertRow(row)
                
                table.setItem(row, 0, QTableWidgetItem(match.id))
                table.setItem(row, 1, QTableWidgetItem(match.group or ""))
                table.setItem(row, 2, QTableWidgetItem(str(match.field) if match.field else ""))
                table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
                table.setItem(row, 4, QTableWidgetItem(match.player1))
                table.setItem(row, 5, QTableWidgetItem(match.player2))
                
                referee_text = match.referee if match.referee else "Da assegnare"
                ref_item = QTableWidgetItem(referee_text)
                if not match.referee:
                    ref_item.setForeground(Qt.red)
                table.setItem(row, 6, ref_item)
                
                status_text = match.status.value if hasattr(match.status, 'value') else str(match.status)
                status_item = QTableWidgetItem(status_text)
                if match.is_played:
                    status_item.setBackground(Qt.green)
                table.setItem(row, 7, status_item)
        
        # Collega segnali
        btn_refresh.clicked.connect(update_table)
        turn_combo.currentTextChanged.connect(update_table)
        cat_combo.currentTextChanged.connect(update_table)
        
        # Carica dati iniziali
        update_table()
        
        dialog.exec()
        
        # Ricarica la visualizzazione principale
        self.refresh()
    
    
    def _sort_visible_matches(self, table, turn_filter, cat_filter):
        """Riordina le partite attualmente visibili nel dialog di modifica."""
        # Raccogli le partite attualmente visibili
        visible_matches = []
        for row in range(table.rowCount()):
            match_id = table.item(row, 0).text()
            for m in self.parent.matches:
                if m.id == match_id and not hasattr(m, 'individual_matches'):
                    visible_matches.append(m)
                    break
        
        if not visible_matches:
            QMessageBox.warning(self, "Attenzione", "Nessuna partita da riordinare")
            return
        
        # Ordina per orario e campo
        sorted_matches = sorted(visible_matches, key=lambda m: (
            m.scheduled_time if m.scheduled_time else "99:99",
            m.field if m.field else 999
        ))
        
        # Aggiorna la tabella con l'ordine corretto
        table.setRowCount(0)
        for match in sorted_matches:
            row = table.rowCount()
            table.insertRow(row)
            
            table.setItem(row, 0, QTableWidgetItem(match.id))
            table.setItem(row, 1, QTableWidgetItem(match.group or ""))
            table.setItem(row, 2, QTableWidgetItem(str(match.field) if match.field else ""))
            table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
            table.setItem(row, 4, QTableWidgetItem(match.player1))
            table.setItem(row, 5, QTableWidgetItem(match.player2))
            
            referee_text = match.referee if match.referee else "Da assegnare"
            ref_item = QTableWidgetItem(referee_text)
            if not match.referee:
                ref_item.setForeground(Qt.red)
            table.setItem(row, 6, ref_item)
            
            status_text = match.status.value if hasattr(match.status, 'value') else str(match.status)
            status_item = QTableWidgetItem(status_text)
            if match.is_played:
                status_item.setBackground(Qt.green)
            table.setItem(row, 7, status_item)
        
        QMessageBox.information(self, "Successo", f"✅ Riordinate {len(sorted_matches)} partite")
    
    
    def _get_selected_matches(self, table):
        """Restituisce la lista delle partite selezionate."""
        selected_rows = set()
        for item in table.selectedItems():
            selected_rows.add(item.row())
        
        matches = []
        for row in selected_rows:
            match_id = table.item(row, 0).text()
            for m in self.parent.matches:
                if m.id == match_id and not hasattr(m, 'individual_matches'):
                    matches.append(m)
                    break
        
        return matches
    
    def _check_player_conflict(self, match, new_time, exclude_match=None):
        """Verifica se un giocatore ha già una partita nello stesso orario."""
        for m in self.parent.matches:
            if exclude_match and m.id == exclude_match.id:
                continue
            if m.scheduled_time == new_time:
                if m.player1 == match.player1 or m.player2 == match.player1 or \
                   m.player1 == match.player2 or m.player2 == match.player2:
                    return True, m.id
        return False, None
    
    def _check_field_conflict(self, match, new_field, new_time, exclude_match=None):
        """Verifica se un campo è già occupato nello stesso orario."""
        for m in self.parent.matches:
            if exclude_match and m.id == exclude_match.id:
                continue
            if m.scheduled_time == new_time and m.field == new_field:
                return True, m.id
        return False, None
    
    def _edit_field(self, table):
        """Modifica il campo delle partite selezionate."""
        matches = self._get_selected_matches(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        new_field, ok = QInputDialog.getInt(
            self, "Modifica Campo", 
            f"Inserisci il nuovo campo per {len(matches)} partite:",
            1, 1, 50, 1
        )
        
        if not ok:
            return
        
        conflicts = []
        for match in matches:
            conflict, conflict_id = self._check_field_conflict(match, new_field, match.scheduled_time, match)
            if conflict:
                conflicts.append(f"{match.id}: campo {new_field} già occupato da {conflict_id}")
        
        if conflicts:
            QMessageBox.warning(self, "Conflitti rilevati", "\n".join(conflicts[:5]))
            return
        
        for match in matches:
            match.field = new_field
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Campo modificato per {len(matches)} partite")
    
    def _edit_time(self, table):
        """Modifica l'orario delle partite selezionate."""
        matches = self._get_selected_matches(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        # Raccogli orari disponibili
        times = sorted(set(m.scheduled_time for m in self.parent.matches if m.scheduled_time))
        
        new_time, ok = QInputDialog.getItem(
            self, "Modifica Orario", 
            f"Seleziona il nuovo orario per {len(matches)} partite:",
            times, 0, False
        )
        
        if not ok:
            return
        
        # Verifica conflitti giocatori
        conflicts = []
        for match in matches:
            conflict, conflict_id = self._check_player_conflict(match, new_time, match)
            if conflict:
                conflicts.append(f"{match.id}: {match.player1} o {match.player2} già in {conflict_id}")
        
        if conflicts:
            QMessageBox.warning(self, "Conflitti rilevati", "\n".join(conflicts[:5]))
            return
        
        for match in matches:
            match.scheduled_time = new_time
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Orario modificato per {len(matches)} partite")
    
    def _edit_referee(self, table):
        """Modifica l'arbitro delle partite selezionate."""
        matches = self._get_selected_matches(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        # Raccogli giocatori disponibili come arbitri
        referees = ["Da assegnare"]
        for player in self.parent.players:
            referees.append(player.display_name)
        
        new_referee, ok = QInputDialog.getItem(
            self, "Modifica Arbitro", 
            f"Seleziona l'arbitro per {len(matches)} partite:",
            referees, 0, True
        )
        
        if not ok:
            return
        
        if new_referee == "Da assegnare":
            new_referee = None
        
        # Verifica regole FISTF per l'arbitro
        for match in matches:
            if new_referee:
                p1 = next((p for p in self.parent.players if p.display_name == match.player1), None)
                p2 = next((p for p in self.parent.players if p.display_name == match.player2), None)
                ref_player = next((p for p in self.parent.players if p.display_name == new_referee), None)
                
                if ref_player and p1 and p2:
                    # Regola: arbitro non può essere dello stesso club
                    if ref_player.club == p1.club or ref_player.club == p2.club:
                        QMessageBox.warning(self, "Regola FISTF", 
                            f"L'arbitro {new_referee} non può arbitrare {match.id} perché è dello stesso club di un giocatore")
                        return
                    
                    # Regola: arbitro non può essere della stessa nazione (se nazioni diverse)
                    if p1.country != p2.country:
                        if ref_player.country == p1.country or ref_player.country == p2.country:
                            QMessageBox.warning(self, "Regola FISTF", 
                                f"L'arbitro {new_referee} non può arbitrare {match.id} perché è della stessa nazione di un giocatore")
                            return
                    
                    # Regola: arbitro non può essere dello stesso girone
                    if ref_player.group == match.group:
                        QMessageBox.warning(self, "Regola FISTF", 
                            f"L'arbitro {new_referee} non può arbitrare {match.id} perché è dello stesso girone")
                        return
        
        for match in matches:
            match.referee = new_referee
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Arbitro assegnato per {len(matches)} partite")
    
    def _swap_fields(self, table):
        """Scambia i campi di due partite selezionate."""
        matches = self._get_selected_matches(table)
        
        if len(matches) != 2:
            QMessageBox.warning(self, "Attenzione", "Seleziona esattamente 2 partite")
            return
        
        match1, match2 = matches[0], matches[1]
        
        # Verifica che abbiano lo stesso orario
        if match1.scheduled_time != match2.scheduled_time:
            QMessageBox.warning(self, "Attenzione", 
                "Le due partite devono avere lo stesso orario per scambiare i campi")
            return
        
        # Scambia i campi
        field1 = match1.field
        field2 = match2.field
        
        match1.field = field2
        match2.field = field1
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Campi scambiati tra {match1.id} e {match2.id}")
    
    def _auto_assign_referees(self, table):
        """Assegna automaticamente gli arbitri alle partite selezionate seguendo le regole FISTF."""
        matches = self._get_selected_matches(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        # Raccogli tutti i giocatori non impegnati come arbitri
        busy_players = set()
        for m in self.parent.matches:
            if m.scheduled_time == matches[0].scheduled_time:  # stesso turno
                busy_players.add(m.player1)
                busy_players.add(m.player2)
        
        available_referees = []
        for player in self.parent.players:
            if player.display_name not in busy_players:
                available_referees.append(player)
        
        if not available_referees:
            QMessageBox.warning(self, "Attenzione", "Nessun arbitro disponibile in questo turno")
            return
        
        assigned = 0
        for match in matches:
            p1 = next((p for p in self.parent.players if p.display_name == match.player1), None)
            p2 = next((p for p in self.parent.players if p.display_name == match.player2), None)
            
            if not p1 or not p2:
                continue
            
            # Trova arbitro adatto
            suitable = []
            for ref in available_referees:
                # Regola FISTF: arbitro non può essere dello stesso club
                if ref.club == p1.club or ref.club == p2.club:
                    continue
                
                # Regola FISTF: arbitro non può essere della stessa nazione (se nazioni diverse)
                if p1.country != p2.country:
                    if ref.country == p1.country or ref.country == p2.country:
                        continue
                
                # Regola FISTF: arbitro non può essere dello stesso girone
                if ref.group == match.group:
                    continue
                
                suitable.append(ref)
            
            if suitable:
                chosen = random.choice(suitable)
                match.referee = chosen.display_name
                available_referees.remove(chosen)
                assigned += 1
            elif available_referees:
                chosen = available_referees[0]
                match.referee = chosen.display_name
                available_referees.remove(chosen)
                assigned += 1
                print(f"⚠️ Nessun arbitro ideale per {match.id}, uso {chosen.display_name}")
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Arbitri assegnati per {assigned}/{len(matches)} partite")
    
    # ========================================
    # METODI EXPORT/IMPORT
    # ========================================
    
    def export_calendar_pdf(self):
        """Esporta il calendario in PDF."""
        if not self.parent.matches:
            QMessageBox.warning(self, "Attenzione", "Nessun calendario da esportare")
            return
        
        try:
            from core.pdf_exporter import PDFExporter
            exporter = PDFExporter()
            
            tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
            filename = exporter.export_schedule(self.parent.matches, tournament_name)
            
            reply = QMessageBox.question(
                self, "PDF Generato",
                f"✅ Calendario esportato in PDF:\n{filename}\n\nVuoi aprire il file?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import subprocess, os
                if os.name == 'nt':
                    os.startfile(filename)
                else:
                    subprocess.call(('xdg-open', filename))
                    
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione PDF:\n{str(e)}")
    
    def export_calendar_csv(self):
        """Esporta il calendario in CSV."""
        if not self.parent.matches:
            QMessageBox.warning(self, "Attenzione", "Nessun calendario da esportare")
            return
        
        from utils.helpers import export_calendar_to_csv
        from datetime import datetime
        
        # Filtra solo partite individuali
        individual_matches = [m for m in self.parent.matches if not hasattr(m, 'individual_matches')]
        
        if not individual_matches:
            QMessageBox.warning(self, "Attenzione", "Nessuna partita individuale da esportare")
            return
        
        tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"calendario_{tournament_name}_{timestamp}.csv"
        
        try:
            filepath = export_calendar_to_csv(individual_matches, filename, tournament_name)
            QMessageBox.information(self, "Successo", f"✅ Calendario esportato in:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'esportazione:\n{str(e)}")

    def import_calendar_csv(self):
        """Importa il calendario da CSV."""
        from pathlib import Path
        from models.match import Match, MatchStatus
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file CSV calendario",
            str(Path("data").absolute()),
            "File CSV (*.csv);;Tutti i file (*.*)"
        )
        
        if not file_path:
            return
        
        reply = QMessageBox.question(self, "Conferma",
                                    "L'importazione sostituirà il calendario esistente. Continuare?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        from utils.helpers import import_calendar_from_csv
        
        try:
            matches_data = import_calendar_from_csv(file_path)
            
            new_matches = []
            for data in matches_data:
                status = MatchStatus.SCHEDULED
                if data["status"] in ["Giocata", "COMPLETED"]:
                    status = MatchStatus.COMPLETED
                elif data["status"] in ["In corso", "IN_PROGRESS"]:
                    status = MatchStatus.IN_PROGRESS
                
                match = Match(
                    id=data["id"],
                    category=data["category"],
                    phase=data["phase"],
                    group=data["group"],
                    field=data["field"],
                    scheduled_time=data["scheduled_time"],
                    player1=data["player1"],
                    player2=data["player2"],
                    referee=data["referee"],
                    status=status
                )
                
                if data["result"] != "vs" and '-' in data["result"]:
                    parts = data["result"].split('-')
                    if len(parts) == 2:
                        try:
                            match.goals1 = int(parts[0].strip())
                            match.goals2 = int(parts[1].strip())
                            match.status = MatchStatus.COMPLETED
                        except:
                            pass
                
                new_matches.append(match)
            
            self.parent.matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
            self.parent.matches.extend(new_matches)
            
            self.refresh()
            
            if hasattr(self.parent, '_update_round_visibility'):
                self.parent._update_round_visibility()
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Importate {len(new_matches)} partite da CSV")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante l'importazione:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def export_calendar_template(self):
        """Esporta un template CSV per il calendario."""
        from utils.helpers import export_calendar_template
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"template_calendario_{timestamp}.csv"
        
        try:
            filepath = export_calendar_template(filename, is_team=False)
            QMessageBox.information(self, "Successo", 
                                   f"✅ Template creato in:\n{filepath}\n\n"
                                   f"Compila il file e poi usa 'Importa CSV' per caricare il calendario.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()