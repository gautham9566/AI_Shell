import os
import json
import requests
import shutil
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
from colorama import Fore, Style
from model_manager import model_manager, get_default_model_path

# Path for storing configuration
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".ai_shell")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default configuration structure
DEFAULT_CONFIG = {
    "api_keys": {
        "aws_bedrock": {
            "access_key_id": "",
            "secret_access_key": "",
            "model_id": "",
            "region": ""
        },
        "openai": {"api_key": "", "base_url": "", "model": ""},
        "anthropic": {"api_key": "", "model": ""},
        "openrouter": {"api_key": "", "model": ""},
        "google_gemini": {"api_key": "", "model": ""},
        "google_vertex": {
            "api_key": "", 
            "project_id": "",
            "location": "",
            "model": ""
        },
        "mistral": {"api_key": "", "model": ""},
        "deepseek": {"api_key": "", "model": ""},
        "together": {"api_key": "", "model": ""},
        "alibaba_qwen": {
            "access_key_id": "",
            "access_key_secret": "",
            "region": "",
            "endpoint": ""
        },
        "vscode_lm": {"api_key": ""},
        "requesty": {"api_key": ""},
        "x_ai": {"api_key": "", "model": ""},
        "sambanova": {"api_key": "", "endpoint": "", "model": ""},
        "asksage": {"api_key": ""},
        "litellm": {"api_key": "", "endpoint": ""},
        "ollama": {"host": "", "model": ""},
        "lmstudio": {"host": ""}
    },
    "local_model": {
        "path": "",
        "n_ctx": 0,
        "n_threads": 0
    },
    "default_provider": ""
}

class Config:
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create empty structure"""
        try:
            # Create config directory if not exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Load existing config or create default structure
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                # Make sure all structure keys exist
                merged_config = DEFAULT_CONFIG.copy()
                self._deep_update(merged_config, config)
                return merged_config
            else:
                self._save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    
    def _deep_update(self, target, source):
        """Recursively update nested dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_api_credentials(self, provider: str) -> Dict[str, str]:
        """Get API credentials for a specific provider"""
        return self.config.get("api_keys", {}).get(provider, {})
    
    def get_local_model_config(self) -> Dict[str, Any]:
        """Get local model configuration with fallbacks"""
        model_config = self.config.get("local_model", {})
        # Set fallback values if not configured
        return {
            "path": model_config.get("path") or "tinyllama.gguf",  # Fallback only if not configured
            "n_ctx": model_config.get("n_ctx") or 2048,
            "n_threads": model_config.get("n_threads") or 4
        }
    
    def get_default_provider(self) -> str:
        """Get default API provider with fallback"""
        return self.config.get("default_provider") or "aws_bedrock"  # Fallback only if not configured
    
    def set_default_provider(self, provider: str):
        """Set default API provider"""
        self.config["default_provider"] = provider
        self._save_config()
    
    def configure(self):
        """Interactive configuration wizard"""
        # Display current configuration first
        self._display_current_config()
        
        print(Fore.CYAN + "\n===== AI Shell Configuration =====")
        print(Fore.GREEN + "1. Configure API Keys")
        print(Fore.GREEN + "2. Configure Local Model")
        print(Fore.GREEN + "3. Cancel")
        print(Style.RESET_ALL)
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            self._configure_api_keys()
        elif choice == "2":
            self._configure_local_model()
        else:
            print("Configuration canceled.")
    
    def _display_current_config(self):
        """Display current configuration values"""
        print(Fore.CYAN + "\n===== Current Configuration =====")
        
        # Show default provider
        default_provider = self.get_default_provider()
        print(f"{Fore.YELLOW}Default Provider: {Fore.WHITE}{default_provider or 'Not set'}")
        
        # Show Local Model Configuration
        local_model = self.get_local_model_config()
        print(f"\n{Fore.YELLOW}Local LLM Configuration:")
        print(f"{Fore.WHITE}  Path: {local_model.get('path') or 'Not set'}")
        print(f"  Context Size: {local_model.get('n_ctx') or 'Not set'}")
        print(f"  Threads: {local_model.get('n_threads') or 'Not set'}")
        
        # Show API Configurations
        print(f"\n{Fore.YELLOW}API Configurations:")
        
        for provider, config in self.config.get("api_keys", {}).items():
            # Skip empty configurations
            if not any(config.values()):
                continue
                
            print(f"\n{Fore.GREEN}{provider}:")
            
            for key, value in config.items():
                # Mask sensitive information
                if value and (key == "api_key" or key == "secret_access_key" or key == "access_key_secret"):
                    masked_value = value[:4] + "****" if len(value) > 4 else "****"
                    print(f"  {key}: {masked_value}")
                elif value:  # Only show non-empty values
                    print(f"  {key}: {value}")
        
        print(Style.RESET_ALL)
    
    def _configure_api_keys(self):
        """Configure API keys for different providers"""
        api_providers = list(DEFAULT_CONFIG["api_keys"].keys())
        
        print(Fore.CYAN + "\n===== Select API Provider =====")
        for i, provider in enumerate(api_providers, 1):
            print(f"{Fore.GREEN}{i}. {provider}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{len(api_providers)+1}. Back{Style.RESET_ALL}")
        
        try:
            choice = int(input("\nEnter provider number: "))
            if choice < 1 or choice > len(api_providers) + 1:
                print("Invalid choice.")
                return
            
            if choice == len(api_providers) + 1:
                return
                
            provider = api_providers[choice-1]
            self._configure_specific_api(provider)
            
            # Ask if this should be the default provider
            set_default = input(f"Set {provider} as the default provider? (y/n): ").lower() == 'y'
            if set_default:
                self.set_default_provider(provider)
                print(f"{provider} set as default provider.")
                
        except (ValueError, IndexError):
            print("Invalid input.")
    
    def _configure_specific_api(self, provider: str):
        """Configure specific API provider credentials"""
        provider_config = self.config["api_keys"].get(provider, {})
        
        print(f"\n{Fore.CYAN}Configuring {provider} credentials:{Style.RESET_ALL}")
        
        if provider == "aws_bedrock":
            provider_config["access_key_id"] = input("Enter AWS Access Key ID: ") or provider_config.get("access_key_id", "")
            provider_config["secret_access_key"] = getpass.getpass("Enter AWS Secret Access Key: ") or provider_config.get("secret_access_key", "")
            provider_config["region"] = input("Enter AWS Region: ") or provider_config.get("region", "")
            provider_config["model_id"] = input("Enter Model ID (e.g. anthropic.claude-3-sonnet-20240229-v1:0): ") or provider_config.get("model_id", "")
            
        elif provider == "openai":
            provider_config["api_key"] = input("Enter OpenAI API Key: ") or provider_config.get("api_key", "")
            provider_config["base_url"] = input("Enter base URL: ") or provider_config.get("base_url", "")
            provider_config["model"] = input("Enter model name (e.g. gpt-4, gpt-3.5-turbo): ") or provider_config.get("model", "")
            
        elif provider == "anthropic":
            provider_config["api_key"] = input("Enter Anthropic API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name (e.g. claude-3-opus-20240229): ") or provider_config.get("model", "")
            
        elif provider == "openrouter":
            provider_config["api_key"] = input("Enter OpenRouter API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name (e.g. openai/gpt-4): ") or provider_config.get("model", "")
            
        elif provider == "google_gemini":
            provider_config["api_key"] = input("Enter Google Gemini API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name (e.g. gemini-pro): ") or provider_config.get("model", "")
            
        elif provider == "google_vertex":
            provider_config["api_key"] = input("Enter GCP API Key: ") or provider_config.get("api_key", "")
            provider_config["project_id"] = input("Enter GCP Project ID: ") or provider_config.get("project_id", "")
            provider_config["location"] = input("Enter GCP Region (e.g. us-central1): ") or provider_config.get("location", "")
            provider_config["model"] = input("Enter model name: ") or provider_config.get("model", "")
            
        elif provider == "mistral":
            provider_config["api_key"] = input("Enter Mistral API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name (e.g. mistral-medium): ") or provider_config.get("model", "")
            
        elif provider == "deepseek":
            provider_config["api_key"] = input("Enter DeepSeek API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name: ") or provider_config.get("model", "")
            
        elif provider == "together":
            provider_config["api_key"] = input("Enter Together API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name: ") or provider_config.get("model", "")
            
        elif provider == "alibaba_qwen":
            provider_config["access_key_id"] = input("Enter Alibaba Access Key ID: ") or provider_config.get("access_key_id", "")
            provider_config["access_key_secret"] = getpass.getpass("Enter Alibaba Access Key Secret: ") or provider_config.get("access_key_secret", "")
            provider_config["region"] = input("Enter Alibaba Region (e.g. cn-hangzhou): ") or provider_config.get("region", "")
            provider_config["endpoint"] = input("Enter Alibaba Endpoint URL: ") or provider_config.get("endpoint", "")
            
        elif provider == "vscode_lm":
            provider_config["api_key"] = input("Enter VS Code LM API Key: ") or provider_config.get("api_key", "")
            
        elif provider == "requesty":
            provider_config["api_key"] = input("Enter Requesty API Key: ") or provider_config.get("api_key", "")
            
        elif provider == "x_ai":
            provider_config["api_key"] = input("Enter X AI API Key: ") or provider_config.get("api_key", "")
            provider_config["model"] = input("Enter model name (e.g. grok-1): ") or provider_config.get("model", "")
            
        elif provider in ["sambanova"]:
            provider_config["api_key"] = input("Enter SambaNova API Key: ") or provider_config.get("api_key", "")
            provider_config["endpoint"] = input("Enter SambaNova Endpoint URL: ") or provider_config.get("endpoint", "")
            provider_config["model"] = input("Enter model name: ") or provider_config.get("model", "")
            
        elif provider == "asksage":
            provider_config["api_key"] = input("Enter AskSage API Key: ") or provider_config.get("api_key", "")
            
        elif provider == "litellm":
            provider_config["api_key"] = input("Enter LiteLLM API Key: ") or provider_config.get("api_key", "")
            provider_config["endpoint"] = input("Enter LiteLLM Endpoint URL: ") or provider_config.get("endpoint", "")
            
        elif provider == "ollama":
            provider_config["host"] = input("Enter Ollama host: ") or provider_config.get("host", "")
            provider_config["model"] = input("Enter model name (e.g. llama3, mistral): ") or provider_config.get("model", "")
            
        elif provider == "lmstudio":
            provider_config["host"] = input("Enter LM Studio host: ") or provider_config.get("host", "")
        
        # Update the configuration
        self.config["api_keys"][provider] = provider_config
        self._save_config()
        print(f"{provider} configuration updated successfully!")
    
    def _configure_local_model(self):
        """Configure local model settings"""
        print(Fore.CYAN + "\n===== Configure Local Model =====")
        print(Fore.GREEN + "1. Download a model")
        print(Fore.GREEN + "2. Use existing model file")
        print(Fore.GREEN + "3. Select from downloaded models")
        print(Fore.GREEN + "4. Delete a model")
        print(Fore.GREEN + "5. Back")
        print(Style.RESET_ALL)
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            self._download_model()
        elif choice == "2":
            self._set_model_path()
        elif choice == "3":
            self._select_model()
        elif choice == "4":
            self._delete_model()
        else:
            return
    
    def _download_model(self):
        """Download a model from URL using model manager"""
        url = input("Enter model download URL: ")
        if not url:
            print("Download canceled.")
            return
            
        filename = input("Enter filename to save as (leave empty for default name): ")
        
        # Use the model_manager to download
        success, file_path = model_manager.download_model(url, filename)
        
        if success:
            self.config["local_model"]["path"] = file_path
            
            # Update model parameters
            n_ctx = input("Enter context size (n_ctx, default 2048): ") or "2048"
            n_threads = input("Enter number of threads (default 4): ") or "4"
            
            self.config["local_model"]["n_ctx"] = int(n_ctx)
            self.config["local_model"]["n_threads"] = int(n_threads)
            self._save_config()
            
            print(f"Model downloaded successfully and set as active model!")
    
    def _set_model_path(self):
        """Set path to existing model file"""
        path = input("Enter full path to model file (leave empty for default location): ")
        if not path:
            path = get_default_model_path()
            print(f"Using default path: {path}")
                
        self.config["local_model"]["path"] = path
        
        # Also update model parameters
        n_ctx = input("Enter context size (n_ctx, default 2048): ") or "2048"
        n_threads = input("Enter number of threads (default 4): ") or "4"
        
        self.config["local_model"]["n_ctx"] = int(n_ctx)
        self.config["local_model"]["n_threads"] = int(n_threads)
            
        self._save_config()
        print(f"Model path updated to {path}")
        
    def _select_model(self):
        """Select a model from downloaded models"""
        models = model_manager.get_models_list()
        
        if not models:
            print("No models found in the models directory.")
            return
            
        print(Fore.CYAN + "\n===== Available Models =====")
        for i, model in enumerate(models, 1):
            print(f"{Fore.GREEN}{i}. {model['filename']} ({model['size_mb']} MB){Style.RESET_ALL}")
        
        try:
            choice = int(input("\nSelect a model (number): "))
            if choice < 1 or choice > len(models):
                print("Invalid choice.")
                return
                
            selected_model = models[choice-1]
            self.config["local_model"]["path"] = selected_model["path"]
            
            # Also update model parameters
            n_ctx = input(f"Enter context size (n_ctx, current: {self.config['local_model'].get('n_ctx', 2048)}): ")
            if n_ctx:
                self.config["local_model"]["n_ctx"] = int(n_ctx)
                
            n_threads = input(f"Enter number of threads (current: {self.config['local_model'].get('n_threads', 4)}): ")
            if n_threads:
                self.config["local_model"]["n_threads"] = int(n_threads)
                
            self._save_config()
            print(f"Selected model: {selected_model['filename']}")
            
        except (ValueError, IndexError):
            print("Invalid input.")
            
    def _delete_model(self):
        """Delete a model"""
        models = model_manager.get_models_list()
        
        if not models:
            print("No models found in the models directory.")
            return
            
        print(Fore.CYAN + "\n===== Available Models =====")
        for i, model in enumerate(models, 1):
            print(f"{Fore.GREEN}{i}. {model['filename']} ({model['size_mb']} MB){Style.RESET_ALL}")
        
        try:
            choice = int(input("\nSelect a model to delete (number): "))
            if choice < 1 or choice > len(models):
                print("Invalid choice.")
                return
                
            selected_model = models[choice-1]
            
            # Confirm deletion
            confirm = input(f"Are you sure you want to delete {selected_model['filename']}? (y/n): ").lower()
            if confirm != 'y':
                print("Deletion canceled.")
                return
                
            # If the model being deleted is the active one, remove it from config
            if self.config["local_model"]["path"] == selected_model["path"]:
                self.config["local_model"]["path"] = ""
                self._save_config()
                
            # Delete the model
            success = model_manager.delete_model(selected_model['filename'])
            if success:
                print(f"Model {selected_model['filename']} deleted successfully.")
            
        except (ValueError, IndexError):
            print("Invalid input.")

    def display_provider_config(self, provider_name):
        """Display configuration for a specific provider"""
        if provider_name == "local":
            # Display local model configuration
            model_config = self.get_local_model_config()
            print(f"\n{Fore.YELLOW}Local LLM Configuration:")
            print(f"{Fore.WHITE}  Path: {model_config.get('path') or 'Not set'}")
            print(f"  Context Size: {model_config.get('n_ctx') or 'Not set'}")
            print(f"  Threads: {model_config.get('n_threads') or 'Not set'}")
            print(Style.RESET_ALL)
        else:
            # Display API provider configuration
            provider_config = self.get_api_credentials(provider_name)
            print(f"\n{Fore.YELLOW}{provider_name.replace('_', ' ').title()} Configuration:")
            
            if not provider_config or not any(provider_config.values()):
                print(f"{Fore.WHITE}  Not configured")
                print(Style.RESET_ALL)
                return
                
            for key, value in provider_config.items():
                # Mask sensitive information
                if value and (key == "api_key" or key == "secret_access_key" or key == "access_key_secret"):
                    masked_value = value[:4] + "****" if len(value) > 4 else "****"
                    print(f"{Fore.WHITE}  {key}: {masked_value}")
                elif value:  # Only show non-empty values
                    print(f"{Fore.WHITE}  {key}: {value}")
            print(Style.RESET_ALL)

# Global instance
config_manager = Config()

if __name__ == "__main__":
    config_manager.configure()
