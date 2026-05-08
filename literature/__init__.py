"""Literature retrieval helpers (Crossref integration)."""

from literature.crossref import (
    CrossrefClient,
    CrossrefError,
    normalize_doi_input,
    work_to_reference_dict,
)

__all__ = [
    "CrossrefClient",
    "CrossrefError",
    "normalize_doi_input",
    "work_to_reference_dict",
]
