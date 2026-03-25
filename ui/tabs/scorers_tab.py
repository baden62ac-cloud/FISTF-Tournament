# ui/tabs/scorers_tab.py
"""
Tab per la classifica marcatori (Cannonieri).
"""
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QComboBox, 
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame)
from PySide6.QtCore import Qt

from ui.base_tab import BaseTab
from core.scorers_calculator import ScorersCalculator

class ScorersTab(BaseTab):
    """Tab per la classifica marcatori"""
    
    def __init__(self, parent):
        super().__init__(parent, "⚽ Classifica Marcatori")
        
        # Riferimenti ai widget (per compatibilità con codice esistente)
        self.scorers_category = None
        self.scorers_table = None
        self.top_scorer_label = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab"""
        
        # === PANNELLO CONTROLLI ===
        controls_group = QGroupBox("Seleziona Categoria")
        controls_layout = QHBoxLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Categoria:"))
        self.scorers_category = QComboBox()
        self.scorers_category.addItem("Tutte")
        
        # Aggiungi categorie dal torneo corrente
        if self.parent.current_tournament:
            for cat in self.parent.current_tournament.categories:
                self.scorers_category.addItem(cat.value)
        
        self.scorers_category.currentTextChanged.connect(self.refresh)
        controls_layout.addWidget(self.scorers_category)
        
        controls_layout.addStretch()
        
        # Pulsante aggiorna
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self.refresh)
        btn_refresh.setStyleSheet("padding: 5px 15px;")
        controls_layout.addWidget(btn_refresh)
        
        self.content_layout.addWidget(controls_group)
        
        # === TABELLA MARCATORI ===
        self.scorers_table = QTableWidget()
        self.scorers_table.setColumnCount(6)
        self.scorers_table.setHorizontalHeaderLabels([
            "Pos", "Giocatore", "Club", "Gol", "Partite", "Media"
        ])
        
        header = self.scorers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.scorers_table)
        
        # === CAPOCANNONIERE DEL TORNEO ===
        top_scorer_frame = QFrame()
        top_scorer_frame.setFrameStyle(QFrame.Box)
        top_scorer_frame.setStyleSheet("background-color: #f5f5f5;")
        top_scorer_layout = QHBoxLayout(top_scorer_frame)
        
        self.top_scorer_label = QLabel("🏆 Capocannoniere del torneo: -")
        self.top_scorer_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #9C27B0;")
        top_scorer_layout.addWidget(self.top_scorer_label)
        top_scorer_layout.addStretch()
        
        self.content_layout.addWidget(top_scorer_frame)
    
    def refresh(self):
        """Aggiorna la classifica marcatori"""
        if not hasattr(self.parent, 'players') or not hasattr(self.parent, 'matches'):
            return
        
        calculator = ScorersCalculator()
        category = self.scorers_category.currentText()
        
        self.scorers_table.setRowCount(0)
        
        if category == "Tutte":
            # Mostra tutti i marcatori di tutte le categorie
            df = calculator.calculate_category_scorers("", self.parent.players, self.parent.matches)
            
            # Calcola capocannoniere assoluto
            top = calculator.calculate_tournament_top_scorer(self.parent.matches)
            if top:
                self.top_scorer_label.setText(f"🏆 Capocannoniere del torneo: {top['giocatore']} ({top['gol']} gol)")
            else:
                self.top_scorer_label.setText("🏆 Capocannoniere del torneo: -")
        else:
            # Filtra per categoria
            cat_players = [p for p in self.parent.players if p.category.value == category]
            df = calculator.calculate_category_scorers(category, cat_players, self.parent.matches)
            
            # Trova il migliore della categoria
            top = calculator.get_top_scorer_by_category(category, self.parent.matches)
            if top:
                self.top_scorer_label.setText(f"🏆 Capocannoniere {category}: {top['giocatore']} ({top['gol']} gol)")
            else:
                self.top_scorer_label.setText(f"🏆 Capocannoniere {category}: -")
        
        if df.empty:
            # Mostra messaggio se non ci sono dati
            self.scorers_table.insertRow(0)
            msg_item = QTableWidgetItem("Nessun gol segnato finora")
            msg_item.setForeground(Qt.gray)
            msg_item.setTextAlignment(Qt.AlignCenter)
            self.scorers_table.setSpan(0, 0, 1, 6)
            self.scorers_table.setItem(0, 0, msg_item)
            return
        
        for row, (idx, row_data) in enumerate(df.iterrows()):
            self.scorers_table.insertRow(row)
            self.scorers_table.setItem(row, 0, QTableWidgetItem(str(row_data["Pos"])))
            self.scorers_table.setItem(row, 1, QTableWidgetItem(row_data["Giocatore"]))
            self.scorers_table.setItem(row, 2, QTableWidgetItem(row_data["Club"]))
            self.scorers_table.setItem(row, 3, QTableWidgetItem(str(row_data["Gol"])))
            self.scorers_table.setItem(row, 4, QTableWidgetItem(str(row_data["Partite"])))
            self.scorers_table.setItem(row, 5, QTableWidgetItem(str(row_data["Media"])))
            
            # Colora il primo classificato
            if row_data["Pos"] == 1:
                for col in range(6):
                    item = self.scorers_table.item(row, col)
                    if item:
                        item.setBackground(Qt.yellow)
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata"""
        self.refresh()