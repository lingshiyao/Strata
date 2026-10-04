const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const baseDir = 'D:/Strata/benchmark_runs/group_mode2';
const baselineDir = 'D:/Strata/benchmark_runs/baseline';
const tasks = fs.readdirSync(baseDir).filter(f => fs.statSync(path.join(baseDir, f)).isDirectory());

console.log('=== COMPLETE 18-BENCHMARK VERIFICATION: BASELINE VS MODE 2 ===\n');

let totalBaseDuration = 0;
let totalMode2Duration = 0;
let totalBaseThink = 0;
let totalMode2Think = 0;
let totalBaseCode = 0;
let totalMode2Code = 0;

const results = [];

tasks.forEach(t => {
  const m2MetricsPath = path.join(baseDir, t, 'metrics.json');
  const m2HtmlPath = path.join(baseDir, t, 'artifact.html');
  const baseMetricsPath = path.join(baselineDir, t, 'metrics.json');
  const baseHtmlPath = path.join(baselineDir, t, 'artifact.html');

  if (!fs.existsSync(m2MetricsPath)) return;
  const m2 = JSON.parse(fs.readFileSync(m2MetricsPath, 'utf8'));
  const base = fs.existsSync(baseMetricsPath) ? JSON.parse(fs.readFileSync(baseMetricsPath, 'utf8')) : null;

  function checkHtmlSyntax(htmlPath) {
    if (!fs.existsSync(htmlPath)) return 'NO_FILE';
    const html = fs.readFileSync(htmlPath, 'utf8');
    const scriptRegex = /<script([\s\S]*?)>([\s\S]*?)<\/script>/gi;
    let match;
    let idx = 0;
    let errors = [];
    while ((match = scriptRegex.exec(html)) !== null) {
      const attrs = match[1];
      const code = match[2];
      if (attrs.includes('importmap') || attrs.includes('application/json')) continue;
      const isModule = attrs.includes('module') || code.includes('import ');
      const tmp = path.join('D:/Strata', `_chk_${Date.now()}_${idx}${isModule ? '.mjs' : '.js'}`);
      fs.writeFileSync(tmp, code, 'utf8');
      try {
        cp.execSync(`node --check "${tmp}"`, { stdio: 'pipe' });
      } catch (err) {
        const stderr = err.stderr ? err.stderr.toString() : err.message;
        const firstLine = stderr.split('\n').find(l => l.includes('SyntaxError') || l.includes('Error')) || 'SyntaxError';
        errors.push(`s${idx}: ${firstLine.trim()}`);
      } finally {
        if (fs.existsSync(tmp)) fs.unlinkSync(tmp);
      }
      idx++;
    }
    return errors.length === 0 ? 'PASS' : `FAIL (${errors.join(', ')})`;
  }

  const m2Syntax = checkHtmlSyntax(m2HtmlPath);
  const baseSyntax = checkHtmlSyntax(baseHtmlPath);

  totalMode2Duration += m2.duration_sec;
  totalMode2Think += m2.thinking_tokens;
  totalMode2Code += m2.content_tokens;

  if (base) {
    totalBaseDuration += base.duration_sec;
    totalBaseThink += base.thinking_tokens;
    totalBaseCode += base.content_tokens;
  }

  const durationDiff = base ? (((m2.duration_sec - base.duration_sec) / base.duration_sec) * 100).toFixed(1) + '%' : 'N/A';

  results.push({
    task: t,
    baseDuration: base ? base.duration_sec.toFixed(1) + 's' : 'N/A',
    m2Duration: m2.duration_sec.toFixed(1) + 's',
    durationDiff,
    baseThink: base ? base.thinking_tokens : 'N/A',
    m2Think: m2.thinking_tokens,
    baseContent: base ? base.content_tokens : 'N/A',
    m2Content: m2.content_tokens,
    baseBytes: base ? (base.code_bytes / 1024).toFixed(1) + 'KB' : 'N/A',
    m2Bytes: (m2.code_bytes / 1024).toFixed(1) + 'KB',
    baseSyntax,
    m2Syntax
  });
});

console.table(results);

console.log('\n=== AGGREGATE SUMMARY ===');
console.log(`Total Wall-Clock Time: Baseline = ${(totalBaseDuration/60).toFixed(1)} min | Mode 2 = ${(totalMode2Duration/60).toFixed(1)} min | Delta = ${(((totalMode2Duration - totalBaseDuration) / totalBaseDuration) * 100).toFixed(1)}%`);
console.log(`Total Thinking Tokens: Baseline = ${totalBaseThink.toLocaleString()} | Mode 2 = ${totalMode2Think.toLocaleString()} | Delta = ${(((totalMode2Think - totalBaseThink) / totalBaseThink) * 100).toFixed(1)}%`);
console.log(`Total Content Tokens:  Baseline = ${totalBaseCode.toLocaleString()} | Mode 2 = ${totalMode2Code.toLocaleString()} | Delta = ${(((totalMode2Code - totalBaseCode) / totalBaseCode) * 100).toFixed(1)}%`);
