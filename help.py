# help.py
from colorama import Fore, Style

class Help:
    @staticmethod
    def show_guide():
        print(Fore.CYAN + "\nAI Shell Usage Guide:")
        print(Fore.GREEN + "1. Natural Language Input:")
        print("- Describe what you want to do in plain English")
        print("- Example: 'show files modified yesterday'")
        
        print(Fore.GREEN + "\n2. Command Options:")
        print("- y: Execute generated command")
        print("- n: Skip execution")
        print("- R: Regenerate command using Claude API")
        
        print(Fore.GREEN + "\n3. Special Commands:")
        print("- \\help: Show this guide")
        print("- \\config: Configure API keys and local model")
        print("- ssh-connect: Connect to remote host")
        print("- local/remote: Switch contexts")
        
        print(Fore.GREEN + "\n4. Command Syntax:")
        print("- Be specific about paths/filters")
        print("- Mention OS requirements if needed")
        print("- Use quotes for complex queries")
        
        print(Fore.GREEN + "\n5. Configuration (\\config):")
        print("- Set up API keys for services (AWS, OpenAI, Anthropic, etc.)")
        print("- Configure or download local model")
        print("- Select your preferred AI provider")
        print(Style.RESET_ALL)