import fs from 'fs';
import path from 'path';
import JavaScriptObfuscator from 'javascript-obfuscator';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const configPath = path.resolve(__dirname, '../obfuscator.config.json');
const distPath = path.resolve(__dirname, '../dist/assets');

if (!fs.existsSync(distPath)) {
  console.log('[*] dist/assets not found, skipping obfuscation');
  process.exit(0);
}

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const files = fs.readdirSync(distPath);
let count = 0;

for (const file of files) {
  if (file.endsWith('.js')) {
    const filePath = path.join(distPath, file);
    const code = fs.readFileSync(filePath, 'utf8');
    console.log(`[*] Obfuscating ${file}...`);
    const obfuscationResult = JavaScriptObfuscator.obfuscate(code, config);
    fs.writeFileSync(filePath, obfuscationResult.getObfuscatedCode(), 'utf8');
    count++;
  }
}

console.log(`[+] Successfully obfuscated ${count} JavaScript files in dist/assets`);
