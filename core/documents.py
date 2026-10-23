"""Documents à trouver dans le bâtiment : chargement et validation des textes.

Format du fichier : chaque document commence par une ligne d'en-tête
    [ligne, colonne] Titre
suivie de son texte. Les positions doivent correspondre aux cases 'D' de la carte.

Module indépendant du moteur de jeu.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from core.level import Cell, FacilityMap

HEADER = re.compile(r"^\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*(.*)$")


class DocumentFormatError(ValueError):
    """Le fichier des documents est mal formé ou ne correspond pas à la carte."""


@dataclass(frozen=True)
class Document:
    """Un texte à lire, posé sur une case de la carte."""

    cell: Cell
    title: str
    text: str


def load_documents(path: str | Path, level: FacilityMap) -> dict[Cell, Document]:
    """Lit le fichier des documents et vérifie qu'il correspond à la carte."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_documents(text, level)


def parse_documents(text: str, level: FacilityMap) -> dict[Cell, Document]:
    """Transforme le texte en documents rangés par case, ou lève DocumentFormatError."""
    documents: dict[Cell, Document] = {}
    for document in _split_into_documents(text):
        if document.cell in documents:
            raise DocumentFormatError(f"Deux documents à la case {document.cell}.")
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
                    f"Ligne {number} : texte avant le premier en-tête « [ligne, colonne] Titre »."
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
        raise DocumentFormatError(f"Ligne {number} : le document n'a pas de titre.")
    text = "\n".join(body).strip()
    if not text:
        raise DocumentFormatError(f"Ligne {number} : le document « {title} » est vide.")
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
            f"Le document « {documents[cell].title} » est à la case {cell}, "
            f"où la carte n'a pas de 'D'."
        )
    missing = sorted(expected - found)
    if missing:
        raise DocumentFormatError(f"Aucun texte pour les cases 'D' : {missing}.")
