#!/usr/bin/env node

console.log('Starting AI Shell...');

const { spawn, execSync } = require('child_process');
const path = require('path');
const os = require('os');

try {
  // Get the directory where the script is installed
  const scriptDir = path.dirname(__dirname);
  
  // Path to the Python script - now located in the aishell subdirectory
  const pythonScriptPath = path.join(scriptDir, 'aishell', 'ai_shell.py');
  
  // Find available Python command
  let pythonCommand = null;
  const possibleCommands = os.platform() === 'win32' 
    ? ['py', 'python', 'python3'] 
    : ['python', 'python3'];
  
  for (const cmd of possibleCommands) {
    try {
      execSync(`${cmd} --version`, { stdio: 'pipe' });
      pythonCommand = cmd;
      break;
    } catch (err) {
      // Try next command
    }
  }
  
  if (!pythonCommand) {
    console.error('Python is not installed or not in your PATH.');
    console.error('Please install Python from https://www.python.org/downloads/');
    process.exit(1);
  }
  
  // Run the Python script
  const pythonProcess = spawn(pythonCommand, [pythonScriptPath], {
    stdio: 'inherit',
    shell: true
  });
  
  pythonProcess.on('error', (error) => {
    console.error('Failed to start Python process:', error);
    console.log('If Python is not in your PATH, make sure to install it and try again.');
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`AI Shell exited with code ${code}`);
  });
} catch (error) {
  console.error('Error running AI Shell:', error);
  process.exit(1);
}