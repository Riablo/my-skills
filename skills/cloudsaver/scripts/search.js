#!/usr/bin/env node

const { execSync } = require('child_process');
const { findCLI } = require('./utils');

const keyword = process.argv.slice(2).join(' ');

if (!keyword) {
  console.error('❌ 请输入搜索关键词');
  console.log('用法: search.js "电影名称"');
  process.exit(1);
}

const cliPath = findCLI();

try {
  console.log(`🔍 正在搜索: "${keyword}"...\n`);

  execSync(`node "${cliPath}" search "${keyword}"`, {
    encoding: 'utf-8',
    stdio: 'inherit',
    timeout: 120000,
  });
} catch (error) {
  if (error.status !== 0) {
    process.exit(error.status);
  }
  console.error('❌ 搜索失败:', error.message);
  process.exit(1);
}
