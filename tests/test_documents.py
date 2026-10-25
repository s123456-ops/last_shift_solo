import pytest

from core.documents import DocumentFormatError, load_documents, parse_documents
from core.level import load_level, parse_level

LEVEL = parse_level("""
#######
#PFD.E#
#G.N.M#
#..D..#
#######
""")

DOCUMENTS = """
[1, 3] Post-it
Le B toujours en dernier.

[3, 3] Rapport
Incident cellule 3.
Confidentiel.
"""


def test_documents_are_matched_to_their_cells():
    documents = parse_documents(DOCUMENTS, LEVEL)
    assert documents[(1, 3)].title == "Post-it"
    assert documents[(3, 3)].text == "Incident cellule 3.\nConfidentiel."


def test_document_on_a_cell_without_d_raises():
    text = "[1, 4] Égaré\nTexte.\n[3, 3] Rapport\nTexte."
    with pytest.raises(DocumentFormatError, match=r"\(1, 4\)"):
        parse_documents(text, LEVEL)


def test_d_without_document_raises():
    with pytest.raises(DocumentFormatError, match="Aucun texte"):
        parse_documents("[1, 3] Post-it\nTexte.", LEVEL)


def test_two_documents_on_the_same_cell_raise():
    text = "[1, 3] A\nTexte.\n[1, 3] B\nTexte.\n[3, 3] C\nTexte."
    with pytest.raises(DocumentFormatError, match="Deux documents"):
        parse_documents(text, LEVEL)


def test_empty_document_raises():
    with pytest.raises(DocumentFormatError, match="vide"):
        parse_documents("[1, 3] Post-it\n\n[3, 3] Rapport\nTexte.", LEVEL)


def test_text_before_first_header_raises():
    with pytest.raises(DocumentFormatError, match="avant le premier"):
        parse_documents("Bonjour\n" + DOCUMENTS, LEVEL)


@pytest.mark.parametrize("language", ["fr", "en"])
def test_shipped_documents_match_shipped_level(language):
    level = load_level("levels/level1.txt")
    documents = load_documents(f"levels/level1_documents.{language}.txt", level)
    assert len(documents) == len(level.document_cells)
