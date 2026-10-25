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
[1, 3] Sticky note
Always do B last.

[3, 3] Report
Incident in cell 3.
Confidential.
"""


def test_documents_are_matched_to_their_cells():
    documents = parse_documents(DOCUMENTS, LEVEL)
    assert documents[(1, 3)].title == "Sticky note"
    assert documents[(3, 3)].text == "Incident in cell 3.\nConfidential."


def test_document_on_a_cell_without_d_raises():
    text = "[1, 4] Misplaced\nText.\n[3, 3] Report\nText."
    with pytest.raises(DocumentFormatError, match=r"\(1, 4\)"):
        parse_documents(text, LEVEL)


def test_d_without_document_raises():
    with pytest.raises(DocumentFormatError, match="No text"):
        parse_documents("[1, 3] Sticky note\nText.", LEVEL)


def test_two_documents_on_the_same_cell_raise():
    text = "[1, 3] A\nText.\n[1, 3] B\nText.\n[3, 3] C\nText."
    with pytest.raises(DocumentFormatError, match="Two documents"):
        parse_documents(text, LEVEL)


def test_empty_document_raises():
    with pytest.raises(DocumentFormatError, match="empty"):
        parse_documents("[1, 3] Sticky note\n\n[3, 3] Report\nText.", LEVEL)


def test_text_before_first_header_raises():
    with pytest.raises(DocumentFormatError, match="before the first"):
        parse_documents("Bonjour\n" + DOCUMENTS, LEVEL)


@pytest.mark.parametrize("language", ["fr", "en"])
def test_shipped_documents_match_shipped_level(language):
    level = load_level("levels/level1.txt")
    documents = load_documents(f"levels/level1_documents.{language}.txt", level)
    assert len(documents) == len(level.document_cells)
