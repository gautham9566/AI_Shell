from .aws_bedrock import AWSBedrockProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider
from .local_llm import LocalLLMProvider
from .base_provider import BaseProvider
from .response_parser import ResponseParser

# Dictionary of provider classes by name
PROVIDERS = {
    "aws_bedrock": AWSBedrockProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
    "openrouter": OpenRouterProvider,
    "local": LocalLLMProvider
}

# Create a provider instance by name
def create_provider(name: str):
    if name in PROVIDERS:
        return PROVIDERS[name]()
    return None
