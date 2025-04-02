import platform
from typing import Dict, List, Optional, Tuple
from termcolor import colored
import os
import random
from time import sleep

# Try to import the config_manager
try:
    from config import config_manager
except ImportError:
    config_manager = None

# Import APIs
from apis import create_provider, PROVIDERS

class AIService:
    def __init__(self, os_type=None):
        """Initialize AI service with both local and cloud backends"""
        self.os_type = os_type or platform.system().lower()
        
        # Provider management
        self.providers = {}  # Initialized providers
        self.initialized_providers = []  # List of successfully initialized provider names
        
        # Set default provider from config
        self.provider = None
        if config_manager:
            self.provider = config_manager.get_default_provider()
        else:
            self.provider = "aws_bedrock"  # Fallback only if no config
            
        # Initialize providers
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all available providers"""
        if not config_manager:
            print(colored("⚠️ No configuration found. Run '\\config' to set up your models", "yellow"))
            return
            
        # Initialize local LLM first, as it should be the default if available
        self._init_provider("local", config_manager.get_local_model_config())
            
        # Initialize API providers
        for provider_name in PROVIDERS:
            if provider_name != "local":  # Already initialized local LLM
                self._init_provider(provider_name, config_manager.get_api_credentials(provider_name))
        
        # If local LLM is available, make it the default regardless of config setting
        if "local" in self.initialized_providers:
            self.provider = "local"
            print(colored("✓ Using local LLM as default provider", "green"))
                
    def _init_provider(self, provider_name: str, config: dict):
        """Initialize a specific provider with its config"""
        provider = create_provider(provider_name)
        if provider and provider.initialize(config):
            self.providers[provider_name] = provider
            self.initialized_providers.append(provider_name)
            
    def generate_command(self, user_input: str, regenerate: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """Generate command using configured providers with smart fallback logic
        
        Args:
            user_input: The user's natural language request
            regenerate: Whether this is a regeneration request (R option)
        """
        # Empty input validation
        if not user_input or not user_input.strip():
            return None, None
            
        # If regenerating, prioritize API providers over local LLM
        if regenerate:
            # Try APIs first (skip local even if it's the default)
            api_providers = [p for p in self.initialized_providers if p != "local"]
            
            # First try the configured default provider if it's an API
            if self.provider in api_providers:
                print(colored(f"↳ Regenerating with {self.providers[self.provider].description}...", "cyan"))
                command, explanation = self.providers[self.provider].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
            
            # Then try other API providers
            for provider_name in api_providers:
                if provider_name == self.provider:  # Skip if we already tried it
                    continue
                    
                print(colored(f"↳ Trying {self.providers[provider_name].description}...", "cyan"))
                command, explanation = self.providers[provider_name].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
                    
            # Fall back to local LLM only if all APIs failed
            if "local" in self.initialized_providers:
                print(colored("↳ All APIs failed, falling back to local LLM", "yellow"))
                command, explanation = self.providers["local"].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
        else:
            # Normal flow (not regenerating)
            # First attempt: Use local LLM if available
            if "local" in self.initialized_providers:
                command, explanation = self.providers["local"].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
        
            # Second attempt: Use default provider
            if self.provider in self.initialized_providers:
                command, explanation = self.providers[self.provider].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
            
            # Third attempt: Try other providers if default failed
            for provider_name in self.initialized_providers:
                # Skip providers we've already tried
                if provider_name == "local" or provider_name == self.provider:
                    continue
                    
                command, explanation = self.providers[provider_name].generate_command(user_input, self.os_type)
                if command:
                    return command, explanation
        
        # No provider available or all providers failed
        available_providers = ", ".join(self.initialized_providers) or "None"
        print(colored(f"⚠️ Command generation failed. Available providers: {available_providers}", "red"))
        return None, None

if __name__ == "__main__":
    print(colored("\n🔧 AI Command Generator Test", "green", attrs=["bold"]))
    print(colored("="*50, "blue"))
    
    ai = AIService()
    
    # Show initialized providers
    print(colored("\nInitialized providers:", "cyan"))
    for provider_name in ai.initialized_providers:
        provider = ai.providers[provider_name]
        print(f"- {provider.description}")
        
    # Test some commands
    tests = [
        "clear screen",
        "list files",
        "show docker containers",
        "search for python files",
        "find large files >100MB",
        "show memory usage",
        "kill process on port 3000"
    ] + (["dir"] if platform.system() == 'Windows' else ["ls"])
    
    for query in tests:
        print(colored(f"\nInput: {query}", "yellow", attrs=["bold"]))
        
        # Generate command
        cmd, explanation = ai.generate_command(query)
        
        if cmd:
            print(colored(f"Command: {cmd}", "green"))
            print(colored(f"Source: {explanation}", "cyan"))
        else:
            print(colored("❌ Failed to generate command", "red"))
            
            # Try default AWS Bedrock if available and not already tried
            if "aws_bedrock" in ai.initialized_providers and ai.provider != "aws_bedrock":
                cmd, explanation = ai.generate_command(query, use_provider="aws_bedrock")
                if cmd:
                    print(colored(f"AWS Bedrock fallback: {cmd}", "green"))
                else:
                    print(colored("❌ AWS Bedrock also failed", "red"))
        
        sleep(random.uniform(0.5, 1.0))  # Rate limiting