# core/pdf_exporter.py
"""
Esportazione PDF di calendari, classifiche, tabelloni e gironi.
Utilizza ReportLab per la generazione PDF.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfgen import canvas
from datetime import datetime
from pathlib import Path
import os

class PDFExporter:
    """Classe per esportare vari documenti in PDF."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura stili personalizzati per i PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            alignment=1,  # Center
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=0,  # Left
            spaceAfter=10,
            textColor=colors.HexColor('#34495e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            alignment=0,
            spaceAfter=5,
            textColor=colors.HexColor('#7f8c8d')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=3,
            textColor=colors.HexColor('#95a5a6')
        ))
    
    def export_schedule(self, matches, tournament_name, filename=None):
        """
        Esporta il calendario partite in PDF (formato landscape).
        
        Args:
            matches: Lista di partite
            tournament_name: Nome del torneo
            filename: Nome file (opzionale)
        
        Returns:
            Path del file creato
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"calendario_{timestamp}.pdf"
        
        # Crea directory pdf se non esiste
        pdf_dir = Path("pdf")
        pdf_dir.mkdir(exist_ok=True)
        filepath = pdf_dir / filename
        
        # Crea il documento PDF in FORMATO LANDSCAPE (orizzontale)
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(A4),  # <-- FORMATO ORIZZONTALE
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # Titolo
        title = Paragraph(f"Calendario Partite - {tournament_name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 8*mm))
        
        # Data generazione
        date_text = Paragraph(f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                            self.styles['CustomNormal'])
        story.append(date_text)
        story.append(Spacer(1, 5*mm))
        
        # Raggruppa partite per turno (orario)
        matches_by_time = {}
        for m in matches:
            if m.scheduled_time:
                if m.scheduled_time not in matches_by_time:
                    matches_by_time[m.scheduled_time] = []
                matches_by_time[m.scheduled_time].append(m)
        
        # Ordina i turni
        for time in sorted(matches_by_time.keys()):
            # Intestazione turno
            time_header = Paragraph(f"Turno delle {time}", self.styles['CustomHeading'])
            story.append(time_header)
            story.append(Spacer(1, 3*mm))
            
            # Prepara dati tabella
            data = [["Campo", "Categoria", "Girone", "Giocatore 1", "Ris.", "Giocatore 2", "Arbitro", "Stato"]]
            
            # Ordina per campo
            sorted_matches = sorted(matches_by_time[time], key=lambda m: m.field if m.field else 0)
            
            for match in sorted_matches:
                # Determina se è partita individuale o a squadre
                if hasattr(match, 'individual_matches'):
                    # Partita a squadre
                    player1 = match.team1 if hasattr(match, 'team1') else match.player1
                    player2 = match.team2 if hasattr(match, 'team2') else match.player2
                    result = match.get_team_result() if hasattr(match, 'get_team_result') and match.is_match_played() else "vs"
                else:
                    # Partita individuale
                    player1 = match.player1
                    player2 = match.player2
                    result = match.result if match.is_played else "vs"
                
                # Ottieni stato come stringa
                if hasattr(match.status, 'value'):
                    status_text = match.status.value
                else:
                    status_text = str(match.status)
                
                data.append([
                    str(match.field) if match.field else "-",
                    match.category,
                    match.group or "-",
                    player1,
                    result,
                    player2,
                    match.referee if match.referee else "-",
                    status_text
                ])
            
            # Crea tabella con larghezze adattate al landscape
            table = Table(data, colWidths=[35, 55, 45, 120, 35, 120, 75, 55])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Colora le righe in base allo stato
            for i, match in enumerate(sorted_matches, start=1):
                if hasattr(match, 'is_match_played'):
                    is_played = match.is_match_played()
                else:
                    is_played = match.is_played
                    
                if is_played:
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#e8f5e8')),
                    ]))
            
            story.append(table)
            story.append(Spacer(1, 8*mm))
        
        # Statistiche finali
        total = len(matches)
        played = 0
        for m in matches:
            if hasattr(m, 'is_match_played'):
                if m.is_match_played():
                    played += 1
            elif m.is_played:
                played += 1
        
        stats_text = Paragraph(f"Totale partite: {total} | Giocate: {played} | Da giocare: {total - played}",
                             self.styles['CustomNormal'])
        story.append(stats_text)
        
        # Genera PDF
        doc.build(story)
        return filepath
    
    def export_standings(self, standings_df, category, group_name, tournament_name, filename=None):
        """
        Esporta una classifica in PDF (robusta per diversi nomi di colonne).
        
        Args:
            standings_df: DataFrame con la classifica
            category: Categoria
            group_name: Nome girone
            tournament_name: Nome del torneo
            filename: Nome file (opzionale)
        
        Returns:
            Path del file creato
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_group = group_name.replace("/", "_").replace("\\", "_")
            filename = f"classifica_{category}_{clean_group}_{timestamp}.pdf"
        
        pdf_dir = Path("pdf")
        pdf_dir.mkdir(exist_ok=True)
        filepath = pdf_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        
        # Titolo
        title = Paragraph(f"Classifica - {tournament_name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 5*mm))
        
        # Sottotitolo
        subtitle = Paragraph(f"Categoria: {category} - Girone {group_name}", self.styles['CustomHeading'])
        story.append(subtitle)
        story.append(Spacer(1, 10*mm))
        
        # Prepara dati tabella in modo robusto (usa get() per evitare KeyError)
        if 'Squadra' in standings_df.columns:
            # Classifica squadre (più colonne)
            headers = ["Pos", "Squadra", "Club", "Punti", "G", "V", "P", "S", "V.Ind", "GF", "GS", "DG"]
            data = [headers]
            
            for _, row in standings_df.iterrows():
                data.append([
                    str(row.get("Pos", "")),
                    row.get("Squadra", ""),
                    row.get("Club", ""),
                    str(row.get("Punti", "")),
                    str(row.get("Giocate", row.get("G", "0"))),
                    str(row.get("Vinte", row.get("V", "0"))),  # Cerca Vinte, altrimenti V
                    str(row.get("Pareggiate", row.get("P", "0"))),  # Cerca Pareggiate, altrimenti P
                    str(row.get("Perse", row.get("S", "0"))),  # Cerca Perse, altrimenti S
                    str(row.get("V", "0")),  # Vittorie individuali
                    str(row.get("GF", "0")),
                    str(row.get("GS", "0")),
                    str(row.get("DG", "0"))
                ])
            
            colWidths = [30, 100, 100, 40, 30, 30, 30, 30, 40, 40, 40, 40]
        else:
            # Classifica individuale
            headers = ["Pos", "Giocatore", "Club", "Punti", "G", "V", "P", "S", "GF", "GS", "DG"]
            data = [headers]
            
            for _, row in standings_df.iterrows():
                data.append([
                    str(row.get("Pos", "")),
                    row.get("Giocatore", ""),
                    row.get("Club", ""),
                    str(row.get("Punti", "")),
                    str(row.get("Giocate", row.get("G", "0"))),
                    str(row.get("V", row.get("Vinte", "0"))),  # Cerca V, altrimenti Vinte
                    str(row.get("Pareggiate", row.get("P", "0"))),  # Cerca Pareggiate, altrimenti P
                    str(row.get("Perse", row.get("S", "0"))),  # Cerca Perse, altrimenti S
                    str(row.get("GF", "0")),
                    str(row.get("GS", "0")),
                    str(row.get("DG", "0"))
                ])
            
            colWidths = [30, 120, 100, 40, 30, 30, 30, 30, 40, 40, 40]
        
        # Crea tabella
        table = Table(data, colWidths=colWidths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Colora il primo classificato
        if len(data) > 1:
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff3cd')),
            ]))
        
        story.append(table)
        
        # Aggiungi legenda criteri FISTF
        story.append(Spacer(1, 10*mm))
        
        if 'Squadra' in standings_df.columns:
            legend_text = "Criteri di classifica FISTF per squadre: Punti, Scontri diretti, Differenza vittorie H2H, Vittorie H2H, Differenza vittorie totale, Vittorie totali, Differenza reti H2H, Gol H2H, Differenza reti totale, Gol totali"
        else:
            legend_text = "Criteri di classifica FISTF: Punti, Scontri diretti, Differenza reti H2H, Gol H2H, Differenza reti totale, Gol totali"
        
        legend = Paragraph(legend_text, self.styles['CustomSmall'])
        story.append(legend)
        
        doc.build(story)
        return filepath
    
    def export_knockout(self, knockout_matches, category, tournament_name, filename=None):
        """
        Esporta il tabellone della fase finale in PDF.
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tabellone_{category}_{timestamp}.pdf"
        
        pdf_dir = Path("pdf")
        pdf_dir.mkdir(exist_ok=True)
        filepath = pdf_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=landscape(A4),  # Anche il tabellone in landscape
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        
        # Titolo
        title = Paragraph(f"Fase Finale - {tournament_name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 5*mm))
        
        subtitle = Paragraph(f"Categoria: {category}", self.styles['CustomHeading'])
        story.append(subtitle)
        story.append(Spacer(1, 10*mm))
        
        # Raggruppa per fase
        phases = ["BARRAGE", "R64", "R32", "R16", "QF", "SF", "F"]
        phase_names = {
            "BARRAGE": "Barrage", 
            "R64": "64° di Finale",
            "R32": "32° di Finale",
            "R16": "16° di Finale",
            "QF": "Quarti di Finale", 
            "SF": "Semifinali", 
            "F": "Finale"
        }
        
        for phase in phases:
            phase_matches = [m for m in knockout_matches if m.phase == phase]
            if not phase_matches:
                continue
            
            # Intestazione fase
            phase_header = Paragraph(phase_names.get(phase, phase), self.styles['CustomHeading'])
            story.append(phase_header)
            story.append(Spacer(1, 3*mm))
            
            # Prepara dati
            data = [["Partita", "Giocatore/Squadra 1", "Ris.", "Giocatore/Squadra 2", "Stato"]]
            
            # Ordina per numero partita
            sorted_matches = sorted(phase_matches, key=lambda m: m.id)
            
            for match in sorted_matches:
                # Determina se è partita individuale o a squadre
                if hasattr(match, 'individual_matches'):
                    player1 = match.team1 if hasattr(match, 'team1') else match.player1
                    player2 = match.team2 if hasattr(match, 'team2') else match.player2
                    is_played = match.is_match_played() if hasattr(match, 'is_match_played') else False
                    result = match.get_team_result() if is_played else "vs"
                else:
                    player1 = match.player1
                    player2 = match.player2
                    is_played = match.is_played
                    result = match.result if is_played else "vs"
                
                # Accorcia i token WIN per leggibilità
                display_player1 = player1
                display_player2 = player2
                if player1.startswith("WIN "):
                    display_player1 = "⚡ Vincitore " + player1[4:]
                if player2.startswith("WIN "):
                    display_player2 = "⚡ Vincitore " + player2[4:]
                
                # Estrai numero partita
                match_num = match.id.split('_')[-1] if '_' in match.id else match.id
                
                # Ottieni stato come stringa
                if hasattr(match.status, 'value'):
                    status_text = match.status.value
                else:
                    status_text = str(match.status)
                
                data.append([
                    match_num,
                    display_player1,
                    result,
                    display_player2,
                    status_text
                ])
            
            # Crea tabella
            table = Table(data, colWidths=[60, 200, 50, 200, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9C27B0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 5*mm))
        
        doc.build(story)
        return filepath
    
    def export_groups(self, groups_df, category, tournament_name, filename=None):
        """
        Esporta la composizione dei gironi in PDF.
        
        Args:
            groups_df: DataFrame con i giocatori e i loro gironi
            category: Categoria
            tournament_name: Nome del torneo
            filename: Nome file (opzionale)
        
        Returns:
            Path del file creato
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"gironi_{category}_{timestamp}.pdf"
        
        pdf_dir = Path("pdf")
        pdf_dir.mkdir(exist_ok=True)
        filepath = pdf_dir / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        
        # Titolo
        title = Paragraph(f"Composizione Gironi - {tournament_name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 5*mm))
        
        # Sottotitolo
        subtitle = Paragraph(f"Categoria: {category}", self.styles['CustomHeading'])
        story.append(subtitle)
        story.append(Spacer(1, 10*mm))
        
        # Informazioni riassuntive
        num_groups = len(groups_df['Girone'].unique())
        num_players = len(groups_df)
        summary = Paragraph(f"Totale: {num_players} giocatori in {num_groups} gironi", self.styles['CustomNormal'])
        story.append(summary)
        story.append(Spacer(1, 5*mm))
        
        # Raggruppa per girone
        for group_name in sorted(groups_df['Girone'].unique()):
            group_data = groups_df[groups_df['Girone'] == group_name]
            
            # Intestazione girone
            group_header = Paragraph(f"Girone {group_name} - {len(group_data)} giocatori", self.styles['CustomSubHeading'])
            story.append(group_header)
            story.append(Spacer(1, 3*mm))
            
            # Prepara dati tabella
            data = [["Pos", "Seed", "Giocatore", "Club", "Nazione", "Licenza"]]
            
            # Ordina per posizione (seed)
            sorted_group = group_data.sort_values(by=['Pos', 'Seed'])
            
            for _, row in sorted_group.iterrows():
                data.append([
                    str(row.get("Pos", "-")),
                    str(row.get("Seed", "-")) if row.get("Seed") else "-",
                    row.get("Giocatore", ""),
                    row.get("Club", ""),
                    row.get("Nazione", ""),
                    row.get("Licenza", "")
                ])
            
            # Crea tabella
            table = Table(data, colWidths=[30, 40, 120, 100, 50, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 5*mm))
        
        doc.build(story)
        return filepath


# Funzioni di utilità per chiamate rapide
def export_schedule(matches, tournament_name):
    """Funzione rapida per esportare calendario."""
    exporter = PDFExporter()
    return exporter.export_schedule(matches, tournament_name)

def export_standings(standings_df, category, group_name, tournament_name):
    """Funzione rapida per esportare classifica."""
    exporter = PDFExporter()
    return exporter.export_standings(standings_df, category, group_name, tournament_name)

def export_knockout(knockout_matches, category, tournament_name):
    """Funzione rapida per esportare tabellone."""
    exporter = PDFExporter()
    return exporter.export_knockout(knockout_matches, category, tournament_name)

def export_groups(groups_df, category, tournament_name):
    """Funzione rapida per esportare gironi."""
    exporter = PDFExporter()
    return exporter.export_groups(groups_df, category, tournament_name)