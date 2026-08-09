from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import RawJob


class AbstractJobAdapter(ABC):
    """Kontrak semua adapter sumber data (plan §6.2)."""

    source: str

    @abstractmethod
    def fetch(self) -> list[RawJob]:
        """Fetch raw listing dari satu sumber. Harus tidak melempar ke sumber lain."""
        raise NotImplementedError
