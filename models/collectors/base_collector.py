# collectors/base_collector.py
from abc import ABC, abstractmethod
from typing import List, Optional
from models.evidence import Evidence

class BaseCollector(ABC):
    """Abstract base class for all OSINT collectors"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def validate_input(self, target: str) -> bool:
        """Check if the target is valid for this collector"""
        pass

    @abstractmethod
    async def execute(self, target: str, investigation_id: str) -> List[Evidence]:
        """
        Perform the reconnaissance.
        Returns a list of Evidence objects.
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Return what this collector can handle (e.g., 'domain', 'ip')"""
        pass