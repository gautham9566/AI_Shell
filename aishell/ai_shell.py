import os
from pathlib import Path
import subprocess
import platform
import sys
import shlex
from difflib import get_close_matches
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.formatted_text import FormattedText
from colorama import init, Fore, Style
import shutil
import paramiko
# Initialize colorama for better cross-platform color support
init()

from ai_service import AIService
from cache import CommandCache
from help import Help

import paramiko
from typing import Optional

class RemoteSession:
    def __init__(self):
        self.ssh: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.cwd = "~"
        self.os_type = ""
        self.hostname = ""

class AIShell:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.ai = AIService()
        self.cache = CommandCache()
        self.help = Help()
        self.os_type = platform.system().lower()
        self.session = self._setup_prompt_session()
        self.WINDOWS_BUILTINS = self._get_windows_builtins()
        self.remote = RemoteSession()
        self.current_context = "local"  # or "remote"

    def _setup_prompt_session(self):
        """Configure interactive prompt with history and autocomplete"""
        style = PTStyle.from_dict({
            'prompt': '#ansigreen bold',
            'path': '#ansicyan',
            'text': '#ansiblue',
        })
        
        return PromptSession(
            history=FileHistory("history.txt"),
            completer=self._create_completer(),
            style=style
        )
    def _get_prompt(self):
        """Generate the prompt with current path"""
        if self.current_context == "remote" and self.remote.ssh:
            # Shorten home directory to ~ for cleaner display
            home = "/home/" + self.remote.ssh.get_transport().get_username() if self.remote.os_type != 'windows' else "C:\\Users\\" + self.remote.ssh.get_transport().get_username()
            cwd = self.remote.cwd
            if cwd.startswith(home):
                cwd = '~' + cwd[len(home):]

            host = f"[ssh://{self.remote.hostname}]"
            prompt_text = [
                ('class:path', f"{host} [{cwd}]"),
                ('class:prompt', "\nAI-Shell> "),
            ]
            return FormattedText(prompt_text)
        else:
            cwd = os.getcwd()
            if self.os_type == 'windows':
                cwd = cwd.replace('\\', '/')  # Use forward slashes for consistency
            # Shorten home directory to ~ for cleaner display
            home = str(Path.home())
            if cwd.startswith(home):
                cwd = '~' + cwd[len(home):]
        
            prompt_text = [
                ('class:path', f"[{cwd}]"),
                ('class:prompt', "\nAI-Shell> "),
            ]
        return FormattedText(prompt_text)
    
    
    def _create_completer(self):
        """Create hybrid completer with proper inheritance"""
        class HybridCompleter(Completer):
            def __init__(self, parent):
                self.parent = parent
                self.basic_commands = [
                    'clear screen', 'list files',
                    'show docker', 'search files',
                    'memory usage', 'kill process'
                ]
            
            def get_remote_completions(self, text):
                if not self.parent.remote.ssh:
                    return
                try:
                    cmd = f"compgen -c" if self.parent.remote.os_type != 'windows' else "help"
                    stdin, stdout, stderr = self.parent.remote.ssh.exec_command(cmd)
                    return stdout.read().decode().splitlines()
                except:
                    return []
            
            def get_completions(self, document, complete_event):
                text = document.text_before_cursor.lower()
                # Use document.get_word_before_cursor() instead of the deprecated method
                current_word = document.get_word_before_cursor(WORD=True)
                # Handle remote completions
                if self.parent.current_context == "remote" and self.parent.remote.ssh:
                    if current_word:  # File/directory completion
                        try:
                            stdin, stdout, stderr = self.parent.remote.ssh.exec_command(
                                f"cd {self.parent.remote.cwd} && compgen -f -- '{current_word}'"
                            )
                            matches = stdout.read().decode().splitlines()
                            for match in matches:
                                is_dir = match.endswith('/')
                                yield Completion(
                                    match,
                                    start_position=-len(current_word),
                                    display_meta='Directory' if is_dir else 'File'
                                )
                        except:
                            pass
                    else:  # Command completion
                        stdin, stdout, stderr = self.parent.remote.ssh.exec_command("compgen -c")
                        commands = stdout.read().decode().splitlines()
                        for cmd in commands:
                            if text in cmd.lower():
                                yield Completion(cmd, start_position=-len(text))
                    return
                # System commands
                sys_commands = self.parent._get_system_commands()
                for cmd in sys_commands:
                    if text in cmd.lower():
                        yield Completion(cmd, start_position=-len(text))

                # Cached commands
                cached = [row[0] for row in self.parent.cache.conn.execute("SELECT query FROM commands")]
                for cmd in cached:
                    if cmd.lower().startswith(text):
                        yield Completion(cmd, start_position=-len(text))

                # Basic AI commands
                for cmd in self.basic_commands:
                    if cmd.lower().startswith(text):
                        yield Completion(cmd, start_position=-len(text))

                # New: File and directory completions
                if current_word:
                    try:
                        # Handle path completion
                        path = Path(current_word)
                        dir_path = path.parent if path.parent != Path('.') else Path()
                        base = path.name

                        # Get matching files/directories
                        matches = []
                        for f in dir_path.iterdir():
                            if self.parent.os_type == 'windows':
                                if f.name.lower().startswith(base.lower()):
                                    matches.append(f)
                            else:
                                if f.name.startswith(base):
                                    matches.append(f)

                        # Generate completions
                        for match in sorted(matches, key=lambda x: x.is_file()):
                            display = match.name
                            if match.is_dir():
                                display += '/'
                            yield Completion(
                                str(match.relative_to(dir_path)),
                                start_position=-len(base),
                                display_meta='Directory' if match.is_dir() else 'File'
                            )
                    except Exception as e:
                        pass
                      
                if self.parent.current_context == "remote":
                    remote_commands = self.get_remote_completions(text)
                    for cmd in remote_commands:
                        if text in cmd.lower():
                            yield Completion(cmd, start_position=-len(text))
                        
                    
        return HybridCompleter(self)
    def _get_current_path(self, text):
        """Get the current path context for completion"""
        if not text:
            return Path.cwd()

        try:
            path = Path(text)
            if path.is_absolute():
                return path.parent
            return (Path.cwd() / path).parent
        except:
            return Path.cwd()
    
    
    def _get_windows_builtins(self):
        """Get Windows built-in commands dynamically"""
        try:
            result = subprocess.run("help", shell=True, stdout=subprocess.PIPE, text=True)
            return set(line.split()[0].lower() for line in result.stdout.splitlines() if line.strip())
        except:
            return set()

    def _translate_command(self, command: str) -> str:
        """Convert Unix commands to Windows equivalents or handle remote special cases"""
        cmd = command.split()[0].lower()
        
        # Handle remote session differently
        if self.current_context == "remote":
            if cmd == 'cls':
                return 'clear'
            return command
        
        # Local Windows translations
        if self.os_type == 'windows':
            translations = {
                'clear': 'cls', 'ls': 'dir', 'grep': 'findstr',
                'cp': 'copy', 'mv': 'move', 'rm': 'del'
            }
            for unix, win in translations.items():
                if command.startswith(f"{unix} ") or command == unix:
                    return command.replace(unix, win, 1)
        return command

    def _is_valid_command(self, command: str) -> bool:
        """Check if command exists in the system"""
        if not command.strip():
            return False
        if self.current_context == "remote":
            cmd = command.split()[0].lower()
            if cmd in ['cd', 'pwd']:
                return True
            try:
                check_cmd = f"command -v {cmd}" if self.remote.os_type != 'windows' else f"where {cmd}"
                stdin, stdout, stderr = self.remote.ssh.exec_command(check_cmd)
                return stdout.channel.recv_exit_status() == 0
            except:
                return False
        cmd = command.split()[0].lower()
        
        # Always treat 'cd' and 'pwd' as valid commands
        if cmd in ['cd', 'pwd']:
            return True
            
        if self.os_type == 'windows' and cmd in self.WINDOWS_BUILTINS:
            return True
            
        if shutil.which(cmd):
            return True

        try:
            check_cmd = "where" if self.os_type == 'windows' else "command -v"
            result = subprocess.run(f"{check_cmd} {cmd}", shell=True, 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except:
            return False

    def _auto_correct(self, user_input: str) -> str:
        """Fix minor command typos"""
        commands = self._get_system_commands() + [
            row[0] for row in self.cache.conn.execute("SELECT query FROM commands")
        ]
        words = user_input.split()
        if words:
            closest = get_close_matches(words[0], commands, n=1, cutoff=0.8)
            if closest:
                return f"{closest[0]} {' '.join(words[1:])}"
        return None

    def _get_system_commands(self):
        """Get available system commands"""
        try:
            return subprocess.getoutput("compgen -c" if self.os_type != 'windows' else "help").splitlines()
        except:
            return []

    def _execute(self, command: str):
        """Execute command in current context"""
        if self.current_context == "remote":
            return self._execute_remote(command)
        else:
            return self._execute_local(command)
    
    def _execute_remote(self, command: str):
        try:
            cmd_parts = command.strip().split()
            if not cmd_parts:
                return False

            # Handle cd command specially
            if cmd_parts[0].lower() == 'cd':
                target_dir = ' '.join(cmd_parts[1:]) if len(cmd_parts) > 1 else "~"
                # Get absolute path
                stdin, stdout, stderr = self.remote.ssh.exec_command(
                    f"cd {self.remote.cwd} && cd {target_dir} && pwd"
                )
                new_path = stdout.read().decode().strip()
                if new_path:
                    self.remote.cwd = new_path
                    self._print(f"Remote directory changed to {new_path}", 'green')
                    return True
                else:
                    error = stderr.read().decode().strip()
                    self._print(f"cd failed: {error}", 'red')
                    return False

            # Handle other commands
            stdin, stdout, stderr = self.remote.ssh.exec_command(
                f"cd {self.remote.cwd} && {command}",
                get_pty=True
            )
             
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            self._last_remote_exit_status = exit_status
            if exit_status == 0:
                self._print(output, 'green')
                success = True
            else:
                self._print(f"Remote error [{exit_status}]: {error}", 'red')
                success = False

            # Update remote working directory
            if command.startswith('cd '):
                self.remote.cwd = self._get_remote_pwd()
                
            return success
        except Exception as e:
            self._print(f"Remote execution failed: {str(e)}", 'red')
            return False
    
    def _execute_local(self, command: str):
        """Safe command execution handler"""
        if command.lower().startswith('ssh '):
            self._print("Use 'ssh-connect' for remote context connections", "yellow")
            return False
        translated = self._translate_command(command)

        cmd_parts = translated.strip().split()
        if not cmd_parts:
            return False

        cmd = cmd_parts[0].lower()

        # Handle built-in commands
        if cmd == 'cd':
            try:
                # Get target directory
                target_dir = ' '.join(cmd_parts[1:]) if len(cmd_parts) > 1 else str(Path.home())
                target_path = Path(target_dir).expanduser().resolve()
                os.chdir(str(target_path))
                self._print(f"Changed directory to {target_path}", color='green')
                return True
            except Exception as e:
                self._print(f"cd: {e}", color='red')
                return False
        elif cmd == 'pwd':
            self._print(os.getcwd(), color='green')
            return True

        # Execute other commands via subprocess
        try:
            subprocess.run(translated, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self._print(f"Command failed: {e.stderr}", color='red')
            return False

    def _print(self, message, color='green'):
        """Safe color printing across different environments"""
        colors = {
            'green': Fore.GREEN,
            'red': Fore.RED,
            'yellow': Fore.YELLOW,
            'blue': Fore.BLUE,
            'cyan': Fore.CYAN
        }
        print(f"{colors.get(color, '')}{message}{Style.RESET_ALL}")

    def run(self):
        self._print("""
           _____    _____ _    _ ______ _      _      
     /\   |_   _|  / ____| |  | |  ____| |    | |     
    /  \    | |   | (___ | |__| | |__  | |    | |     
   / /\ \   | |    \___ \|  __  |  __| | |    | |     
  / ____ \ _| |_   ____) | |  | | |____| |____| |____ 
 /_/    \_\_____| |_____/|_|  |_|______|______|______|
                                                      
""", 'cyan')
        self._print("Configure your API and change default model using \\config command", 'yellow')
        self._print("\n🚀 AI-Powered Shell (type 'exit shell' to quit)")
        while True:
            try:
                user_input = self.session.prompt(self._get_prompt).strip()
                if user_input == '\\help':
                    self.help.show_guide()
                    continue
                                
                elif user_input.strip() == "\\config":
                    # Run the configuration wizard
                    from config import config_manager
                    config_manager.configure()
                    continue  # Skip further processing for this input
                # Handle SSH connection
                if user_input.startswith('ssh-connect '):
                    try:
                        parts = shlex.split(user_input)
                        if len(parts) < 4 or '-i' not in parts:
                            raise ValueError

                        user_host = [p for p in parts if '@' in p][0]
                        key_index = parts.index('-i')
                        key_path = parts[key_index + 1]

                        username, hostname = user_host.split('@') if '@' in user_host else (None, user_host)

                        if not all([username, hostname, key_path]):
                            raise ValueError

                        self._connect_ssh(hostname, username, key_path)
                    except Exception as e:
                        self._print("Usage: ssh-connect [user@host] -i [key.pem]\nExample: ssh-connect ubuntu@ec2-host -i hyd.pem", "red")
                    continue
                
                # Handle context switching and disconnection
                if user_input == "local":
                    self.current_context = "local"
                    continue
                if user_input == "remote":
                    if self.remote.ssh:
                        self.current_context = "remote"
                    else:
                        self._print("Not connected to remote host", "red")
                    continue
                if user_input.lower() == "disconnect" and self.current_context == "remote":
                    if self.remote.ssh:
                        self.remote.ssh.close()
                        self.remote = RemoteSession()  # Reset remote session
                        self.current_context = "local"
                        self._print("Disconnected from remote host", "green")
                    else:
                        self._print("Not connected to remote host", "red")
                    continue
                
                if user_input.lower() in ['exit shell', 'quit', 'exit']:
                    if self.remote.ssh:
                        self.remote.ssh.close()
                    break
                if not user_input:
                    continue

                # Block direct SSH commands
                if user_input.strip().startswith('ssh '):
                    self._print("Use 'ssh-connect' for remote connections", "yellow")
                    continue

                # Try direct execution only for known commands
                if self._is_valid_command(user_input.split()[0]):
                    self._print("⚡ Running system command", 'yellow')
                    try:
                        success = self._execute(user_input)
                        # Command was executed directly, continue loop
                        continue
                    except (subprocess.CalledProcessError, Exception) as e:
                        pass
                        
                # Auto-correct attempt
                corrected = self._auto_correct(user_input)
                if corrected:
                    self._print(f"🛠️ Auto-corrected to: {corrected}", 'cyan')
                    self._execute(corrected)
                    continue

                # Check cache
                cached, explanation = self.cache.get(user_input)
                if cached:
                    self._print("🔍 Using cached command", 'yellow')
                    self._execute(cached)
                    continue

                # AI generation for everything else
                self._print("🤖 Generating command...", 'cyan')
                command, explanation = self.ai.generate_command(user_input)
                if not command:
                    self._print("❌ Failed to generate command", 'red')
                    continue
                
                regenerate = True
                while regenerate:
                    self._print(f"\nCommand: {command}", 'green')
                    if explanation:
                        self._print(f"Explanation: {explanation}", 'cyan')

                    answer = input(f"{Fore.YELLOW}Run command? (y/N/R){Style.RESET_ALL} ").lower()

                    if answer == 'y':
                        success = self._execute(command)
                        if success:
                            self.cache.save(user_input, command, explanation)
                        regenerate = False
                    elif answer == 'r':
                        self._print("🤖 Regenerating command...", 'cyan')
                        # Use the new regenerate parameter instead of use_claude
                        command, explanation = self.ai.generate_command(user_input, regenerate=True)
                        if not command:
                            self._print("❌ Regeneration failed!", 'red')
                            regenerate = False
                    else:
                        regenerate = False
            except KeyboardInterrupt:
                print("\nUse 'exit shell' to quit")
            except Exception as e:
                self._print(f"Error: {str(e)}", 'red')
    
    def _connect_ssh(self, hostname: str, username: str, key_path: str):
        self.remote.ssh = paramiko.SSHClient()
        self.remote.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Load SSH key
            key_path = key_path.strip('"\'')
            if not os.path.exists(key_path):
                raise FileNotFoundError(f"Key file not found: {key_path}")
            key = paramiko.RSAKey.from_private_key_file(key_path)
            self.remote.ssh.connect(
                hostname=hostname,
                username=username,
                pkey=key,
                timeout=10
            )
            self.remote.sftp = self.remote.ssh.open_sftp()
            self.remote.hostname = hostname
            self.current_context = "remote"
            self.remote.os_type = self._detect_remote_os()
            self.remote.cwd = self._get_remote_pwd()
            self._print(f"Connected to {hostname}", 'green')
        except paramiko.AuthenticationException:
            self._print("Authentication failed. Verify key and username.", 'red')
        except paramiko.SSHException as e:
            self._print(f"SSH Error: {str(e)}", 'red')
        except Exception as e:
            self._print(f"Remote execution failed: {str(e)}", 'red')
            self._print(f"Connection failed: {str(e)}", 'red')
    


    def _detect_remote_os(self):
        _, stdout, _ = self.remote.ssh.exec_command("uname -s")
        return stdout.read().decode().strip().lower()

    def _get_remote_pwd(self):
        _, stdout, _ = self.remote.ssh.exec_command("pwd")
        return stdout.read().decode().strip()

def main():
    try:
        AIShell().run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
