#!/usr/bin/env python3
"""
Ingesta de documentos Markdown en Qdrant (knowledge base RAG).

Uso:
    cd backend && uv run python ../scripts/ingest_knowledge.py [directorio]

Por defecto indexa todo `knowledge/` desde la raíz del proyecto.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.rag.indexer import index_directory  # noqa: E402
from app.rag.qdrant_client import qdrant_store  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    root = Path(__file__).resolve().parent.parent
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "knowledge"

    if not target.exists():
        logger.error(f"Directorio no existe: {target}")
        sys.exit(1)

    logger.info(f"Indexando: {target}")
    result = await index_directory(target)

    total = await qdrant_store.count()
    await qdrant_store.close()

    logger.info("---")
    logger.info(f"Archivos indexados: {result['files']}")
    logger.info(f"Chunks nuevos: {result['chunks']}")
    if result["errors"]:
        logger.warning(f"Errores: {len(result['errors'])}")
        for err in result["errors"]:
            logger.warning(f"  - {err}")
    logger.info(f"Total en colección '{qdrant_store.collection}': {total}")


if __name__ == "__main__":
    asyncio.run(main())
