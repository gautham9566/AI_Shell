const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const os = require('os');

console.log('Installing AI Shell...');

try {
  // Make the main script executable on Unix-like systems
  if (os.platform() !== 'win32') {
    const aishellPath = path.join(__dirname, 'bin', 'ai-shell.js');
    fs.chmodSync(aishellPath, '755');
    console.log('Made AI Shell executable');
  }
  
  // Check if Python is installed - try multiple commands
  let pythonCommand = '';
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
      // Command failed, try next one
    }
  }
  
  if (!pythonCommand) {
    console.error('Python not found. Please install Python to use AI Shell.');
    console.error('Visit https://www.python.org/downloads/ to download and install Python.');
    process.exit(1);
  }
  
  // Install Python dependencies if requirements.txt exists
  const reqPath = path.join(__dirname, 'requirements.txt');
  if (fs.existsSync(reqPath)) {
    console.log('Installing Python dependencies...');
    try {
      execSync(`${pythonCommand} -m pip install -r "${reqPath}"`, { stdio: 'inherit' });
    } catch (err) {
      console.error('Failed to install Python dependencies. You may need to install them manually.');
      console.error(`Run: ${pythonCommand} -m pip install -r "${reqPath}"`);
    }
  }
  
  // Create a platform-specific runner script
  if (os.platform() === 'win32') {
    createWindowsBatchFile(pythonCommand);
  } else {
    createUnixShellScript(pythonCommand);
  }
  
  console.log('\nAI Shell has been installed successfully!');
  console.log('You can now run it by typing "ai-shell" in your terminal.');
} catch (error) {
  console.error('Error during installation:', error);
  process.exit(1);
}

function createWindowsBatchFile(pythonCommand) {
  const batchPath = path.join(__dirname, 'bin', 'ai-shell.bat');
  const scriptContent = `@echo off
${pythonCommand} "%~dp0\\..\\aishell\\ai_shell.py" %*
`;
  fs.writeFileSync(batchPath, scriptContent);
  console.log('Created Windows batch file for running AI Shell');
}

function createUnixShellScript(pythonCommand) {
  const shellPath = path.join(__dirname, 'bin', 'ai-shell');
  const scriptContent = `#!/bin/sh
${pythonCommand} "$(dirname "$0")/../aishell/ai_shell.py" "$@"
`;
  fs.writeFileSync(shellPath, scriptContent);
  fs.chmodSync(shellPath, '755');
  console.log('Created Unix shell script for running AI Shell');
}
