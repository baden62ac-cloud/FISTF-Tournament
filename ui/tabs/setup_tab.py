# ui/tabs/setup_tab.py
"""
Tab per la configurazione del torneo.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QDateEdit, QComboBox, QCheckBox,
                               QGroupBox, QFormLayout, QFrame, QPushButton,
                               QRadioButton, QMessageBox)
from PySide6.QtCore import Qt, QDate
from datetime import date

from ui.base_tab import BaseTab
from core.fistf_rules import Category
from models.tournament import TournamentConfig


class SetupTab(BaseTab):
    """Tab per la configurazione del torneo."""
    
    def __init__(self, parent):
        super().__init__(parent, "⚙️ Setup Torneo")
        
        # Riferimenti ai widget (per compatibilità con codice esistente)
        self.tournament_name = None
        self.start_date = None
        self.end_date = None
        self.venue = None
        self.organizer = None
        self.organizer_email = None
        self.event_type = None
        
        # Categorie FISTF
        self.cat_open = None
        self.cat_veterans = None
        self.cat_women = None
        self.cat_u20 = None
        self.cat_u16 = None
        self.cat_u12 = None
        
        # Categorie Regionali
        self.cat_eccellenza = None
        self.cat_promozione = None
        self.cat_moicat = None
        
        # Tipo competizione
        self.comp_type_individual = None
        self.comp_type_team = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        # Container per form
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        
        # Nome Torneo
        self.tournament_name = QLineEdit()
        self.tournament_name.setPlaceholderText("Es: Messina International Open 2026")
        form_layout.addRow("Nome Torneo:", self.tournament_name)
        
        # Data Inizio
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(30))
        self.start_date.setCalendarPopup(True)
        form_layout.addRow("Data Inizio:", self.start_date)
        
        # Data Fine
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addDays(31))
        self.end_date.setCalendarPopup(True)
        form_layout.addRow("Data Fine:", self.end_date)
        
        # Sede
        self.venue = QLineEdit()
        self.venue.setPlaceholderText("Es: Palazzo dello Sport, Messina")
        form_layout.addRow("Sede:", self.venue)
        
        # Organizzatore
        self.organizer = QLineEdit()
        self.organizer.setPlaceholderText("Es: ASD Subbuteo Messina")
        form_layout.addRow("Organizzatore:", self.organizer)
        
        # Email
        self.organizer_email = QLineEdit()
        self.organizer_email.setPlaceholderText("Es: info@subbuteomessina.it")
        form_layout.addRow("Email:", self.organizer_email)
        
        # Tipo Evento
        self.event_type = QComboBox()
        self.event_type.addItems([
            "Major Grand Prix", "International Grand Prix", "Golden Grand Prix",
            "International Open", "Satellite", "Regionale", "Provinciale"
        ])
        form_layout.addRow("Tipo Evento:", self.event_type)
        
        # Categorie FISTF
        fistf_group = QGroupBox("Categorie FISTF")
        fistf_layout = QHBoxLayout(fistf_group)
        
        self.cat_open = QCheckBox("Open")
        self.cat_open.setChecked(True)
        fistf_layout.addWidget(self.cat_open)
        
        self.cat_veterans = QCheckBox("Veterans")
        self.cat_veterans.setChecked(True)
        fistf_layout.addWidget(self.cat_veterans)
        
        self.cat_women = QCheckBox("Women")
        fistf_layout.addWidget(self.cat_women)
        
        self.cat_u20 = QCheckBox("U20")
        fistf_layout.addWidget(self.cat_u20)
        
        self.cat_u16 = QCheckBox("U16")
        fistf_layout.addWidget(self.cat_u16)
        
        self.cat_u12 = QCheckBox("U12")
        fistf_layout.addWidget(self.cat_u12)
        
        form_layout.addRow("", fistf_group)
        
        # Categorie Regionali
        regional_group = QGroupBox("Categorie Regionali")
        regional_layout = QHBoxLayout(regional_group)
        
        self.cat_eccellenza = QCheckBox("Eccellenza")
        regional_layout.addWidget(self.cat_eccellenza)
        
        self.cat_promozione = QCheckBox("Promozione")
        regional_layout.addWidget(self.cat_promozione)
        
        self.cat_moicat = QCheckBox("MOICAT")
        regional_layout.addWidget(self.cat_moicat)
        
        note_label = QLabel("(stesse regole FISTF)")
        note_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        regional_layout.addWidget(note_label)
        regional_layout.addStretch()
        
        form_layout.addRow("", regional_group)
        
        # Tipo Competizione
        comp_type_group = QGroupBox("Tipo Competizione")
        comp_type_layout = QHBoxLayout(comp_type_group)
        
        self.comp_type_individual = QRadioButton("🏆 Individuale")
        self.comp_type_individual.setChecked(True)
        self.comp_type_individual.toggled.connect(self.on_competition_type_changed)
        comp_type_layout.addWidget(self.comp_type_individual)
        
        self.comp_type_team = QRadioButton("👥 Squadre")
        self.comp_type_team.toggled.connect(self.on_competition_type_changed)
        comp_type_layout.addWidget(self.comp_type_team)
        
        info_label = QLabel("(max 8 giocatori per squadra, 4 per partita)")
        info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        comp_type_layout.addWidget(info_label)
        comp_type_layout.addStretch()
        
        form_layout.addRow("", comp_type_group)
        
        # Linea separatrice
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow("", line)
        
        self.content_layout.addWidget(form_container)
        
        # Pulsante crea torneo
        btn_create = QPushButton("🚀 Crea Torneo")
        btn_create.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_create.clicked.connect(self.create_tournament)
        self.content_layout.addWidget(btn_create)
        
        self.content_layout.addStretch()
    
    def on_competition_type_changed(self):
        """Gestisce il cambio tra individuale e squadre."""
        is_team = self.comp_type_team.isChecked()
        
        if is_team:
            self.parent.statusBar().showMessage("Modalità: TORNEO A SQUADRE - Iscrizioni squadre con roster")
        else:
            self.parent.statusBar().showMessage("Modalità: TORNEO INDIVIDUALE")
    
    def get_available_categories(self) -> list:
        """Restituisce le categorie disponibili in base al tipo competizione."""
        is_team = self.comp_type_team.isChecked()
        
        selected_categories = []
        
        if is_team:
            if self.cat_open.isChecked():
                selected_categories.append(Category.TEAM_OPEN)
            if self.cat_veterans.isChecked():
                selected_categories.append(Category.TEAM_VETERANS)
            if self.cat_women.isChecked():
                selected_categories.append(Category.TEAM_WOMEN)
            if self.cat_u20.isChecked():
                selected_categories.append(Category.TEAM_U20)
            if self.cat_u16.isChecked():
                selected_categories.append(Category.TEAM_U16)
            if self.cat_u12.isChecked():
                selected_categories.append(Category.TEAM_U12)
            if self.cat_eccellenza.isChecked():
                selected_categories.append(Category.TEAM_ECCELLENZA)
            if self.cat_promozione.isChecked():
                selected_categories.append(Category.TEAM_PROMOZIONE)
            if self.cat_moicat.isChecked():
                selected_categories.append(Category.TEAM_MOICAT)
        else:
            if self.cat_open.isChecked():
                selected_categories.append(Category.OPEN)
            if self.cat_veterans.isChecked():
                selected_categories.append(Category.VETERANS)
            if self.cat_women.isChecked():
                selected_categories.append(Category.WOMEN)
            if self.cat_u20.isChecked():
                selected_categories.append(Category.U20)
            if self.cat_u16.isChecked():
                selected_categories.append(Category.U16)
            if self.cat_u12.isChecked():
                selected_categories.append(Category.U12)
            if self.cat_eccellenza.isChecked():
                selected_categories.append(Category.ECCELLENZA)
            if self.cat_promozione.isChecked():
                selected_categories.append(Category.PROMOZIONE)
            if self.cat_moicat.isChecked():
                selected_categories.append(Category.MOICAT)
        
        return selected_categories
    
    def get_categories_summary(self, selected_categories: list) -> tuple:
        """Restituisce tuple (fistf_cats, regional_cats)."""
        fistf_cats = []
        regional_cats = []
        
        for cat in selected_categories:
            cat_value = cat.value
            if "Team" in cat_value:
                display_cat = cat_value.replace("Team ", "")
                if display_cat in ["Open", "Veterans", "Women", "U20", "U16", "U12"]:
                    fistf_cats.append(display_cat)
                else:
                    regional_cats.append(display_cat)
            else:
                if cat_value in ["Open", "Veterans", "Women", "U20", "U16", "U12"]:
                    fistf_cats.append(cat_value)
                else:
                    regional_cats.append(cat_value)
        
        return fistf_cats, regional_cats
    
    def create_tournament(self):
        """Crea un nuovo torneo con supporto Individuale/Squadre."""
        is_team = self.comp_type_team.isChecked()
        selected_categories = self.get_available_categories()
        
        if not self.tournament_name.text():
            QMessageBox.warning(self, "Errore", "Inserisci il nome del torneo")
            return
        
        if not selected_categories:
            QMessageBox.warning(self, "Errore", "Seleziona almeno una categoria")
            return
        
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        if end < start:
            QMessageBox.warning(self, "Errore", "La data di fine non può essere prima della data di inizio")
            return
        
        tournament_type_str = "SQUADRE" if is_team else "INDIVIDUALE"
        
        self.parent.current_tournament = TournamentConfig(
            name=self.tournament_name.text(),
            start_date=start,
            end_date=end,
            venue=self.venue.text() or "Da definire",
            organizer=self.organizer.text() or "Da definire",
            organizer_email=self.organizer_email.text() or "",
            event_type=self.event_type.currentText(),
            categories=selected_categories,
            tournament_type="team" if is_team else "individual"
        )
        
        self.parent.tournament_type = "team" if is_team else "individual"
        
        # Calcola categorie per il messaggio
        fistf_cats, regional_cats = self.get_categories_summary(selected_categories)
        
        msg = f"✅ Torneo '{self.parent.current_tournament.name}' creato con successo!\n\n"
        msg += f"📅 Date: {start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}\n"
        msg += f"📍 Sede: {self.parent.current_tournament.venue}\n"
        msg += f"🏷️ Tipo: {tournament_type_str}\n"
        
        if fistf_cats:
            msg += f"\n🏆 Categorie FISTF ({len(fistf_cats)}):\n   • " + "\n   • ".join(fistf_cats) + "\n"
        
        if regional_cats:
            msg += f"\n🌍 Categorie Regionali ({len(regional_cats)}):\n   • " + "\n   • ".join(regional_cats) + "\n"
        
        if is_team:
            msg += f"\n👥 Regole squadre applicate:\n"
            msg += f"   • Min 3 giocatori per squadra\n"
            msg += f"   • Max 8 giocatori per squadra\n"
            msg += f"   • 4 giocatori per partita\n"
            msg += f"   • Max 2 stranieri per partita\n"
        
        QMessageBox.information(self, "Successo", msg)
        
        # Ricostruisci le tab dopo la creazione del torneo
        self.parent.rebuild_tabs_after_creation()
        
        self.parent.statusBar().showMessage(
            f"Torneo attivo: {self.parent.current_tournament.name} - "
            f"{tournament_type_str} - {len(selected_categories)} categorie"
        )
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        pass