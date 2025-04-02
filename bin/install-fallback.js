const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

console.log('Running fallback installation...');

try {
  const rootDir = path.dirname(__dirname);
  
  // Find available Python command
  let pythonCommand = 'python';
  const possibleCommands = os.platform() === 'win32' 
    ? ['py', 'python', 'python3'] 
    : ['python', 'python3'];
  
  for (const cmd of possibleCommands) {
    try {
      execSync(`${cmd} --version`, { stdio: 'pipe' });
      pythonCommand = cmd;
      console.log(`Using Python command: ${cmd}`);
      break;
    } catch (err) {
      // Try next command
    }
  }
  
  // Create platform-specific runner scripts
  if (os.platform() === 'win32') {
    createWindowsBatchFile(rootDir, pythonCommand);
  } else {
    createUnixShellScript(rootDir, pythonCommand);
  }
  
  console.log('\nAI Shell has been installed with limited functionality.');
  console.log(`You can run it using the "ai-shell" command or directly with "${pythonCommand} aishell/ai_shell.py"`);
} catch (error) {
  console.error('Error during fallback installation:', error);
}

function createWindowsBatchFile(rootDir, pythonCommand) {
  const batchPath = path.join(rootDir, 'bin', 'ai-shell.bat');
  const scriptContent = `@echo off
${pythonCommand} "%~dp0\\..\\aishell\\ai_shell.py" %*
`;
  fs.writeFileSync(batchPath, scriptContent);
  console.log('Created Windows batch file for running AI Shell');
}

function createUnixShellScript(rootDir, pythonCommand) {
  const shellPath = path.join(rootDir, 'bin', 'ai-shell');
  const scriptContent = `#!/bin/sh
${pythonCommand} "$(dirname "$0")/../aishell/ai_shell.py" "$@"
`;
  fs.writeFileSync(shellPath, scriptContent);
  try {
    fs.chmodSync(shellPath, '755');
  } catch (e) {
    console.warn('Could not set execute permissions. You may need to run: chmod +x bin/ai-shell');
  }
  console.log('Created Unix shell script for running AI Shell');
}
