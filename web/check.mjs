// One-file sanity check (no test framework, just node assert).
// Run: node check.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const { humanizeVi } = await import('./src/lib/humanize.js');

const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'public/data/augments.json'), 'utf-8'));

// 1. counts
assert.equal(data.count, 376, 'expected 376 augments');
assert.equal(data.augments.length, 376);
const first = data.augments[0];
assert.ok(first.id && first.name, 'first augment has id+name');
// ảnh đã bỏ — field image không còn
assert.ok(!('image' in first), 'no image field in data (removed)');

// 2. pair filter: Fire+damage
const pair = data.augments.filter((a) =>
  a.effects.some((e) => {
    const [t, d] = e.split(':');
    return t === 'Fire' && d === 'damage';
  })
);
assert.ok(pair.length > 0 && pair.length < 50, 'pair filter yields sensible count');

// 3. humanizeVI
assert.equal(humanizeVi('offensiveFireModifier', 25), 'Tăng +25% sát thương Lửa');
assert.equal(humanizeVi('defensiveFireModifier', 30), '+30 kháng Lửa');
assert.equal(humanizeVi('characterLifeModifier', 12), 'Tăng +12% Máu');
assert.equal(humanizeVi('retaliationColdMin', 5), 'Phản +5 sát thương Băng');
assert.equal(humanizeVi('characterStrength', 8), '+8 Sức mạnh');
assert.equal(humanizeVi('offensiveSlowFireDuration', 2), 'Làm chậm tốc độ Lửa của địch: +2 giây');
assert.equal(humanizeVi('offensiveFireResistanceReduction', 10), 'Giảm +10% kháng Lửa của địch');
assert.equal(humanizeVi('defensiveBlockChance', 15), '+15% tỉ lệ Block');

console.log('OK — augments:', data.count, 'version:', data.game_version, 'pair Fire+damage:', pair.length, 'humanize samples: 8/8');
