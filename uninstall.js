const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

console.log('Uninstalling AI Shell...');

try {
  // Try to uninstall both the old and new package names
  try {
    execSync('npm uninstall -g aishell', { stdio: 'pipe' });
    console.log('Removed global npm package (aishell)');
  } catch (e) {
    // This might fail if not installed, which is fine
  }
  
  try {
    execSync('npm uninstall -g ai-shell', { stdio: 'pipe' });
    console.log('Removed global npm package (ai-shell)');
  } catch (e) {
    // This might fail if not installed, which is fine
  }
  
  // If on Windows, try to remove conflicting Python package if it exists
  if (os.platform() === 'win32') {
    try {
      execSync('pip uninstall -y aishell', { stdio: 'pipe' });
      console.log('Removed conflicting Python package (aishell)');
    } catch (e) {
      // This might fail if the package doesn't exist, which is fine
    }
  }
  
  console.log('AI Shell has been uninstalled.');
} catch (error) {
  console.error('Error during uninstallation:', error);
  process.exit(1);
}
