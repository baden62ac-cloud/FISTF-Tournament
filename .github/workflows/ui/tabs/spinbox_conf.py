# utils/spinbox_styles.py
"""
Stili e funzioni di utilità per gli spinbox dell'applicazione.
Centralizza la configurazione degli spinbox per uniformità e manutenibilità.
"""
from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from typing import Optional, Literal

# ========================================
# STILI SPINBOX
# ========================================

# Stile base per spinbox standard
STYLE_SPINBOX_BASE = """
    QSpinBox {
        font-size: 12px;
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 4px;
        min-width: 60px;
    }
    QSpinBox:hover {
        border-color: #999999;
        background-color: #fafafa;
    }
    QSpinBox:focus {
        border-color: #2196F3;
        background-color: white;
        outline: none;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px;
        background-color: #f0f0f0;
        border-radius: 2px;
        border: none;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #e0e0e0;
    }
    QSpinBox::up-arrow, QSpinBox::down-arrow {
        width: 10px;
        height: 10px;
    }
    QSpinBox::up-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 5px solid #666;
    }
    QSpinBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #666;
    }
"""

# Stile per spinbox di grandi dimensioni (es. gol)
STYLE_SPINBOX_LARGE = """
    QSpinBox {
        font-size: 16px;
        font-weight: bold;
        background-color: white;
        border: 2px solid #cccccc;
        border-radius: 6px;
        padding: 6px;
        min-width: 80px;
        min-height: 35px;
    }
    QSpinBox:hover {
        border-color: #999999;
        background-color: #fafafa;
    }
    QSpinBox:focus {
        border-color: #FF9800;
        background-color: #fff3e0;
        outline: none;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 28px;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 3px;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #e0e0e0;
    }
"""

# Stile per spinbox gol (giocatore 1 - verde)
STYLE_SPINBOX_GOAL1 = STYLE_SPINBOX_LARGE + """
    QSpinBox {
        background-color: #e8f5e8;
        border-color: #4CAF50;
    }
    QSpinBox:focus {
        border-color: #FF9800;
        background-color: #fff3e0;
    }
"""

# Stile per spinbox gol (giocatore 2 - rosso)
STYLE_SPINBOX_GOAL2 = STYLE_SPINBOX_LARGE + """
    QSpinBox {
        background-color: #ffebee;
        border-color: #f44336;
    }
    QSpinBox:focus {
        border-color: #FF9800;
        background-color: #fff3e0;
    }
"""

# Stile per spinbox gironi (evidenziato)
STYLE_SPINBOX_GROUPS = """
    QSpinBox {
        font-size: 13px;
        font-weight: bold;
        background-color: white;
        border: 2px solid #4CAF50;
        border-radius: 5px;
        padding: 4px;
        min-width: 60px;
    }
    QSpinBox:focus {
        border-color: #2196F3;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px;
        background-color: #e8f5e8;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #c8e6c9;
    }
"""

# Stile per spinbox campi
STYLE_SPINBOX_FIELDS = """
    QSpinBox {
        font-size: 12px;
        font-weight: bold;
        background-color: #e8f5e9;
        border: 2px solid #4CAF50;
        border-radius: 5px;
        padding: 4px;
        min-width: 60px;
    }
    QSpinBox:focus {
        border-color: #FF9800;
        background-color: #fff3e0;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px;
        background-color: #e8f5e8;
    }
"""

# Stile per spinbox seed
STYLE_SPINBOX_SEED = """
    QSpinBox {
        font-size: 11px;
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 4px;
        min-width: 70px;
    }
    QSpinBox:hover {
        border-color: #999999;
    }
    QSpinBox:focus {
        border-color: #2196F3;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 18px;
    }
"""

# Stile per spinbox piccoli
STYLE_SPINBOX_SMALL = """
    QSpinBox {
        font-size: 11px;
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 2px;
        min-width: 50px;
    }
    QSpinBox:hover {
        border-color: #999999;
    }
    QSpinBox:focus {
        border-color: #2196F3;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 16px;
    }
"""

# ========================================
# FUNZIONI DI UTILITÀ
# ========================================

def create_spinbox(
    min_val: int = 0,
    max_val: int = 100,
    default: int = 0,
    width: int = 70,
    height: Optional[int] = None,
    alignment: Literal['center', 'left', 'right'] = 'center',
    style: Literal['base', 'large', 'goal1', 'goal2', 'groups', 'fields', 'seed', 'small'] = 'base',
    tooltip: str = "",
    enabled: bool = True,
    special_text: str = ""
) -> QSpinBox:
    """
    Crea uno spinbox con stile uniforme.
    
    Args:
        min_val: valore minimo
        max_val: valore massimo
        default: valore di default
        width: larghezza in pixel
        height: altezza in pixel (opzionale)
        alignment: allineamento ('center', 'left', 'right')
        style: stile predefinito ('base', 'large', 'goal1', 'goal2', 'groups', 'fields', 'seed', 'small')
        tooltip: testo di aiuto
        enabled: se abilitato
        special_text: testo speciale per valore 0 (es. "Nessuno")
    
    Returns:
        QSpinBox configurato
    """
    spinbox = QSpinBox()
    spinbox.setMinimum(min_val)
    spinbox.setMaximum(max_val)
    spinbox.setValue(default)
    spinbox.setFixedWidth(width)
    
    if height:
        spinbox.setFixedHeight(height)
    
    # Imposta allineamento
    if alignment == 'center':
        spinbox.setAlignment(Qt.AlignCenter)
    elif alignment == 'left':
        spinbox.setAlignment(Qt.AlignLeft)
    elif alignment == 'right':
        spinbox.setAlignment(Qt.AlignRight)
    
    # Imposta testo speciale per valore 0
    if special_text:
        spinbox.setSpecialValueText(special_text)
    
    # Imposta tooltip
    if tooltip:
        spinbox.setToolTip(tooltip)
    
    # Abilita/disabilita
    spinbox.setEnabled(enabled)
    
    # Applica stile
    styles = {
        'base': STYLE_SPINBOX_BASE,
        'large': STYLE_SPINBOX_LARGE,
        'goal1': STYLE_SPINBOX_GOAL1,
        'goal2': STYLE_SPINBOX_GOAL2,
        'groups': STYLE_SPINBOX_GROUPS,
        'fields': STYLE_SPINBOX_FIELDS,
        'seed': STYLE_SPINBOX_SEED,
        'small': STYLE_SPINBOX_SMALL,
    }
    
    spinbox.setStyleSheet(styles.get(style, STYLE_SPINBOX_BASE))
    
    return spinbox


def create_spinbox_goal(
    player: int = 1,
    default: int = 0,
    width: int = 80,
    height: int = 40,
    tooltip: str = ""
) -> QSpinBox:
    """
    Crea uno spinbox per l'inserimento gol.
    
    Args:
        player: 1 per giocatore di sinistra (verde), 2 per giocatore di destra (rosso)
        default: valore di default
        width: larghezza in pixel
        height: altezza in pixel
        tooltip: testo di aiuto
    
    Returns:
        QSpinBox configurato per gol
    """
    style = 'goal1' if player == 1 else 'goal2'
    default_tooltip = f"Gol del {'primo' if player == 1 else 'secondo'} giocatore"
    
    return create_spinbox(
        min_val=0,
        max_val=20,
        default=default,
        width=width,
        height=height,
        alignment='center',
        style=style,
        tooltip=tooltip or default_tooltip
    )


def create_spinbox_seed(
    default: int = 0,
    width: int = 80,
    tooltip: str = "Seed (posizione nel ranking). Lascia 0 per nessun seed."
) -> QSpinBox:
    """
    Crea uno spinbox per il seed di giocatori/squadre.
    
    Returns:
        QSpinBox configurato per seed
    """
    return create_spinbox(
        min_val=1,
        max_val=999,
        default=default,
        width=width,
        alignment='center',
        style='seed',
        tooltip=tooltip,
        special_text="Nessuno"
    )


def create_spinbox_groups(
    default: int = 2,
    min_val: int = 1,
    max_val: int = 16,
    width: int = 70,
    tooltip: str = "Numero di gironi per questa categoria"
) -> QSpinBox:
    """
    Crea uno spinbox per il numero di gironi.
    
    Returns:
        QSpinBox configurato per gironi
    """
    return create_spinbox(
        min_val=min_val,
        max_val=max_val,
        default=default,
        width=width,
        alignment='center',
        style='groups',
        tooltip=tooltip
    )


def create_spinbox_fields(
    default: int = 4,
    min_val: int = 1,
    max_val: int = 20,
    width: int = 70,
    tooltip: str = "Numero di campi disponibili per questo torneo"
) -> QSpinBox:
    """
    Crea uno spinbox per il numero di campi.
    
    Returns:
        QSpinBox configurato per campi
    """
    return create_spinbox(
        min_val=min_val,
        max_val=max_val,
        default=default,
        width=width,
        alignment='center',
        style='fields',
        tooltip=tooltip
    )


def create_spinbox_quick(
    default: int = 0,
    width: int = 70,
    height: int = 35,
    player: int = 1
) -> QSpinBox:
    """
    Crea uno spinbox per inserimento rapido risultati.
    
    Args:
        default: valore di default
        width: larghezza
        height: altezza
        player: 1 (verde) o 2 (rosso)
    
    Returns:
        QSpinBox configurato
    """
    return create_spinbox_goal(
        player=player,
        default=default,
        width=width,
        height=height,
        tooltip=f"Gol del {'primo' if player == 1 else 'secondo'} giocatore"
    )


# ========================================
# ESEMPIO DI UTILIZZO
# ========================================

if __name__ == "__main__":
    # Questo blocco mostra come utilizzare le funzioni
    print("=" * 60)
    print("SPINBOX STYLES - Esempi di utilizzo")
    print("=" * 60)
    print()
    print("Per utilizzare gli spinbox nei vari file:")
    print()
    print("1. Importa le funzioni:")
    print("   from utils.spinbox_styles import create_spinbox, create_spinbox_goal, create_spinbox_seed")
    print()
    print("2. Esempi di creazione:")
    print()
    print("   # Spinbox per seed giocatore")
    print("   seed = create_spinbox_seed(default=1)")
    print()
    print("   # Spinbox per numero gironi")
    print("   spin_groups = create_spinbox_groups(default=2)")
    print()
    print("   # Spinbox per campi")
    print("   spin_fields = create_spinbox_fields(default=4)")
    print()
    print("   # Spinbox per gol (giocatore 1 - verde)")
    print("   goals1 = create_spinbox_goal(player=1)")
    print()
    print("   # Spinbox per gol (giocatore 2 - rosso)")
    print("   goals2 = create_spinbox_goal(player=2)")
    print()
    print("   # Spinbox personalizzato")
    print("   custom = create_spinbox(min_val=0, max_val=100, default=50, style='large')")
    print()
    print("=" * 60)