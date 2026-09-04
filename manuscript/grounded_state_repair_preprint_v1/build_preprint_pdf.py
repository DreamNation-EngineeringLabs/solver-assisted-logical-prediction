"""Render the solver-assisted prediction audit as a publication-style PDF."""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
SOURCE = HERE / "manuscript.md"
OUTPUT = PROJECT / "output/pdf/solver_assisted_logical_prediction_audit_preprint.pdf"
TMP = PROJECT / "tmp/pdfs/grounded_state_repair_preprint_v1"

NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#0F767A")
INK = colors.HexColor("#18232D")
MUTED = colors.HexColor("#526170")
PALE = colors.HexColor("#EEF6F6")
PALE_BLUE = colors.HexColor("#EDF2F7")
RULE = colors.HexColor("#B6C4CE")


def _font_paths() -> tuple[Path, Path, Path, Path] | None:
    candidates = (
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
            Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"),
        ),
        (
            Path("/Library/Fonts/Arial.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/Library/Fonts/Times New Roman.ttf"),
            Path("/Library/Fonts/Times New Roman Bold.ttf"),
        ),
    )
    return next((candidate for candidate in candidates if all(path.is_file() for path in candidate)), None)


FONT_PATHS = _font_paths()
if FONT_PATHS:
    pdfmetrics.registerFont(TTFont("PaperSans", str(FONT_PATHS[0])))
    pdfmetrics.registerFont(TTFont("PaperSansBold", str(FONT_PATHS[1])))
    pdfmetrics.registerFont(TTFont("PaperSerif", str(FONT_PATHS[2])))
    pdfmetrics.registerFont(TTFont("PaperSerifBold", str(FONT_PATHS[3])))
    SANS, SANS_BOLD, SERIF, SERIF_BOLD = "PaperSans", "PaperSansBold", "PaperSerif", "PaperSerifBold"
else:
    SANS, SANS_BOLD, SERIF, SERIF_BOLD = "Helvetica", "Helvetica-Bold", "Times-Roman", "Times-Bold"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName=SANS_BOLD, fontSize=22, leading=26, textColor=NAVY, alignment=TA_LEFT, spaceAfter=10),
        "author": ParagraphStyle("Author", parent=base["Normal"], fontName=SANS_BOLD, fontSize=10.4, leading=13, textColor=INK, spaceAfter=2),
        "date": ParagraphStyle("Date", parent=base["Normal"], fontName=SANS, fontSize=8.8, leading=11, textColor=MUTED, spaceAfter=13),
        "abstract_label": ParagraphStyle("AbstractLabel", parent=base["Heading2"], fontName=SANS_BOLD, fontSize=10.6, leading=13, textColor=TEAL, spaceAfter=5),
        "abstract": ParagraphStyle("Abstract", parent=base["BodyText"], fontName=SERIF, fontSize=9.3, leading=12.4, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=0),
        "keywords": ParagraphStyle("Keywords", parent=base["BodyText"], fontName=SANS, fontSize=8.2, leading=10.5, textColor=MUTED, spaceBefore=5, spaceAfter=10),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName=SANS_BOLD, fontSize=14.1, leading=17.2, textColor=NAVY, spaceBefore=15, spaceAfter=6, keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName=SANS_BOLD, fontSize=10.8, leading=13.2, textColor=TEAL, spaceBefore=9, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName=SERIF, fontSize=9.25, leading=12.6, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName=SERIF, fontSize=9.15, leading=12.3, textColor=INK, leftIndent=10, spaceAfter=1.5),
        "table": ParagraphStyle("Table", parent=base["BodyText"], fontName=SERIF, fontSize=7.25, leading=9.2, textColor=INK, alignment=TA_LEFT),
        "table_head": ParagraphStyle("TableHead", parent=base["BodyText"], fontName=SANS_BOLD, fontSize=7.1, leading=8.8, textColor=colors.white, alignment=TA_LEFT),
        "reference": ParagraphStyle("Reference", parent=base["BodyText"], fontName=SERIF, fontSize=7.8, leading=10.3, textColor=INK, leftIndent=12, firstLineIndent=-12, spaceAfter=4),
        "flow": ParagraphStyle("Flow", parent=base["BodyText"], fontName=SANS, fontSize=8.15, leading=10.2, textColor=INK, alignment=TA_CENTER),
        "flow_caption": ParagraphStyle("FlowCaption", parent=base["BodyText"], fontName=SANS, fontSize=7.55, leading=9.3, textColor=MUTED, alignment=TA_CENTER, spaceAfter=7),
    }


STYLES = _styles()


def _clean(text: str) -> str:
    substitutions = {
        "×": "x",
        "–": "-",
        "—": "-",
        "−": "-",
        "≤": "<=",
        "≥": ">=",
        "Ø": "O",
        "ø": "o",
        "’": "'",
        "“": '"',
        "”": '"',
    }
    for source, replacement in substitutions.items():
        text = text.replace(source, replacement)
    return text


def _inline(text: str) -> str:
    value = html.escape(_clean(text), quote=False)
    value = re.sub(r"`([^`]+)`", rf'<font name="Courier" size="7.5">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    return value


def _table_widths(count: int, width: float) -> list[float]:
    patterns = {
        2: (0.39, 0.61),
        3: (0.32, 0.23, 0.45),
        4: (0.28, 0.20, 0.17, 0.35),
        5: (0.17, 0.19, 0.09, 0.08, 0.47),
        6: (0.30, 0.11, 0.11, 0.14, 0.15, 0.19),
    }
    return [width * ratio for ratio in patterns.get(count, tuple(1 / count for _ in range(count)))]


def _parse_table(lines: list[str], start: int, width: float) -> tuple[Table, int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            rows.append(cells)
        index += 1
    if not rows or len({len(row) for row in rows}) != 1:
        raise ValueError("Malformed Markdown table")
    rendered: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = STYLES["table_head"] if row_index == 0 else STYLES["table"]
        rendered.append([Paragraph(_inline(cell), style) for cell in row])
    table = Table(rendered, colWidths=_table_widths(len(rows[0]), width), repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), (colors.white, PALE_BLUE)),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table, index


def _paragraph(lines: Iterable[str]) -> str:
    return " ".join(line.strip() for line in lines).strip()


def _study_flow(width: float) -> list[object]:
    steps = (
        ("Sealed v7 pilot", "192 binary ProofWriter items: relevant certificate improves system accuracy."),
        ("Mechanism boundary", "Full certificate is answer-diagnostic; system result does not identify state use."),
        ("Three-class diagnostics", "Qwen2.5-3B: mapping / unknown failure. Qwen3-1.7B: all-A label anchoring."),
        ("Sealed binary five-arm factorial", "None | irrelevant | conclusion only | proof prefix | full; Qwen2.5-3B qualifies."),
        ("Correct endpoint", "Prefix beats irrelevant proof but not conclusion-only; internal state repair remains unresolved."),
    )
    rows: list[list[object]] = []
    for index, (heading, detail) in enumerate(steps):
        box = Table([[Paragraph(f"<b>{_inline(heading)}</b><br/>{_inline(detail)}", STYLES["flow"])]], colWidths=[width * 0.79], hAlign="CENTER")
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE if index in (0, 2) else PALE_BLUE),
            ("BOX", (0, 0), (-1, -1), 0.7, TEAL if index in (0, 4) else RULE),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        rows.append([box])
        if index < len(steps) - 1:
            rows.append([Paragraph("↓", ParagraphStyle("FlowArrow", parent=STYLES["flow"], fontName=SANS_BOLD, fontSize=12, leading=10, textColor=TEAL))])
    outer = Table(rows, colWidths=[width], hAlign="CENTER")
    outer.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [Spacer(1, 2), outer, Spacer(1, 3), Paragraph("Figure 1. Study flow and claim boundary. The completed binary factorial is distinct from terminal three-class qualification gates.", STYLES["flow_caption"])]


def _document_story(markdown: str, width: float) -> list[object]:
    lines = markdown.splitlines()
    story: list[object] = []
    index = 0
    section = ""
    abstract_open = False
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(_inline(stripped[2:]), STYLES["title"]))
            story.append(HRFlowable(width="100%", thickness=1.4, color=TEAL, spaceBefore=1, spaceAfter=9))
            index += 1
            continue
        if stripped.startswith("**Anonymous"):
            story.append(Paragraph(_inline(stripped), STYLES["author"]))
            index += 1
            continue
        if stripped.startswith("*Preprint"):
            story.append(Paragraph(_inline(stripped), STYLES["date"]))
            index += 1
            continue
        if stripped.startswith("## "):
            section = stripped[3:]
            abstract_open = section == "Abstract"
            story.append(Paragraph(_inline(section), STYLES["abstract_label"] if abstract_open else STYLES["h1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(_inline(stripped[4:]), STYLES["h2"]))
            index += 1
            continue
        if stripped == ":::study-flow":
            story.extend(_study_flow(width))
            index += 1
            continue
        if stripped.startswith("| "):
            table, index = _parse_table(lines, index, width)
            story.append(Spacer(1, 2))
            story.append(table)
            story.append(Spacer(1, 8))
            continue
        if stripped.startswith("- "):
            bullets: list[ListItem] = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                bullets.append(ListItem(Paragraph(_inline(lines[index].strip()[2:]), STYLES["bullet"]), leftIndent=7))
                index += 1
            story.append(ListFlowable(bullets, bulletType="bullet", leftIndent=14, bulletFontName=SANS, bulletFontSize=6.5, spaceAfter=5))
            continue
        if stripped == "---":
            story.append(HRFlowable(width="100%", thickness=0.55, color=RULE, spaceBefore=4, spaceAfter=7))
            index += 1
            continue
        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("# ", "## ", "### ", "| ", "- ")) or candidate == "---":
                break
            paragraph_lines.append(lines[index])
            index += 1
        text = _paragraph(paragraph_lines)
        if text.startswith("**Keywords:**"):
            story.append(Paragraph(_inline(text), STYLES["keywords"]))
            abstract_open = False
            continue
        style = STYLES["abstract"] if abstract_open else STYLES["reference"] if section == "References" else STYLES["body"]
        paragraph = Paragraph(_inline(text), style)
        if abstract_open:
            box = Table([[paragraph]], colWidths=[width], hAlign="LEFT")
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), PALE),
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(KeepTogether([box, Spacer(1, 2)]))
        else:
            story.append(paragraph)
    return story


def _footer(canvas, doc) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    page = canvas.getPageNumber()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.45)
    canvas.line(doc.leftMargin, 12.5 * mm, A4[0] - doc.rightMargin, 12.5 * mm)
    canvas.setFont(SANS, 7.2)
    canvas.setFillColor(MUTED)
    if page > 1:
        canvas.drawString(doc.leftMargin, 8.5 * mm, "Auditing Solver-Assisted Logical Prediction")
    canvas.drawRightString(A4[0] - doc.rightMargin, 8.5 * mm, f"Preprint draft | {page}")
    canvas.restoreState()


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18.5 * mm,
        rightMargin=18.5 * mm,
        topMargin=18 * mm,
        bottomMargin=19 * mm,
        title="Auditing Solver-Assisted Logical Prediction with a Sealed Five-Arm Certificate Factorial",
        author="Anonymous author(s)",
    )
    story = _document_story(SOURCE.read_text(encoding="utf-8"), document.width)
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
