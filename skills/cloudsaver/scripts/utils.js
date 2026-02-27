const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const KNOWN_PATHS = [
  path.join(process.env.HOME, 'Projects', 'CloudSaver', 'dist', 'index.js'),
  path.join(process.env.HOME, 'projects', 'CloudSaver', 'dist', 'index.js'),
];

function findCLI() {
  // 1. 检查 PATH 中是否有全局安装的 cloudsaver
  try {
    const globalPath = execSync('which cloudsaver', { encoding: 'utf-8' }).trim();
    if (globalPath) return globalPath;
  } catch (_) {
    // not in PATH
  }

  // 2. 检查已知本地路径
  for (const p of KNOWN_PATHS) {
    if (fs.existsSync(p)) return p;
  }

  // 3. 未找到，输出安装指引
  console.error('❌ 未找到 CloudSaver CLI\n');
  console.error('请先安装 CloudSaver CLI：\n');
  console.error('  cd ~/Projects');
  console.error('  git clone https://github.com/Riablo/CloudSaver.git');
  console.error('  cd CloudSaver');
  console.error('  npm install');
  console.error('  npm run build\n');
  console.error('安装完成后重新运行此命令。');
  process.exit(1);
}

module.exports = { findCLI };
