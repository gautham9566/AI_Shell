import re
from typing import Tuple, Optional

class ResponseParser:
    """Helper class to parse and clean responses from LLMs"""
    
    @staticmethod
    def parse_response(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse response from API calls to extract command and explanation"""
        if not text or not isinstance(text, str):
            return None, None
            
        # Clean and split by lines
        text = text.strip()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            return None, None
            
        # First line should be the command
        command = ResponseParser.clean_command(lines[0])
        
        # Rest is explanation
        explanation = ' '.join(lines[1:]) if len(lines) > 1 else None
        
        return command, explanation
        
    @staticmethod
    def parse_claude_response(text: str, os_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Multi-stage response parsing with priority:
        1. Code blocks
        2. First valid command line
        3. Fallback patterns"""
        if not text or not isinstance(text, str):
            return None, None
            
        text = text.strip()

        # Stage 1: Check for code blocks
        code_block_match = re.search(r"```(?:bash|shell|cmd|powershell)?\s*\n?(.+?)\n```", text, re.DOTALL)
        if code_block_match:
            content = code_block_match.group(1).strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if lines and ResponseParser.is_valid_command(lines[0]):
                explanation = ' '.join(lines[1:]) if len(lines) > 1 else None
                return lines[0], explanation

        # Stage 2: Line-by-line parsing
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if ResponseParser.is_valid_command(line):
                explanation = ' '.join(lines[i+1:]) if i+1 < len(lines) else None
                return line, explanation

        # Stage 3: Fallback pattern matching
        command_match = re.search(r'(?:^|\n)([^\n`{}\]>]+?)(?:\n|$)', text)
        
        # Special patterns
        if os_type == 'windows':
            powershell_pattern = re.search(r'(powershell.*where.*size|Get-ChildItem.*where)', text, re.IGNORECASE)
            if powershell_pattern:
                return powershell_pattern.group().strip(), None
        else:
            size_pattern = re.search(r'(find\s+.*-size\s+[-+]\d+[MGK])', text)
            if size_pattern:
                return size_pattern.group().strip(), None
                
        if command_match and ResponseParser.is_valid_command(command_match.group(1)):
            return command_match.group(1).strip(), None
            
        return None, None
    
    @staticmethod
    def is_valid_command(command: str) -> bool:
        """Strict validation for safe, executable commands"""
        if not command or command.lower() == "none":
            return False
            
        # Clean the command before checking validity
        command = command.strip()
        
        # Remove common non-command markers
        if command.startswith('```') or command.endswith('```'):
            return False
            
        banned_patterns = [
            r'^[`{}\[\]\\]',  # Starts with code block or JSON characters
            r'[;&|]\s*$',  # Ends with command separator
            r'\b(rm\s+-rf|chmod\s+777|dd\s+if=)',  # Dangerous commands
        ]
        
        return (len(command) < 250 and 
                not any(re.search(pattern, command) for pattern in banned_patterns))

    @staticmethod
    def clean_command(command: str) -> Optional[str]:
        """Clean and validate the generated command"""
        if not command or command.lower() == "none":
            return None
            
        # Remove quotes and comments
        command = re.sub(r'["\']', '', command.split('#')[0].split('//')[0].strip())
        
        # Basic validation
        if len(command) > 200:
            return None
            
        # Remove common prefixes
        for prefix in ["command:", "cmd:", "$ ", "`"]:
            if command.lower().startswith(prefix):
                command = command[len(prefix):].strip()
                
        # Remove backticks which may appear at beginning or end
        command = command.strip('`')
                
        return command if command and ResponseParser.is_valid_command(command) else None
