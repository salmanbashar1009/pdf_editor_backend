"""Stdlib logging setup. Never logs PDF contents, translation text, or secrets."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("pdf_editor").setLevel(getattr(logging, level.upper(), logging.INFO))