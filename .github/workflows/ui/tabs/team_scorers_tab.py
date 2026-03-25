"""
Tab per la visualizzazione della classifica marcatori nei tornei a squadre.
"""
from typing import List, Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QComboBox, QCheckBox,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon
from collections import defaultdict
import pandas as pd
from pathlib import Path

from ui.base_tab import BaseTab
from core.team_scorers_calculator import TeamScorersCalculator


class TeamScorersTab(BaseTab):
    """
    Tab per classifica marcatori nei tornei a squadre.
    Mostra i gol segnati negli incontri individuali.
    """
    
    def __init__(self, parent):
        super().__init__(parent, "⚽ Cannonieri Squadre")
        
        # Flag di sicurezza
        self._initializing = True
        self._refreshing = False
        
        # Riferimenti UI
        self.scorers_category = None
        self.include_knockout_check = None
        self.scorers_table = None
        self.lbl_stats = None
        self.top_scorer_label = None
        self.export_csv_btn = None
        self.export_excel_btn = None
        
        # Calcolatore (verrà inizializzato al primo refresh)
        self.calculator = None
        
        self.setup_ui()
        self._initializing = False
        print("   ✅ TeamScorersTab inizializzata")
    
    def setup_ui(self):
        """Crea l'interfaccia della tab"""
        
        # ========================================
        # TITOLO
        # ========================================
        title = QLabel("⚽ Classifica Cannonieri - Torneo a Squadre")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px; color: #2c3e50;")
        self.content_layout.addWidget(title)
        
        # ========================================
        # PANNELLO CONTROLLI
        # ========================================
        controls_group = QGroupBox("Opzioni Visualizzazione")
        controls_layout = QHBoxLayout(controls_group)
        
        # Filtro categoria
        controls_layout.addWidget(QLabel("Categoria:"))
        self.scorers_category = QComboBox()
        self.scorers_category.addItem("Tutte le categorie")
        if self.parent.current_tournament:
            for cat in self.parent.current_tournament.categories:
                if "Team" in cat.value:
                    self.scorers_category.addItem(cat.value)
        self.scorers_category.currentTextChanged.connect(self.refresh)
        controls_layout.addWidget(self.scorers_category)
        
        # Checkbox fase finale
        self.include_knockout_check = QCheckBox("Includi fase finale")
        self.include_knockout_check.setChecked(True)
        self.include_knockout_check.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                spacing: 8px;
                margin-left: 15px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.include_knockout_check.toggled.connect(self.refresh)
        controls_layout.addWidget(self.include_knockout_check)
        
        controls_layout.addStretch()
        
        # Pulsante aggiorna
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self.refresh)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        controls_layout.addWidget(btn_refresh)
        
        self.content_layout.addWidget(controls_group)
        
        # ========================================
        # TOP SCORER (EVIDENZIATO)
        # ========================================
        self.top_scorer_label = QLabel("🏆 Capocannoniere: -")
        self.top_scorer_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                color: #856404;
                margin: 10px 0px;
            }
        """)
        self.top_scorer_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.top_scorer_label)
        
        # ========================================
        # TABELLA MARCATORI
        # ========================================
        self.scorers_table = QTableWidget()
        self.scorers_table.setColumnCount(10)
        self.scorers_table.setHorizontalHeaderLabels([
            "Pos", "Giocatore", "Squadra", "Club", "Gol", 
            "Gol Gironi", "Gol Finale", "Partite", "Media", "Triplette"
        ])
        
        # Imposta dimensioni colonne
        header = self.scorers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # Pos
        header.setSectionResizeMode(1, QHeaderView.Stretch)            # Giocatore
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)   # Squadra
        header.setSectionResizeMode(3, QHeaderView.Stretch)            # Club
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)   # Gol
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)   # Gol Gironi
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # Gol Finale
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)   # Partite
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)   # Media
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)   # Triplette
        
        # Stile header
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        
        # Alternanza righe
        self.scorers_table.setAlternatingRowColors(True)
        self.scorers_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #cfe2ff;
            }
        """)
        
        self.content_layout.addWidget(self.scorers_table)
        
        # ========================================
        # PANNELLO STATISTICHE ED ESPORTAZIONE
        # ========================================
        bottom_layout = QHBoxLayout()
        
        # Statistiche
        self.lbl_stats = QLabel("Totale gol: 0 | Marcatori: 0 | Media: 0.00")
        self.lbl_stats.setStyleSheet("font-size: 11pt; padding: 5px; color: #2c3e50;")
        bottom_layout.addWidget(self.lbl_stats)
        
        bottom_layout.addStretch()
        
        # Pulsanti esportazione
        self.export_csv_btn = QPushButton("📄 Esporta CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        bottom_layout.addWidget(self.export_csv_btn)
        
        self.export_excel_btn = QPushButton("📊 Esporta Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        self.export_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        bottom_layout.addWidget(self.export_excel_btn)
        
        self.content_layout.addLayout(bottom_layout)
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata"""
        if self._initializing:
            return
        if hasattr(self.parent, '_loading_tournament') and self.parent._loading_tournament:
            return
        self.refresh()
    
    def refresh(self):
        """Aggiorna la classifica marcatori"""
        
        if self._refreshing:
            return
        
        self._refreshing = True
        
        try:
            # Verifica presenza squadre
            if not hasattr(self.parent, 'teams') or not self.parent.teams:
                self._show_empty_state("Nessuna squadra iscritta")
                return
            
            # Filtra partite a squadre
            team_matches = [
                m for m in self.parent.matches 
                if hasattr(m, 'individual_matches')
            ]
            
            if not team_matches:
                self._show_empty_state("Nessuna partita a squadre giocata")
                return
            
            # Inizializza calcolatore
            self.calculator = TeamScorersCalculator(self.parent.teams)
            
            # Ottieni categoria selezionata
            category = self.scorers_category.currentText()
            if category == "Tutte le categorie":
                category = ""
            
            # Ottieni opzione fase finale
            include_knockout = self.include_knockout_check.isChecked()
            
            # Calcola classifica
            df = self.calculator.calculate_category_scorers(
                category, team_matches, include_knockout
            )
            
            if df.empty:
                self._show_empty_state("Nessun gol segnato")
                return
            
            # Popola tabella
            self._populate_table(df)
            
            # Aggiorna statistiche
            self._update_stats(df, team_matches)
            
            # Aggiorna top scorer
            self._update_top_scorer(category, team_matches)
            
        except Exception as e:
            print(f"❌ Errore in refresh: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Errore", f"Errore nel calcolo: {str(e)}")
        
        finally:
            self._refreshing = False
    
    def _show_empty_state(self, message: str):
        """Mostra messaggio quando non ci sono dati"""
        self.scorers_table.setRowCount(0)
        self.scorers_table.insertRow(0)
        msg_item = QTableWidgetItem(f"👉 {message}")
        msg_item.setForeground(Qt.blue)
        msg_item.setTextAlignment(Qt.AlignCenter)
        msg_item.setFont(QFont("Arial", 12, QFont.Bold))
        self.scorers_table.setSpan(0, 0, 1, 10)
        self.scorers_table.setItem(0, 0, msg_item)
        
        self.lbl_stats.setText("Totale gol: 0 | Marcatori: 0 | Media: 0.00")
        self.top_scorer_label.setText("🏆 Capocannoniere: -")
    
    def _populate_table(self, df: pd.DataFrame):
        """Popola la tabella con i dati del DataFrame"""
        self.scorers_table.setRowCount(0)
        
        for row, (_, row_data) in enumerate(df.iterrows()):
            self.scorers_table.insertRow(row)
            
            # Posizione
            pos_item = QTableWidgetItem(str(row_data["Pos"]))
            pos_item.setTextAlignment(Qt.AlignCenter)
            pos_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.scorers_table.setItem(row, 0, pos_item)
            
            # Giocatore
            player_item = QTableWidgetItem(row_data["Giocatore"])
            player_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.scorers_table.setItem(row, 1, player_item)
            
            # Squadra
            team_item = QTableWidgetItem(row_data["Squadra"])
            team_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 2, team_item)
            
            # Club
            club_item = QTableWidgetItem(row_data["Club"])
            club_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 3, club_item)
            
            # Gol totali
            goals_item = QTableWidgetItem(str(row_data["Gol"]))
            goals_item.setTextAlignment(Qt.AlignCenter)
            goals_item.setFont(QFont("Arial", 10, QFont.Bold))
            
            # Colora in base al numero di gol
            if row_data["Gol"] >= 10:
                goals_item.setForeground(QColor(198, 40, 40))  # Rosso scuro
                goals_item.setFont(QFont("Arial", 10, QFont.Bold))
            elif row_data["Gol"] >= 5:
                goals_item.setForeground(QColor(255, 160, 0))  # Arancione
            elif row_data["Gol"] >= 3:
                goals_item.setForeground(QColor(46, 125, 50))  # Verde
            
            self.scorers_table.setItem(row, 4, goals_item)
            
            # Gol Gironi
            group_item = QTableWidgetItem(str(row_data["Gol Gironi"]))
            group_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 5, group_item)
            
            # Gol Finale
            ko_item = QTableWidgetItem(str(row_data["Gol Finale"]))
            ko_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 6, ko_item)
            
            # Partite
            matches_item = QTableWidgetItem(str(row_data["Partite"]))
            matches_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 7, matches_item)
            
            # Media
            avg_item = QTableWidgetItem(f"{row_data['Media']:.2f}")
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setItem(row, 8, avg_item)
            
            # Triplette
            hattrick_item = QTableWidgetItem(str(row_data["Triplette"]))
            hattrick_item.setTextAlignment(Qt.AlignCenter)
            if row_data["Triplette"] > 0:
                hattrick_item.setForeground(QColor(255, 215, 0))  # Oro
                hattrick_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.scorers_table.setItem(row, 9, hattrick_item)
            
            # Evidenzia il primo classificato
            if row_data["Pos"] == 1:
                for col in range(10):
                    item = self.scorers_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 243, 205))  # Giallo chiaro
        
        # Ridimensiona colonne
        self.scorers_table.resizeColumnsToContents()
    
    def _update_stats(self, df: pd.DataFrame, team_matches: List):
        """Aggiorna le statistiche riassuntive"""
        total_goals = df["Gol"].sum() if not df.empty else 0
        total_scorers = len(df)
        
        # Calcola media gol per partita
        played_matches = [m for m in team_matches if m.is_match_played()]
        avg_per_match = total_goals / len(played_matches) if played_matches else 0
        
        self.lbl_stats.setText(
            f"📊 Totale gol: {total_goals} | Marcatori: {total_scorers} | "
            f"Media: {avg_per_match:.2f} gol/partita | Partite giocate: {len(played_matches)}"
        )
    
    def _update_top_scorer(self, category: str, team_matches: List):
        """Aggiorna il label del capocannoniere"""
        if not self.calculator:
            return
        
        if category:
            top = self.calculator.get_top_scorer_by_category(category, team_matches)
        else:
            top = self.calculator.calculate_tournament_top_scorer(team_matches)
        
        if top:
            text = f"🏆 Capocannoniere: {top['giocatore']} ({top['gol']} gol)"
            if 'squadra' in top and top['squadra']:
                text += f" - {top['squadra']}"
            if 'categoria' in top and top['categoria']:
                text += f" ({top['categoria']})"
            self.top_scorer_label.setText(text)
        else:
            self.top_scorer_label.setText("🏆 Capocannoniere: -")
    
    def export_to_csv(self):
        """Esporta classifica in CSV"""
        if not self.calculator or self.scorers_table.rowCount() == 0:
            QMessageBox.warning(self, "Attenzione", "Nessuna classifica da esportare")
            return
        
        # Ricrea DataFrame dalla tabella
        data = []
        for row in range(self.scorers_table.rowCount()):
            if self.scorers_table.item(row, 0) and self.scorers_table.item(row, 0).text().isdigit():
                row_data = {
                    "Pos": self.scorers_table.item(row, 0).text(),
                    "Giocatore": self.scorers_table.item(row, 1).text(),
                    "Squadra": self.scorers_table.item(row, 2).text(),
                    "Club": self.scorers_table.item(row, 3).text(),
                    "Gol": int(self.scorers_table.item(row, 4).text()),
                    "Gol Gironi": int(self.scorers_table.item(row, 5).text()),
                    "Gol Finale": int(self.scorers_table.item(row, 6).text()),
                    "Partite": int(self.scorers_table.item(row, 7).text()),
                    "Media": float(self.scorers_table.item(row, 8).text()),
                    "Triplette": int(self.scorers_table.item(row, 9).text())
                }
                data.append(row_data)
        
        df = pd.DataFrame(data)
        
        # Scegli file
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva classifica marcatori",
            str(Path("data") / "marcatori_squadre.csv"),
            "File CSV (*.csv);;Tutti i file (*.*)"
        )
        
        if file_path:
            try:
                self.calculator.export_to_csv(df, file_path)
                QMessageBox.information(self, "Successo", f"File salvato:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")
    
    def export_to_excel(self):
        """Esporta classifica in Excel"""
        if not self.calculator or self.scorers_table.rowCount() == 0:
            QMessageBox.warning(self, "Attenzione", "Nessuna classifica da esportare")
            return
        
        # Ricrea DataFrame dalla tabella (stessa logica di export_to_csv)
        data = []
        for row in range(self.scorers_table.rowCount()):
            if self.scorers_table.item(row, 0) and self.scorers_table.item(row, 0).text().isdigit():
                row_data = {
                    "Pos": self.scorers_table.item(row, 0).text(),
                    "Giocatore": self.scorers_table.item(row, 1).text(),
                    "Squadra": self.scorers_table.item(row, 2).text(),
                    "Club": self.scorers_table.item(row, 3).text(),
                    "Gol": int(self.scorers_table.item(row, 4).text()),
                    "Gol Gironi": int(self.scorers_table.item(row, 5).text()),
                    "Gol Finale": int(self.scorers_table.item(row, 6).text()),
                    "Partite": int(self.scorers_table.item(row, 7).text()),
                    "Media": float(self.scorers_table.item(row, 8).text()),
                    "Triplette": int(self.scorers_table.item(row, 9).text())
                }
                data.append(row_data)
        
        df = pd.DataFrame(data)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva classifica marcatori",
            str(Path("data") / "marcatori_squadre.xlsx"),
            "File Excel (*.xlsx);;Tutti i file (*.*)"
        )
        
        if file_path:
            try:
                self.calculator.export_to_excel(df, file_path)
                QMessageBox.information(self, "Successo", f"File salvato:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore durante il salvataggio:\n{str(e)}")


# ========================================
# NOTA: Per integrare questa tab nel main.py,
# aggiungi queste righe in create_tournament()
# dopo la creazione delle altre tab squadre:
#
# print("   📍 Creazione tab cannonieri squadre...")
# from ui.tabs.team_scorers_tab import TeamScorersTab
# self.tabs.addTab(TeamScorersTab(self), "Cannonieri Squadre")
# ========================================