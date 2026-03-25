# ui/tabs/standings_tab.py
"""
Tab per la visualizzazione delle classifiche complete (torneo individuale).
Una tabella per categoria con intestazioni fisse, sfondi alternati per girone,
e primo/ultimo classificato evidenziati.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea, QSizePolicy,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QBrush
import pandas as pd

from ui.base_tab import BaseTab
from core.standings_calculator import StandingsCalculator


class StandingsTab(BaseTab):
    """Tab per le classifiche complete di TUTTE le categorie."""
    
    def __init__(self, parent):
        super().__init__(parent, "📊 Classifiche Complete")
        
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
        
        controls_layout.addWidget(QLabel("📊 CLASSIFICHE COMPLETE"))
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
        """Aggiorna la visualizzazione delle classifiche."""
        if not hasattr(self.parent, 'players') or not hasattr(self.parent, 'matches'):
            return
        
        # Pulisci contenuto
        self._clear_content()
        
        # Trova tutte le categorie con giocatori
        categories = set()
        for player in self.parent.players:
            if "Team" not in player.category.value:
                categories.add(player.category.value)
        
        if not categories:
            label = QLabel("⚠️ Nessuna categoria trovata")
            label.setStyleSheet("font-size: 14px; color: orange; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            self.content_layout_inner.addWidget(label)
            return
        
        # Ordina categorie
        categories = sorted(categories)
        
        # Calcolatore
        calculator = StandingsCalculator()
        
        # Per ogni categoria
        for category in categories:
            # Header categoria
            self._add_category_header(category)
            
            # Trova tutti i gironi di questa categoria
            groups_in_category = set()
            for player in self.parent.players:
                if player.category.value == category and player.group:
                    groups_in_category.add(player.group)
            
            if not groups_in_category:
                continue
            
            groups_in_category = sorted(groups_in_category)
            
            # Crea una tabella unica per categoria con intestazioni e sfondi alternati
            self._add_category_table_with_alternating_groups(category, groups_in_category, calculator)
    
    def _add_category_header(self, category: str):
        """Aggiunge l'header per una categoria."""
        header = QLabel(f"🏆 {category.upper()}")
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
            players_in_group = [p for p in self.parent.players 
                               if p.category.value == category and p.group == group_name]
            
            group_matches = []
            for match in self.parent.matches:
                if (match.group and match.group.endswith(f"-{group_name}") and 
                    not hasattr(match, 'individual_matches')):
                    group_matches.append(match)
            
            df = calculator.calculate_group_standings(group_name, players_in_group, group_matches)
            
            if df.empty:
                continue
            
            start_row = len(all_rows)
            
            # Aggiungi righe del girone
            for _, row in df.iterrows():
                all_rows.append({
                    "Girone": group_name,
                    "Pos": row["Pos"],
                    "Giocatore": row["Giocatore"],
                    "Club": row["Club"],
                    "Punti": row["Punti"],
                    "Giocate": row["Giocate"],
                    "Vinte": row["Vinte"],
                    "Pareggiate": row["Pareggiate"],
                    "Perse": row["Perse"],
                    "GF": row["GF"],
                    "GS": row["GS"],
                    "DG": row["DG"],
                    "HTH_P": row.get("HTH_P", 0),
                    "HTH_DG": row.get("HTH_DG", 0),
                    "HTH_GF": row.get("HTH_GF", 0)
                })
            
            end_row = len(all_rows) - 1
            group_info.append((start_row, end_row, group_name))
        
        if not all_rows:
            return
        
        # Crea tabella
        table = QTableWidget()
        table.setColumnCount(15)
        table.setHorizontalHeaderLabels([
            "Girone", "Pos", "Giocatore", "Club", "Pti", "G", "V", "P", "S", 
            "GF", "GS", "DG", "HTH-P", "HTH-DG", "HTH-GF"
        ])
        
        # Imposta larghezza colonne
        table.setColumnWidth(0, 60)    # Girone
        table.setColumnWidth(1, 40)    # Pos
        table.setColumnWidth(2, 180)   # Giocatore
        table.setColumnWidth(3, 100)   # Club
        table.setColumnWidth(4, 45)    # Pti
        table.setColumnWidth(5, 35)    # G
        table.setColumnWidth(6, 35)    # V
        table.setColumnWidth(7, 35)    # P
        table.setColumnWidth(8, 35)    # S
        table.setColumnWidth(9, 45)    # GF
        table.setColumnWidth(10, 45)   # GS
        table.setColumnWidth(11, 50)   # DG
        table.setColumnWidth(12, 55)   # HTH-P
        table.setColumnWidth(13, 55)   # HTH-DG
        table.setColumnWidth(14, 55)   # HTH-GF
        
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
            
            # Girone
            girone_item = QTableWidgetItem(row_data["Girone"])
            girone_item.setBackground(bg_color)
            table.setItem(row, 0, girone_item)
            
            # Pos
            pos_item = QTableWidgetItem(str(row_data["Pos"]))
            pos_item.setTextAlignment(Qt.AlignCenter)
            pos_item.setBackground(bg_color)
            table.setItem(row, 1, pos_item)
            
            # Giocatore
            giocatore_item = QTableWidgetItem(row_data["Giocatore"])
            giocatore_item.setBackground(bg_color)
            table.setItem(row, 2, giocatore_item)
            
            # Club
            club = row_data["Club"]
            if len(club) > 12:
                club = club[:10] + ".."
            club_item = QTableWidgetItem(club)
            club_item.setBackground(bg_color)
            table.setItem(row, 3, club_item)
            
            # Punti
            punti_item = QTableWidgetItem(str(row_data["Punti"]))
            punti_item.setTextAlignment(Qt.AlignCenter)
            punti_item.setBackground(bg_color)
            if row_data["Punti"] > 0:
                punti_item.setForeground(QBrush(QColor(39, 174, 96)))
            table.setItem(row, 4, punti_item)
            
            # Giocate
            giocate_item = QTableWidgetItem(str(row_data["Giocate"]))
            giocate_item.setTextAlignment(Qt.AlignCenter)
            giocate_item.setBackground(bg_color)
            table.setItem(row, 5, giocate_item)
            
            # Vinte
            vinte_item = QTableWidgetItem(str(row_data["Vinte"]))
            vinte_item.setTextAlignment(Qt.AlignCenter)
            vinte_item.setBackground(bg_color)
            table.setItem(row, 6, vinte_item)
            
            # Pareggiate
            pareggiate_item = QTableWidgetItem(str(row_data["Pareggiate"]))
            pareggiate_item.setTextAlignment(Qt.AlignCenter)
            pareggiate_item.setBackground(bg_color)
            table.setItem(row, 7, pareggiate_item)
            
            # Perse
            perse_item = QTableWidgetItem(str(row_data["Perse"]))
            perse_item.setTextAlignment(Qt.AlignCenter)
            perse_item.setBackground(bg_color)
            table.setItem(row, 8, perse_item)
            
            # GF
            gf_item = QTableWidgetItem(str(row_data["GF"]))
            gf_item.setTextAlignment(Qt.AlignCenter)
            gf_item.setBackground(bg_color)
            table.setItem(row, 9, gf_item)
            
            # GS
            gs_item = QTableWidgetItem(str(row_data["GS"]))
            gs_item.setTextAlignment(Qt.AlignCenter)
            gs_item.setBackground(bg_color)
            table.setItem(row, 10, gs_item)
            
            # DG
            dg = row_data["DG"]
            dg_item = QTableWidgetItem(str(dg))
            dg_item.setTextAlignment(Qt.AlignCenter)
            dg_item.setBackground(bg_color)
            if dg > 0:
                dg_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif dg < 0:
                dg_item.setForeground(QBrush(QColor(231, 76, 60)))
            table.setItem(row, 11, dg_item)
            
            # HTH-P
            hth_p = row_data["HTH_P"]
            hth_p_item = QTableWidgetItem(str(hth_p))
            hth_p_item.setTextAlignment(Qt.AlignCenter)
            hth_p_item.setBackground(bg_color)
            if hth_p > 0:
                hth_p_item.setForeground(QBrush(QColor(39, 174, 96)))
            hth_p_item.setToolTip("Punti negli scontri diretti")
            table.setItem(row, 12, hth_p_item)
            
            # HTH-DG
            hth_dg = row_data["HTH_DG"]
            hth_dg_item = QTableWidgetItem(str(hth_dg))
            hth_dg_item.setTextAlignment(Qt.AlignCenter)
            hth_dg_item.setBackground(bg_color)
            if hth_dg > 0:
                hth_dg_item.setForeground(QBrush(QColor(39, 174, 96)))
            elif hth_dg < 0:
                hth_dg_item.setForeground(QBrush(QColor(231, 76, 60)))
            hth_dg_item.setToolTip("Differenza reti negli scontri diretti")
            table.setItem(row, 13, hth_dg_item)
            
            # HTH-GF
            hth_gf = row_data["HTH_GF"]
            hth_gf_item = QTableWidgetItem(str(hth_gf))
            hth_gf_item.setTextAlignment(Qt.AlignCenter)
            hth_gf_item.setBackground(bg_color)
            hth_gf_item.setToolTip("Gol segnati negli scontri diretti")
            table.setItem(row, 14, hth_gf_item)
            
            # Evidenzia primo classificato per girone (verde più intenso)
            if row_data["Pos"] == 1:
                for col in range(15):
                    item = table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 230, 200))  # Verde chiaro scuro
            
            # Evidenzia ultimo classificato per girone (rosso chiaro)
            if group_idx is not None:
                start, end, _ = group_info[group_idx]
                if row == end:
                    for col in range(15):
                        item = table.item(row, col)
                        if item:
                            item.setBackground(QColor(255, 220, 220))  # Rosso chiaro
        
        # Aggiungi un bordo inferiore più spesso dopo ogni girone (separatore)
        for i, (start, end, group_name) in enumerate(group_info):
            if i < len(group_info) - 1:
                # Aggiungi una linea di separazione visiva
                for col in range(15):
                    if end + 1 < table.rowCount():
                        item = table.item(end, col)
                        if item:
                            # Non possiamo fare bordi spessi, ma possiamo evidenziare l'ultima riga
                            pass
        
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
        
        legend_layout.addWidget(QLabel(f"📊 {num_groups} gironi - {num_rows} giocatori"))
        legend_layout.addStretch()
        
        # Legenda colori
        legend_layout.addWidget(QLabel("🟢 1° classificato"))
        legend_layout.addWidget(QLabel("🔴 Ultimo classificato"))
        legend_layout.addWidget(QLabel("⬜ Girone dispari"))
        legend_layout.addWidget(QLabel("⬜ Girone pari (grigio)"))
        legend_layout.addStretch()
        
        hth_label = QLabel("HTH-P = Punti scontri diretti | HTH-DG = Diff. reti | HTH-GF = Gol scontri diretti")
        hth_label.setStyleSheet("color: #7f8c8d; font-size: 9px;")
        legend_layout.addWidget(hth_label)
        
        self.content_layout_inner.addWidget(legend_frame)
    
    def _clear_content(self):
        """Pulisce il contenuto dello scroll area."""
        while self.content_layout_inner.count():
            item = self.content_layout_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def export_excel(self):
        """Esporta tutte le classifiche in Excel con fogli separati per categoria."""
        try:
            calculator = StandingsCalculator()
            
            tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filename = data_dir / f"classifiche_{tournament_name}_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                categories = set()
                for player in self.parent.players:
                    if "Team" not in player.category.value:
                        categories.add(player.category.value)
                
                for category in sorted(categories):
                    groups_in_category = set()
                    for player in self.parent.players:
                        if player.category.value == category and player.group:
                            groups_in_category.add(player.group)
                    
                    all_rows = []
                    for group_name in sorted(groups_in_category):
                        players_in_group = [p for p in self.parent.players 
                                           if p.category.value == category and p.group == group_name]
                        
                        group_matches = []
                        for match in self.parent.matches:
                            if (match.group and match.group.endswith(f"-{group_name}") and 
                                not hasattr(match, 'individual_matches')):
                                group_matches.append(match)
                        
                        df = calculator.calculate_group_standings(group_name, players_in_group, group_matches)
                        if not df.empty:
                            df.insert(0, "Girone", group_name)
                            all_rows.append(df)
                    
                    if all_rows:
                        combined_df = pd.concat(all_rows, ignore_index=True)
                        sheet_name = category[:31]
                        combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            QMessageBox.information(self, "Successo", f"✅ Classifiche esportate in Excel:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def export_pdf(self):
        """Esporta tutte le classifiche in PDF con separazione per categoria."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            
            calculator = StandingsCalculator()
            
            tournament_name = self.parent.current_tournament.name if self.parent.current_tournament else "Torneo"
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            
            from pathlib import Path
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            filename = data_dir / f"classifiche_{tournament_name}_{timestamp}.pdf"
            
            doc = SimpleDocTemplate(str(filename), pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            story = []
            
            # Titolo
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=20)
            story.append(Paragraph(f"Classifiche - {tournament_name}", title_style))
            story.append(Spacer(1, 10))
            
            categories = set()
            for player in self.parent.players:
                if "Team" not in player.category.value:
                    categories.add(player.category.value)
            
            first_category = True
            for category in sorted(categories):
                if not first_category:
                    story.append(PageBreak())
                first_category = False
                
                # Header categoria
                cat_style = ParagraphStyle('CategoryStyle', parent=styles['Heading1'], fontSize=14, 
                                           textColor=colors.HexColor('#e67e22'), spaceAfter=12)
                story.append(Paragraph(f"🏆 {category.upper()}", cat_style))
                story.append(Spacer(1, 5))
                
                groups_in_category = set()
                for player in self.parent.players:
                    if player.category.value == category and player.group:
                        groups_in_category.add(player.group)
                
                for group_name in sorted(groups_in_category):
                    players_in_group = [p for p in self.parent.players 
                                       if p.category.value == category and p.group == group_name]
                    
                    group_matches = []
                    for match in self.parent.matches:
                        if (match.group and match.group.endswith(f"-{group_name}") and 
                            not hasattr(match, 'individual_matches')):
                            group_matches.append(match)
                    
                    df = calculator.calculate_group_standings(group_name, players_in_group, group_matches)
                    if df.empty:
                        continue
                    
                    # Header girone
                    group_style = ParagraphStyle('GroupStyle', parent=styles['Heading2'], fontSize=12, 
                                                  textColor=colors.HexColor('#2c3e50'), spaceAfter=6)
                    story.append(Paragraph(f"GIRONE {group_name}", group_style))
                    
                    # Tabella
                    table_data = [["Pos", "Giocatore", "Club", "Pti", "G", "V", "P", "S", 
                                   "GF", "GS", "DG", "HTH-P", "HTH-DG", "HTH-GF"]]
                    
                    for _, row in df.iterrows():
                        table_data.append([
                            str(row["Pos"]),
                            row["Giocatore"][:20],
                            row["Club"][:12],
                            str(row["Punti"]),
                            str(row["Giocate"]),
                            str(row["Vinte"]),
                            str(row["Pareggiate"]),
                            str(row["Perse"]),
                            str(row["GF"]),
                            str(row["GS"]),
                            str(row["DG"]),
                            str(row.get("HTH_P", 0)),
                            str(row.get("HTH_DG", 0)),
                            str(row.get("HTH_GF", 0))
                        ])
                    
                    table = Table(table_data, colWidths=[0.7*cm, 4*cm, 2*cm, 0.7*cm, 0.6*cm, 0.6*cm, 0.6*cm, 0.6*cm,
                                                          0.7*cm, 0.7*cm, 0.7*cm, 0.8*cm, 0.8*cm, 0.8*cm])
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
            
            QMessageBox.information(self, "Successo", f"✅ Classifiche esportate in PDF:\n{filename}")
            
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