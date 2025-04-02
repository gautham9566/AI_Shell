from typing import Tuple, Optional, Dict, Any
from termcolor import colored
import importlib.util

from .base_provider import BaseProvider
from .response_parser import ResponseParser

class OllamaProvider(BaseProvider):
    """Ollama API provider for local LLM integration"""
    
    def __init__(self):
        self.client = None
        self.model = None
        self.host = None
        
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def description(self) -> str:
        return f"Ollama ({self.model})" if self.model else "Ollama"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Ollama with configuration"""
        try:
            # Check if Ollama package is installed
            if importlib.util.find_spec("ollama") is None:
                print(colored("⚠️ Ollama package not installed. Run 'pip install ollama'", "yellow"))
                return False
                
            import ollama
            self.host = config.get("host")
            self.model = config.get("model")
            
            if not self.host:
                print(colored("⚠️ Ollama host not configured", "yellow"))
                return False
                
            # Set Ollama host
            ollama.set_host(self.host)
            
            # Test connection by listing models
            model_list = ollama.list()
            
            # Check if the specified model exists
            if self.model and not any(m['name'] == self.model for m in model_list.get('models', [])):
                print(colored(f"⚠️ Model '{self.model}' not found in Ollama. Available models: {[m['name'] for m in model_list.get('models', [])]}.", "yellow"))
                
                # Try to use first available model if specified model not found
                if model_list.get('models'):
                    self.model = model_list.get('models')[0]['name']
                    print(colored(f"Using available model: {self.model}", "yellow"))
                else:
                    print(colored("No models available in Ollama", "red"))
                    return False
            elif not self.model and model_list.get('models'):
                # Use first available model if not specified
                self.model = model_list.get('models')[0]['name']
            
            self.client = ollama
            print(colored(f"✓ Ollama initialized successfully with model {self.model}", "green"))
            return True
            
        except Exception as e:
            print(colored(f"⚠️ Ollama initialization failed: {str(e)}", "yellow"))
            return False
    
    def generate_command(self, user_input: str, os_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate command using Ollama"""
        if not self.client or not self.model:
            return None, None
            
        try:
            prompt = f"""Convert this to a {os_type} terminal command.
            Only output the command, nothing else.
            Request: {user_input}
            Command:"""
            
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"num_predict": 100}
            )
            
            if not response or not response.get("response"):
                return None, None
                
            raw_command = response["response"].strip()
            command = ResponseParser.clean_command(raw_command)
            
            return command, f"Generated by Ollama ({self.model})" if command else None
            
        except Exception as e:
            print(colored(f"⚠️ Ollama Error: {str(e)}", "red"))
            return None, None
