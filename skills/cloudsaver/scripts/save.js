#!/usr/bin/env node

const { execSync } = require('child_process');
const { findCLI } = require('./utils');

const url = process.argv[2];

if (!url) {
  console.error('❌ 请输入115分享链接');
  console.log('用法: save.js "https://115.com/s/xxxxx"');
  process.exit(1);
}

if (!url.match(/(?:115|115cdn|anxia)\.com\/s\//)) {
  console.error('❌ 无效的115分享链接');
  console.log('链接格式应为: https://115.com/s/xxxxx 或 https://115cdn.com/s/xxxxx');
  process.exit(1);
}

const cliPath = findCLI();

try {
  console.log(`💾 准备转存: ${url}\n`);

  execSync(`node "${cliPath}" save "${url}"`, {
    encoding: 'utf-8',
    stdio: 'inherit',
    timeout: 120000,
  });
} catch (error) {
  if (error.status !== 0) {
    process.exit(error.status);
  }
  console.error('❌ 转存失败:', error.message);
  process.exit(1);
}
