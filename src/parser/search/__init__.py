from __future__ import annotations

from abc import ABC, abstractmethod

from parser.models import Mention


class SearchProvider(ABC):
    name: str

    @abstractmethod
    def search(
        self,
        query: str,
        year: int,
        month: int,
    ) -> list[Mention]:
        """Ищет упоминания за указанный месяц."""
