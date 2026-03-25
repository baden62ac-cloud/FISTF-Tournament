# ui/tabs/players_tab.py
"""
Tab per la gestione delle iscrizioni giocatori.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFileDialog,
                               QDialog, QFormLayout, QLineEdit, QComboBox,
                               QSpinBox, QDialogButtonBox, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from collections import Counter

from ui.base_tab import BaseTab
from models.player import Player, Category
from models.match import MatchStatus


class PlayersTab(BaseTab):
    """Tab per le iscrizioni giocatori."""
    
    def __init__(self, parent):
        super().__init__(parent, "👥 Iscrizioni Giocatori")
        
        # Riferimenti UI
        self.players_table = None
        self.lbl_stats = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Crea l'interfaccia della tab."""
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Nuovo Giocatore")
        btn_add.clicked.connect(self.add_player_dialog)
        toolbar.addWidget(btn_add)
        
        btn_import = QPushButton("📤 Importa da CSV")
        btn_import.clicked.connect(self.import_players_dialog)
        toolbar.addWidget(btn_import)
        
        btn_export = QPushButton("📥 Esporta Excel")
        btn_export.clicked.connect(self.export_players)
        toolbar.addWidget(btn_export)
        
        btn_template = QPushButton("📋 Crea Template")
        btn_template.clicked.connect(self.create_players_template_csv)
        toolbar.addWidget(btn_template)
        
        btn_test = QPushButton("🧪 Aggiungi Test")
        btn_test.clicked.connect(self.add_test_players)
        toolbar.addWidget(btn_test)
        
        btn_delete = QPushButton("🗑️ Elimina Giocatore")
        btn_delete.clicked.connect(self.delete_player)
        btn_delete.setStyleSheet("background-color: #f44336; color: white;")
        toolbar.addWidget(btn_delete)
        
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)
        
        # Tabella giocatori
        self.players_table = QTableWidget()
        self.players_table.setColumnCount(7)
        self.players_table.setHorizontalHeaderLabels([
            "Licenza", "Cognome", "Nome", "Categoria", "Club", "Nazione", "Seed"
        ])
        
        self.players_table.cellDoubleClicked.connect(self.on_player_double_clicked)
        
        header = self.players_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.content_layout.addWidget(self.players_table)
        
        # Statistiche
        stats_layout = QHBoxLayout()
        self.lbl_stats = QLabel("Totale giocatori: 0")
        stats_layout.addWidget(self.lbl_stats)
        stats_layout.addStretch()
        self.content_layout.addLayout(stats_layout)
    
    def refresh(self):
        """Aggiorna la tabella giocatori."""
        if not hasattr(self.parent, 'players'):
            return
        
        self.players_table.setRowCount(0)
        
        for row, player in enumerate(self.parent.players):
            self.players_table.insertRow(row)
            self.players_table.setItem(row, 0, QTableWidgetItem(player.licence))
            self.players_table.setItem(row, 1, QTableWidgetItem(player.last_name))
            self.players_table.setItem(row, 2, QTableWidgetItem(player.first_name))
            self.players_table.setItem(row, 3, QTableWidgetItem(player.category.value))
            self.players_table.setItem(row, 4, QTableWidgetItem(player.club))
            self.players_table.setItem(row, 5, QTableWidgetItem(player.country))
            seed_text = str(player.seed) if player.seed else ""
            self.players_table.setItem(row, 6, QTableWidgetItem(seed_text))
        
        if self.parent.players:
            cat_counts = Counter([p.category.value for p in self.parent.players])
            cat_text = " | ".join([f"{cat}: {count}" for cat, count in cat_counts.items()])
            self.lbl_stats.setText(f"Totale giocatori: {len(self.parent.players)}  ({cat_text})")
        else:
            self.lbl_stats.setText("Totale giocatori: 0")
    
    def add_player_dialog(self):
        """Dialog per nuovo giocatore."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo nella tab Setup")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Nuovo Giocatore")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        first_name = QLineEdit()
        first_name.setPlaceholderText("Es: RICCARDO")
        layout.addRow("Nome *:", first_name)
        
        last_name = QLineEdit()
        last_name.setPlaceholderText("Es: NATOLI")
        layout.addRow("Cognome *:", last_name)
        
        licence = QLineEdit()
        licence.setPlaceholderText("Es: ITA12345")
        layout.addRow("Licenza FISTF *:", licence)
        
        category = QComboBox()
        for cat in self.parent.current_tournament.categories:
            category.addItem(cat.value)
        layout.addRow("Categoria *:", category)
        
        club = QLineEdit()
        club.setPlaceholderText("Es: ASD Subbuteo Messina")
        layout.addRow("Club *:", club)
        
        country = QLineEdit()
        country.setText("ITA")
        country.setMaxLength(3)
        layout.addRow("Nazione *:", country)
        
        seed = QSpinBox()
        seed.setMinimum(1)
        seed.setMaximum(999)
        seed.setSpecialValueText("Nessuno")
        seed.setValue(0)
        layout.addRow("Seed:", seed)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            if not first_name.text() or not last_name.text() or not licence.text() or not club.text():
                QMessageBox.warning(self, "Errore", "Compila tutti i campi obbligatori (*)")
                return
            
            selected_category = None
            for cat in Category:
                if cat.value == category.currentText():
                    selected_category = cat
                    break
            
            player = Player(
                first_name=first_name.text().upper(),
                last_name=last_name.text().upper(),
                licence=licence.text().upper(),
                category=selected_category,
                club=club.text(),
                country=country.text().upper(),
                seed=seed.value() if seed.value() > 0 else None
            )
            
            if any(p.licence == player.licence for p in self.parent.players):
                QMessageBox.warning(self, "Errore", f"Licenza {player.licence} già esistente!")
                return
            
            self.parent.players.append(player)
            self.refresh()
            self.parent.statusBar().showMessage(f"✅ Giocatore {player.display_name} aggiunto")
    
    def delete_player(self):
        """Elimina il giocatore selezionato."""
        current_row = self.players_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un giocatore da eliminare")
            return
        
        licence_item = self.players_table.item(current_row, 0)
        if not licence_item:
            return
        
        licence = licence_item.text()
        
        player_to_delete = None
        for player in self.parent.players:
            if player.licence == licence:
                player_to_delete = player
                break
        
        if not player_to_delete:
            return
        
        player_name = player_to_delete.display_name
        
        # Verifica partite giocate
        matches_played = [m for m in self.parent.matches 
                         if (m.player1 == player_name or m.player2 == player_name) 
                         and m.is_played]
        
        warning_msg = f"Sei sicuro di voler eliminare il giocatore {player_name}?"
        
        if matches_played:
            warning_msg = f"⚠️ ATTENZIONE: Il giocatore {player_name} ha già giocato {len(matches_played)} partite!\n\n"
            warning_msg += "Eliminarlo causerà problemi nel calendario e nei risultati.\n\n"
            warning_msg += "Sei veramente sicuro?"
        
        reply = QMessageBox.question(self, "Conferma Eliminazione",
                                    warning_msg,
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        self.parent.players.remove(player_to_delete)
        
        # Rimuovi dai gironi
        for cat_groups in self.parent.groups.values():
            for group_name, group_players in cat_groups.items():
                if player_to_delete in group_players:
                    group_players.remove(player_to_delete)
        
        # Aggiorna partite
        for match in self.parent.matches:
            if match.player1 == player_name:
                match.player1 = "RITIRATO"
                match.status = MatchStatus.FORFEIT
                match.winner = match.player2
                match.notes = f"{player_name} ritirato"
            if match.player2 == player_name:
                match.player2 = "RITIRATO"
                match.status = MatchStatus.FORFEIT
                match.winner = match.player1
                match.notes = f"{player_name} ritirato"
        
        self.refresh()
        
        # Aggiorna altre tab
        if hasattr(self.parent, 'refresh_groups_display'):
            self.parent.refresh_groups_display()
        
        QMessageBox.information(self, "Successo", 
                               f"Giocatore {player_name} eliminato.\n"
                               f"Le sue partite sono state assegnate come FORFAIT.")
        
        self.parent.statusBar().showMessage(f"✅ Giocatore {player_name} eliminato")
    
    def on_player_double_clicked(self, row, column):
        """Modifica i dati del giocatore selezionato."""
        licence_item = self.players_table.item(row, 0)
        if not licence_item:
            return
        
        licence = licence_item.text()
        
        player = None
        for p in self.parent.players:
            if p.licence == licence:
                player = p
                break
        
        if not player:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifica Giocatore - {player.display_name}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        first_name = QLineEdit()
        first_name.setText(player.first_name)
        layout.addRow("Nome:", first_name)
        
        last_name = QLineEdit()
        last_name.setText(player.last_name)
        layout.addRow("Cognome:", last_name)
        
        licence_edit = QLineEdit()
        licence_edit.setText(player.licence)
        licence_edit.setEnabled(False)
        layout.addRow("Licenza (non modificabile):", licence_edit)
        
        category = QComboBox()
        for cat in Category:
            category.addItem(cat.value)
        category.setCurrentText(player.category.value)
        layout.addRow("Categoria:", category)
        
        club = QLineEdit()
        club.setText(player.club)
        layout.addRow("Club:", club)
        
        country = QLineEdit()
        country.setText(player.country)
        country.setMaxLength(3)
        layout.addRow("Nazione:", country)
        
        seed = QSpinBox()
        seed.setMinimum(1)
        seed.setMaximum(999)
        seed.setSpecialValueText("Nessuno")
        seed.setValue(player.seed if player.seed else 0)
        layout.addRow("Seed:", seed)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.Accepted:
            player.first_name = first_name.text().upper()
            player.last_name = last_name.text().upper()
            
            selected_category = None
            for cat in Category:
                if cat.value == category.currentText():
                    selected_category = cat
                    break
            player.category = selected_category
            
            player.club = club.text()
            player.country = country.text().upper()
            player.seed = seed.value() if seed.value() > 0 else None
            
            self.refresh()
            self.parent.statusBar().showMessage(f"✅ Giocatore {player.display_name} aggiornato")
    
    def import_players_dialog(self):
        """Dialog per importare giocatori da CSV."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo nella tab Setup")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file CSV",
            str(Path(".").absolute()),
            "File CSV (*.csv);;Tutti i file (*.*)"
        )
        
        if not file_path:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Opzioni Import")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Formato CSV richiesto:\n"
                      "first_name,last_name,licence,category,club,country,seed\n"
                      "RICCARDO,NATOLI,ITA12345,Open,ASD Subbuteo Messina,ITA,1\n\n"
                      "I campi seed sono opzionali")
        label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(label)
        
        options_group = QGroupBox("Opzioni")
        options_layout = QVBoxLayout(options_group)
        
        import_skip_errors = QCheckBox("Salta righe con errori")
        import_skip_errors.setChecked(True)
        options_layout.addWidget(import_skip_errors)
        
        import_preview = QCheckBox("Solo anteprima (non importare)")
        import_preview.setChecked(False)
        options_layout.addWidget(import_preview)
        
        layout.addWidget(options_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        self.import_from_csv(file_path, import_skip_errors.isChecked(), import_preview.isChecked())
    
    def import_from_csv(self, file_path, skip_errors=True, preview_only=False):
        """Importa giocatori da file CSV."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path)
            
            if preview_only:
                QMessageBox.information(self, "Info", "Modalità anteprima - nessun giocatore importato")
                return
            
            required_cols = ['first_name', 'last_name', 'licence', 'category', 'club', 'country']
            missing = [c for c in required_cols if c not in df.columns]
            
            if missing:
                QMessageBox.critical(self, "Errore", f"Colonne mancanti nel file CSV:\n{', '.join(missing)}")
                return
            
            success = 0
            errors = []
            duplicates = 0
            
            existing_licences = [p.licence for p in self.parent.players]
            
            for idx, row in df.iterrows():
                try:
                    category_value = str(row['category']).strip()
                    category_enum = None
                    for cat in Category:
                        if cat.value == category_value:
                            category_enum = cat
                            break
                    
                    if not category_enum:
                        errors.append(f"Riga {idx+2}: Categoria '{category_value}' non valida")
                        if not skip_errors:
                            break
                        continue
                    
                    licence_value = str(row['licence']).strip().upper()
                    
                    if licence_value in existing_licences:
                        duplicates += 1
                        if not skip_errors:
                            errors.append(f"Riga {idx+2}: Licenza '{licence_value}' già esistente")
                            break
                        continue
                    
                    country_value = str(row['country']).strip().upper()[:3]
                    if len(country_value) != 3:
                        errors.append(f"Riga {idx+2}: Nazione '{country_value}' non valida")
                        if not skip_errors:
                            break
                        continue
                    
                    player = Player(
                        first_name=str(row['first_name']).strip().upper(),
                        last_name=str(row['last_name']).strip().upper(),
                        licence=licence_value,
                        category=category_enum,
                        club=str(row['club']).strip(),
                        country=country_value,
                        seed=int(row['seed']) if pd.notna(row.get('seed')) and row['seed'] != '' else None
                    )
                    
                    self.parent.players.append(player)
                    existing_licences.append(licence_value)
                    success += 1
                    
                except Exception as e:
                    errors.append(f"Riga {idx+2}: {str(e)}")
                    if not skip_errors:
                        break
            
            report = f"✅ Importati {success} giocatori con successo!\n"
            if duplicates > 0:
                report += f"⚠️ Saltati {duplicates} giocatori duplicati\n"
            if errors:
                report += f"\n❌ {len(errors)} errori riscontrati"
            
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Risultato Import")
            msg_box.setText(report)
            
            if errors:
                msg_box.setDetailedText("\n".join(errors[:20]))
            
            msg_box.exec()
            
            if success > 0:
                self.refresh()
                self.parent.statusBar().showMessage(f"✅ Importati {success} giocatori da CSV")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante la lettura del file:\n{str(e)}")
    
    def create_players_template_csv(self):
        """Crea un file CSV template per l'importazione giocatori."""
        import pandas as pd
        from pathlib import Path
        
        template_data = [
            {"first_name": "RICCARDO", "last_name": "NATOLI", "licence": "ITA12345",
             "category": "Open", "club": "ASD Subbuteo Messina", "country": "ITA", "seed": 1},
            {"first_name": "ALESSANDRO", "last_name": "NATOLI", "licence": "ITA12346",
             "category": "Open", "club": "ASD Subbuteo Messina", "country": "ITA", "seed": 2},
            {"first_name": "CARMELO", "last_name": "SCIACCA", "licence": "ITA12347",
             "category": "Veterans", "club": "ASD Subbuteo Messina", "country": "ITA", "seed": 3}
        ]
        
        df = pd.DataFrame(template_data)
        filename = "template_iscrizioni_giocatori.csv"
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "Template Creato", 
                               f"File template giocatori creato:\n{Path(filename).absolute()}")
    
    def export_players(self):
        """Esporta giocatori in Excel."""
        if not self.parent.players:
            QMessageBox.warning(self, "Attenzione", "Nessun giocatore da esportare")
            return
        
        import pandas as pd
        from pathlib import Path
        
        data = []
        for p in self.parent.players:
            data.append({
                'Licenza FISTF': p.licence,
                'Cognome': p.last_name,
                'Nome': p.first_name,
                'Categoria': p.category.value,
                'Club': p.club,
                'Nazione': p.country,
                'Seed': p.seed if p.seed else ''
            })
        
        df = pd.DataFrame(data)
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f"giocatori_{timestamp}.xlsx"
        
        try:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Successo", f"File salvato:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def add_test_players(self):
        """Aggiunge giocatori di test."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo nella tab Setup")
            return
        
        test_players = [
            Player(first_name="RICCARDO", last_name="NATOLI", licence="ITA12345",
                  category=Category.OPEN, club="ASD Subbuteo Messina", country="ITA", seed=1),
            Player(first_name="ALESSANDRO", last_name="NATOLI", licence="ITA12346",
                  category=Category.OPEN, club="ASD Subbuteo Messina", country="ITA", seed=2),
            Player(first_name="CARMELO", last_name="SCIACCA", licence="ITA12347",
                  category=Category.OPEN, club="ASD Subbuteo Messina", country="ITA", seed=3),
            Player(first_name="RICCARDO", last_name="LA ROSA", licence="ITA12348",
                  category=Category.OPEN, club="Palermo", country="ITA", seed=4),
            Player(first_name="DANIELE", last_name="CALCAGNO", licence="ITA12349",
                  category=Category.OPEN, club="Cosenza", country="ITA", seed=5),
            Player(first_name="CESARE", last_name="NATOLI", licence="ITA12350",
                  category=Category.OPEN, club="ASD Subbuteo Messina", country="ITA", seed=6),
            Player(first_name="GIUSEPPE", last_name="FRASCA", licence="ITA12351",
                  category=Category.VETERANS, club="ASD Subbuteo Messina", country="ITA", seed=1),
            Player(first_name="GIANLUCA", last_name="BUONO", licence="ITA12352",
                  category=Category.VETERANS, club="Bagheria", country="ITA", seed=2),
        ]
        
        for tp in test_players:
            if not any(p.licence == tp.licence for p in self.parent.players):
                self.parent.players.append(tp)
        
        self.refresh()
        self.parent.statusBar().showMessage("✅ Giocatori di test aggiunti")
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()