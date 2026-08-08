from app.services.chunking import chunk_text, clean


def test_clean_collapses_whitespace():
    assert clean("a\t\t b\n\n\nc") == "a b\nc"


def test_short_text_returns_no_chunks():
    assert chunk_text("hola") == []


def test_chunking_produces_multiple_bounded_pieces():
    text = "palabra " * 400  # ~3200 caracteres
    chunks = chunk_text(text, chunk_chars=1000, overlap=150)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)


def test_overlap_advances_less_than_chunk_size():
    # Con solape, el paso es (chunk_chars - overlap); dos textos de ~1200 chars
    # deben generar 2 fragmentos.
    text = "x" * 1200
    chunks = chunk_text("hola " + text, chunk_chars=1000, overlap=150)
    assert len(chunks) == 2
