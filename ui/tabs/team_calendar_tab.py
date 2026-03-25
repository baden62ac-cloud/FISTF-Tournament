# ui/tabs/team_calendar_tab.py
"""
Tab per la gestione del calendario partite a squadre con modifica manuale.
Ottimizzato per tornei a squadre con blocchi di 4 campi per incontro.
Rispetta le regole FISTF per l'ordine delle partite e i conflitti.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QSpinBox, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QDialogButtonBox,
                               QFrame, QFileDialog, QTabWidget, QTextEdit,
                               QInputDialog, QFormLayout, QLineEdit)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Tuple, Dict, Optional
import random

from ui.base_tab import BaseTab
from core.team_scheduler import generate_team_tournament_schedule
from models.match import MatchStatus


class TeamCalendarTab(BaseTab):
    """Tab per il calendario partite a squadre con modifica manuale"""
    
    def __init__(self, parent):
        super().__init__(parent, "📅 Calendario Partite a Squadre")
        
        # Riferimenti UI
        self.calendar_table = None
        self.calendar_category = None
        self.spin_fields = None
        self.lbl_calendar_stats = None
        self.btn_generate = None
        self.btn_export = None
        self.btn_export_csv = None
        self.btn_import_csv = None
        self.btn_template = None
        self.btn_manual_edit = None
        self.fields_per_category = {}
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab"""
        
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
        controls_group = QGroupBox("Opzioni Calendario Squadre")
        controls_layout = QHBoxLayout(controls_group)
        
        # Campi totali
        controls_layout.addWidget(QLabel("Campi totali:"))
        self.spin_fields = QSpinBox()
        self.spin_fields.setMinimum(4)
        self.spin_fields.setMaximum(40)
        self.spin_fields.setValue(12)
        self.spin_fields.setSingleStep(4)
        self.spin_fields.setFixedWidth(90)
        self.spin_fields.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.spin_fields)
        controls_layout.addWidget(QLabel("(multiplo di 4)"))
        
        # Filtro categoria
        controls_layout.addWidget(QLabel("Categoria:"))
        self.calendar_category = QComboBox()
        self.calendar_category.addItem("Tutte")
        if self.parent.current_tournament:
            for cat in self.parent.current_tournament.categories:
                if "Team" in cat.value:
                    self.calendar_category.addItem(cat.value)
        self.calendar_category.currentTextChanged.connect(self.filter_calendar)
        controls_layout.addWidget(self.calendar_category)
        
        controls_layout.addStretch()
        
        # Pulsante configura campi
        btn_configure = QPushButton("⚙️ Configura Campi")
        btn_configure.clicked.connect(self.configure_fields)
        btn_configure.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(btn_configure)
        
        # Pulsante genera
        self.btn_generate = QPushButton("🎲 Genera Calendario")
        self.btn_generate.clicked.connect(self.generate_schedule)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_generate)
        
        # Pulsante modifica manuale
        self.btn_manual_edit = QPushButton("✏️ Modifica Manuale")
        self.btn_manual_edit.clicked.connect(self.manual_edit_schedule)
        self.btn_manual_edit.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_manual_edit)
        
        # Pulsante esporta Excel
        self.btn_export = QPushButton("📥 Esporta Excel")
        self.btn_export.clicked.connect(self.export_schedule)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_export)
        
        # Pulsante esporta CSV
        self.btn_export_csv = QPushButton("📊 Esporta CSV")
        self.btn_export_csv.clicked.connect(self.export_calendar_csv)
        self.btn_export_csv.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_export_csv)
        
        # Pulsante importa CSV
        self.btn_import_csv = QPushButton("📂 Importa CSV")
        self.btn_import_csv.clicked.connect(self.import_calendar_csv)
        self.btn_import_csv.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_import_csv)
        
        # Pulsante template CSV
        self.btn_template = QPushButton("📋 Template CSV")
        self.btn_template.clicked.connect(self.export_calendar_template)
        self.btn_template.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.btn_template)
        
        self.content_layout.addWidget(controls_group)
        
        # ========================================
        # INFO CAMPI
        # ========================================
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #e3f2fd; border-radius: 4px; padding: 5px;")
        info_layout = QHBoxLayout(info_frame)
        self.lbl_fields_info = QLabel("ℹ️ I campi sono organizzati in blocchi da 4. Ogni incontro a squadre occupa un intero blocco.")
        self.lbl_fields_info.setStyleSheet("color: #0d47a1;")
        info_layout.addWidget(self.lbl_fields_info)
        info_layout.addStretch()
        self.content_layout.addWidget(info_frame)
        
        # ========================================
        # TABELLA CALENDARIO
        # ========================================
        self.calendar_table = QTableWidget()
        self.calendar_table.setColumnCount(10)
        self.calendar_table.setHorizontalHeaderLabels([
            "ID", "Girone", "Campi", "Orario", "Squadra 1", "Ris.", "Squadra 2", "Dettaglio", "Arbitro", "Categoria"
        ])
        
        # Abilita doppio clic per modificare arbitro
        self.calendar_table.itemDoubleClicked.connect(self.on_arbitro_double_clicked)
        
        header = self.calendar_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.calendar_table)
        
        # ========================================
        # STATISTICHE
        # ========================================
        stats_layout = QHBoxLayout()
        self.lbl_calendar_stats = QLabel("Incontri totali: 0")
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
        completed_label = QLabel("⬜ Completata")
        completed_label.setStyleSheet("background-color: #e8f5e8; padding: 2px 8px; border-radius: 3px;")
        legend_layout.addWidget(completed_label)
        scheduled_label = QLabel("⬜ Programmata")
        scheduled_label.setStyleSheet("background-color: #fff3e0; padding: 2px 8px; border-radius: 3px;")
        legend_layout.addWidget(scheduled_label)
        legend_layout.addStretch()
        self.content_layout.addWidget(legend_frame)
    
    def refresh(self):
        """Aggiorna la visualizzazione del calendario"""
        if not hasattr(self.parent, 'matches'):
            return
        
        # Fix stati - converti eventuali stringhe vecchie a None
        for match in self.parent.matches:
            if hasattr(match, 'individual_matches'):
                if isinstance(match.status, str):
                    # Mappa i vecchi stati a None (non giocata)
                    if match.status in ["SCHEDULED", "Programmata", "IN_PROGRESS", "In corso"]:
                        match.status = None
                    elif match.status in ["COMPLETED", "Giocata"]:
                        match.status = MatchStatus.COMPLETED
                    elif match.status in ["FORFEIT", "Forfait"]:
                        match.status = MatchStatus.FORFEIT
        
        self.calendar_table.setRowCount(0)
        
        # Filtra solo partite a squadre
        team_matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
        
        if not team_matches:
            self.lbl_calendar_stats.setText("Nessun incontro a squadre generato")
            self.calendar_table.insertRow(0)
            msg_item = QTableWidgetItem("👉 Nessun incontro generato - Clicca 'Genera Calendario'")
            msg_item.setForeground(Qt.blue)
            msg_item.setTextAlignment(Qt.AlignCenter)
            self.calendar_table.setSpan(0, 0, 1, 10)
            self.calendar_table.setItem(0, 0, msg_item)
            return
        
        # Filtra per categoria
        cat = self.calendar_category.currentText()
        filtered_matches = team_matches
        if cat != "Tutte":
            filtered_matches = [m for m in team_matches if m.category == cat]
        
        # Ordina per orario e girone
        filtered_matches = sorted(filtered_matches, key=lambda m: (
            m.scheduled_time if m.scheduled_time else "99:99",
            m.group if m.group else ""
        ))
        
        for row, match in enumerate(filtered_matches):
            self.calendar_table.insertRow(row)
            
            # ID
            self.calendar_table.setItem(row, 0, QTableWidgetItem(match.id))
            
            # Girone
            self.calendar_table.setItem(row, 1, QTableWidgetItem(match.group or ""))
            
            # Campi
            if hasattr(match, 'individual_matches') and match.individual_matches:
                fields = [str(im.table) for im in match.individual_matches if im.table]
                fields_text = ", ".join(fields) if fields else "4 campi"
            else:
                fields_text = str(match.field) if match.field else "?"
            self.calendar_table.setItem(row, 2, QTableWidgetItem(fields_text))
            
            # Orario
            self.calendar_table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
            
            # Squadra 1
            team1_name = match.player1
            if hasattr(match, 'team1') and match.team1:
                team = next((t for t in self.parent.teams if t.id == match.team1), None)
                if team:
                    team1_name = team.display_name
            self.calendar_table.setItem(row, 4, QTableWidgetItem(team1_name))
            
            # Risultato
            if hasattr(match, 'team1_wins') and match.is_played:
                result_text = f"{match.team1_wins}-{match.team2_wins}"
                result_item = QTableWidgetItem(result_text)
                result_item.setBackground(Qt.green)
            else:
                result_text = "vs"
                result_item = QTableWidgetItem(result_text)
            self.calendar_table.setItem(row, 5, result_item)
            
            # Squadra 2
            team2_name = match.player2
            if hasattr(match, 'team2') and match.team2:
                team = next((t for t in self.parent.teams if t.id == match.team2), None)
                if team:
                    team2_name = team.display_name
            self.calendar_table.setItem(row, 6, QTableWidgetItem(team2_name))
            
            # Dettaglio incontri
            if hasattr(match, 'individual_matches') and match.individual_matches:
                details = []
                for im in match.individual_matches:
                    if im.is_played:
                        details.append(f"T{im.table}: {im.goals1}-{im.goals2}")
                    else:
                        details.append(f"T{im.table}: vs")
                detail_text = " | ".join(details)
            else:
                detail_text = "4 incontri"
            detail_item = QTableWidgetItem(detail_text)
            detail_item.setToolTip("Doppio clic per dettaglio")
            self.calendar_table.setItem(row, 7, detail_item)
            
            # Arbitro (colonna 8)
            referee_text = getattr(match, 'referee', None)
            if not referee_text:
                referee_text = "Da assegnare"
            referee_item = QTableWidgetItem(referee_text)
            if not getattr(match, 'referee', None):
                referee_item.setForeground(Qt.red)
            self.calendar_table.setItem(row, 8, referee_item)
            
            # Categoria (colonna 9)
            self.calendar_table.setItem(row, 9, QTableWidgetItem(match.category))
        
        # Statistiche
        total = len(team_matches)
        filtered = len(filtered_matches)
        played = sum(1 for m in filtered_matches if m.is_played)
        unique_times = sorted(set(m.scheduled_time for m in filtered_matches if m.scheduled_time))
        turns = len(unique_times)
        
        if cat != "Tutte":
            self.lbl_calendar_stats.setText(f"Incontri: {filtered}/{total} (filtro: {cat}) | Giocati: {played} | Turni: {turns}")
        else:
            self.lbl_calendar_stats.setText(f"Incontri totali: {total} | Giocati: {played} | Turni: {turns}")
    
    def filter_calendar(self):
        self.refresh()
    
    def configure_fields(self):
        """Dialog per configurare i campi per categoria (multipli di 4)"""
        if not self.parent.current_tournament:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurazione Campi per Categoria - Squadre")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("⚠️ I campi per categoria devono essere MULTIPLI DI 4 (ogni incontro occupa 4 campi)."))
        layout.addWidget(QLabel(" "))
        
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Campi totali disponibili:"))
        spin_total = QSpinBox()
        spin_total.setMinimum(4)
        spin_total.setMaximum(40)
        spin_total.setSingleStep(4)
        spin_total.setValue(self.spin_fields.value())
        total_layout.addWidget(spin_total)
        total_layout.addStretch()
        layout.addLayout(total_layout)
        
        layout.addWidget(QLabel(" "))
        
        scroll = QWidget()
        scroll_layout = QVBoxLayout(scroll)
        
        category_spins = {}
        team_categories = [cat for cat in self.parent.current_tournament.categories if "Team" in cat.value]
        
        for cat in team_categories:
            cat_layout = QHBoxLayout()
            cat_layout.addWidget(QLabel(f"  {cat.value}:"))
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(20)
            spin.setSingleStep(4)
            
            if "Open" in cat.value:
                spin.setValue(8)
            elif "Veterans" in cat.value:
                spin.setValue(4)
            else:
                spin.setValue(4)
            
            cat_layout.addWidget(spin)
            cat_layout.addWidget(QLabel(" campi"))
            cat_layout.addStretch()
            
            lbl_blocks = QLabel(f"→ {spin.value() // 4} blocchi")
            lbl_blocks.setStyleSheet("color: #666;")
            cat_layout.addWidget(lbl_blocks)
            
            def update_blocks_label(spin, label):
                def update():
                    blocks = spin.value() // 4
                    label.setText(f"→ {blocks} blocchi")
                return update
            
            spin.valueChanged.connect(update_blocks_label(spin, lbl_blocks))
            scroll_layout.addLayout(cat_layout)
            category_spins[cat.value] = spin
        
        scroll_layout.addStretch()
        
        scroll_area = QWidget()
        scroll_area.setLayout(scroll_layout)
        
        scroll_widget = QWidget()
        scroll_widget_layout = QVBoxLayout(scroll_widget)
        scroll_widget_layout.addWidget(scroll_area)
        
        layout.addWidget(scroll_widget)
        layout.addWidget(QLabel(" "))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        total_fields = spin_total.value()
        self.spin_fields.setValue(total_fields)
        
        self.fields_per_category = {}
        for cat, spin in category_spins.items():
            if spin.value() >= 4:
                self.fields_per_category[cat] = spin.value()
        
        total_blocks = total_fields // 4
        total_cat_blocks = sum(v // 4 for v in self.fields_per_category.values())
        
        if total_cat_blocks > total_blocks:
            QMessageBox.warning(self, "Attenzione", 
                               f"La somma dei blocchi ({total_cat_blocks}) supera i blocchi totali ({total_blocks}).")
        
        QMessageBox.information(self, "Configurazione Salvata", 
                               f"✅ Configurazione campi salvata:\nCampi totali: {total_fields} ({total_blocks} blocchi)")
    
    def generate_schedule(self):
        """Genera il calendario partite per tutte le categorie squadre"""
        if not self.parent.current_tournament:
            return
        
        has_team_groups = any(key.startswith("team_groups_") for key in self.parent.groups)
        if not has_team_groups:
            QMessageBox.warning(self, "Attenzione", 
                               "Nessun girone squadre trovato!\nVai su 'Gironi Squadre' e distribuisci le squadre.")
            return
        
        total_fields = self.spin_fields.value()
        if total_fields % 4 != 0:
            QMessageBox.warning(self, "Attenzione", 
                               f"I campi totali ({total_fields}) non sono multipli di 4.\nImposta un numero multiplo di 4.")
            return
        
        if not self.fields_per_category:
            reply = QMessageBox.question(self, "Configurazione Campi",
                                        "Prima di generare il calendario, devi configurare i campi per categoria.\n\n"
                                        "Vuoi configurarli ora?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.configure_fields()
                if not self.fields_per_category:
                    return
            else:
                return
        
        for cat, fields in self.fields_per_category.items():
            if fields % 4 != 0:
                QMessageBox.warning(self, "Attenzione", 
                                   f"I campi per {cat} ({fields}) non sono multipli di 4.\nRiconfigura i campi.")
                self.configure_fields()
                return
        
        total_blocks = total_fields // 4
        total_cat_blocks = sum(v // 4 for v in self.fields_per_category.values())
        if total_cat_blocks > total_blocks:
            QMessageBox.warning(self, "Attenzione", 
                               f"La somma dei blocchi ({total_cat_blocks}) supera i blocchi totali ({total_blocks}).")
            self.configure_fields()
            return
        
        # Raccogli tutti i gironi squadre
        all_team_groups = {}
        team_categories = [cat for cat in self.parent.current_tournament.categories if "Team" in cat.value]
        
        prefix_map = {
            "Team Open": "TO", "Team Veterans": "TV", "Team Women": "TW",
            "Team U20": "TU20", "Team U16": "TU16", "Team U12": "TU12",
            "Team Eccellenza": "TE", "Team Promozione": "TP", "Team MOICAT": "TM"
        }
        
        for cat in team_categories:
            groups_key = f"team_groups_{cat.value}"
            if groups_key in self.parent.groups:
                for group_name, teams in self.parent.groups[groups_key].items():
                    prefix = prefix_map.get(cat.value, "TX")
                    full_group_name = f"{prefix}-{group_name}"
                    all_team_groups[full_group_name] = teams
        
        if not all_team_groups:
            QMessageBox.warning(self, "Attenzione", "Nessun girone squadre trovato!")
            return
        
        existing_team_matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
        if existing_team_matches:
            reply = QMessageBox.question(self, "Conferma",
                                        f"Esistono già {len(existing_team_matches)} incontri a squadre.\n"
                                        "La nuova generazione li sostituirà. Continuare?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        try:
            new_matches = generate_team_tournament_schedule(
                all_team_groups,
                total_fields=total_fields,
                fields_per_category=self.fields_per_category
            )
            
            self.parent.matches = [m for m in self.parent.matches if not hasattr(m, 'individual_matches')]
            self.parent.matches.extend(new_matches)
            
            self.refresh()
            
            matches_by_category = defaultdict(int)
            for m in new_matches:
                matches_by_category[m.category] += 1
            
            unique_times = sorted(set(m.scheduled_time for m in new_matches if m.scheduled_time))
            total_incontri = len(new_matches)
            max_incontri_per_turno = total_fields // 4
            turni_minimi = (total_incontri + max_incontri_per_turno - 1) // max_incontri_per_turno
            
            stats = "\n".join([f"  {cat}: {count} incontri" for cat, count in sorted(matches_by_category.items())])
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Calendario squadre generato!\n"
                                   f"📊 Totale: {total_incontri} incontri\n"
                                   f"⏰ {len(unique_times)} turni\n"
                                   f"📋 Distribuzione:\n{stats}")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_match_details(self, row, col):
        """Mostra i dettagli della partita a squadre selezionata"""
        match_id_item = self.calendar_table.item(row, 0)
        if not match_id_item:
            return
        
        match_id = match_id_item.text()
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            QMessageBox.warning(self, "Attenzione", "Incontro non trovato")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Dettaglio Incontro - {match.id}")
        dialog.setModal(True)
        dialog.resize(650, 450)
        
        layout = QVBoxLayout(dialog)
        
        header = QLabel(f"<b>{match.player1} vs {match.player2}</b>")
        header.setStyleSheet("font-size: 16px; padding: 10px; background-color: #f0f0f0; border-radius: 4px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        if hasattr(match, 'individual_matches') and match.individual_matches:
            fields = [str(im.table) for im in match.individual_matches if im.table]
            fields_info = QLabel(f"🏟️ Campi occupati: {', '.join(fields)}")
            fields_info.setStyleSheet("padding: 5px; color: #666;")
            layout.addWidget(fields_info)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Tavolo", "Giocatore 1", "Gol 1", "Gol 2", "Giocatore 2", "Stato"])
        
        for i, ind_match in enumerate(match.individual_matches):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(str(ind_match.table)))
            table.setItem(i, 1, QTableWidgetItem(ind_match.player1))
            table.setItem(i, 4, QTableWidgetItem(ind_match.player2))
            
            if ind_match.is_played:
                table.setItem(i, 2, QTableWidgetItem(str(ind_match.goals1)))
                table.setItem(i, 3, QTableWidgetItem(str(ind_match.goals2)))
                status_item = QTableWidgetItem("Giocata")
                status_item.setBackground(Qt.green)
            else:
                table.setItem(i, 2, QTableWidgetItem("-"))
                table.setItem(i, 3, QTableWidgetItem("-"))
                status_item = QTableWidgetItem("")
                status_item.setBackground(Qt.lightGray)
            table.setItem(i, 5, status_item)
        
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        
        if hasattr(match, 'team1_wins') and match.is_played:
            summary = QLabel(f"<b>Risultato finale:</b> {match.team1_wins} - {match.team2_wins}")
        else:
            summary = QLabel("<b>Risultato finale:</b> da giocare")
        summary.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f0f0f0; border-radius: 4px;")
        summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(summary)
        
        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setFixedWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    # ========================================
    # GESTIONE ARBITRI A SQUADRE
    # ========================================
    
    def on_arbitro_double_clicked(self, item):
        """Gestisce doppio clic sulla colonna arbitri."""
        row = item.row()
        col = item.column()
        
        if col != 8:
            return
        
        match_id_item = self.calendar_table.item(row, 0)
        if not match_id_item:
            return
        
        match_id = match_id_item.text()
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            return
        
        self._edit_referees_dialog(match)
    
    def _get_available_referees_for_match(self, match):
        """Restituisce le squadre disponibili per arbitrare una partita secondo regole FISTF."""
        all_teams = []
        for team in self.parent.teams:
            if team.category == match.category:
                all_teams.append(team)
        
        playing_teams = []
        if hasattr(match, 'team1') and match.team1:
            team1 = next((t for t in self.parent.teams if t.id == match.team1), None)
            if team1:
                playing_teams.append(team1)
        if hasattr(match, 'team2') and match.team2:
            team2 = next((t for t in self.parent.teams if t.id == match.team2), None)
            if team2:
                playing_teams.append(team2)
        
        available = []
        
        for team in all_teams:
            if team in playing_teams:
                continue
            
            same_club = False
            for pt in playing_teams:
                if pt.club and team.club == pt.club:
                    same_club = True
                    break
            if same_club:
                continue
            
            if team.group == match.group:
                continue
            
            if len(playing_teams) == 2:
                team1, team2 = playing_teams[0], playing_teams[1]
                if team1.country != team2.country:
                    if team.country == team1.country or team.country == team2.country:
                        continue
            
            available.append(team)
        
        return available
    
    def _edit_referees_dialog(self, match):
        """Dialog per modificare l'arbitro (squadra) per la partita."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Arbitro - {match.id}")
        dialog.setModal(True)
        dialog.resize(500, 350)
        
        layout = QVBoxLayout(dialog)
        
        header = QLabel(f"<b>{match.player1}</b> vs <b>{match.player2}</b>")
        header.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f0f0f0; border-radius: 4px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        info = QLabel(f"Girone: {match.group} | Categoria: {match.category}")
        info.setStyleSheet("color: #666; padding: 5px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        available_referees = self._get_available_referees_for_match(match)
        
        layout.addWidget(QLabel("Seleziona la squadra arbitro:"))
        
        referee_combo = QComboBox()
        referee_combo.addItem("-- Nessun arbitro --", None)
        
        for team in available_referees:
            team_display = team.display_name
            if team.club:
                team_display += f" ({team.club})"
            referee_combo.addItem(team_display, team.id)
        
        current_ref = getattr(match, 'referee', None)
        if current_ref:
            for i in range(referee_combo.count()):
                data = referee_combo.itemData(i)
                if data and hasattr(data, '__str__') and str(data) == current_ref:
                    referee_combo.setCurrentIndex(i)
                    break
                elif data == current_ref:
                    referee_combo.setCurrentIndex(i)
                    break
        
        layout.addWidget(referee_combo)
        
        rules_frame = QFrame()
        rules_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 4px; padding: 8px; margin-top: 10px;")
        rules_layout = QVBoxLayout(rules_frame)
        
        rules_title = QLabel("📋 Regole FISTF per l'arbitro:")
        rules_title.setStyleSheet("font-weight: bold; font-size: 11px;")
        rules_layout.addWidget(rules_title)
        
        rules = [
            "• Non può essere dello stesso club delle squadre che giocano",
            "• Non può essere dello stesso girone",
            "• Non può essere della stessa nazione (se le nazioni sono diverse)"
        ]
        
        for rule in rules:
            rule_label = QLabel(rule)
            rule_label.setStyleSheet("color: #666; font-size: 10px; margin-left: 10px;")
            rules_layout.addWidget(rule_label)
        
        layout.addWidget(rules_frame)
        
        btn_layout = QHBoxLayout()
        
        btn_auto = QPushButton("🎲 Assegna Automaticamente")
        btn_auto.clicked.connect(lambda: self._auto_assign_referee_for_match(match, referee_combo))
        btn_auto.setStyleSheet("background-color: #FF9800; color: white; padding: 8px 15px; border-radius: 4px;")
        btn_layout.addWidget(btn_auto)
        
        btn_layout.addStretch()
        
        btn_save = QPushButton("💾 Salva")
        btn_save.clicked.connect(lambda: self._save_referee(match, referee_combo, dialog))
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("✖ Annulla")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
        
        self.refresh()
    
    def _auto_assign_referee_for_match(self, match, referee_combo):
        available = self._get_available_referees_for_match(match)
        
        if not available:
            QMessageBox.warning(self, "Attenzione", 
                               "Nessuna squadra disponibile per arbitrare!\n"
                               "Verifica che ci siano squadre di altre società/gironi.")
            return
        
        chosen = random.choice(available)
        
        for i in range(referee_combo.count()):
            if referee_combo.itemData(i) == chosen.id:
                referee_combo.setCurrentIndex(i)
                break
        
        QMessageBox.information(self, "Arbitro assegnato", 
                               f"✅ Arbitro selezionato: {chosen.display_name}")
    
    def _save_referee(self, match, referee_combo, dialog):
        referee_id = referee_combo.currentData()
        
        referee_team = None
        if referee_id:
            referee_team = next((t for t in self.parent.teams if t.id == referee_id), None)
        
        # Salva sia il nome che l'ID
        match.referee = referee_team.display_name if referee_team else None
        match.referee_id = referee_id if referee_id else None
        
        # Debug
        print(f"   ✅ Arbitro salvato per {match.id}: {match.referee} (ID: {match.referee_id})")
        
        dialog.accept()
        self.refresh()
        self.parent.statusBar().showMessage(f"✅ Arbitro salvato per {match.id}")
    
    # ========================================
    # MODIFICA MANUALE DEL CALENDARIO
    # ========================================
    
    def manual_edit_schedule(self):
        """Apre il dialog per la modifica manuale del calendario."""
        if not self.parent.matches:
            QMessageBox.warning(self, "Attenzione", "Nessun calendario da modificare. Genera prima il calendario.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifica Manuale Calendario - Squadre")
        dialog.setModal(True)
        dialog.resize(1200, 700)
        
        layout = QVBoxLayout(dialog)
        
        instructions = QLabel(
            "📋 **Istruzioni:**\n"
            "• Seleziona una o più partite (clicca sulle righe)\n"
            "• Usa i pulsanti per modificare campo, orario o arbitro\n"
            "• Le modifiche devono rispettare le regole FISTF:\n"
            "   - Una squadra non può giocare due partite nello stesso turno\n"
            "   - L'arbitro non può essere dello stesso club/nazione delle squadre\n"
            "   - L'ordine delle partite all'interno dei gironi è fisso (FISTF 2.3.2)"
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
            if "Team" in cat.value:
                cat_combo.addItem(cat.value)
        filter_layout.addWidget(cat_combo)
        
        filter_layout.addStretch()
        btn_refresh = QPushButton("🔄 Aggiorna")
        filter_layout.addWidget(btn_refresh)
        
        layout.addWidget(filter_frame)
        
        # Tabella
        table = QTableWidget()
        table.setColumnCount(10)
        table.setHorizontalHeaderLabels([
            "ID", "Girone", "Campi", "Orario", "Squadra 1", "Ris.", "Squadra 2", "Dettaglio", "Arbitro", "Categoria"
        ])
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.ExtendedSelection)
        
        header = table.horizontalHeader()
        for i in range(10):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(table)
        
        # Pannello azioni
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 10px; margin-top: 10px;")
        actions_layout = QHBoxLayout(actions_frame)
        
        btn_edit_field = QPushButton("🏟️ Modifica Campo")
        btn_edit_field.clicked.connect(lambda: self._edit_field_team(table))
        btn_edit_field.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_edit_field)
        
        btn_edit_time = QPushButton("⏰ Modifica Orario")
        btn_edit_time.clicked.connect(lambda: self._edit_time_team(table))
        btn_edit_time.setStyleSheet("background-color: #FF9800; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_edit_time)
        
        btn_edit_referee = QPushButton("👤 Modifica Arbitro")
        btn_edit_referee.clicked.connect(lambda: self._edit_referee_team(table))
        btn_edit_referee.setStyleSheet("background-color: #9C27B0; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_edit_referee)
        
        btn_sort = QPushButton("🔄 Riordina (questo turno)")
        btn_sort.clicked.connect(lambda: self._sort_visible_matches_team(table, turn_combo.currentText(), cat_combo.currentText()))
        btn_sort.setStyleSheet("background-color: #00BCD4; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_sort)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #ccc;")
        actions_layout.addWidget(separator)
        
        btn_swap = QPushButton("🔄 Scambia Campi")
        btn_swap.clicked.connect(lambda: self._swap_fields_team(table))
        btn_swap.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_swap)
        
        btn_auto_referee = QPushButton("🎲 Assegna Arbitri")
        btn_auto_referee.clicked.connect(lambda: self._auto_assign_referees_team(table))
        btn_auto_referee.setStyleSheet("background-color: #00BCD4; color: white; padding: 8px 15px; font-weight: bold;")
        actions_layout.addWidget(btn_auto_referee)
        
        actions_layout.addStretch()
        
        btn_close = QPushButton("✖ Chiudi")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setStyleSheet("background-color: #f44336; color: white; padding: 8px 20px; border-radius: 4px;")
        actions_layout.addWidget(btn_close)
        
        layout.addWidget(actions_frame)
        
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
            
            matches = [m for m in matches if hasattr(m, 'individual_matches')]
            
            for row, match in enumerate(matches):
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(match.id))
                table.setItem(row, 1, QTableWidgetItem(match.group or ""))
                
                if hasattr(match, 'individual_matches') and match.individual_matches:
                    fields = [str(im.table) for im in match.individual_matches if im.table]
                    fields_text = ", ".join(fields) if fields else "4 campi"
                else:
                    fields_text = str(match.field) if match.field else "?"
                table.setItem(row, 2, QTableWidgetItem(fields_text))
                
                table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
                
                team1_name = match.player1
                if hasattr(match, 'team1') and match.team1:
                    team = next((t for t in self.parent.teams if t.id == match.team1), None)
                    if team:
                        team1_name = team.display_name
                table.setItem(row, 4, QTableWidgetItem(team1_name))
                
                if hasattr(match, 'team1_wins') and match.is_played:
                    result_text = f"{match.team1_wins}-{match.team2_wins}"
                else:
                    result_text = "vs"
                table.setItem(row, 5, QTableWidgetItem(result_text))
                
                team2_name = match.player2
                if hasattr(match, 'team2') and match.team2:
                    team = next((t for t in self.parent.teams if t.id == match.team2), None)
                    if team:
                        team2_name = team.display_name
                table.setItem(row, 6, QTableWidgetItem(team2_name))
                
                if hasattr(match, 'individual_matches') and match.individual_matches:
                    details = []
                    for im in match.individual_matches:
                        if im.is_played:
                            details.append(f"T{im.table}: {im.goals1}-{im.goals2}")
                        else:
                            details.append(f"T{im.table}: vs")
                    detail_text = " | ".join(details)
                else:
                    detail_text = "4 incontri"
                table.setItem(row, 7, QTableWidgetItem(detail_text))
                
                referee_text = getattr(match, 'referee', None)
                if not referee_text:
                    referee_text = "Da assegnare"
                referee_item = QTableWidgetItem(referee_text)
                if not getattr(match, 'referee', None):
                    referee_item.setForeground(Qt.red)
                table.setItem(row, 8, referee_item)
                
                table.setItem(row, 9, QTableWidgetItem(match.category))
        
        btn_refresh.clicked.connect(update_table)
        turn_combo.currentTextChanged.connect(update_table)
        cat_combo.currentTextChanged.connect(update_table)
        
        update_table()
        dialog.exec()
        self.refresh()
    
    def _get_selected_matches_team(self, table):
        selected_rows = set()
        for item in table.selectedItems():
            selected_rows.add(item.row())
        
        matches = []
        for row in selected_rows:
            match_id = table.item(row, 0).text()
            for m in self.parent.matches:
                if m.id == match_id and hasattr(m, 'individual_matches'):
                    matches.append(m)
                    break
        return matches
    
    def _check_team_conflict(self, match, new_time, exclude_match=None):
        for m in self.parent.matches:
            if exclude_match and m.id == exclude_match.id:
                continue
            if m.scheduled_time == new_time:
                if m.player1 == match.player1 or m.player2 == match.player1 or \
                   m.player1 == match.player2 or m.player2 == match.player2:
                    return True, m.id
        return False, None
    
    def _check_field_block_conflict(self, match, new_block_start, new_time, exclude_match=None):
        block_fields = list(range(new_block_start, new_block_start + 4))
        for m in self.parent.matches:
            if exclude_match and m.id == exclude_match.id:
                continue
            if m.scheduled_time == new_time:
                if hasattr(m, 'individual_matches') and m.individual_matches:
                    occupied_fields = [im.table for im in m.individual_matches if im.table]
                    if any(f in block_fields for f in occupied_fields):
                        return True, m.id
        return False, None
    
    def _edit_field_team(self, table):
        matches = self._get_selected_matches_team(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        new_block, ok = QInputDialog.getInt(
            self, "Modifica Campo", 
            f"Inserisci il primo campo del blocco (1, 5, 9, ...) per {len(matches)} partite:",
            1, 1, 40, 4
        )
        
        if not ok:
            return
        
        if new_block % 4 != 1:
            QMessageBox.warning(self, "Attenzione", 
                               "Il blocco di campi deve iniziare con un campo dispari (1, 5, 9, 13, ...)")
            return
        
        conflicts = []
        for match in matches:
            conflict, conflict_id = self._check_field_block_conflict(match, new_block, match.scheduled_time, match)
            if conflict:
                conflicts.append(f"{match.id}: blocco {new_block}-{new_block+3} già occupato da {conflict_id}")
        
        if conflicts:
            QMessageBox.warning(self, "Conflitti rilevati", "\n".join(conflicts[:5]))
            return
        
        for match in matches:
            if hasattr(match, 'individual_matches'):
                for i, im in enumerate(match.individual_matches):
                    im.table = new_block + i
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Campo modificato per {len(matches)} partite")
    
    def _edit_time_team(self, table):
        matches = self._get_selected_matches_team(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        times = sorted(set(m.scheduled_time for m in self.parent.matches if m.scheduled_time))
        new_time, ok = QInputDialog.getItem(
            self, "Modifica Orario", 
            f"Seleziona il nuovo orario per {len(matches)} partite:",
            times, 0, False
        )
        
        if not ok:
            return
        
        conflicts = []
        for match in matches:
            conflict, conflict_id = self._check_team_conflict(match, new_time, match)
            if conflict:
                conflicts.append(f"{match.id}: {match.player1} o {match.player2} già in {conflict_id}")
        
        if conflicts:
            QMessageBox.warning(self, "Conflitti rilevati", "\n".join(conflicts[:5]))
            return
        
        for match in matches:
            match.scheduled_time = new_time
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Orario modificato per {len(matches)} partite")
    
    def _edit_referee_team(self, table):
        matches = self._get_selected_matches_team(table)
        if len(matches) != 1:
            QMessageBox.warning(self, "Attenzione", "Seleziona una sola partita per modificare l'arbitro")
            return
        
        match = matches[0]
        self._edit_referees_dialog(match)
    
    def _swap_fields_team(self, table):
        matches = self._get_selected_matches_team(table)
        
        if len(matches) != 2:
            QMessageBox.warning(self, "Attenzione", "Seleziona esattamente 2 partite")
            return
        
        match1, match2 = matches[0], matches[1]
        
        if match1.scheduled_time != match2.scheduled_time:
            QMessageBox.warning(self, "Attenzione", "Le due partite devono avere lo stesso orario")
            return
        
        if hasattr(match1, 'individual_matches') and hasattr(match2, 'individual_matches'):
            fields1 = [im.table for im in match1.individual_matches]
            fields2 = [im.table for im in match2.individual_matches]
            
            for i, im in enumerate(match1.individual_matches):
                im.table = fields2[i] if i < len(fields2) else im.table
            for i, im in enumerate(match2.individual_matches):
                im.table = fields1[i] if i < len(fields1) else im.table
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Campi scambiati tra {match1.id} e {match2.id}")
    
    def _auto_assign_referees_team(self, table):
        matches = self._get_selected_matches_team(table)
        if not matches:
            QMessageBox.warning(self, "Attenzione", "Seleziona almeno una partita")
            return
        
        assigned = 0
        for match in matches:
            available = self._get_available_referees_for_match(match)
            
            if not available:
                continue
            
            chosen = random.choice(available)
            match.referee = chosen.display_name
            assigned += 1
        
        self.refresh()
        QMessageBox.information(self, "Successo", f"Arbitri assegnati per {assigned}/{len(matches)} partite")
    
    def _sort_visible_matches_team(self, table, turn_filter, cat_filter):
        visible_matches = []
        for row in range(table.rowCount()):
            match_id = table.item(row, 0).text()
            for m in self.parent.matches:
                if m.id == match_id and hasattr(m, 'individual_matches'):
                    visible_matches.append(m)
                    break
        
        if not visible_matches:
            QMessageBox.warning(self, "Attenzione", "Nessuna partita da riordinare")
            return
        
        sorted_matches = sorted(visible_matches, key=lambda m: (
            m.scheduled_time if m.scheduled_time else "99:99",
            m.group if m.group else ""
        ))
        
        table.setRowCount(0)
        for match in sorted_matches:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(match.id))
            table.setItem(row, 1, QTableWidgetItem(match.group or ""))
            
            if hasattr(match, 'individual_matches') and match.individual_matches:
                fields = [str(im.table) for im in match.individual_matches if im.table]
                fields_text = ", ".join(fields) if fields else "4 campi"
            else:
                fields_text = str(match.field) if match.field else "?"
            table.setItem(row, 2, QTableWidgetItem(fields_text))
            
            table.setItem(row, 3, QTableWidgetItem(match.scheduled_time or ""))
            
            team1_name = match.player1
            if hasattr(match, 'team1') and match.team1:
                team = next((t for t in self.parent.teams if t.id == match.team1), None)
                if team:
                    team1_name = team.display_name
            table.setItem(row, 4, QTableWidgetItem(team1_name))
            
            if hasattr(match, 'team1_wins') and match.is_played:
                result_text = f"{match.team1_wins}-{match.team2_wins}"
            else:
                result_text = "vs"
            table.setItem(row, 5, QTableWidgetItem(result_text))
            
            team2_name = match.player2
            if hasattr(match, 'team2') and match.team2:
                team = next((t for t in self.parent.teams if t.id == match.team2), None)
                if team:
                    team2_name = team.display_name
            table.setItem(row, 6, QTableWidgetItem(team2_name))
            
            if hasattr(match, 'individual_matches') and match.individual_matches:
                details = []
                for im in match.individual_matches:
                    if im.is_played:
                        details.append(f"T{im.table}: {im.goals1}-{im.goals2}")
                    else:
                        details.append(f"T{im.table}: vs")
                detail_text = " | ".join(details)
            else:
                detail_text = "4 incontri"
            table.setItem(row, 7, QTableWidgetItem(detail_text))
            
            referee_text = getattr(match, 'referee', None)
            if not referee_text:
                referee_text = "Da assegnare"
            table.setItem(row, 8, QTableWidgetItem(referee_text))
            
            table.setItem(row, 9, QTableWidgetItem(match.category))
        
        QMessageBox.information(self, "Successo", f"✅ Riordinate {len(sorted_matches)} partite")
    
    # ========================================
    # METODI EXPORT/IMPORT
    # ========================================
    
    def export_schedule(self):
        """Esporta calendario in Excel"""
        if not hasattr(self.parent, 'matches') or not self.parent.matches:
            QMessageBox.warning(self, "Attenzione", "Nessun calendario da esportare")
            return
        
        team_matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
        if not team_matches:
            QMessageBox.warning(self, "Attenzione", "Nessun incontro a squadre da esportare")
            return
        
        import pandas as pd
        
        data = []
        for m in team_matches:
            individual_details = []
            for i, im in enumerate(m.individual_matches, 1):
                if im.is_played:
                    individual_details.append(f"T{im.table}: {im.goals1}-{im.goals2}")
                else:
                    individual_details.append(f"T{im.table}: vs")
            
            data.append({
                "ID": m.id, "Categoria": m.category, "Fase": m.phase, "Girone": m.group,
                "Campi": ", ".join([str(im.table) for im in m.individual_matches if im.table]),
                "Orario": m.scheduled_time, "Squadra 1": m.player1, "Squadra 2": m.player2,
                "Risultato Squadre": f"{m.team1_wins}-{m.team2_wins}" if m.is_played else "vs",
                "Dettaglio Incontri": " | ".join(individual_details),
                "Arbitro": getattr(m, 'referee', 'Da assegnare'),
                "Stato": "Giocata" if m.is_played else ("Forfait" if m.is_forfeit else "")
            })
        
        df = pd.DataFrame(data)
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f"calendario_squadre_{timestamp}.xlsx"
        
        try:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Successo", f"✅ File salvato:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def export_calendar_csv(self):
        """Esporta il calendario squadre in CSV."""
        if not self.parent.matches:
            return
        
        team_matches = [m for m in self.parent.matches if hasattr(m, 'individual_matches')]
        if not team_matches:
            return
        
        from utils.helpers import export_calendar_to_csv
        from datetime import datetime
        
        tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"calendario_squadre_{tournament_name}_{timestamp}.csv"
        
        try:
            filepath = export_calendar_to_csv(team_matches, filename, tournament_name)
            QMessageBox.information(self, "Successo", f"✅ Calendario esportato in:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def import_calendar_csv(self):
        """Importa il calendario squadre da CSV."""
        from pathlib import Path
        from models.team_match import TeamMatch, IndividualMatchResult
        from models.match import MatchStatus
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona file CSV calendario",
            str(Path("data").absolute()), "File CSV (*.csv);;Tutti i file (*.*)"
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
                individual_matches = [
                    IndividualMatchResult(player1="", player2="", table=i+1, status=None)
                    for i in range(4)
                ]
                
                status = None
                if data["status"] in ["Giocata", "COMPLETED"]:
                    status = MatchStatus.COMPLETED
                elif data["status"] in ["Forfait", "FORFEIT"]:
                    status = MatchStatus.FORFEIT
                
                match = TeamMatch(
                    id=data["id"], category=data["category"], phase=data["phase"],
                    group=data["group"], scheduled_time=data["scheduled_time"],
                    player1=data["player1"], player2=data["player2"],
                    status=status, individual_matches=individual_matches
                )
                
                if "arbitro" in data and data["arbitro"] and data["arbitro"] != "Da assegnare":
                    match.referee = data["arbitro"]
                
                if data["result"] != "vs" and '-' in data["result"]:
                    parts = data["result"].split('-')
                    if len(parts) == 2:
                        try:
                            wins1 = int(parts[0].strip())
                            wins2 = int(parts[1].strip())
                            for i in range(4):
                                if i < wins1:
                                    individual_matches[i].goals1 = 1
                                    individual_matches[i].goals2 = 0
                                elif i < wins1 + wins2:
                                    individual_matches[i].goals1 = 0
                                    individual_matches[i].goals2 = 1
                                else:
                                    individual_matches[i].goals1 = 0
                                    individual_matches[i].goals2 = 0
                                individual_matches[i].status = MatchStatus.COMPLETED
                            match.status = MatchStatus.COMPLETED
                        except:
                            pass
                
                new_matches.append(match)
            
            self.parent.matches = [m for m in self.parent.matches if not hasattr(m, 'individual_matches')]
            self.parent.matches.extend(new_matches)
            self.refresh()
            
            QMessageBox.information(self, "Successo", f"✅ Importate {len(new_matches)} partite da CSV")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_calendar_template(self):
        """Esporta un template CSV per il calendario squadre."""
        from utils.helpers import export_calendar_template
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"template_calendario_squadre_{timestamp}.csv"
        
        try:
            filepath = export_calendar_template(filename, is_team=True)
            QMessageBox.information(self, "Successo", 
                                   f"✅ Template creato in:\n{filepath}\n\n"
                                   f"Compila il file e poi usa 'Importa CSV' per caricare il calendario.\n\n"
                                   f"⚠️ Nota: Ogni incontro occupa 4 campi consecutivi.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def on_tab_selected(self):
        self.refresh()