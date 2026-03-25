# utils/helpers.py
"""
Funzioni di utilità per FISTF Tournament Manager.
"""
import re
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date
from pathlib import Path


# ========================================
# FUNZIONI DI VALIDAZIONE
# ========================================

def validate_licence(licence: str) -> bool:
    """
    Valida il formato licenza FISTF.
    Formato: 3 lettere + 5 numeri (es. ITA12345)
    """
    pattern = r'^[A-Z]{3}\d{5}$'
    return bool(re.match(pattern, licence.upper()))


def validate_country(country: str) -> str:
    """Normalizza il codice paese a 3 lettere maiuscole."""
    return country.upper()[:3]


def validate_team_id(team_id: str) -> bool:
    """Valida il formato ID squadra."""
    pattern = r'^[A-Z0-9_]{3,20}$'
    return bool(re.match(pattern, team_id.upper()))


# ========================================
# FUNZIONI DI CONVERSIONE
# ========================================

def safe_int(value: Any, default: int = 0) -> int:
    """Converte in int in modo sicuro."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Converte in float in modo sicuro."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_result(result_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parsa una stringa risultato nel formato "X-Y".
    Restituisce (gol1, gol2) o (None, None) se non valido.
    """
    if not result_str or result_str == "vs":
        return None, None
    
    if '-' in result_str:
        parts = result_str.split('-')
        if len(parts) == 2:
            try:
                g1 = int(parts[0].strip())
                g2 = int(parts[1].strip())
                return g1, g2
            except ValueError:
                pass
    
    return None, None


# ========================================
# FUNZIONI DI FILE
# ========================================

def ensure_directory(path: Path) -> Path:
    """Crea la directory se non esiste."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir() -> Path:
    """Restituisce il percorso della directory data."""
    data_dir = Path("data")
    return ensure_directory(data_dir)


def get_pdf_dir() -> Path:
    """Restituisce il percorso della directory pdf."""
    pdf_dir = Path("pdf")
    return ensure_directory(pdf_dir)


def get_saves_dir() -> Path:
    """Restituisce il percorso della directory saves."""
    saves_dir = Path("saves")
    return ensure_directory(saves_dir)


def get_backup_dir() -> Path:
    """Restituisce il percorso della directory backup."""
    backup_dir = Path("saves/backup")
    return ensure_directory(backup_dir)


def get_timestamp() -> str:
    """Restituisce timestamp formattato per nomi file."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def sanitize_filename(name: str) -> str:
    """Pulisce una stringa per usarla come nome file."""
    # Rimuove caratteri non validi
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Sostituisce spazi con underscore
    name = name.replace(' ', '_')
    # Limita lunghezza
    if len(name) > 100:
        name = name[:100]
    return name


# ========================================
# FUNZIONI DI DATA
# ========================================

def format_date(d: date) -> str:
    """Formatta una data in formato DD/MM/YYYY."""
    return d.strftime('%d/%m/%Y')


def format_datetime(dt: datetime) -> str:
    """Formatta un datetime in formato DD/MM/YYYY HH:MM."""
    return dt.strftime('%d/%m/%Y %H:%M')


def parse_date(date_str: str) -> Optional[date]:
    """Parsa una stringa data nel formato YYYY-MM-DD."""
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


# ========================================
# FUNZIONI DI STATISTICHE
# ========================================

def calculate_win_percentage(wins: int, total: int) -> float:
    """Calcola la percentuale di vittorie."""
    if total == 0:
        return 0.0
    return (wins / total) * 100


def calculate_average(goals: int, matches: int) -> float:
    """Calcola la media gol per partita."""
    if matches == 0:
        return 0.0
    return round(goals / matches, 2)


def format_average(avg: float) -> str:
    """Formatta una media con 2 decimali."""
    return f"{avg:.2f}"


# ========================================
# FUNZIONI DI DISTRIBUZIONE GIRONI
# ========================================

def calculate_group_sizes(num_players: int, num_groups: int) -> List[int]:
    """
    Calcola le dimensioni dei gironi secondo regole FISTF.
    I gironi più piccoli vanno all'inizio.
    """
    base_size = num_players // num_groups
    remainder = num_players % num_groups
    
    sizes = [base_size] * (num_groups - remainder) + [base_size + 1] * remainder
    
    # Regole FISTF: se base_size è 3, i gironi da 4 vanno alla fine
    if base_size == 3:
        return [3] * (num_groups - remainder) + [4] * remainder
    elif base_size == 4:
        return [4] * (num_groups - remainder) + [5] * remainder
    elif base_size == 5:
        return [5] * (num_groups - remainder) + [6] * remainder
    
    return sizes


def get_qualifiers_from_group_size(group_size: int) -> int:
    """
    Restituisce quanti giocatori si qualificano in base alla dimensione del girone.
    Regole FISTF:
    - 3-4 giocatori: 2 qualificati
    - 5-6 giocatori: 3 qualificati
    - 7+ giocatori: 4 qualificati
    """
    if group_size <= 4:
        return 2
    elif group_size <= 6:
        return 3
    else:
        return 4


# ========================================
# FUNZIONI DI SORTEGGIO
# ========================================

def snake_distribution(items: List[Any], num_groups: int, group_sizes: List[int]) -> List[List[Any]]:
    """
    Distribuisce gli items nei gironi con pattern a serpentina.
    I primi items (con seed più alto) vanno nei primi gironi.
    """
    groups = [[] for _ in range(num_groups)]
    available = group_sizes.copy()
    
    direction = 1
    current_idx = 0
    
    for item in items:
        groups[current_idx].append(item)
        available[current_idx] -= 1
        
        # Calcola prossimo indice
        next_idx = current_idx + direction
        
        # Cambia direzione se necessario
        if next_idx < 0 or next_idx >= num_groups:
            direction *= -1
            next_idx = current_idx + direction
        
        # Cerca prossimo girone con posti disponibili
        while 0 <= next_idx < num_groups and available[next_idx] == 0:
            next_idx += direction
            if next_idx < 0 or next_idx >= num_groups:
                direction *= -1
                next_idx = current_idx + direction
        
        current_idx = next_idx
    
    return groups


# ========================================
# FUNZIONI DI ESPORTAZIONE
# ========================================

def prepare_export_dataframe(standings_data: List[Dict]) -> Dict[str, Any]:
    """Prepara i dati per l'esportazione Excel."""
    import pandas as pd
    return pd.DataFrame(standings_data)


def save_dataframe_excel(df: Any, filename: str, sheet_name: str = "Classifica") -> Path:
    """Salva un DataFrame in Excel."""
    data_dir = get_data_dir()
    filepath = data_dir / filename
    
    df.to_excel(filepath, index=False, sheet_name=sheet_name)
    return filepath


def save_dataframe_csv(df: Any, filename: str) -> Path:
    """Salva un DataFrame in CSV."""
    data_dir = get_data_dir()
    filepath = data_dir / filename
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return filepath


# ========================================
# FUNZIONI DI DEBUG
# ========================================

def print_dict_structure(d: Dict, indent: int = 0, max_depth: int = 3):
    """Stampa la struttura di un dizionario per debug."""
    if max_depth <= 0:
        print("  " * indent + "...")
        return
    
    for key, value in d.items():
        if isinstance(value, dict):
            print("  " * indent + f"{key}:")
            print_dict_structure(value, indent + 1, max_depth - 1)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            print("  " * indent + f"{key}: [{len(value)} items]")
            if max_depth > 1:
                print_dict_structure(value[0], indent + 1, max_depth - 1)
        else:
            print("  " * indent + f"{key}: {type(value).__name__}")


def log_function_call(func):
    """Decorator per log delle chiamate a funzione."""
    import functools
    import logging
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Chiamata: {func.__name__}()")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Risultato: {func.__name__}() -> OK")
            return result
        except Exception as e:
            logger.error(f"Errore in {func.__name__}(): {e}")
            raise
    
    return wrapper

# ========================================
# FUNZIONI PER IMPORT/EXPORT CALENDARIO
# ========================================

def export_calendar_to_csv(matches, filename: str, tournament_name: str = "") -> str:
    """
    Esporta il calendario partite in formato CSV.
    
    Args:
        matches: Lista di partite (individuali o squadre)
        filename: Nome del file
        tournament_name: Nome del torneo per intestazione
    
    Returns:
        Percorso del file creato
    """
    import pandas as pd
    from pathlib import Path
    
    data = []
    for match in matches:
        # Determina se è partita individuale o a squadre
        is_team = hasattr(match, 'individual_matches')
        
        if is_team:
            # Partita a squadre
            team1_name = match.player1
            team2_name = match.player2
            result = match.team_result if match.is_played else "vs"
            detail = " | ".join([f"{im.goals1}-{im.goals2}" if im.is_played else "vs" 
                                 for im in match.individual_matches])
        else:
            # Partita individuale
            team1_name = match.player1
            team2_name = match.player2
            result = match.result if match.is_played else "vs"
            detail = ""
        
        data.append({
            "ID": match.id,
            "Categoria": match.category,
            "Fase": match.phase,
            "Girone": match.group or "",
            "Campo": match.field or "",
            "Orario": match.scheduled_time or "",
            "Giocatore/Squadra 1": team1_name,
            "Risultato": result,
            "Giocatore/Squadra 2": team2_name,
            "Arbitro": match.referee if hasattr(match, 'referee') else "",
            "Stato": match.status.value if hasattr(match.status, 'value') else str(match.status),
            "Dettaglio": detail
        })
    
    df = pd.DataFrame(data)
    
    # Crea directory data se non esiste
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / filename
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return str(filepath)


def import_calendar_from_csv(file_path: str) -> list:
    """
    Importa il calendario da file CSV.
    
    Args:
        file_path: Percorso del file CSV
    
    Returns:
        Lista di dizionari con i dati delle partite
    """
    import pandas as pd
    
    df = pd.read_csv(file_path, encoding='utf-8')
    
    matches_data = []
    for _, row in df.iterrows():
        match_data = {
            "id": str(row.get("ID", "")),
            "category": str(row.get("Categoria", "")),
            "phase": str(row.get("Fase", "Groups")),
            "group": str(row.get("Girone", "")) if pd.notna(row.get("Girone")) else None,
            "field": int(row.get("Campo", 0)) if pd.notna(row.get("Campo")) and str(row.get("Campo")).isdigit() else None,
            "scheduled_time": str(row.get("Orario", "")) if pd.notna(row.get("Orario")) else None,
            "player1": str(row.get("Giocatore/Squadra 1", "")),
            "result": str(row.get("Risultato", "vs")),
            "player2": str(row.get("Giocatore/Squadra 2", "")),
            "referee": str(row.get("Arbitro", "")) if pd.notna(row.get("Arbitro")) else None,
            "status": str(row.get("Stato", "Programmata")),
            "detail": str(row.get("Dettaglio", "")) if pd.notna(row.get("Dettaglio")) else None
        }
        matches_data.append(match_data)
    
    return matches_data


def export_calendar_template(filename: str = "template_calendario.csv", is_team: bool = False) -> str:
    """
    Esporta un template CSV per l'importazione del calendario.
    
    Args:
        filename: Nome del file
        is_team: True per torneo a squadre, False per individuale
    
    Returns:
        Percorso del file creato
    """
    import pandas as pd
    from pathlib import Path
    
    if is_team:
        # Template per torneo a squadre
        data = [{
            "ID": "TO_A_1",
            "Categoria": "Team Open",
            "Fase": "Groups",
            "Girone": "TO-A",
            "Campo": 1,
            "Orario": "09:00",
            "Giocatore/Squadra 1": "ASD Messina A",
            "Risultato": "vs",
            "Giocatore/Squadra 2": "Palermo Sharks",
            "Arbitro": "Da assegnare",
            "Stato": "Programmata",
            "Dettaglio": "4 incontri"
        }]
    else:
        # Template per torneo individuale
        data = [{
            "ID": "O-A-1",
            "Categoria": "Open",
            "Fase": "Groups",
            "Girone": "O-A",
            "Campo": 1,
            "Orario": "09:00",
            "Giocatore/Squadra 1": "NATOLI RICCARDO",
            "Risultato": "vs",
            "Giocatore/Squadra 2": "NATOLI ALESSANDRO",
            "Arbitro": "Da assegnare",
            "Stato": "Programmata",
            "Dettaglio": ""
        }]
    
    df = pd.DataFrame(data)
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / filename
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return str(filepath)


def create_groups_display(groups: dict, title: str = "", is_team: bool = False):
    """
    Crea un widget per visualizzare i gironi in layout ottimizzato.
    
    Args:
        groups: Dizionario {nome_girone: lista_giocatori/squadre}
        title: Titolo da mostrare sopra i gironi
        is_team: True per squadre, False per giocatori
    
    Returns:
        QWidget con la visualizzazione ottimizzata
    """
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    
    # Widget principale
    main_widget = QWidget()
    main_layout = QVBoxLayout(main_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    
    # Titolo se fornito
    if title:
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px 0; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
    
    # Area scroll per i gironi
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameStyle(QFrame.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    # Container per i gironi
    groups_container = QWidget()
    groups_layout = QGridLayout(groups_container)
    groups_layout.setSpacing(15)
    groups_layout.setContentsMargins(10, 10, 10, 10)
    
    # Calcola il numero di colonne in base al numero di gironi
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
    
    # Stile comune per i widget girone
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
    
    player_style = """
        padding: 4px 8px;
        margin: 2px;
        border-radius: 4px;
        background-color: white;
        font-size: 11px;
    """
    
    for idx, (group_name, items) in enumerate(sorted(groups.items())):
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
        count_label = QLabel(f"📊 {len(items)} {'squadre' if is_team else 'giocatori'}")
        count_label.setStyleSheet("font-size: 10px; color: #7f8c8d; text-align: center;")
        count_label.setAlignment(Qt.AlignCenter)
        group_layout.addWidget(count_label)
        
        # Linea separatrice
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #bdc3c7; max-height: 1px;")
        group_layout.addWidget(line)
        
        # Lista giocatori/squadre
        if is_team:
            # Ordina squadre
            sorted_items = sorted(items, key=lambda x: (x.seed if x.seed else 999, x.name))
            for team in sorted_items:
                seed_text = f"[{team.seed}]" if team.seed else ""
                players_text = f" ({len(team.players)} gioc.)"
                team_text = f"• {team.display_name} {seed_text}{players_text}"
                label = QLabel(team_text)
                label.setStyleSheet(player_style)
                label.setWordWrap(True)
                group_layout.addWidget(label)
        else:
            # Ordina giocatori
            sorted_items = sorted(items, key=lambda x: (x.seed if x.seed else 999, x.last_name))
            for player in sorted_items:
                seed_text = f"[{player.seed}]" if player.seed else ""
                player_text = f"• {player.display_name} {seed_text} - {player.club}"
                label = QLabel(player_text)
                label.setStyleSheet(player_style)
                label.setWordWrap(True)
                group_layout.addWidget(label)
        
        # Aggiungi un po' di spazio alla fine
        group_layout.addStretch()
        
        # Imposta larghezza minima e massima
        group_widget.setMinimumWidth(280)
        group_widget.setMaximumWidth(400)
        
        groups_layout.addWidget(group_widget, row, col)
    
    # Aggiungi spazi vuoti per allineamento
    for i in range(rows * cols - num_groups):
        spacer = QWidget()
        spacer.setFixedWidth(0)
        groups_layout.addWidget(spacer, rows - 1, cols - 1 - i)
    
    scroll_area.setWidget(groups_container)
    main_layout.addWidget(scroll_area)
    
    return main_widget