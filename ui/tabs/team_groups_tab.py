# ui/tabs/team_groups_tab.py
"""
Tab per la gestione dei gironi squadre secondo regole FISTF.
Regole implementate (pag. 20, 2.3.1):
- Gironi preferibilmente da 4 squadre
- Gironi da 3 vanno per primi
- Gironi da 5+ vanno per ultimi
- Distribuzione serpentina con seed
- Modifica manuale con sistema di selezione e scambio (no drag&drop)
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGroupBox, QComboBox, QSpinBox,
                               QCheckBox, QScrollArea, QFrame, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox,
                               QDialog, QListWidget, QListWidgetItem,
                               QFileDialog, QGridLayout, QSplitter,
                               QInputDialog)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from ui.base_tab import BaseTab


class TeamGroupsTab(BaseTab):
    """Tab per la gestione dei gironi squadre secondo regole FISTF."""
    
    def __init__(self, parent):
        super().__init__(parent, "🪩 Gestione Gironi Squadre")
        
        # Riferimenti UI
        self.team_group_category = None
        self.lbl_cat_teams = None
        self.lbl_cat_groups = None
        self.team_spin_groups = None
        self.chk_separate_clubs = None
        self.btn_edit_team_groups = None
        self.team_groups_title = None
        self.team_groups_container = None
        self.team_groups_layout = None
        
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
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        
        # Categoria
        cat_group = QGroupBox("Categoria")
        cat_layout = QHBoxLayout(cat_group)
        self.team_group_category = QComboBox()
        for cat in self.parent.current_tournament.categories:
            if "Team" in cat.value:
                self.team_group_category.addItem(cat.value)
        self.team_group_category.currentTextChanged.connect(self.refresh)
        cat_layout.addWidget(self.team_group_category)
        controls_layout.addWidget(cat_group)
        
        # Statistiche
        stats_group = QGroupBox("Statistiche")
        stats_layout = QHBoxLayout(stats_group)
        self.lbl_cat_teams = QLabel("👥 0 squadre")
        stats_layout.addWidget(self.lbl_cat_teams)
        self.lbl_cat_groups = QLabel("🪩 0 gironi")
        stats_layout.addWidget(self.lbl_cat_groups)
        controls_layout.addWidget(stats_group)
        
        # Distribuzione
        dist_group = QGroupBox("Distribuzione")
        dist_layout = QHBoxLayout(dist_group)
        
        dist_layout.addWidget(QLabel("Gironi:"))
        self.team_spin_groups = QSpinBox()
        self.team_spin_groups.setMinimum(1)
        self.team_spin_groups.setMaximum(16)
        self.team_spin_groups.setValue(2)
        self.team_spin_groups.setFixedWidth(70)
        self.team_spin_groups.setAlignment(Qt.AlignCenter)
        self.team_spin_groups.setStyleSheet("""
            QSpinBox {
                font-size: 12px;
                font-weight: bold;
                background-color: white;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 6px;
            }
            QSpinBox:focus {
                border-color: #2196F3;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 15px;
                background-color: #f0f0f0;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e0e0e0;
            }
        """)
        dist_layout.addWidget(self.team_spin_groups)
        
        btn_distribute = QPushButton("🎲 Distribuisci Squadre")
        btn_distribute.clicked.connect(self.distribute_team_groups)
        btn_distribute.setStyleSheet("""
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
        dist_layout.addWidget(btn_distribute)
        
        self.chk_separate_clubs = QCheckBox("🔀 Separa squadre stesso club")
        self.chk_separate_clubs.setChecked(True)
        self.chk_separate_clubs.setToolTip(
            "Regola FISTF: le squadre dello stesso club dovrebbero essere in gironi diversi."
        )
        dist_layout.addWidget(self.chk_separate_clubs)
        dist_layout.addStretch()
        controls_layout.addWidget(dist_group)
        
        # Azioni
        actions_group = QGroupBox("Azioni")
        actions_layout = QHBoxLayout(actions_group)
        
        btn_reset = QPushButton("🗑️ Reset Gironi")
        btn_reset.clicked.connect(self.reset_team_groups)
        btn_reset.setStyleSheet("background-color: #f44336; color: white;")
        actions_layout.addWidget(btn_reset)
        
        self.btn_edit_team_groups = QPushButton("✏️ Modifica Manuale")
        self.btn_edit_team_groups.clicked.connect(self.manual_edit_team_groups)
        self.btn_edit_team_groups.setEnabled(False)
        actions_layout.addWidget(self.btn_edit_team_groups)
        
        btn_export = QPushButton("📥 Esporta Excel")
        btn_export.clicked.connect(self.export_team_groups)
        actions_layout.addWidget(btn_export)
        
        btn_import = QPushButton("📤 Importa da Excel")
        btn_import.clicked.connect(self.import_team_groups_from_excel)
        btn_import.setStyleSheet("background-color: #4CAF50; color: white;")
        actions_layout.addWidget(btn_import)
        
        controls_layout.addWidget(actions_group)
        controls_layout.addStretch()
        self.content_layout.addWidget(controls_container)
        
        # ========================================
        # TITOLO GIRONI
        # ========================================
        self.team_groups_title = QLabel("")
        self.team_groups_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        self.content_layout.addWidget(self.team_groups_title)
        
        # ========================================
        # SCROLL AREA PER GIRONI
        # ========================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.team_groups_container = QWidget()
        self.team_groups_layout = QVBoxLayout(self.team_groups_container)
        scroll.setWidget(self.team_groups_container)
        self.content_layout.addWidget(scroll)
    
    def _create_groups_grid(self, groups: dict, category: str) -> QWidget:
        """Crea una visualizzazione a griglia ottimizzata per i gironi."""
        
        # Widget principale
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Calcola numero di colonne in base al numero di gironi
        num_groups = len(groups)
        if num_groups <= 2:
            cols = 1
        elif num_groups <= 4:
            cols = 2
        elif num_groups <= 6:
            cols = 2
        elif num_groups <= 9:
            cols = 3
        else:
            cols = 4
        
        rows = (num_groups + cols - 1) // cols
        
        # Griglia per i gironi
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setContentsMargins(10, 10, 10, 10)
        
        # Stili
        group_style = """
            QWidget {
                border: 2px solid #3498db;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            QWidget:hover {
                border-color: #e67e22;
                background-color: #fff5e8;
            }
        """
        
        title_style = """
            font-weight: bold;
            font-size: 14px;
            color: #2c3e50;
            background-color: #e3f2fd;
            padding: 8px;
            border-radius: 6px;
        """
        
        team_style = """
            padding: 4px 8px;
            margin: 2px;
            border-radius: 4px;
            background-color: white;
            font-size: 11px;
        """
        
        for idx, (group_name, teams) in enumerate(sorted(groups.items())):
            row = idx // cols
            col = idx % cols
            
            # Widget contenitore del girone
            group_widget = QWidget()
            group_widget.setStyleSheet(group_style)
            group_layout = QVBoxLayout(group_widget)
            group_layout.setSpacing(8)
            group_layout.setContentsMargins(10, 10, 10, 10)
            
            # Intestazione girone
            header = QLabel(f"🏆 GIRONE {group_name}")
            header.setStyleSheet(title_style)
            header.setAlignment(Qt.AlignCenter)
            group_layout.addWidget(header)
            
            # Contatore
            count_label = QLabel(f"📊 {len(teams)} squadre")
            count_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
            count_label.setAlignment(Qt.AlignCenter)
            group_layout.addWidget(count_label)
            
            # Linea separatrice
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #bdc3c7; max-height: 1px;")
            group_layout.addWidget(line)
            
            # Squadre ordinate
            sorted_teams = sorted(teams, key=lambda x: (x.seed if x.seed else 999, x.name))
            for team in sorted_teams:
                seed_text = f"[{team.seed}]" if team.seed else ""
                players_text = f" ({len(team.players)} gioc.)"
                team_text = f"• {team.display_name} {seed_text}{players_text}"
                label = QLabel(team_text)
                label.setStyleSheet(team_style)
                label.setWordWrap(True)
                group_layout.addWidget(label)
            
            group_layout.addStretch()
            group_widget.setMinimumWidth(280)
            group_widget.setMaximumWidth(400)
            
            grid.addWidget(group_widget, row, col)
        
        # Aggiungi spazi vuoti per allineamento
        for i in range(rows * cols - num_groups):
            spacer = QWidget()
            spacer.setFixedWidth(0)
            grid.addWidget(spacer, rows - 1, cols - 1 - i)
        
        layout.addLayout(grid)
        return container
    
    def calculate_team_group_sizes(self, n_teams: int, num_groups: int) -> list:
        """
        Calcola dimensioni gironi squadre secondo regole FISTF (pag. 20, 2.3.1):
        - Preferire gironi da 4 quando possibile
        - Gironi più piccoli vanno per primi
        - Gironi più grandi vanno per ultimi
        """
        base_size = n_teams // num_groups
        remainder = n_teams % num_groups
        
        # Regole FISTF per la distribuzione delle dimensioni
        if base_size == 3:
            # Es: 11 squadre, 3 gruppi -> [3, 4, 4] (primo gruppo da 3)
            sizes = [3] * (num_groups - remainder) + [4] * remainder
            
        elif base_size == 4:
            # Es: 18 squadre, 4 gruppi -> [4, 4, 5, 5] (gruppi 4 prima, poi 5)
            sizes = [4] * (num_groups - remainder) + [5] * remainder
            
        elif base_size == 5:
            # Es: 22 squadre, 4 gruppi -> [5, 5, 6, 6] (gruppi 5 prima, poi 6)
            sizes = [5] * (num_groups - remainder) + [6] * remainder
            
        elif base_size >= 6:
            # Gruppi più grandi di 6
            sizes = [base_size] * (num_groups - remainder) + [base_size + 1] * remainder
            
        else:
            # base_size = 1 o 2 -> non dovrebbe accadere, ma gestiamo
            sizes = [base_size] * (num_groups - remainder) + [base_size + 1] * remainder
        
        return sizes
    
    def distribute_team_groups(self):
        """Distribuisce le squadre nei gironi secondo regole FISTF (serpentina con seed)."""
        if not self.parent.current_tournament:
            QMessageBox.warning(self, "Attenzione", "Prima crea un torneo")
            return
        
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        cat_teams = [t for t in self.parent.teams if t.category == cat]
        
        if len(cat_teams) < 3:
            QMessageBox.warning(self, "Attenzione", 
                               f"Solo {len(cat_teams)} squadre. Servono almeno 3 per formare gironi.")
            return
        
        num_groups = self.team_spin_groups.value()
        
        if num_groups > len(cat_teams):
            QMessageBox.warning(self, "Errore", 
                               f"Non puoi creare {num_groups} gironi con {len(cat_teams)} squadre")
            return
        
        # Conferma se esistono partite
        if self.parent.matches:
            reply = QMessageBox.question(self, "Conferma",
                                        "Esistono già partite generate. La nuova distribuzione le cancellerà. Continuare?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.parent.matches = []
        
        # Calcola dimensioni gironi secondo regole FISTF (piccoli per primi)
        group_sizes = self.calculate_team_group_sizes(len(cat_teams), num_groups)
        
        print(f"\n🎲 Distribuzione {len(cat_teams)} squadre in {num_groups} gironi")
        print(f"   Dimensioni secondo FISTF (piccoli prima): {group_sizes}")
        
        # ========================================
        # ORDINAMENTO SQUADRE CON SEED
        # ========================================
        teams_with_seed = [t for t in cat_teams if t.seed]
        teams_without_seed = [t for t in cat_teams if not t.seed]
        
        teams_with_seed.sort(key=lambda t: t.seed)
        teams_without_seed.sort(key=lambda t: t.name)
        
        sorted_teams = teams_with_seed + teams_without_seed
        
        # ========================================
        # NOMI GIRONI (A, B, C, ...)
        # ========================================
        group_names = [chr(65 + i) for i in range(num_groups)]
        groups = {name: [] for name in group_names}
        
        # ========================================
        # DISTRIBUZIONE SERPENTINA
        # ========================================
        direction = 1  # 1 = avanti, -1 = indietro
        current_idx = 0
        
        for i, team in enumerate(sorted_teams):
            # Assicurati che current_idx sia valido
            if current_idx < 0:
                current_idx = 0
            if current_idx >= num_groups:
                current_idx = num_groups - 1
            
            # Aggiungi squadra al girone corrente
            group_name = group_names[current_idx]
            groups[group_name].append(team)
            
            print(f"   {i+1:2}. {team.display_name[:20]} (seed:{team.seed or '-'}) → Girone {group_name}")
            
            # Calcola prossimo indice (serpentina) se non è l'ultimo
            if i < len(sorted_teams) - 1:
                next_idx = current_idx + direction
                
                # Cambia direzione se fuori dai limiti
                if next_idx < 0 or next_idx >= num_groups:
                    direction *= -1
                    next_idx = current_idx + direction
                
                # Cerca il prossimo girone con posti disponibili
                attempts = 0
                max_attempts = num_groups * 2
                
                while attempts < max_attempts and (next_idx < 0 or next_idx >= num_groups or 
                       len(groups[group_names[next_idx]]) >= group_sizes[next_idx]):
                    
                    if next_idx < 0 or next_idx >= num_groups:
                        direction *= -1
                        next_idx = current_idx + direction
                    elif len(groups[group_names[next_idx]]) >= group_sizes[next_idx]:
                        next_idx += direction
                    
                    attempts += 1
                    
                    # Se non troviamo posti, prendi il primo disponibile
                    if attempts >= max_attempts:
                        for idx in range(num_groups):
                            if len(groups[group_names[idx]]) < group_sizes[idx]:
                                next_idx = idx
                                direction = 1 if idx > current_idx else -1
                                break
                        break
                
                # Assicurati che next_idx sia valido
                if next_idx < 0:
                    next_idx = 0
                if next_idx >= num_groups:
                    next_idx = num_groups - 1
                
                current_idx = next_idx
        
        # ========================================
        # OTTIMIZZA SEPARAZIONE CLUB (se richiesto)
        # ========================================
        if self.chk_separate_clubs.isChecked():
            print("\n   🔄 Ottimizzazione separazione club...")
            groups = self._optimize_club_separation(groups, group_sizes)
        
        # Salva gruppi
        groups_key = f"team_groups_{cat}"
        self.parent.groups[groups_key] = groups
        
        for group_name, group_teams in groups.items():
            for team in group_teams:
                team.group = group_name
        
        self.refresh()
        
        size_info = ", ".join([f"{chr(65+i)}:{size}" for i, size in enumerate(group_sizes)])
        QMessageBox.information(self, "Successo", 
                               f"✅ Distribuzione completata:\n{len(cat_teams)} squadre in {num_groups} gironi\nDimensioni: {size_info}")
    
    def _optimize_club_separation(self, groups: dict, group_sizes: list) -> dict:
        """Ottimizza la separazione dei club nei gironi squadre."""
        num_groups = len(groups)
        max_iterations = 50
        
        for _ in range(max_iterations):
            moved = False
            
            # Raccogli posizioni dei club
            club_positions = {}
            for group_name, teams in groups.items():
                for team in teams:
                    if team.club not in club_positions:
                        club_positions[team.club] = []
                    club_positions[team.club].append((group_name, team))
            
            # Per ogni club con più squadre nello stesso girone
            for club, positions in club_positions.items():
                # Raggruppa per girone
                per_group = {}
                for group_name, team in positions:
                    if group_name not in per_group:
                        per_group[group_name] = []
                    per_group[group_name].append(team)
                
                # Per ogni girone con più squadre dello stesso club
                for group_name, club_teams in per_group.items():
                    if len(club_teams) <= 1:
                        continue
                    
                    # Prova a spostare le squadre in eccesso
                    for team_to_move in club_teams[1:]:
                        # Cerca un girone senza questo club
                        for target_group in groups.keys():
                            if target_group == group_name:
                                continue
                            # Verifica se il girone target ha già questo club
                            if any(t.club == club for t in groups[target_group]):
                                continue
                            # Verifica se c'è spazio
                            target_idx = ord(target_group) - 65
                            if len(groups[target_group]) < group_sizes[target_idx]:
                                # Sposta
                                groups[group_name].remove(team_to_move)
                                groups[target_group].append(team_to_move)
                                moved = True
                                print(f"      ✅ Spostato {team_to_move.display_name} "
                                      f"da girone {group_name} a {target_group}")
                                break
                        if moved:
                            break
                    if moved:
                        break
                if moved:
                    break
            
            if not moved:
                break
        
        return groups
    
    def refresh(self):
        """Aggiorna la visualizzazione dei gironi squadre."""
        if not self.parent.current_tournament:
            return
        
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        # Calcola statistiche
        cat_teams = [t for t in self.parent.teams if t.category == cat]
        self.lbl_cat_teams.setText(f"👥 {len(cat_teams)} squadre")
        
        groups_key = f"team_groups_{cat}"
        cat_groups = self.parent.groups.get(groups_key, {})
        self.lbl_cat_groups.setText(f"🪩 {len(cat_groups)} gironi")
        
        # Pulisci layout
        for i in reversed(range(self.team_groups_layout.count())): 
            widget = self.team_groups_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if not cat_groups:
            label = QLabel("Nessun girone creato. Clicca 'Distribuisci Squadre' per crearli.")
            label.setAlignment(Qt.AlignCenter)
            self.team_groups_layout.addWidget(label)
            self.btn_edit_team_groups.setEnabled(False)
            return
        
        self.btn_edit_team_groups.setEnabled(True)
        
        # Crea visualizzazione a griglia ottimizzata
        groups_display = self._create_groups_grid(cat_groups, cat)
        self.team_groups_layout.addWidget(groups_display)
    
    def reset_team_groups(self):
        """Resetta i gironi squadre per la categoria corrente."""
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        reply = QMessageBox.question(self, "Conferma",
                                    f"Eliminare tutti i gironi per la categoria {cat}?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        
        for team in self.parent.teams:
            if team.category == cat:
                team.group = None
        
        groups_key = f"team_groups_{cat}"
        if groups_key in self.parent.groups:
            del self.parent.groups[groups_key]
        
        self.refresh()
    
    def export_team_groups(self):
        """Esporta gironi squadre in Excel."""
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        groups_key = f"team_groups_{cat}"
        groups = self.parent.groups.get(groups_key, {})
        
        if not groups:
            QMessageBox.warning(self, "Attenzione", f"Nessun girone per la categoria {cat}")
            return
        
        import pandas as pd
        
        data = []
        for group_name, group_teams in groups.items():
            for team in group_teams:
                players_list = ", ".join([p.display_name for p in team.players[:3]])
                if len(team.players) > 3:
                    players_list += f" e {len(team.players)-3} altri"
                
                data.append({
                    "Girone": group_name,
                    "Seed": team.seed if team.seed else "",
                    "ID Squadra": team.id,
                    "Squadra": team.display_name,
                    "Club": team.club or "",
                    "Nazione": team.country,
                    "Categoria": cat,
                    "N. Giocatori": len(team.players),
                    "Giocatori": players_list
                })
        
        df = pd.DataFrame(data)
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = data_dir / f"gironi_squadre_{cat}_{timestamp}.xlsx"
        
        try:
            df.to_excel(filename, index=False)
            QMessageBox.information(self, "Successo", 
                                   f"✅ File salvato:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def import_team_groups_from_excel(self):
        """Importa gironi squadre da Excel modificato."""
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona file Excel con gironi modificati",
            str(Path("data").absolute()),
            "File Excel (*.xlsx);;Tutti i file (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            required_cols = ['Girone', 'Squadra']
            missing = [c for c in required_cols if c not in df.columns]
            
            if missing:
                QMessageBox.critical(self, "Errore", 
                                    f"Colonne mancanti nel file Excel:\n{', '.join(missing)}")
                return
            
            new_groups = {}
            errors = []
            teams_processed = 0
            
            for _, row in df.iterrows():
                group_name = str(row['Girone']).strip()
                if not group_name:
                    continue
                
                team_id = str(row['ID Squadra']).strip() if pd.notna(row.get('ID Squadra')) else ""
                team_name = str(row['Squadra']).strip()
                
                team = None
                if team_id:
                    team = next((t for t in self.parent.teams if t.id == team_id and t.category == cat), None)
                if not team and team_name:
                    team = next((t for t in self.parent.teams if t.display_name == team_name and t.category == cat), None)
                
                if not team:
                    errors.append(f"Squadra '{team_name}' (ID: {team_id}) non trovata")
                    continue
                
                if group_name not in new_groups:
                    new_groups[group_name] = []
                
                if team in new_groups[group_name]:
                    errors.append(f"Squadra {team.display_name} duplicata")
                    continue
                
                new_groups[group_name].append(team)
                teams_processed += 1
            
            if new_groups:
                groups_key = f"team_groups_{cat}"
                self.parent.groups[groups_key] = new_groups
                
                for group_name, teams in new_groups.items():
                    for team in teams:
                        team.group = group_name
                
                self.refresh()
                
                msg = f"✅ Importate {teams_processed} squadre in {len(new_groups)} gironi"
                if errors:
                    msg += f"\n\n⚠️ {len(errors)} errori:\n" + "\n".join(errors[:5])
                QMessageBox.information(self, "Successo", msg)
            else:
                QMessageBox.warning(self, "Attenzione", "Nessuna squadra importata")
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore: {str(e)}")
    
    def manual_edit_team_groups(self):
        """Dialog per modifica manuale dei gironi squadre con sistema di selezione e scambio (no drag&drop)."""
        cat = self.team_group_category.currentText()
        if not cat:
            return
        
        groups_key = f"team_groups_{cat}"
        if groups_key not in self.parent.groups:
            QMessageBox.warning(self, "Attenzione", "Nessun girone da modificare")
            return
        
        groups = self.parent.groups[groups_key]
        cat_teams = [t for t in self.parent.teams if t.category == cat]
        ideal_sizes = self.calculate_team_group_sizes(len(cat_teams), len(groups))
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifica Gironi Squadre - {cat}")
        dialog.setModal(True)
        dialog.resize(1200, 800)
        
        layout = QVBoxLayout(dialog)
        
        # Istruzioni
        instructions = QLabel(
            "📋 **Istruzioni:**\n"
            "1. Seleziona una squadra da un girone (clicca sul nome)\n"
            "2. Seleziona una squadra da un altro girone\n"
            "3. Clicca '🔄 Scambia Selezione' per scambiarle\n\n"
            "📊 Verde = numero squadre corretto | Arancione = poche | Rosso = troppe"
        )
        instructions.setStyleSheet("color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Widget principale con splitter orizzontale
        splitter = QSplitter(Qt.Horizontal)
        
        # Dizionari per tenere traccia dei widget
        group_widgets = {}
        group_names = list(groups.keys())
        
        # Crea un widget per ogni girone
        for i, group_name in enumerate(sorted(group_names)):
            teams = groups[group_name]
            container = QWidget()
            vbox = QVBoxLayout(container)
            
            ideal = ideal_sizes[i]
            current = len(teams)
            
            # Colore del bordo in base allo stato
            if current == ideal:
                border_color = "#4CAF50"  # Verde
            elif current < ideal:
                border_color = "#FF9800"  # Arancione
            else:
                border_color = "#f44336"  # Rosso
            
            container.setStyleSheet(f"""
                QWidget {{
                    border: 2px solid {border_color};
                    border-radius: 8px;
                    background-color: #fafafa;
                }}
            """)
            
            # Header con nome girone e conteggio
            header = QLabel(f"<b style='font-size:14px'>GIRONE {group_name}</b>  <span style='color:{border_color}'>({current}/{ideal})</span>")
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("padding: 5px; background-color: #e0e0e0; border-radius: 4px;")
            vbox.addWidget(header)
            
            # Lista squadre
            list_widget = QListWidget()
            list_widget.setSelectionMode(QListWidget.ExtendedSelection)
            list_widget.setStyleSheet("""
                QListWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                QListWidget::item:selected {
                    background-color: #2196F3;
                    color: white;
                }
                QListWidget::item:hover {
                    background-color: #e3f2fd;
                }
            """)
            
            for team in sorted(teams, key=lambda t: t.display_name):
                seed = f"[{team.seed}]" if team.seed else ""
                players_count = f" ({len(team.players)} gioc.)"
                text = f"{seed} {team.display_name}{players_count}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, team)
                list_widget.addItem(item)
            
            vbox.addWidget(list_widget)
            
            # Pulsanti per spostamenti rapidi all'interno dello stesso girone
            btn_layout = QHBoxLayout()
            
            btn_move_up = QPushButton("⬆️ Su")
            btn_move_up.clicked.connect(lambda checked, lw=list_widget: self._move_item_up(lw))
            btn_move_up.setFixedWidth(50)
            
            btn_move_down = QPushButton("⬇️ Giù")
            btn_move_down.clicked.connect(lambda checked, lw=list_widget: self._move_item_down(lw))
            btn_move_down.setFixedWidth(50)
            
            btn_layout.addWidget(btn_move_up)
            btn_layout.addWidget(btn_move_down)
            vbox.addLayout(btn_layout)
            
            group_widgets[group_name] = list_widget
            
            splitter.addWidget(container)
        
        # Imposta proporzioni uguali
        splitter.setSizes([int(dialog.width() / len(groups))] * len(groups))
        layout.addWidget(splitter)
        
        # ========================================
        # PANNELLO AZIONI
        # ========================================
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
        
        # Pulsante Scambia Selezione
        btn_swap = QPushButton("🔄 Scambia Selezione")
        btn_swap.clicked.connect(lambda: self._swap_selected_teams(group_widgets))
        btn_swap.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        actions_layout.addWidget(btn_swap)
        
        # Pulsante Sposta in...
        btn_move_to = QPushButton("📦 Sposta selezionati in...")
        btn_move_to.clicked.connect(lambda: self._move_selected_team_to_group(group_widgets, group_names))
        btn_move_to.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        actions_layout.addWidget(btn_move_to)
        
        # Pulsante Svuota Selezione
        btn_clear = QPushButton("🗑️ Svuota Selezione")
        btn_clear.clicked.connect(lambda: self._clear_selection(group_widgets))
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        actions_layout.addWidget(btn_clear)
        
        actions_layout.addStretch()
        
        # Pulsante Salva e Annulla
        btn_save = QPushButton("💾 Salva Modifiche")
        btn_save.clicked.connect(lambda: self._save_edit_changes(dialog, cat, group_widgets))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        actions_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("✖ Annulla")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 30px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        actions_layout.addWidget(btn_cancel)
        
        layout.addWidget(actions_frame)
        
        # Info aggiuntive
        info_label = QLabel("💡 **Suggerimento:** Seleziona squadre in gironi diversi e clicca 'Scambia Selezione' per scambiarle. Usa 'Sposta selezionati in...' per spostare una squadra in un altro girone.")
        info_label.setStyleSheet("color: #666; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        dialog.exec()
    
    def _move_item_up(self, list_widget: QListWidget):
        """Sposta l'elemento selezionato verso l'alto."""
        current_row = list_widget.currentRow()
        if current_row > 0:
            item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row - 1, item)
            list_widget.setCurrentRow(current_row - 1)
    
    def _move_item_down(self, list_widget: QListWidget):
        """Sposta l'elemento selezionato verso il basso."""
        current_row = list_widget.currentRow()
        if current_row < list_widget.count() - 1:
            item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row + 1, item)
            list_widget.setCurrentRow(current_row + 1)
    
    def _swap_selected_teams(self, group_widgets: dict):
        """Scambia le squadre selezionate tra due gironi."""
        selected_items = []
        selected_groups = []
        
        # Raccogli tutti gli elementi selezionati
        for group_name, list_widget in group_widgets.items():
            for item in list_widget.selectedItems():
                selected_items.append(item)
                selected_groups.append(group_name)
        
        if len(selected_items) != 2:
            QMessageBox.warning(self, "Attenzione", 
                               f"Seleziona esattamente 2 squadre da scambiare (una per girone).\nAttualmente selezionati: {len(selected_items)}")
            return
        
        # Verifica che siano in gironi diversi
        if selected_groups[0] == selected_groups[1]:
            QMessageBox.warning(self, "Attenzione", 
                               "Le due squadre devono essere in gironi diversi per essere scambiate.")
            return
        
        # Ottieni i list widget
        list1 = group_widgets[selected_groups[0]]
        list2 = group_widgets[selected_groups[1]]
        
        # Ottieni gli indici
        row1 = list1.row(selected_items[0])
        row2 = list2.row(selected_items[1])
        
        # Scambia i dati
        team1 = selected_items[0].data(Qt.UserRole)
        team2 = selected_items[1].data(Qt.UserRole)
        
        # Aggiorna le liste (ricrea gli item per mantenere i dati)
        text1 = selected_items[0].text()
        text2 = selected_items[1].text()
        
        list1.takeItem(row1)
        list2.takeItem(row2)
        
        new_item1 = QListWidgetItem(text2)
        new_item1.setData(Qt.UserRole, team2)
        list1.insertItem(row1, new_item1)
        
        new_item2 = QListWidgetItem(text1)
        new_item2.setData(Qt.UserRole, team1)
        list2.insertItem(row2, new_item2)
        
        # Aggiorna la selezione
        list1.clearSelection()
        list2.clearSelection()
        new_item1.setSelected(True)
        new_item2.setSelected(True)
    
    def _move_selected_team_to_group(self, group_widgets: dict, group_names: list):
        """Sposta la squadra selezionata in un altro girone."""
        # Trova la squadra selezionata
        selected_item = None
        source_group = None
        source_list = None
        
        for group_name, list_widget in group_widgets.items():
            for item in list_widget.selectedItems():
                selected_item = item
                source_group = group_name
                source_list = list_widget
                break
            if selected_item:
                break
        
        if not selected_item:
            QMessageBox.warning(self, "Attenzione", "Nessuna squadra selezionata.")
            return
        
        # Mostra dialog per selezionare il girone di destinazione
        target_group, ok = QInputDialog.getItem(
            self, "Sposta squadra", 
            f"Sposta {selected_item.text()} in quale girone?",
            group_names, 0, False
        )
        
        if not ok or target_group == source_group:
            return
        
        # Esegui lo spostamento
        target_list = group_widgets[target_group]
        team = selected_item.data(Qt.UserRole)
        text = selected_item.text()
        
        row = source_list.row(selected_item)
        source_list.takeItem(row)
        
        new_item = QListWidgetItem(text)
        new_item.setData(Qt.UserRole, team)
        target_list.addItem(new_item)
        
        # Aggiorna la selezione
        source_list.clearSelection()
        new_item.setSelected(True)
    
    def _clear_selection(self, group_widgets: dict):
        """Svuota tutte le selezioni."""
        for list_widget in group_widgets.values():
            list_widget.clearSelection()
    
    def _save_edit_changes(self, dialog, category, group_widgets):
        """Salva le modifiche ai gironi squadre."""
        groups_key = f"team_groups_{category}"
        new_groups = {}
        
        for group_name, list_widget in group_widgets.items():
            teams = []
            for i in range(list_widget.count()):
                teams.append(list_widget.item(i).data(Qt.UserRole))
            new_groups[group_name] = teams
        
        self.parent.groups[groups_key] = new_groups
        
        for group_name, teams in new_groups.items():
            for team in teams:
                team.group = group_name
        
        dialog.accept()
        self.refresh()
        QMessageBox.information(self, "Successo", "Modifiche ai gironi salvate!")
    
    def on_tab_selected(self):
        """Chiamato quando la tab viene selezionata."""
        self.refresh()