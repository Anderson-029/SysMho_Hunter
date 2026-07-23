"""
Indexer — Chunking e indexación de documentos Markdown en Qdrant.

Formato esperado de cada documento fuente (Markdown con frontmatter YAML):

    ---
    source: portswigger
    category: idor
    cwe: CWE-639
    severity: high
    url: https://portswigger.net/web-security/access-control/idor
    ---
    # Insecure Direct Object References (IDOR)

    ## Descripción
    ...

    ## Cómo detectar
    ...

Cada sección "## Titulo" se indexa como un chunk independiente,
para que la búsqueda semántica devuelva fragmentos precisos.
"""

import logging
import re
from pathlib import Path

from app.rag.embeddings import embedding_client
from app.rag.qdrant_client import qdrant_store

logger = logging.getLogger(__name__)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


class IndexerError(Exception):
    pass


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Extrae metadata YAML simple (key: value) y el cuerpo Markdown."""
    match = FRONTMATTER_RE.match(raw)
    if not match:
        raise IndexerError("Documento sin frontmatter válido (---...---)")

    meta_block, body = match.groups()
    metadata = {}
    for line in meta_block.strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip()
    return metadata, body


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Divide el cuerpo Markdown en chunks por encabezado ## (nivel 2)."""
    sections = re.split(r"^## ", body, flags=re.MULTILINE)
    chunks = []
    # sections[0] es el título principal (# Titulo) antes del primer ##
    intro = sections[0].strip()
    if intro:
        chunks.append(("intro", intro))

    for section in sections[1:]:
        lines = section.splitlines()
        title = lines[0].strip() if lines else "sin_titulo"
        text = "\n".join(lines[1:]).strip()
        if text:
            chunks.append((title, text))

    return chunks


async def index_document(file_path: Path) -> int:
    """Indexa un archivo Markdown completo. Retorna cantidad de chunks."""
    raw = file_path.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(raw)

    source = metadata.get("source", "unknown")
    category = metadata.get("category", "unknown")
    extra_meta = {
        k: v for k, v in metadata.items() if k not in ("source", "category")
    }
    extra_meta["file"] = str(file_path)

    chunks = _split_sections(body)
    if not chunks:
        logger.warning(f"[Indexer] Sin chunks en {file_path}")
        return 0

    count = 0
    for title, text in chunks:
        chunk_meta = {**extra_meta, "section": title}
        vector = await embedding_client.embed(text)
        await qdrant_store.upsert_document(
            vector=vector,
            text=text,
            source=source,
            category=category,
            metadata=chunk_meta,
        )
        count += 1

    logger.info(
        f"[Indexer] {file_path.name}: {count} chunks indexados "
        f"(source={source}, category={category})"
    )
    return count


async def index_directory(directory: Path) -> dict:
    """Indexa recursivamente todos los .md de un directorio.

    Returns:
        Resumen: {"files": N, "chunks": N, "errors": [paths con fallo]}
    """
    await qdrant_store.ensure_collection()

    md_files = sorted(directory.rglob("*.md"))
    total_chunks = 0
    errors = []

    for file_path in md_files:
        try:
            total_chunks += await index_document(file_path)
        except IndexerError as e:
            logger.error(f"[Indexer] {file_path}: {e}")
            errors.append(str(file_path))

    return {
        "files": len(md_files) - len(errors),
        "chunks": total_chunks,
        "errors": errors,
    }
