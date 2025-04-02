from typing import Tuple, Optional, Dict, Any
import abc

class BaseProvider(abc.ABC):
    """Base interface that all API providers must implement"""
    
    @abc.abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the provider with configuration"""
        pass
        
    @abc.abstractmethod
    def generate_command(self, user_input: str, os_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate a command from user input
        
        Returns:
            tuple: (command, explanation) or (None, None) on failure
        """
        pass
        
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the provider"""
        pass
        
    @property
    def description(self) -> str:
        """Return human-readable description of provider"""
        return self.name.replace('_', ' ').title()
