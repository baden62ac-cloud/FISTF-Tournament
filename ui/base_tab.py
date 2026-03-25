# ui/base_tab.py
"""
Classe base per tutte le tab dell'applicazione.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class BaseTab(QWidget):
    """Classe base per tutte le tab"""
    
    def __init__(self, parent, title):
        super().__init__()
        self.parent = parent  # Riferimento a TournamentManager
        self.title = title
        
        # Layout principale
        layout = QVBoxLayout(self)
        
        # Titolo della tab
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Layout per il contenuto (le sottoclassi ci aggiungeranno i widget)
        self.content_layout = layout
    
    def refresh(self):
        """Aggiorna il contenuto della tab. Da override nelle sottoclassi."""
        pass
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata. Da override se necessario."""
        pass