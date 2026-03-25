"""
Tab per la fase finale a squadre (eliminazione diretta).
FISTF Tournament Organisers' Handbook 2025-26, Sezione 2.2.5
Gestione pareggi: Sudden Death (10 min, primo gol su qualsiasi tavolo) → Shoot-out
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QComboBox, QSpinBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QDialog, QFrame, QGridLayout,
                               QScrollArea, QFileDialog, QTextEdit, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import random

from ui.base_tab import BaseTab
from models.match import MatchStatus
from core.team_knockout_generator import TeamKnockoutGenerator
from core.team_standings_calculator import TeamStandingsCalculator


class TeamKnockoutTab(BaseTab):
    """Tab per la fase finale a squadre"""
    
    def __init__(self, parent):
        super().__init__(parent, "🏆 Fase Finale Squadre")
        
        # Riferimenti UI
        self.knockout_category = None
        self.knockout_filter = None
        self.knockout_table = None
        self.knockout_phase = None
        self.knockout_match = None
        self.knockout_goals1 = None
        self.knockout_goals2 = None
        self.lbl_stats = None
        self.btn_generate = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab"""
        
        # ========================================
        # PANNELLO GENERAZIONE
        # ========================================
        controls_group = QGroupBox("Generazione Tabellone")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #9C27B0;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Categoria:"))
        self.knockout_category = QComboBox()
        if self.parent.current_tournament:
            for cat in self.parent.current_tournament.categories:
                if "Team" in cat.value:
                    self.knockout_category.addItem(cat.value)
        self.knockout_category.currentTextChanged.connect(self._update_generate_button_state)
        controls_layout.addWidget(self.knockout_category)
        
        self.btn_generate = QPushButton("🎲 Genera Fase Finale Squadre")
        self.btn_generate.clicked.connect(self.generate_knockout_stage)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_generate.setEnabled(False)
        controls_layout.addWidget(self.btn_generate)
        
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
        if self.parent.current_tournament:
            for cat in self.parent.current_tournament.categories:
                if "Team" in cat.value:
                    self.knockout_filter.addItem(cat.value)
        self.knockout_filter.currentTextChanged.connect(self.refresh)
        filter_layout.addWidget(self.knockout_filter)
        
        filter_layout.addStretch()
        
        btn_debug = QPushButton("🔍 Debug Token")
        btn_debug.clicked.connect(self.debug_tokens)
        btn_debug.setStyleSheet("background-color: #607D8B; color: white; padding: 5px 15px; border-radius: 4px;")
        filter_layout.addWidget(btn_debug)
        
        btn_propagate = QPushButton("🔄 Forza Propagazione")
        btn_propagate.clicked.connect(self.propagate_winners)
        btn_propagate.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 15px; border-radius: 4px;")
        filter_layout.addWidget(btn_propagate)
        
        btn_fix = QPushButton("🔧 Ripara Partite")
        btn_fix.clicked.connect(self.fix_all_team_matches)
        btn_fix.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 4px;")
        filter_layout.addWidget(btn_fix)
        
        self.content_layout.addWidget(filter_group)
        
        # ========================================
        # TABELLA PARTITE
        # ========================================
        self.knockout_table = QTableWidget()
        self.knockout_table.setColumnCount(7)
        self.knockout_table.setHorizontalHeaderLabels([
            "Fase", "Partita", "Squadra 1", "Ris.", "Squadra 2", "Dettaglio", "Stato"
        ])
        
        self.knockout_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        header = self.knockout_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.knockout_table.cellDoubleClicked.connect(self.on_match_double_clicked)
        
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
        
        quick_layout.addWidget(QLabel("Risultato Squadre:"))
        
        self.knockout_goals1 = QSpinBox()
        self.knockout_goals1.setMinimum(0)
        self.knockout_goals1.setMaximum(4)
        self.knockout_goals1.setFixedWidth(90)
        self.knockout_goals1.setAlignment(Qt.AlignCenter)
        quick_layout.addWidget(self.knockout_goals1)
        
        quick_layout.addWidget(QLabel("-"))
        
        self.knockout_goals2 = QSpinBox()
        self.knockout_goals2.setMinimum(0)
        self.knockout_goals2.setMaximum(4)
        self.knockout_goals2.setFixedWidth(90)
        self.knockout_goals2.setAlignment(Qt.AlignCenter)
        quick_layout.addWidget(self.knockout_goals2)
        
        btn_save = QPushButton("💾 Salva")
        btn_save.clicked.connect(self.save_quick_result)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 4px;")
        quick_layout.addWidget(btn_save)
        
        btn_details = QPushButton("📋 Inserisci Dettaglio")
        btn_details.clicked.connect(self.show_match_editor_dialog)
        btn_details.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px; border-radius: 4px;")
        quick_layout.addWidget(btn_details)
        
        quick_layout.addStretch()
        self.content_layout.addWidget(quick_group)
        
        # ========================================
        # STATISTICHE
        # ========================================
        stats_layout = QHBoxLayout()
        self.lbl_stats = QLabel("Partite fase finale: 0 | Giocate: 0 | Da giocare: 0")
        stats_layout.addWidget(self.lbl_stats)
        stats_layout.addStretch()
        self.content_layout.addLayout(stats_layout)
    
    # ========================================
    # VERIFICA PARTITE GIRONI
    # ========================================
    
    def _are_all_group_matches_played(self, category: str) -> bool:
        """Verifica se tutte le partite dei gironi per una categoria sono state giocate."""
        group_matches = [m for m in self.parent.matches 
                        if hasattr(m, 'individual_matches') 
                        and hasattr(m, 'category')
                        and m.category == category 
                        and hasattr(m, 'phase')
                        and m.phase == "Groups"]
        
        if not group_matches:
            return False
        
        for match in group_matches:
            if not self._is_match_played(match):
                return False
        
        return True
    
    def _update_generate_button_state(self):
        """Aggiorna lo stato del pulsante 'Genera Fase Finale'."""
        cat = self.knockout_category.currentText()
        if not cat:
            self.btn_generate.setEnabled(False)
            self.btn_generate.setToolTip("Seleziona una categoria")
            return
        
        all_played = self._are_all_group_matches_played(cat)
        self.btn_generate.setEnabled(all_played)
        
        if not all_played:
            self.btn_generate.setToolTip("⚠️ Tutte le partite dei gironi devono essere completate prima di generare la fase finale.")
        else:
            self.btn_generate.setToolTip("🎲 Genera il tabellone della fase finale")
    
    def _is_match_played(self, match) -> bool:
        """Verifica se una partita a squadre è stata giocata."""
        if hasattr(match, 'individual_matches') and match.individual_matches:
            for im in match.individual_matches:
                if im.goals1 is None or im.goals2 is None:
                    return False
            return True
        
        if hasattr(match, 'status'):
            if match.status == MatchStatus.COMPLETED:
                return True
        
        if hasattr(match, 'winner') and match.winner:
            return True
        
        return False
    
    def _get_status_text(self, status) -> str:
        """Converte lo status in stringa."""
        if status is None:
            return ""
        if hasattr(status, 'value'):
            return status.value
        return str(status)
    
    # ========================================
    # METODI PRINCIPALI
    # ========================================
    
    def refresh(self):
        """Aggiorna la tabella della fase finale"""
        self.knockout_table.setRowCount(0)
        
        filter_cat = self.knockout_filter.currentText()
        
        knockout_matches = [m for m in self.parent.matches 
                           if hasattr(m, 'individual_matches')
                           and hasattr(m, 'phase')
                           and m.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]]
        
        if filter_cat != "Tutte":
            knockout_matches = [m for m in knockout_matches if m.category == filter_cat]
        
        phase_order = {"BARRAGE": 0, "R64": 1, "R32": 2, "R16": 3, "QF": 4, "SF": 5, "F": 6}
        knockout_matches.sort(key=lambda m: (phase_order.get(m.phase, 99), m.id))
        
        played_count = 0
        
        for row, match in enumerate(knockout_matches):
            self.knockout_table.insertRow(row)
            
            phase_display = {
                "BARRAGE": "Spareggio",
                "QF": "Quarti",
                "SF": "Semifinale",
                "F": "Finale",
                "R16": "16esimi",
                "R32": "32esimi",
                "R64": "64esimi"
            }.get(match.phase, match.phase)
            
            phase_item = QTableWidgetItem(phase_display)
            phase_item.setTextAlignment(Qt.AlignCenter)
            self.knockout_table.setItem(row, 0, phase_item)
            
            display_id = match.id.split('_', 1)[1] if '_' in match.id else match.id
            id_item = QTableWidgetItem(display_id)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.knockout_table.setItem(row, 1, id_item)
            
            team1_display = match.player1 if match.player1 else ""
            if team1_display and team1_display.startswith("WIN "):
                team1_display = f"⚡ {team1_display}"
            self.knockout_table.setItem(row, 2, QTableWidgetItem(team1_display))
            
            result_text = "vs"
            is_played = self._is_match_played(match)
            
            if is_played:
                wins1 = 0
                wins2 = 0
                for im in match.individual_matches:
                    if im.goals1 is not None and im.goals2 is not None:
                        if im.goals1 > im.goals2:
                            wins1 += 1
                        elif im.goals2 > im.goals1:
                            wins2 += 1
                result_text = f"{wins1}-{wins2}"
                played_count += 1
            
            result_item = QTableWidgetItem(result_text)
            result_item.setTextAlignment(Qt.AlignCenter)
            
            if is_played:
                if wins1 > wins2:
                    result_item.setBackground(QColor(144, 238, 144))
                elif wins2 > wins1:
                    result_item.setBackground(QColor(255, 200, 200))
                else:
                    result_item.setBackground(QColor(255, 255, 200))
            
            self.knockout_table.setItem(row, 3, result_item)
            
            team2_display = match.player2 if match.player2 else ""
            if team2_display and team2_display.startswith("WIN "):
                team2_display = f"⚡ {team2_display}"
            self.knockout_table.setItem(row, 4, QTableWidgetItem(team2_display))
            
            if hasattr(match, 'individual_matches') and match.individual_matches:
                details = []
                for i, im in enumerate(match.individual_matches, 1):
                    if im.goals1 is not None and im.goals2 is not None:
                        details.append(f"T{i}: {im.goals1}-{im.goals2}")
                    else:
                        details.append(f"T{i}: vs")
                detail_text = " | ".join(details)
            else:
                detail_text = "4 incontri"
            
            detail_item = QTableWidgetItem(detail_text)
            detail_item.setToolTip("Doppio clic per inserire risultati dettagliati")
            self.knockout_table.setItem(row, 5, detail_item)
            
            status_text = self._get_status_text(match.status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            if is_played:
                status_item.setBackground(QColor(144, 238, 144))
            elif status_text:
                status_item.setBackground(QColor(211, 211, 211))
            
            self.knockout_table.setItem(row, 6, status_item)
        
        total = len(knockout_matches)
        self.lbl_stats.setText(f"Partite fase finale: {total} | Giocate: {played_count} | Da giocare: {total - played_count}")
        
        self.update_match_list()
        self._update_generate_button_state()
    
    def update_match_list(self):
        """Aggiorna la lista delle partite per fase"""
        self.knockout_match.clear()
        
        phase = self.knockout_phase.currentText()
        filter_cat = self.knockout_filter.currentText()
        
        count = 0
        for match in self.parent.matches:
            if (hasattr(match, 'individual_matches') and 
                hasattr(match, 'phase') and
                match.phase == phase and 
                not self._is_match_played(match)):
                
                if filter_cat == "Tutte" or match.category == filter_cat:
                    team1 = match.player1[:30] + "..." if len(match.player1) > 30 else match.player1
                    team2 = match.player2[:30] + "..." if len(match.player2) > 30 else match.player2
                    display_text = f"{match.id} - {team1} vs {team2}"
                    self.knockout_match.addItem(display_text, match.id)
                    count += 1
        
        if count == 0:
            self.knockout_match.addItem("Nessuna partita disponibile")
    
    def generate_knockout_stage(self):
        """Genera il tabellone della fase finale per squadre"""
        cat = self.knockout_category.currentText()
        if not cat:
            QMessageBox.warning(self, "Attenzione", "Seleziona una categoria")
            return
        
        if not self._are_all_group_matches_played(cat):
            QMessageBox.warning(self, "Attenzione", 
                               f"Non tutte le partite dei gironi per {cat} sono state completate.\n\n"
                               "Inserisci tutti i risultati prima di generare la fase finale.")
            return
        
        print(f"\n🎲 Generazione fase finale per {cat}")
        
        groups_key = f"team_groups_{cat}"
        if groups_key not in self.parent.groups:
            QMessageBox.warning(self, "Attenzione", f"Nessun girone per la categoria {cat}")
            return
        
        calculator = TeamStandingsCalculator()
        group_standings = {}
        
        group_number = 1
        for group_name in sorted(self.parent.groups[groups_key].keys()):
            teams = self.parent.groups[groups_key][group_name]
            
            prefix = self._get_prefix(cat)
            full_group = f"{prefix}-{group_name}"
            
            group_matches = [m for m in self.parent.matches 
                            if hasattr(m, 'individual_matches')
                            and hasattr(m, 'group')
                            and m.group == full_group]
            
            print(f"\n   Calcolo classifica per girone {group_name} ({len(teams)} squadre, {len(group_matches)} partite)")
            
            df = calculator.calculate_group_standings(group_name, teams, group_matches)
            
            if not df.empty:
                group_teams = []
                for _, row in df.iterrows():
                    team = next((t for t in teams if t.display_name == row["Squadra"]), None)
                    if team:
                        group_teams.append(team)
                
                if group_teams:
                    group_standings[str(group_number)] = group_teams
                    print(f"   ✅ Girone {group_name} → numero {group_number}: {len(group_teams)} squadre")
                    group_number += 1
            else:
                sorted_teams = sorted(teams, key=lambda t: t.seed if t.seed else 999)
                if sorted_teams:
                    group_standings[str(group_number)] = sorted_teams
                    print(f"   ⚠️ Girone {group_name} → usando ordine seed: {len(sorted_teams)} squadre")
                    group_number += 1
        
        if not group_standings:
            QMessageBox.warning(self, "Errore", "Impossibile calcolare classifiche")
            return
        
        group_sizes = [len(teams) for teams in self.parent.groups[groups_key].values()]
        temp_generator = TeamKnockoutGenerator()
        qualifiers_per_group = temp_generator.get_qualifiers_per_group(group_sizes)
        
        print(f"\n📊 Qualificati per girone:")
        for g_num, q in qualifiers_per_group.items():
            print(f"   Girone {g_num}: {q} qualificati")
        
        generator = TeamKnockoutGenerator()
        qualified = generator.get_qualified_teams(group_standings, qualifiers_per_group)
        
        print(f"\n🏆 Squadre qualificate:")
        for group_num, teams in qualified.items():
            print(f"   Gruppo {group_num}: {[t.display_name for t in teams]}")
        
        try:
            category_prefix = self._get_prefix(cat)
            
            knockout_matches = generator.generate_bracket(
                len(group_standings),
                qualified,
                category=cat,
                category_prefix=category_prefix
            )
            
            # Rimuovi vecchie partite di fase finale per questa categoria
            self.parent.matches = [m for m in self.parent.matches 
                                  if not (hasattr(m, 'category') and m.category == cat 
                                         and hasattr(m, 'phase') and m.phase in 
                                         ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"])]
            
            self.parent.matches.extend(knockout_matches)
            
            print(f"\n✅ Generate {len(knockout_matches)} partite di fase finale per {cat}")
            for m in knockout_matches:
                team1 = m.player1 if m.player1 else m.token1
                team2 = m.player2 if m.player2 else m.token2
                print(f"   {m.id}: {team1} vs {team2}")
                print(f"      individual_matches: {len(m.individual_matches) if m.individual_matches else 0}")
            
            self.refresh()
            
            QMessageBox.information(self, "Successo", 
                                   f"✅ Fase finale per {cat} generata!\n{len(knockout_matches)} partite")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _get_prefix(self, category):
        """Restituisce il prefisso per una categoria"""
        prefix_map = {
            "Team Open": "TO",
            "Team Veterans": "TV",
            "Team Women": "TW",
            "Team U20": "TU20",
            "Team U16": "TU16",
            "Team U12": "TU12",
            "Team Eccellenza": "TE",
            "Team Promozione": "TP",
            "Team MOICAT": "TM"
        }
        return prefix_map.get(category, "TX")
    
    # ========================================
    # GESTIONE PARTITE
    # ========================================
    
    def on_match_double_clicked(self, row, col):
        """Gestisce doppio clic su partita"""
        match_id_item = self.knockout_table.item(row, 1)
        if not match_id_item:
            return
        
        phase_item = self.knockout_table.item(row, 0)
        if not phase_item:
            return
        
        phase_map = {
            "Spareggio": "BARRAGE",
            "Quarti": "QF",
            "Semifinale": "SF",
            "Finale": "F",
            "16esimi": "R16",
            "32esimi": "R32",
            "64esimi": "R64"
        }
        
        phase_code = phase_map.get(phase_item.text(), phase_item.text())
        match_id = f"{phase_code}_{match_id_item.text()}"
        
        match = None
        for m in self.parent.matches:
            if m.id.endswith(match_id) or m.id == match_id:
                match = m
                break
        
        if match and hasattr(match, 'individual_matches'):
            self.show_match_editor(match)
    
    def show_match_editor_dialog(self):
        """Mostra dialog per inserimento dettagliato"""
        if self.knockout_match.count() == 0 or self.knockout_match.currentText() == "Nessuna partita disponibile":
            QMessageBox.warning(self, "Attenzione", "Seleziona una partita")
            return
        
        match_id = self.knockout_match.currentData()
        if not match_id:
            return
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            QMessageBox.warning(self, "Errore", "Partita non trovata")
            return
        
        self.show_match_editor(match)
    
    def fix_all_team_matches(self):
        """Ripara tutte le partite a squadre creando individual_matches mancanti"""
        from models.team_match import IndividualMatchResult
        
        print("\n" + "="*70)
        print("🔧 RIPARAZIONE PARTITE A SQUADRE")
        print("="*70)
        
        fixed = 0
        for match in self.parent.matches:
            if hasattr(match, 'phase') and match.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]:
                if not hasattr(match, 'individual_matches') or match.individual_matches is None:
                    print(f"   ⚠️ {match.id}: individual_matches mancante")
                    match.individual_matches = []
                    for i in range(4):
                        match.individual_matches.append(
                            IndividualMatchResult(
                                player1="",
                                player2="",
                                table=i+1,
                                goals1=None,
                                goals2=None,
                                status=None,
                                notes=""
                            )
                        )
                    fixed += 1
                
                elif len(match.individual_matches) == 0:
                    print(f"   ⚠️ {match.id}: individual_matches vuoto")
                    for i in range(4):
                        match.individual_matches.append(
                            IndividualMatchResult(
                                player1="",
                                player2="",
                                table=i+1,
                                goals1=None,
                                goals2=None,
                                status=None,
                                notes=""
                            )
                        )
                    fixed += 1
                
                elif len(match.individual_matches) != 4:
                    print(f"   ⚠️ {match.id}: {len(match.individual_matches)} incontri (attesi 4)")
                    while len(match.individual_matches) < 4:
                        match.individual_matches.append(
                            IndividualMatchResult(
                                player1="",
                                player2="",
                                table=len(match.individual_matches)+1,
                                goals1=None,
                                goals2=None,
                                status=None,
                                notes=""
                            )
                        )
                    fixed += 1
        
        if fixed > 0:
            print(f"\n✅ Riparate {fixed} partite a squadre")
            self.refresh()
            QMessageBox.information(self, "Successo", f"Riparate {fixed} partite a squadre")
        else:
            print("\n✅ Nessuna riparazione necessaria")
            QMessageBox.information(self, "Info", "Tutte le partite sono corrette")
    
    def show_match_editor(self, match):
        """
        Mostra editor dettagliato per la partita con selezione giocatori.
        Stile simile a team_results_tab.
        Gestisce i pareggi con Sudden Death e Shoot-out.
        """
        if not match:
            return
        
        # ========================================
        # FIX: CREA INDIVIDUAL_MATCHES SE MANCANTI
        # ========================================
        from models.team_match import IndividualMatchResult
        
        if not hasattr(match, 'individual_matches') or match.individual_matches is None:
            print(f"⚠️ Partita {match.id}: individual_matches mancante! Creazione...")
            match.individual_matches = []
        
        if len(match.individual_matches) == 0:
            print(f"⚠️ Partita {match.id}: individual_matches vuoto! Creazione 4 incontri...")
            for i in range(4):
                match.individual_matches.append(
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None,
                        notes=""
                    )
                )
            print(f"   ✅ Creati {len(match.individual_matches)} incontri")
        
        elif len(match.individual_matches) < 4:
            print(f"⚠️ Partita {match.id}: solo {len(match.individual_matches)} incontri, completamento...")
            while len(match.individual_matches) < 4:
                match.individual_matches.append(
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=len(match.individual_matches)+1,
                        goals1=None,
                        goals2=None,
                        status=None,
                        notes=""
                    )
                )
            print(f"   ✅ Ora {len(match.individual_matches)} incontri")
        
        # ========================================
        # CREA DIALOG
        # ========================================
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Inserisci Risultati - {match.id}")
        dialog.setModal(True)
        dialog.resize(1100, 700)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        
        # ========================================
        # HEADER
        # ========================================
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 12px;")
        header_layout = QHBoxLayout(header_frame)
        
        team1_label = QLabel(f"🔵 {match.player1}")
        team1_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(team1_label)
        
        header_layout.addStretch()
        
        vs_label = QLabel("VS")
        vs_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e67e22;")
        header_layout.addWidget(vs_label)
        
        header_layout.addStretch()
        
        team2_label = QLabel(f"🔴 {match.player2}")
        team2_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(team2_label)
        
        layout.addWidget(header_frame)
        
        # ========================================
        # CARICA GIOCATORI
        # ========================================
        team1_players = []
        team2_players = []
        team1_name = match.player1
        team2_name = match.player2
        
        if hasattr(self.parent, 'teams'):
            for team in self.parent.teams:
                if team.display_name == team1_name:
                    team1_players = team.players.copy()
                if team.display_name == team2_name:
                    team2_players = team.players.copy()
        
        if not team1_players and hasattr(match, 'team1') and match.team1:
            team1 = next((t for t in self.parent.teams if t.id == match.team1), None)
            if team1:
                team1_players = team1.players.copy()
                team1_name = team1.display_name
        
        if not team2_players and hasattr(match, 'team2') and match.team2:
            team2 = next((t for t in self.parent.teams if t.id == match.team2), None)
            if team2:
                team2_players = team2.players.copy()
                team2_name = team2.display_name
        
        # ========================================
        # INFO SOSTITUZIONI
        # ========================================
        subs_info_frame = QFrame()
        subs_info_frame.setStyleSheet("background-color: #fff3e0; border-radius: 6px; padding: 6px;")
        subs_info_layout = QHBoxLayout(subs_info_frame)
        subs_info_label = QLabel("🔄 Sostituzioni: Squadra 1: 0/2 | Squadra 2: 0/2")
        subs_info_label.setStyleSheet("color: #e67e22; font-size: 11px;")
        subs_info_layout.addWidget(subs_info_label)
        subs_info_layout.addStretch()
        layout.addWidget(subs_info_frame)
        
        # ========================================
        # TABELLA INCONTRI (STILE TEAM_RESULTS_TAB)
        # ========================================
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Tavolo", "Giocatore 1", "Gol", "", "Gol", "Giocatore 2", "Note", "Sost."
        ])
        
        table.setColumnWidth(0, 70)
        table.setColumnWidth(1, 160)
        table.setColumnWidth(2, 90)
        table.setColumnWidth(3, 20)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 160)
        table.setColumnWidth(6, 50)
        table.setColumnWidth(7, 60)
        
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        spin1_widgets = []
        spin2_widgets = []
        combo1_widgets = []
        combo2_widgets = []
        note_buttons = []
        subs_buttons = []
        substitutions_used = {"team1": 0, "team2": 0}
        
        for i, im in enumerate(match.individual_matches):
            table.insertRow(i)
            table.setRowHeight(i, 50)
            
            # Tavolo
            item = QTableWidgetItem(str(im.table))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Arial", 11, QFont.Bold))
            table.setItem(i, 0, item)
            
            # Giocatore 1 (ComboBox)
            combo1 = QComboBox()
            combo1.addItem("-- Seleziona --")
            for player in team1_players:
                combo1.addItem(player.display_name)
            if im.player1 and im.player1 != "":
                idx = combo1.findText(im.player1)
                if idx >= 0:
                    combo1.setCurrentIndex(idx)
            combo1.setStyleSheet("""
                QComboBox {
                    border: 1px solid #2196F3;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 10px;
                }
            """)
            combo1.currentTextChanged.connect(lambda text, idx=i: self._update_player_assignment(match, idx, text, "team1"))
            table.setCellWidget(i, 1, combo1)
            combo1_widgets.append(combo1)
            
            # Gol 1
            spin1 = QSpinBox()
            spin1.setMinimum(0)
            spin1.setMaximum(20)
            spin1.setFixedSize(80, 30)
            spin1.setAlignment(Qt.AlignCenter)
            if im.goals1 is not None:
                spin1.setValue(im.goals1)
            spin1.setStyleSheet("""
                QSpinBox {
                    border: 1px solid #f44336;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 11px;
                }
                QSpinBox::up-button {
                    width: 16px;
                    height: 12px;
                    subcontrol-position: top right;
                }
                QSpinBox::down-button {
                    width: 16px;
                    height: 12px;
                    subcontrol-position: bottom right;
                }
                QSpinBox::up-arrow {
                    width: 10px;
                    height: 6px;
                }
                QSpinBox::down-arrow {
                    width: 10px;
                    height: 6px;
                }
            """)
            
            table.setCellWidget(i, 2, spin1)
            spin1_widgets.append(spin1)
            
            # Trattino
            dash = QLabel("-")
            dash.setAlignment(Qt.AlignCenter)
            dash.setStyleSheet("font-weight: bold;")
            table.setCellWidget(i, 3, dash)
            
            # Gol 2
            spin2 = QSpinBox()
            spin2.setMinimum(0)
            spin2.setMaximum(20)
            spin2.setFixedSize(80, 30)
            spin2.setAlignment(Qt.AlignCenter)
            if im.goals2 is not None:
                spin2.setValue(im.goals2)
            spin2.setStyleSheet("""
                QSpinBox {
                    border: 1px solid #f44336;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 11px;
                }
                QSpinBox::up-button {
                    width: 16px;
                    height: 12px;
                    subcontrol-position: top right;
                }
                QSpinBox::down-button {
                    width: 16px;
                    height: 12px;
                    subcontrol-position: bottom right;
                }
                QSpinBox::up-arrow {
                    width: 10px;
                    height: 6px;
                }
                QSpinBox::down-arrow {
                    width: 10px;
                    height: 6px;
                }
            """)
            
            table.setCellWidget(i, 4, spin2)
            spin2_widgets.append(spin2)
            
            # Giocatore 2 (ComboBox)
            combo2 = QComboBox()
            combo2.addItem("-- Seleziona --")
            for player in team2_players:
                combo2.addItem(player.display_name)
            if im.player2 and im.player2 != "":
                idx = combo2.findText(im.player2)
                if idx >= 0:
                    combo2.setCurrentIndex(idx)
            combo2.setStyleSheet("""
                QComboBox {
                    border: 1px solid #f44336;
                    border-radius: 3px;
                    padding: 2px;
                    font-size: 10px;
                }
            """)
            combo2.currentTextChanged.connect(lambda text, idx=i: self._update_player_assignment(match, idx, text, "team2"))
            table.setCellWidget(i, 5, combo2)
            combo2_widgets.append(combo2)
            
            # Pulsante Note
            btn_note = QPushButton("📝")
            btn_note.setFixedSize(32, 28)
            btn_note.setToolTip("Note incontro")
            btn_note.setStyleSheet("background-color: #607D8B; color: white; border-radius: 4px;")
            btn_note.clicked.connect(lambda checked, idx=i: self._show_match_note_dialog(match, idx))
            table.setCellWidget(i, 6, btn_note)
            note_buttons.append(btn_note)
            
            # Pulsante Sostituzione
            btn_sub = QPushButton("🔄")
            btn_sub.setFixedSize(32, 28)
            btn_sub.setToolTip("Sostituisci giocatore (max 2 per squadra)")
            btn_sub.setStyleSheet("background-color: #FF9800; color: white; border-radius: 4px;")
            btn_sub.clicked.connect(lambda checked, idx=i: self._show_substitution_dialog_simple(
                match, idx, team1_players, team2_players, substitutions_used, subs_info_label))
            table.setCellWidget(i, 7, btn_sub)
            subs_buttons.append(btn_sub)
        
        table.setRowCount(len(match.individual_matches))
        layout.addWidget(table)
        
        # ========================================
        # RIEPILOGO
        # ========================================
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 6px; padding: 10px; margin-top: 10px;")
        summary_layout = QHBoxLayout(summary_frame)
        
        result_label = QLabel("RISULTATO: 0 - 0")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        summary_layout.addWidget(result_label)
        
        summary_layout.addStretch()
        
        status_label = QLabel("⚪ INCOMPLETA")
        status_label.setStyleSheet("font-size: 12px; padding: 4px 12px; background-color: #e0e0e0; border-radius: 12px;")
        summary_layout.addWidget(status_label)
        
        layout.addWidget(summary_frame)
        
        # ========================================
        # AVVISO
        # ========================================
        warning_label = QLabel("⚠️ In caso di pareggio → Sudden Death (10 min) → Shoot-out")
        warning_label.setStyleSheet("color: #f39c12; font-size: 10px; padding: 5px;")
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)
        
        # ========================================
        # FUNZIONI DI AGGIORNAMENTO
        # ========================================
        def update_summary():
            wins1 = 0
            wins2 = 0
            all_valid = True
            
            for i in range(len(match.individual_matches)):
                if i < len(spin1_widgets) and i < len(spin2_widgets):
                    g1 = spin1_widgets[i].value()
                    g2 = spin2_widgets[i].value()
                    
                    p1 = combo1_widgets[i].currentText() if i < len(combo1_widgets) else ""
                    p2 = combo2_widgets[i].currentText() if i < len(combo2_widgets) else ""
                    
                    if p1 == "-- Seleziona --" or p2 == "-- Seleziona --":
                        all_valid = False
                    
                    if g1 > g2:
                        wins1 += 1
                    elif g2 > g1:
                        wins2 += 1
            
            result_label.setText(f"RISULTATO: {wins1} - {wins2}")
            
            if wins1 > wins2:
                result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e7d32;")
            elif wins2 > wins1:
                result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #c62828;")
            else:
                if wins1 > 0 or wins2 > 0:
                    result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f57c00;")
                else:
                    result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            
            all_played = all(
                spin1_widgets[i].value() > 0 or spin2_widgets[i].value() > 0 
                for i in range(len(match.individual_matches))
            )
            
            if all_valid and all_played:
                status_label.setText("✅ COMPLETATA")
                status_label.setStyleSheet("font-size: 12px; padding: 4px 12px; background-color: #c8e6c9; color: #2e7d32; border-radius: 12px;")
            elif all_valid:
                status_label.setText("⏳ PRONTA")
                status_label.setStyleSheet("font-size: 12px; padding: 4px 12px; background-color: #bbdef5; color: #1976D2; border-radius: 12px;")
            else:
                status_label.setText("⚠️ INCOMPLETA")
                status_label.setStyleSheet("font-size: 12px; padding: 4px 12px; background-color: #ffe0b2; color: #f57c00; border-radius: 12px;")
        
        for spin in spin1_widgets + spin2_widgets:
            spin.valueChanged.connect(update_summary)
        for combo in combo1_widgets + combo2_widgets:
            combo.currentTextChanged.connect(update_summary)
        
        # ========================================
        # PULSANTI
        # ========================================
        btn_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 SALVA")
        btn_save.setFixedHeight(45)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 30px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        def save_results():
            missing = []
            for i in range(len(match.individual_matches)):
                if i < len(combo1_widgets) and combo1_widgets[i].currentText() == "-- Seleziona --":
                    missing.append(f"Tavolo {i+1} - Squadra 1")
                if i < len(combo2_widgets) and combo2_widgets[i].currentText() == "-- Seleziona --":
                    missing.append(f"Tavolo {i+1} - Squadra 2")
            
            if missing:
                QMessageBox.warning(dialog, "Attenzione", 
                                   f"Giocatori non assegnati:\n" + "\n".join(missing))
                return
            
            wins1 = 0
            wins2 = 0
            for i in range(len(match.individual_matches)):
                if i < len(spin1_widgets) and i < len(spin2_widgets):
                    g1 = spin1_widgets[i].value()
                    g2 = spin2_widgets[i].value()
                    if g1 > g2:
                        wins1 += 1
                    elif g2 > g1:
                        wins2 += 1
            
            if wins1 == wins2:
                reply = QMessageBox.question(dialog, "Pareggio",
                    f"La partita è finita in parità {wins1}-{wins2}.\n\n"
                    "⚡ Si procede con SUDDEN DEATH (10 minuti)?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    dialog.accept()
                    self.show_sudden_death(match, team1_name, team2_name)
                return
            
            for i, im in enumerate(match.individual_matches):
                if i < len(combo1_widgets):
                    im.player1 = combo1_widgets[i].currentText()
                if i < len(combo2_widgets):
                    im.player2 = combo2_widgets[i].currentText()
                if i < len(spin1_widgets):
                    im.goals1 = spin1_widgets[i].value()
                if i < len(spin2_widgets):
                    im.goals2 = spin2_widgets[i].value()
                if im.goals1 == 0 and im.goals2 == 0:
                    im.status = None
                else:
                    im.status = MatchStatus.COMPLETED
            
            match.winner = match.team1 if wins1 > wins2 else match.team2
            match.status = MatchStatus.COMPLETED
            
            self.propagate_winners()
            dialog.accept()
            self.refresh()
            QMessageBox.information(self, "Successo", f"✅ Risultati salvati per {match.id}")
        
        btn_save.clicked.connect(save_results)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("✖ ANNULLA")
        btn_cancel.setFixedHeight(45)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-size: 14px;
                padding: 8px 30px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        update_summary()
        dialog.exec()
        self.refresh()
    
    def _show_match_note_dialog(self, match, table_idx):
        """Mostra dialog per note dell'incontro."""
        if table_idx >= len(match.individual_matches):
            return
        
        im = match.individual_matches[table_idx]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Note - Tavolo {table_idx + 1}")
        dialog.setModal(True)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        info = QLabel(f"<b>Tavolo {table_idx + 1}</b><br>{match.player1} vs {match.player2}")
        info.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        layout.addWidget(info)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(im.notes or "")
        text_edit.setPlaceholderText("Ammonizioni, espulsioni, incidenti, etc...")
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Salva")
        btn_save.clicked.connect(lambda: self._save_match_note(im, text_edit.toPlainText(), dialog))
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px;")
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annulla")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px; border-radius: 4px;")
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _save_match_note(self, individual_match, notes, dialog):
        """Salva le note dell'incontro."""
        individual_match.notes = notes
        dialog.accept()
    
    def _show_substitution_dialog_simple(self, match, table_idx, team1_players, team2_players, substitutions_used, subs_info_label):
        """Mostra dialog per sostituzioni (stile team_results_tab)."""
        if table_idx >= len(match.individual_matches):
            return
        
        im = match.individual_matches[table_idx]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sostituzione - Tavolo {table_idx + 1}")
        dialog.setModal(True)
        dialog.resize(450, 400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"🔄 SOSTITUZIONE - Tavolo {table_idx + 1}"))
        layout.addWidget(QLabel(f"<b>{match.player1}</b> vs <b>{match.player2}</b>"))
        
        # Selezione squadra
        layout.addWidget(QLabel("Squadra:"))
        team_combo = QComboBox()
        team_combo.addItem("Squadra 1 (Blu)", "team1")
        team_combo.addItem("Squadra 2 (Rossa)", "team2")
        layout.addWidget(team_combo)
        
        # Giocatore uscente
        layout.addWidget(QLabel("Giocatore uscente:"))
        out_combo = QComboBox()
        layout.addWidget(out_combo)
        
        # Giocatore entrante
        layout.addWidget(QLabel("Giocatore entrante:"))
        in_combo = QComboBox()
        layout.addWidget(in_combo)
        
        # Motivo
        layout.addWidget(QLabel("Motivo (opzionale):"))
        motivo_edit = QLineEdit()
        motivo_edit.setPlaceholderText("Infortunio, tattica, etc.")
        layout.addWidget(motivo_edit)
        
        note = QLabel("ℹ️ Il subentrato eredita le sanzioni. Max 2 sostituzioni per squadra.")
        note.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(note)
        
        def update_player_lists():
            team = team_combo.currentData()
            out_combo.clear()
            in_combo.clear()
            
            if team == "team1":
                current_player = im.player1
                all_players = team1_players
            else:
                current_player = im.player2
                all_players = team2_players
            
            for player in all_players:
                out_combo.addItem(player.display_name)
            
            if current_player and current_player != "" and current_player != "-- Seleziona --":
                idx = out_combo.findText(current_player)
                if idx >= 0:
                    out_combo.setCurrentIndex(idx)
            
            for player in all_players:
                if player.display_name != out_combo.currentText():
                    in_combo.addItem(player.display_name)
        
        def update_in_combo():
            in_combo.clear()
            team = team_combo.currentData()
            current_out = out_combo.currentText()
            
            if team == "team1":
                players = team1_players
            else:
                players = team2_players
            
            for player in players:
                if player.display_name != current_out:
                    in_combo.addItem(player.display_name)
        
        team_combo.currentIndexChanged.connect(update_player_lists)
        out_combo.currentTextChanged.connect(update_in_combo)
        update_player_lists()
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("🔄 Sostituisci")
        btn_ok.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; border-radius: 4px;")
        btn_ok.clicked.connect(lambda: self._apply_substitution_simple(
            match, table_idx, team_combo.currentData(), out_combo.currentText(), 
            in_combo.currentText(), motivo_edit.text(), substitutions_used, 
            subs_info_label, dialog))
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Annulla")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px; border-radius: 4px;")
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def _apply_substitution_simple(self, match, table_idx, team, out_player, in_player, motivo, substitutions_used, subs_info_label, dialog):
        """Applica la sostituzione."""
        if table_idx >= len(match.individual_matches):
            return
        
        if not in_player or in_player == "":
            QMessageBox.warning(self, "Errore", "Seleziona un giocatore entrante")
            return
        
        im = match.individual_matches[table_idx]
        subs_used = substitutions_used.get(team, 0)
        
        if subs_used >= 2:
            QMessageBox.warning(self, "Sostituzioni esaurite", "Hai già effettuato il massimo di 2 sostituzioni per questa squadra.")
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if team == "team1":
            old_player = im.player1
            im.player1 = in_player
            substitutions_used["team1"] = subs_used + 1
            note_text = f"[{timestamp}] SOSTITUZIONE Squadra 1 - Tavolo {table_idx+1}: {out_player} → {in_player}"
        else:
            old_player = im.player2
            im.player2 = in_player
            substitutions_used["team2"] = subs_used + 1
            note_text = f"[{timestamp}] SOSTITUZIONE Squadra 2 - Tavolo {table_idx+1}: {out_player} → {in_player}"
        
        if motivo:
            note_text += f" ({motivo})"
        
        im.notes = (im.notes or "") + note_text + "\n"
        
        subs1 = substitutions_used.get("team1", 0)
        subs2 = substitutions_used.get("team2", 0)
        subs_info_label.setText(f"🔄 Sostituzioni: Squadra 1: {subs1}/2 | Squadra 2: {subs2}/2")
        
        self.refresh()
        dialog.accept()
        QMessageBox.information(self, "Sostituito", f"✅ {in_player} sostituisce {out_player}")
    
    def _update_player_assignment(self, match, table_idx, player_name, team):
        """Aggiorna l'assegnazione del giocatore quando cambia la combo box."""
        if table_idx < len(match.individual_matches):
            if team == "team1":
                if player_name and player_name != "-- Seleziona --":
                    match.individual_matches[table_idx].player1 = player_name
                else:
                    match.individual_matches[table_idx].player1 = ""
            else:
                if player_name and player_name != "-- Seleziona --":
                    match.individual_matches[table_idx].player2 = player_name
                else:
                    match.individual_matches[table_idx].player2 = ""
    
    # ========================================
    # SUDDEN DEATH E SHOOT-OUT
    # ========================================
    
    def show_sudden_death(self, match, team1_name, team2_name):
        """
        Gestisce sudden death per partite a squadre.
        Durata: 10 minuti
        Tutti e 4 i tavoli giocano contemporaneamente
        Primo gol su qualsiasi tavolo vince
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sudden Death - {match.id}")
        dialog.setModal(True)
        dialog.setMinimumSize(950, 750)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"⚽ SUDDEN DEATH SQUADRE - 10 MINUTI ⚽")
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
        
        # Info squadre
        teams_frame = QFrame()
        teams_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 10px;")
        teams_layout = QHBoxLayout(teams_frame)
        
        t1_box = QFrame()
        t1_box.setStyleSheet("background-color: #e3f2fd; border-radius: 8px; padding: 10px;")
        t1_layout = QVBoxLayout(t1_box)
        t1_name = QLabel(team1_name)
        t1_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        t1_name.setAlignment(Qt.AlignCenter)
        t1_gol = QLabel("0")
        t1_gol.setStyleSheet("font-size: 48px; font-weight: bold; color: #1976D2;")
        t1_gol.setAlignment(Qt.AlignCenter)
        t1_layout.addWidget(t1_name)
        t1_layout.addWidget(t1_gol)
        
        vs_label = QLabel("VS")
        vs_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 0 20px;")
        
        t2_box = QFrame()
        t2_box.setStyleSheet("background-color: #ffebee; border-radius: 8px; padding: 10px;")
        t2_layout = QVBoxLayout(t2_box)
        t2_name = QLabel(team2_name)
        t2_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        t2_name.setAlignment(Qt.AlignCenter)
        t2_gol = QLabel("0")
        t2_gol.setStyleSheet("font-size: 48px; font-weight: bold; color: #d32f2f;")
        t2_gol.setAlignment(Qt.AlignCenter)
        t2_layout.addWidget(t2_name)
        t2_layout.addWidget(t2_gol)
        
        teams_layout.addWidget(t1_box)
        teams_layout.addWidget(vs_label)
        teams_layout.addWidget(t2_box)
        layout.addWidget(teams_frame)
        
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
        
        rule_label = QLabel("⚡ Primo gol su QUALSIASI tavolo vince la partita! ⚡")
        rule_label.setStyleSheet("font-size: 14px; color: #ffaa66;")
        rule_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(rule_label)
        
        layout.addWidget(timer_frame)
        
        # Tabella dei 4 tavoli
        tables_label = QLabel("📋 TAVOLI IN GIOCO:")
        tables_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(tables_label)
        
        tables_frame = QFrame()
        tables_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;")
        tables_layout = QGridLayout(tables_frame)
        tables_layout.setSpacing(10)
        
        table_widgets = []
        
        for i in range(4):
            table_box = QFrame()
            table_box.setStyleSheet("""
                QFrame {
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    background-color: white;
                    padding: 10px;
                }
            """)
            table_layout = QVBoxLayout(table_box)
            
            table_header = QLabel(f"🏓 TAVOLO {i+1}")
            table_header.setStyleSheet("font-weight: bold; font-size: 12px; background-color: #e9ecef; padding: 5px; border-radius: 4px;")
            table_header.setAlignment(Qt.AlignCenter)
            table_layout.addWidget(table_header)
            
            p1_name = "?"
            p2_name = "?"
            if hasattr(match, 'individual_matches') and len(match.individual_matches) > i:
                p1_name = match.individual_matches[i].player1 or "?"
                p2_name = match.individual_matches[i].player2 or "?"
            
            players_label = QLabel(f"{p1_name}\nvs\n{p2_name}")
            players_label.setAlignment(Qt.AlignCenter)
            players_label.setStyleSheet("font-size: 11px;")
            table_layout.addWidget(players_label)
            
            score_label = QLabel("0 - 0")
            score_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            score_label.setAlignment(Qt.AlignCenter)
            table_layout.addWidget(score_label)
            
            btn_frame = QHBoxLayout()
            
            btn_t1 = QPushButton(f"GOL\n{team1_name[:15]}")
            btn_t1.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    font-size: 10px;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            
            btn_t2 = QPushButton(f"GOL\n{team2_name[:15]}")
            btn_t2.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-size: 10px;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
            
            btn_frame.addWidget(btn_t1)
            btn_frame.addWidget(btn_t2)
            table_layout.addLayout(btn_frame)
            
            tables_layout.addWidget(table_box, i // 2, i % 2)
            
            table_widgets.append({
                'score_label': score_label,
                'g1': 0,
                'g2': 0,
                'btn1': btn_t1,
                'btn2': btn_t2
            })
        
        layout.addWidget(tables_frame)
        
        # Log eventi
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 6px; border: 1px solid #dee2e6;")
        log_layout = QVBoxLayout(log_frame)
        
        log_title = QLabel("📋 Cronologia eventi:")
        log_title.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(log_title)
        
        log_text = QLabel("In attesa di gol...")
        log_text.setStyleSheet("font-family: monospace; font-size: 11px; color: #6c757d;")
        log_text.setWordWrap(True)
        log_layout.addWidget(log_text)
        
        layout.addWidget(log_frame)
        
        # Bottone forzatura shoot-out
        btn_force = QPushButton("🎯 Forza Shoot-out")
        btn_force.setStyleSheet("background-color: #9c27b0; color: white; padding: 10px; border-radius: 6px;")
        layout.addWidget(btn_force)
        
        # Variabili di stato
        remaining = 600
        match_ended = False
        events = []
        
        def update_timer():
            nonlocal remaining, match_ended
            if match_ended:
                return
            if remaining <= 0:
                timer.stop()
                dialog.accept()
                self.show_penalty_shootout(match, team1_name, team2_name)
                return
            remaining -= 1
            mins = remaining // 60
            secs = remaining % 60
            timer_label.setText(f"{mins:02d}:{secs:02d}")
        
        def add_goal(table_idx, team):
            nonlocal match_ended, events
            if match_ended:
                return
            
            now = datetime.now().strftime("%H:%M:%S")
            widget = table_widgets[table_idx]
            
            if team == 1:
                widget['g1'] += 1
                events.append(f"[{now}] ⚽ TAVOLO {table_idx+1}: {team1_name} segna!")
            else:
                widget['g2'] += 1
                events.append(f"[{now}] ⚽ TAVOLO {table_idx+1}: {team2_name} segna!")
            
            widget['score_label'].setText(f"{widget['g1']} - {widget['g2']}")
            log_text.setText("\n".join(events[-8:]))
            
            if widget['g1'] > 0 or widget['g2'] > 0:
                match_ended = True
                timer.stop()
                
                if widget['g1'] > 0:
                    winner_team = 1
                    events.append(f"[{now}] 🏆 VITTORIA! {team1_name} vince il sudden death al tavolo {table_idx+1}!")
                    t1_box.setStyleSheet("background-color: #c8e6c9; border-radius: 8px; padding: 10px;")
                else:
                    winner_team = 2
                    events.append(f"[{now}] 🏆 VITTORIA! {team2_name} vince il sudden death al tavolo {table_idx+1}!")
                    t2_box.setStyleSheet("background-color: #c8e6c9; border-radius: 8px; padding: 10px;")
                
                log_text.setText("\n".join(events[-8:]))
                
                QMessageBox.information(dialog, "PARTITA TERMINATA",
                                       f"🏆 GOL al Tavolo {table_idx+1}!\n\n"
                                       f"{team1_name if winner_team == 1 else team2_name} vince il sudden death!")
                
                # Salva risultato
                for i, w in enumerate(table_widgets):
                    if i < len(match.individual_matches):
                        match.individual_matches[i].goals1 = w['g1']
                        match.individual_matches[i].goals2 = w['g2']
                        match.individual_matches[i].status = MatchStatus.COMPLETED
                
                match.winner = match.team1 if winner_team == 1 else match.team2
                match.status = MatchStatus.COMPLETED
                
                self.propagate_winners()
                dialog.accept()
                self.refresh()
        
        def force_shootout():
            nonlocal match_ended
            match_ended = True
            timer.stop()
            dialog.accept()
            self.show_penalty_shootout(match, team1_name, team2_name)
        
        for idx, w in enumerate(table_widgets):
            w['btn1'].clicked.connect(lambda checked, i=idx, t=1: add_goal(i, t))
            w['btn2'].clicked.connect(lambda checked, i=idx, t=2: add_goal(i, t))
        
        btn_force.clicked.connect(force_shootout)
        
        timer = QTimer()
        timer.timeout.connect(update_timer)
        timer.start(1000)
        
        dialog.exec()
        if timer.isActive():
            timer.stop()
        
        self.refresh()
    
    def show_penalty_shootout(self, match, team1_name, team2_name):
        """
        Gestisce lo shoot-out per partite a squadre.
        Ogni squadra nomina 1 giocatore, si tira a turno fino a quando
        una squadra segna e l'altra sbaglia.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Shoot-out Squadre - {match.id}")
        dialog.setModal(True)
        dialog.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"⚽ SHOOT-OUT SQUADRE ⚽")
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
        
        # Info squadre
        teams_frame = QFrame()
        teams_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 10px;")
        teams_layout = QHBoxLayout(teams_frame)
        
        t1_box = QFrame()
        t1_box.setStyleSheet("background-color: #e3f2fd; border-radius: 8px; padding: 10px;")
        t1_layout = QVBoxLayout(t1_box)
        t1_name = QLabel(team1_name)
        t1_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        t1_name.setAlignment(Qt.AlignCenter)
        t1_score = QLabel("0")
        t1_score.setStyleSheet("font-size: 36px; font-weight: bold; color: #1976D2;")
        t1_score.setAlignment(Qt.AlignCenter)
        t1_layout.addWidget(t1_name)
        t1_layout.addWidget(t1_score)
        
        vs_label = QLabel("VS")
        vs_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 0 20px;")
        
        t2_box = QFrame()
        t2_box.setStyleSheet("background-color: #ffebee; border-radius: 8px; padding: 10px;")
        t2_layout = QVBoxLayout(t2_box)
        t2_name = QLabel(team2_name)
        t2_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
        t2_name.setAlignment(Qt.AlignCenter)
        t2_score = QLabel("0")
        t2_score.setStyleSheet("font-size: 36px; font-weight: bold; color: #d32f2f;")
        t2_score.setAlignment(Qt.AlignCenter)
        t2_layout.addWidget(t2_name)
        t2_layout.addWidget(t2_score)
        
        teams_layout.addWidget(t1_box)
        teams_layout.addWidget(vs_label)
        teams_layout.addWidget(t2_box)
        layout.addWidget(teams_frame)
        
        # Selezione giocatori
        selection_frame = QFrame()
        selection_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 8px; padding: 15px;")
        selection_layout = QHBoxLayout(selection_frame)
        
        # Squadra 1
        t1_sel_box = QGroupBox("Scegli tiratore")
        t1_sel_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 6px;
                margin-top: 10px;
            }
        """)
        t1_sel_layout = QVBoxLayout(t1_sel_box)
        
        t1_player_combo = QComboBox()
        t1_player_combo.addItem("-- Seleziona --")
        
        team1 = None
        if hasattr(match, 'team1') and hasattr(self.parent, 'teams'):
            team1 = next((t for t in self.parent.teams if t.id == match.team1), None)
        
        if team1 and hasattr(team1, 'players'):
            for p in team1.players:
                t1_player_combo.addItem(p.display_name, p.licence)
        
        t1_sel_layout.addWidget(t1_player_combo)
        
        # VS
        vs_shoot = QLabel("VS")
        vs_shoot.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 20px;")
        
        # Squadra 2
        t2_sel_box = QGroupBox("Scegli tiratore")
        t2_sel_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #f44336;
                border-radius: 6px;
                margin-top: 10px;
            }
        """)
        t2_sel_layout = QVBoxLayout(t2_sel_box)
        
        t2_player_combo = QComboBox()
        t2_player_combo.addItem("-- Seleziona --")
        
        team2 = None
        if hasattr(match, 'team2') and hasattr(self.parent, 'teams'):
            team2 = next((t for t in self.parent.teams if t.id == match.team2), None)
        
        if team2 and hasattr(team2, 'players'):
            for p in team2.players:
                t2_player_combo.addItem(p.display_name, p.licence)
        
        t2_sel_layout.addWidget(t2_player_combo)
        
        selection_layout.addWidget(t1_sel_box)
        selection_layout.addWidget(vs_shoot)
        selection_layout.addWidget(t2_sel_box)
        layout.addWidget(selection_frame)
        
        # Tabella tiri
        info_label = QLabel("Ogni squadra sceglie 1 giocatore per lo shoot-out.\nSi tira a turno fino a quando una squadra segna e l'altra sbaglia.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        layout.addWidget(info_label)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Tiro", "Squadra", "Giocatore", "Risultato"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        
        for i in range(20):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            table.setItem(i, 1, QTableWidgetItem(""))
            table.setItem(i, 2, QTableWidgetItem(""))
            table.setItem(i, 3, QTableWidgetItem("⬜"))
            table.item(i, 0).setTextAlignment(Qt.AlignCenter)
            table.item(i, 3).setTextAlignment(Qt.AlignCenter)
        
        table.setColumnWidth(0, 60)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 200)
        table.setColumnWidth(3, 100)
        layout.addWidget(table)
        
        # Stato corrente
        current_label = QLabel("🎯 Seleziona i giocatori e premi 'Inizia Shoot-out'")
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
        p1_player = None
        p2_player = None
        kicks_p1 = []
        kicks_p2 = []
        current_kick = 0
        game_over = False
        
        def update_display():
            total_p1 = sum(kicks_p1)
            total_p2 = sum(kicks_p2)
            t1_score.setText(str(total_p1))
            t2_score.setText(str(total_p2))
            
            for i in range(len(kicks_p1)):
                table.setItem(i, 1, QTableWidgetItem(team1_name))
                table.setItem(i, 2, QTableWidgetItem(p1_player if p1_player else "?"))
                table.setItem(i, 3, QTableWidgetItem("✓" if kicks_p1[i] else "✗"))
                table.item(i, 3).setForeground(Qt.darkGreen if kicks_p1[i] else Qt.darkRed)
            
            for i in range(len(kicks_p2)):
                table.setItem(i, 1, QTableWidgetItem(team2_name))
                table.setItem(i, 2, QTableWidgetItem(p2_player if p2_player else "?"))
                table.setItem(i, 3, QTableWidgetItem("✓" if kicks_p2[i] else "✗"))
                table.item(i, 3).setForeground(Qt.darkGreen if kicks_p2[i] else Qt.darkRed)
            
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
            
            if len(kicks_p1) <= len(kicks_p2):
                kicks_p1.append(goal)
                current_label.setText(f"🎯 {team1_name} - {'GOAL!' if goal else 'SBAGLIA!'}")
            else:
                kicks_p2.append(goal)
                current_label.setText(f"🎯 {team2_name} - {'GOAL!' if goal else 'SBAGLIA!'}")
            
            update_display()
            current_kick = len(kicks_p1) + len(kicks_p2)
            
            if len(kicks_p1) > 0 and len(kicks_p2) > 0:
                last_p1 = kicks_p1[-1] if kicks_p1 else False
                last_p2 = kicks_p2[-1] if kicks_p2 else False
                
                if last_p1 and not last_p2:
                    game_over = True
                    match.winner = match.team1
                elif not last_p1 and last_p2:
                    game_over = True
                    match.winner = match.team2
            
            if game_over:
                total1 = sum(kicks_p1)
                total2 = sum(kicks_p2)
                for i, im in enumerate(match.individual_matches):
                    im.goals1 = 1 if i < total1 else 0
                    im.goals2 = 1 if i < total2 else 0
                    im.status = MatchStatus.COMPLETED
                
                match.status = MatchStatus.COMPLETED
                self.propagate_winners()
                
                QMessageBox.information(dialog, "PARTITA TERMINATA",
                                       f"🏆 {match.winner} vince lo shoot-out!\n\n"
                                       f"Risultato: {total1}-{total2}")
                
                dialog.accept()
                self.refresh()
                return
            
            next_team = team1_name if len(kicks_p1) <= len(kicks_p2) else team2_name
            current_label.setText(f"🎯 Prossimo tiro: {next_team}")
        
        def start_shootout():
            nonlocal p1_player, p2_player
            
            p1_player = t1_player_combo.currentText()
            p2_player = t2_player_combo.currentText()
            
            if p1_player == "-- Seleziona --" or p2_player == "-- Seleziona --":
                QMessageBox.warning(dialog, "Attenzione", "Seleziona un giocatore per entrambe le squadre!")
                return
            
            btn_start.setEnabled(False)
            t1_player_combo.setEnabled(False)
            t2_player_combo.setEnabled(False)
            btn_goal.setEnabled(True)
            btn_miss.setEnabled(True)
            
            current_label.setText(f"🎯 Primo tiro: {team1_name} ({p1_player})")
        
        btn_start.clicked.connect(start_shootout)
        btn_goal.clicked.connect(lambda: process_kick(True))
        btn_miss.clicked.connect(lambda: process_kick(False))
        
        dialog.exec()
        self.refresh()

    def save_quick_result(self):
        """Salva risultato rapido (solo punteggio squadre)"""
        if self.knockout_match.count() == 0 or self.knockout_match.currentText() == "Nessuna partita disponibile":
            QMessageBox.warning(self, "Attenzione", "Seleziona una partita")
            return
        
        match_id = self.knockout_match.currentData()
        if not match_id:
            return
        
        match = None
        for m in self.parent.matches:
            if m.id == match_id and hasattr(m, 'individual_matches'):
                match = m
                break
        
        if not match:
            QMessageBox.warning(self, "Errore", "Partita non trovata")
            return
        
        wins1 = self.knockout_goals1.value()
        wins2 = self.knockout_goals2.value()
        
        if wins1 + wins2 != 4:
            QMessageBox.warning(self, "Attenzione", 
                            "Il totale delle vittorie deve essere 4 (es. 3-1, 2-2, 4-0)")
            return
        
        # Gestione pareggio
        if wins1 == wins2:
            reply = QMessageBox.question(self, "Pareggio",
                "La partita è finita in parità.\n\n"
                "⚡ Si procede con SUDDEN DEATH (10 minuti, primo gol su qualsiasi tavolo vince).\n\n"
                "Procedere?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.No:
                return
            
            # Ottieni i nomi delle squadre per il sudden death
            team1_name = match.player1
            team2_name = match.player2
            if hasattr(match, 'team1') and hasattr(self.parent, 'teams'):
                team1 = next((t for t in self.parent.teams if t.id == match.team1), None)
                team2 = next((t for t in self.parent.teams if t.id == match.team2), None)
                if team1:
                    team1_name = team1.display_name
                if team2:
                    team2_name = team2.display_name
            
            self.show_sudden_death(match, team1_name, team2_name)
            return
        
        # Nessun pareggio
        # Verifica e crea individual_matches se mancanti
        if not hasattr(match, 'individual_matches') or match.individual_matches is None:
            from models.team_match import IndividualMatchResult
            match.individual_matches = []
            for i in range(4):
                match.individual_matches.append(
                    IndividualMatchResult(
                        player1="",
                        player2="",
                        table=i+1,
                        goals1=None,
                        goals2=None,
                        status=None,
                        notes=""
                    )
                )
        
        for i in range(4):
            if i < wins1:
                match.individual_matches[i].goals1 = 1
                match.individual_matches[i].goals2 = 0
            else:
                match.individual_matches[i].goals1 = 0
                match.individual_matches[i].goals2 = 1
            match.individual_matches[i].status = MatchStatus.COMPLETED
        
        match.status = MatchStatus.COMPLETED
        match.winner = match.team1 if wins1 > wins2 else match.team2
        
        self.propagate_winners()
        self.refresh()
        
        # Rimuovi dalla lista rapida
        current_index = self.knockout_match.currentIndex()
        self.knockout_match.removeItem(current_index)
        
        self.knockout_goals1.setValue(0)
        self.knockout_goals2.setValue(0)
        
        if self.knockout_match.count() == 0:
            self.knockout_match.addItem("Nessuna partita disponibile")
        
        QMessageBox.information(self, "Successo", f"Risultato salvato per {match.id}")
    
    # ========================================
    # PROPAGAZIONE E DEBUG
    # ========================================
    
    def propagate_winners(self):
        """Propaga i vincitori alle fasi successive"""
        print("\n" + "="*70)
        print("🔄 Propagazione vincitori fase finale squadre")
        print("="*70)
        
        generator = TeamKnockoutGenerator()
        resolved = generator.propagate_winners(self.parent.matches, self.parent.teams)
        
        self.refresh()
        print(f"\n✅ Propagazione completata: {resolved} token risolti")
    
    def debug_tokens(self):
        """Stampa i token per debug"""
        print("\n" + "="*70)
        print("🔍 DEBUG TOKEN FASE FINALE SQUADRE")
        print("="*70)
        knockout_matches = [m for m in self.parent.matches 
                           if hasattr(m, 'individual_matches')
                           and hasattr(m, 'phase')
                           and m.phase in ["BARRAGE", "QF", "SF", "F", "R16", "R32", "R64"]]
        
        for match in sorted(knockout_matches, key=lambda x: x.id):
            print(f"\n{match.id}:")
            print(f"  team1: '{match.team1 if hasattr(match, 'team1') else 'N/A'}'")
            print(f"  team2: '{match.team2 if hasattr(match, 'team2') else 'N/A'}'")
            print(f"  player1: '{match.player1}'")
            print(f"  player2: '{match.player2}'")
            if hasattr(match, 'token1'):
                print(f"  token1: '{match.token1}'")
            if hasattr(match, 'token2'):
                print(f"  token2: '{match.token2}'")
            if self._is_match_played(match):
                wins1 = 0
                wins2 = 0
                for im in match.individual_matches:
                    if im.goals1 is not None and im.goals2 is not None:
                        if im.goals1 > im.goals2:
                            wins1 += 1
                        elif im.goals2 > im.goals1:
                            wins2 += 1
                print(f"  RISULTATO: {wins1}-{wins2}")
                print(f"  VINCITORE: '{match.winner if hasattr(match, 'winner') else 'N/A'}'")
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata"""
        self._update_generate_button_state()
        self.refresh()