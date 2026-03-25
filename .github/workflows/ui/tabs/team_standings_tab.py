# ui/tabs/team_standings_tab.py
"""
Tab per le classifiche complete dei gironi a squadre.
Una tabella per categoria con intestazioni fisse, sfondi alternati per girone,
e primo/ultimo classificato evidenziati.
Criteri FISTF specifici per squadre (FISTF 2.2.2.b):
1. Punti squadra
2. Punti scontri diretti (HTH-P)
3. Differenza vittorie individuali H2H (HTH-DiffV)
4. Vittorie individuali H2H (HTH-V)
5. Differenza vittorie individuali totale (Diff.V)
6. Vittorie individuali totali (V.Ind)
7. Differenza reti H2H (HTH-DG)
8. Gol segnati H2H
9. Differenza reti totale (DG)
10. Gol segnati totali (GF)
11. Shoot-out
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QBrush
import pandas as pd

from ui.base_tab import BaseTab
from core.team_standings_calculator import TeamStandingsCalculator


class TeamStandingsTab(BaseTab):
    """Tab per le classifiche complete dei gironi a squadre."""
    
    def __init__(self, parent):
        super().__init__(parent, "📊 Classifiche Squadre")
        
        # Riferimenti UI
        self.scroll_area = None
        self.content_widget = None
        self.content_layout_inner = None
        self.btn_export_excel = None
        self.btn_export_pdf = None
        self.btn_refresh = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        # Assicurati che content_layout esista
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
        
        # ========================================
        # PANNELLO CONTROLLI
        # ========================================
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 10px;
            }
        """)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        controls_layout.addWidget(QLabel("📊 CLASSIFICHE SQUADRE"))
        controls_layout.addStretch()
        
        self.btn_refresh = QPushButton("🔄 Aggiorna")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        controls_layout.addWidget(self.btn_refresh)
        
        self.btn_export_excel = QPushButton("📊 Esporta Excel")
        self.btn_export_excel.clicked.connect(self.export_excel)
        self.btn_export_excel.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        controls_layout.addWidget(self.btn_export_excel)
        
        self.btn_export_pdf = QPushButton("📄 Esporta PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        controls_layout.addWidget(self.btn_export_pdf)
        
        self.content_layout.addWidget(controls_frame)
        
        # ========================================
        # SCROLL AREA
        # ========================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #fafafa;
                border: none;
            }
        """)
        
        self.content_widget = QWidget()
        self.content_layout_inner = QVBoxLayout(self.content_widget)
        self.content_layout_inner.setSpacing(20)
        self.content_layout_inner.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.content_widget)
        self.content_layout.addWidget(self.scroll_area)
    
    def refresh(self):
        """Aggiorna la visualizzazione delle classifiche squadre."""
        if not hasattr(self.parent, 'teams') or not hasattr(self.parent, 'matches'):
            return
        
        # Pulisci contenuto
        self._clear_content()
        
        # Trova tutte le categorie squadre con gironi
        categories = set()
        for key in self.parent.groups:
            if key.startswith("team_groups_"):
                category = key.replace("team_groups_", "")
                categories.add(category)
        
        if not categories:
            label = QLabel("⚠️ Nessuna categoria squadre trovata")
            label.setStyleSheet("font-size: 14px; color: orange; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            self.content_layout_inner.addWidget(label)
            return
        
        # Ordina categorie
        categories = sorted(categories)
        
        # Calcolatore
        calculator = TeamStandingsCalculator()
        
        # Per ogni categoria
        for category in categories:
            # Header categoria
            self._add_category_header(category)
            
            # Trova tutti i gironi di questa categoria
            groups_key = f"team_groups_{category}"
            if groups_key not in self.parent.groups:
                continue
            
            groups_in_category = sorted(self.parent.groups[groups_key].keys())
            
            if not groups_in_category:
                continue
            
            # Crea una tabella unica per categoria con sfondi alternati
            self._add_category_table_with_alternating_groups(category, groups_in_category, calculator)
    
    def _add_category_header(self, category: str):
        """Aggiunge l'header per una categoria."""
        # Rimuovi "Team " dal nome categoria per visualizzazione
        display_name = category.replace("Team ", "")
        header = QLabel(f"🏆 {display_name.upper()}")
        header.setStyleSheet("""
            font-weight: bold;
            font-size: 18px;
            color: #e67e22;
            background-color: #fef5e8;
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 15px;
            margin-bottom: 10px;
        """)
        header.setAlignment(Qt.AlignCenter)
        self.content_layout_inner.addWidget(header)
    
    def _add_category_table_with_alternating_groups(self, category: str, groups: list, calculator):
        """Crea una tabella unica per categoria con sfondi alternati per girone."""
        
        # Raccogli tutti i dati dei gironi
        all_rows = []
        group_info = []  # (start_row, end_row, group_name)
        
        for group_name in groups:
            # Trova squadre nel girone
            groups_key = f"team_groups_{category}"
            teams_in_group = self.parent.groups[groups_key].get(group_name, [])
            
            if not teams_in_group:
                continue
            
            # Raccogli partite del girone
            full_group_name = self._get_full_group_name(category, group_name)
            group_matches = []
            for match in self.parent.matches:
                if (hasattr(match, 'individual_matches') and 
                    match.group == full_group_name):
                    group_matches.append(match)
            
            # Calcola classifica
            df = calculator.calculate_group_standings(group_name, teams_in_group, group_matches)
            
            if df.empty:
                continue
            
            start_row = len(all_rows)
            
            # Aggiungi righe del girone
            for _, row in df.iterrows():
                all_rows.append({
                    "Girone": group_name,
                    "Pos": row["Pos"],
                    "Squadra": row["Squadra"],
                    "Club": row["Club"],
                    "Punti": row["Punti"],
                    "Giocate": row["Giocate"],
                    "Vinte": row["Vinte"],
                    "Pareggiate": row["Pareggiate"],
                    "Perse": row["Perse"],
                    "V_Ind": row["V"],  # Vittorie individuali
                    "Diff_V": row["DIFF_V"],
                    "GF": row["GF"],
                    "GS": row["GS"],
                    "DG": row["DG"],
                    "HTH_P": row["HTH_Punti"],
                    "HTH_V": row["HTH_V"],
                    "HTH_DiffV": row["HTH_DIFF_V"],
                    "HTH_DG": row["HTH_DG"]
                })
            
            end_row = len(all_rows) - 1
            group_info.append((start_row, end_row, group_name))
        
        if not all_rows:
            return
        
        # Crea tabella con 18 colonne
        table = QTableWidget()
        table.setColumnCount(18)
        table.setHorizontalHeaderLabels([
            "Girone", "Pos", "Squadra", "Club", "Pti", "G", "V", "P", "S",
            "V.Ind", "Diff.V", "GF", "GS", "DG", 
            "HTH-P", "HTH-V", "HTH-DiffV", "HTH-DG"
        ])
        
        # Imposta larghezza colonne
        table.setColumnWidth(0, 60)    # Girone
        table.setColumnWidth(1, 40)    # Pos
        table.setColumnWidth(2, 180)   # Squadra
        table.setColumnWidth(3, 100)   # Club
        table.setColumnWidth(4, 45)    # Pti
        table.setColumnWidth(5, 35)    # G
        table.setColumnWidth(6, 35)    # V
        table.setColumnWidth(7, 35)    # P
        table.setColumnWidth(8, 35)    # S
        table.setColumnWidth(9, 50)    # V.Ind
        table.setColumnWidth(10, 50)   # Diff.V
        table.setColumnWidth(11, 45)   # GF
        table.setColumnWidth(12, 45)   # GS
        table.setColumnWidth(13, 50)   # DG
        table.setColumnWidth(14, 55)   # HTH-P
        table.setColumnWidth(15, 55)   # HTH-V
        table.setColumnWidth(16, 65)   # HTH-DiffV
        table.setColumnWidth(17, 55)   # HTH-DG
        
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(False)  # Disabilitiamo alternanza automatica
        table.setFont(QFont("Arial", 9))
        
        # Popola tabella
        table.setRowCount(len(all_rows))
        
        # Definisci colori per gironi alternati
        colors = [
            QColor(255, 255, 255),  # Bianco per girone 1
            QColor(248, 249, 250),  # Grigio molto chiaro per girone 2
            QColor(255, 255, 255),  # Bianco per girone 3
            QColor(248, 249, 250),  # Grigio molto chiaro per girone 4
        ]
        
        for row, row_data in enumerate(all_rows):
            # Trova a quale girone appartiene questa riga
            group_idx = None
            for i, (start, end, group_name) in enumerate(group_info):
                if start <= row <= end:
                    group_idx = i
                    break
            
            # Scegli colore in base all'indice del girone
            bg_color = colors[group_idx % len(colors)] if group_idx is not None else QColor(255, 255, 255)
            
            # Colonna 0: Girone
            girone_item = QTableWidgetItem(row_data["Girone"])
            girone_item.setBackground(bg_color)
            table.setItem(row, 0, girone_item)
            
            # Colonna 1: Pos
            pos_item = QTableWidgetItem(str(row_data["Pos"]))
            pos_item.setTextAlignment(Qt.AlignCenter)
            pos_item.setBackground(bg_color)
            table.setItem(row, 1, pos_item)
            
            # Colonna 2: Squadra
            squadra_item = QTableWidgetItem(row_data["Squadra"])
            squadra_item.setBackground(bg_color)
            table.setItem(row, 2, squadra_item)
            
            # Colonna 3: Club
            club = row_data["Club"]
            if len(club) > 12:
                club = club[:10] + ".."
            club_item = QTableWidgetItem(club)
            club_item.setBackground(bg_color)
            table.setItem(row, 3, club_item)
            
            # Colonna 4: Punti
            punti_item = QTableWidgetItem(str(row_data["Punti"]))
            punti_item.setTextAlignment(Qt.AlignCenter)
            punti_item.setBackground(bg_color)
            if row_data["Punti"] > 0:
                punti_item.setForeground(QBrush(QColor(39, 174, 96)))
            table.setItem(row, 4, punti_item)
            
            # Colonna 5: Giocate
            giocate_item = QTableWidgetItem(str(row_data["Giocate"]))
            giocate_item.setTextAlignment(Qt.AlignCenter)
            giocate_item.setBackground(bg_color)
            table.setItem(row, 5, giocate_item)
            
            # Colonna 6: Vinte
            vinte_item = QTableWidgetItem(str(row_data["Vinte"]))
            vinte_item.setTextAlignment(Qt.AlignCenter)
            vinte_item.setBackground(bg_color)
            table.setItem(row, 6, vinte_item)
            
            # Colonna 7: Pareggiate
            pareggiate_item = QTableWidgetItem(str(row_data["Pareggiate"]))
            pareggiate_item.setTextAlignment(Qt.AlignCenter)
            pareggiate_item.setBackground(bg_color)
            table.setItem(row, 7, pareggiate_item)
            
            # Colonna 8: Perse
            perse_item = QTableWidgetItem(str(row_data["Perse"]))
            perse_item.setTextAlignment(Qt.AlignCenter)
            perse_item.setBackground(bg_color)
            table.setItem(row, 8, perse_item)
            
            # Colonna 9: Vittorie Individuali
            v_ind_item = QTableWidgetItem(str(row_data["V_Ind"]))
            v_ind_item.setTextAlignment(Qt.AlignCenter)
            v_ind_item.setBackground(bg_color)
            table.setItem(row, 9, v_ind_item)
            
            # Colonna 10: Differenza Vittorie
            diff_v = row_data["Diff_V"]
            diff_v_item = QTableWidgetItem(str(diff_v))
            diff_v_item.setTextAlignment(Qt.AlignCenter)
            diff_v_item.setBackground(bg_color)
            if diff_v > 0:
                diff_v_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif diff_v < 0:
                diff_v_item.setForeground(QBrush(QColor(231, 76, 60)))
            table.setItem(row, 10, diff_v_item)
            
            # Colonna 11: GF
            gf_item = QTableWidgetItem(str(row_data["GF"]))
            gf_item.setTextAlignment(Qt.AlignCenter)
            gf_item.setBackground(bg_color)
            table.setItem(row, 11, gf_item)
            
            # Colonna 12: GS
            gs_item = QTableWidgetItem(str(row_data["GS"]))
            gs_item.setTextAlignment(Qt.AlignCenter)
            gs_item.setBackground(bg_color)
            table.setItem(row, 12, gs_item)
            
            # Colonna 13: DG
            dg = row_data["DG"]
            dg_item = QTableWidgetItem(str(dg))
            dg_item.setTextAlignment(Qt.AlignCenter)
            dg_item.setBackground(bg_color)
            if dg > 0:
                dg_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif dg < 0:
                dg_item.setForeground(QBrush(QColor(231, 76, 60)))
            table.setItem(row, 13, dg_item)
            
            # Colonna 14: HTH-P
            hth_p = row_data["HTH_P"]
            hth_p_item = QTableWidgetItem(str(hth_p))
            hth_p_item.setTextAlignment(Qt.AlignCenter)
            hth_p_item.setBackground(bg_color)
            if hth_p > 0:
                hth_p_item.setForeground(QBrush(QColor(39, 174, 96)))
            hth_p_item.setToolTip("Punti negli scontri diretti")
            table.setItem(row, 14, hth_p_item)
            
            # Colonna 15: HTH-V
            hth_v = row_data["HTH_V"]
            hth_v_item = QTableWidgetItem(str(hth_v))
            hth_v_item.setTextAlignment(Qt.AlignCenter)
            hth_v_item.setBackground(bg_color)
            if hth_v > 0:
                hth_v_item.setForeground(QBrush(QColor(39, 174, 96)))
            hth_v_item.setToolTip("Vittorie individuali negli scontri diretti")
            table.setItem(row, 15, hth_v_item)
            
            # Colonna 16: HTH-DiffV
            hth_diff_v = row_data["HTH_DiffV"]
            hth_diff_v_item = QTableWidgetItem(str(hth_diff_v))
            hth_diff_v_item.setTextAlignment(Qt.AlignCenter)
            hth_diff_v_item.setBackground(bg_color)
            if hth_diff_v > 0:
                hth_diff_v_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif hth_diff_v < 0:
                hth_diff_v_item.setForeground(QBrush(QColor(231, 76, 60)))
            hth_diff_v_item.setToolTip("Differenza vittorie negli scontri diretti")
            table.setItem(row, 16, hth_diff_v_item)
            
            # Colonna 17: HTH-DG
            hth_dg = row_data["HTH_DG"]
            hth_dg_item = QTableWidgetItem(str(hth_dg))
            hth_dg_item.setTextAlignment(Qt.AlignCenter)
            hth_dg_item.setBackground(bg_color)
            if hth_dg > 0:
                hth_dg_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif hth_dg < 0:
                hth_dg_item.setForeground(QBrush(QColor(231, 76, 60)))
            hth_dg_item.setToolTip("Differenza reti negli scontri diretti")
            table.setItem(row, 17, hth_dg_item)
            
            # Evidenzia primo classificato per girone
            if row_data["Pos"] == 1:
                for col in range(18):
                    item = table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 230, 200))  # Verde chiaro scuro
            
            # Evidenzia ultimo classificato per girone (rosso chiaro)
            if group_idx is not None:
                start, end, _ = group_info[group_idx]
                if row == end:
                    for col in range(18):
                        item = table.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 220, 220))  # Rosso chiaro
        
        # Aggiungi widget con scroll orizzontale
        table_container = QWidget()
        table_layout = QHBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(table)
        
        # Scroll area orizzontale
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(table_container)
        
        # Calcola altezza
        row_height = 26
        scroll_area.setFixedHeight(len(all_rows) * row_height + 45)
        
        # Aggiungi al layout principale
        self.content_layout_inner.addWidget(scroll_area)
        
        # Aggiungi legenda
        self._add_category_legend(category, len(groups), len(all_rows))
    
    def _add_category_legend(self, category: str, num_groups: int, num_rows: int):
        """Aggiunge una legenda per la categoria."""
        display_name = category.replace("Team ", "")
        legend_frame = QFrame()
        legend_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 4px;
                padding: 6px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
        """)
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(8, 4, 8, 4)
        
        legend_layout.addWidget(QLabel(f"📊 {display_name}: {num_groups} gironi - {num_rows} squadre"))
        legend_layout.addStretch()
        
        # Legenda colori
        legend_layout.addWidget(QLabel("🟢 1° classificato"))
        legend_layout.addWidget(QLabel("🔴 Ultimo classificato"))
        legend_layout.addWidget(QLabel("⬜ Girone dispari"))
        legend_layout.addWidget(QLabel("⬜ Girone pari (grigio)"))
        legend_layout.addStretch()
        
        hth_label = QLabel("HTH-P = Punti | HTH-V = Vitt.Ind | HTH-DiffV = Diff.Vitt.Ind | HTH-DG = Diff.Reti")
        hth_label.setStyleSheet("color: #7f8c8d; font-size: 9px;")
        legend_layout.addWidget(hth_label)
        
        self.content_layout_inner.addWidget(legend_frame)
    
    def _get_full_group_name(self, category: str, group_name: str) -> str:
        """Restituisce il nome completo del girone con prefisso."""
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
        prefix = prefix_map.get(category, "TX")
        return f"{prefix}-{group_name}"
    
    def _clear_content(self):
        """Pulisce il contenuto dello scroll area."""
        while self.content_layout_inner.count():
            item = self.content_layout_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def export_excel(self):
        """Esporta tutte le classifiche squadre in Excel con fogli separati per categoria."""
        try:
            calculator = TeamStandingsCalculator()
            
            tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filename = data_dir / f"classifiche_squadre_{tournament_name}_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                categories = set()
                for key in self.parent.groups:
                    if key.startswith("team_groups_"):
                        category = key.replace("team_groups_", "")
                        categories.add(category)
                
                for category in sorted(categories):
                    groups_key = f"team_groups_{category}"
                    if groups_key not in self.parent.groups:
                        continue
                    
                    all_rows = []
                    for group_name in sorted(self.parent.groups[groups_key].keys()):
                        teams_in_group = self.parent.groups[groups_key].get(group_name, [])
                        if not teams_in_group:
                            continue
                        
                        full_group_name = self._get_full_group_name(category, group_name)
                        group_matches = []
                        for match in self.parent.matches:
                            if (hasattr(match, 'individual_matches') and 
                                match.group == full_group_name):
                                group_matches.append(match)
                        
                        df = calculator.calculate_group_standings(group_name, teams_in_group, group_matches)
                        if not df.empty:
                            df.insert(0, "Girone", group_name)
                            all_rows.append(df)
                    
                    if all_rows:
                        combined_df = pd.concat(all_rows, ignore_index=True)
                        sheet_name = category.replace("Team ", "")[:31]
                        combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            QMessageBox.information(self, "Successo", f"✅ Classifiche squadre esportate in Excel:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def export_pdf(self):
        """Esporta tutte le classifiche squadre in PDF."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            
            calculator = TeamStandingsCalculator()
            
            tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filename = data_dir / f"classifiche_squadre_{tournament_name}_{timestamp}.pdf"
            
            doc = SimpleDocTemplate(str(filename), pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            story = []
            
            # Titolo
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=20)
            story.append(Paragraph(f"Classifiche Squadre - {tournament_name}", title_style))
            story.append(Spacer(1, 10))
            
            categories = set()
            for key in self.parent.groups:
                if key.startswith("team_groups_"):
                    category = key.replace("team_groups_", "")
                    categories.add(category)
            
            first_category = True
            for category in sorted(categories):
                if not first_category:
                    story.append(PageBreak())
                first_category = False
                
                # Header categoria
                display_name = category.replace("Team ", "")
                cat_style = ParagraphStyle('CategoryStyle', parent=styles['Heading1'], fontSize=14, 
                                           textColor=colors.HexColor('#e67e22'), spaceAfter=12)
                story.append(Paragraph(f"🏆 {display_name.upper()}", cat_style))
                story.append(Spacer(1, 5))
                
                groups_key = f"team_groups_{category}"
                if groups_key not in self.parent.groups:
                    continue
                
                for group_name in sorted(self.parent.groups[groups_key].keys()):
                    teams_in_group = self.parent.groups[groups_key].get(group_name, [])
                    if not teams_in_group:
                        continue
                    
                    full_group_name = self._get_full_group_name(category, group_name)
                    group_matches = []
                    for match in self.parent.matches:
                        if (hasattr(match, 'individual_matches') and 
                            match.group == full_group_name):
                            group_matches.append(match)
                    
                    df = calculator.calculate_group_standings(group_name, teams_in_group, group_matches)
                    if df.empty:
                        continue
                    
                    # Header girone
                    group_style = ParagraphStyle('GroupStyle', parent=styles['Heading2'], fontSize=12, 
                                                  textColor=colors.HexColor('#2c3e50'), spaceAfter=6)
                    story.append(Paragraph(f"GIRONE {group_name}", group_style))
                    
                    # Tabella
                    table_data = [["Pos", "Squadra", "Club", "Pti", "G", "V", "P", "S", 
                                   "V.Ind", "Diff.V", "GF", "GS", "DG", 
                                   "HTH-P", "HTH-V", "HTH-DiffV", "HTH-DG"]]
                    
                    for _, row in df.iterrows():
                        table_data.append([
                            str(row["Pos"]),
                            row["Squadra"][:20],
                            row["Club"][:12],
                            str(row["Punti"]),
                            str(row["Giocate"]),
                            str(row["Vinte"]),
                            str(row["Pareggiate"]),
                            str(row["Perse"]),
                            str(row["V"]),
                            str(row["DIFF_V"]),
                            str(row["GF"]),
                            str(row["GS"]),
                            str(row["DG"]),
                            str(row["HTH_Punti"]),
                            str(row["HTH_V"]),
                            str(row["HTH_DIFF_V"]),
                            str(row["HTH_DG"])
                        ])
                    
                    table = Table(table_data, colWidths=[0.7*cm, 4*cm, 2*cm, 0.7*cm, 0.6*cm, 0.6*cm, 0.6*cm, 0.6*cm,
                                                          0.8*cm, 0.8*cm, 0.7*cm, 0.7*cm, 0.7*cm, 
                                                          0.8*cm, 0.8*cm, 0.9*cm, 0.8*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ecf0f1')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    
                    story.append(table)
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            
            QMessageBox.information(self, "Successo", f"✅ Classifiche squadre esportate in PDF:\n{filename}")
            
            reply = QMessageBox.question(self, "PDF Generato", "Vuoi aprire il file?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                import subprocess, os
                if os.name == 'nt':
                    os.startfile(filename)
                else:
                    subprocess.call(('xdg-open', filename))
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()