"""Documents to find in the building: loading and validating their texts.

File format: each document starts with a header line
    [row, column] Title
followed by its text. Positions must match the 'D' cells of the map.

Engine-independent module.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from core.level import Cell, FacilityMap

HEADER = re.compile(r"^\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*(.*)$")


class DocumentFormatError(ValueError):
    """The documents file is malformed or does not match the map."""


@dataclass(frozen=True)
class Document:
    """A text to read, lying on a cell of the map."""

    cell: Cell
    title: str
    text: str


def load_documents(path: str | Path, level: FacilityMap) -> dict[Cell, Document]:
    """Reads the documents file and checks that it matches the map."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_documents(text, level)


def parse_documents(text: str, level: FacilityMap) -> dict[Cell, Document]:
    """Turns the text into documents indexed by cell, or raises DocumentFormatError."""
    documents: dict[Cell, Document] = {}
    for document in _split_into_documents(text):
        if document.cell in documents:
            raise DocumentFormatError(f"Two documents on cell {document.cell}.")
        documents[document.cell] = document
    _check_matches_level(documents, level)
    return documents


def _split_into_documents(text: str) -> list[Document]:
    documents = []
    header = None
    body: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = HEADER.match(line.strip())
        if match:
            if header is not None:
                documents.append(_build_document(header, body))
            header = (number, match)
            body = []
        elif header is None:
            if line.strip():
                raise DocumentFormatError(
                    f"Line {number}: text before the first header '[row, column] Title'."
                )
        else:
            body.append(line)
    if header is not None:
        documents.append(_build_document(header, body))
    return documents


def _build_document(header, body: list[str]) -> Document:
    number, match = header
    title = match.group(3).strip()
    if not title:
        raise DocumentFormatError(f"Line {number}: the document has no title.")
    text = "\n".join(body).strip()
    if not text:
        raise DocumentFormatError(f"Line {number}: the document '{title}' is empty.")
    return Document(
        cell=(int(match.group(1)), int(match.group(2))), title=title, text=text
    )


def _check_matches_level(documents: dict[Cell, Document], level: FacilityMap) -> None:
    expected = set(level.document_cells)
    found = set(documents)
    misplaced = sorted(found - expected)
    if misplaced:
        cell = misplaced[0]
        raise DocumentFormatError(
            f"The document '{documents[cell].title}' is on cell {cell}, "
            f"where the map has no 'D'."
        )
    missing = sorted(expected - found)
    if missing:
        raise DocumentFormatError(f"No text for the 'D' cells: {missing}.")
