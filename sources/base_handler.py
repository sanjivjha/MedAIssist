# sources/base_handler.py
from abc import ABC, abstractmethod

class BaseSourceHandler(ABC):
    @abstractmethod
    def fetch_data(self, query: str) -> list:
        pass