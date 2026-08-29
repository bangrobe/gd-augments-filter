// Vietnamese humanizer — port của build_db.py humanize() sang JS
// Input: stat key + value -> Player-friendly Vietnamese label
const DMG = {Physical:'offensivePhysical',Fire:'offensiveFire',Cold:'offensiveCold',Lightning:'offensiveLightning',Poison:'offensivePoison',Aether:'offensiveAether',Chaos:'offensiveChaos',Pierce:'offensivePierce',Vitality:'offensiveLife',Elemental:'offensiveElemental',Bleeding:'offensiveBleeding'};
const RES = {Physical:'defensivePhysical',Fire:'defensiveFire',Cold:'defensiveCold',Lightning:'defensiveLightning',Poison:'defensivePoison',Aether:'defensiveAether',Chaos:'defensiveChaos',Pierce:'defensivePierce',Vitality:'defensiveLife',Elemental:'defensiveElemental',Bleeding:'defensiveBleeding'};
const RET = {Physical:'retaliationPhysical',Fire:'retaliationFire',Cold:'retaliationCold',Lightning:'retaliationLightning',Poison:'retaliationPoison',Aether:'retaliationAether',Chaos:'retaliationChaos',Vitality:'retaliationLife',Bleeding:'retaliationBleeding'};
const DT_VI = {Physical:'Vật lý',Fire:'Lửa',Cold:'Băng',Lightning:'Sét',Poison:'Độc',Aether:'Aether',Chaos:'Hỗn mang',Pierce:'Xuyên giáp',Vitality:'Sinh lực',Elemental:'Nguyên tố',Bleeding:'Chảy máu'};
const DT_EN = {Physical:'Physical',Fire:'Fire',Cold:'Cold',Lightning:'Lightning',Poison:'Poison',Aether:'Aether',Chaos:'Chaos',Pierce:'Pierce',Vitality:'Vitality',Elemental:'Elemental',Bleeding:'Bleeding'};

function detectDt(key, dicts) {
  for (const t in dicts.DMG) if (key.startsWith(dicts.DMG[t]) || key === 'offensiveBase' + t + 'Max') return t;
  for (const t in dicts.RES) if (key.startsWith(dicts.RES[t])) return t;
  for (const t in dicts.RET) if (key.startsWith(dicts.RET[t])) return t;
  return null;
}

function fmtVal(v) {
  const f = Number(v);
  if (Number.isNaN(f)) return String(v);
  if (Number.isInteger(f)) return String(f);
  return f.toFixed(1);
}

const DMG_KEYS = Object.keys(DMG);
const RET_KEYS = Object.keys(RET);

export function humanizeVi(key, val) {
  const v = fmtVal(val);
  const sign = (typeof val === 'number' && val >= 0) ? '+' : '';
  const dt = detectDt(key, {DMG, RES, RET});
  const dtvi = dt ? (DT_VI[dt] || dt) : '';

  if (key.startsWith('offensive')) {
    if (key.includes('Slow')) {
      const slowDt = dt || detectDt(key.replace('Slow', ''), {DMG, RES, RET});
      const slowVi = slowDt ? (DT_VI[slowDt] || slowDt) : '';
      if (key.endsWith('Modifier')) return `Làm chậm ${sign}${v}% tốc độ ${slowVi} của địch`.replace('  ', ' ');
      if (key.includes('Duration')) return `Làm chậm tốc độ ${slowVi} của địch: ${sign}${v} giây`;
      return `Làm chậm tốc độ ${slowVi} của địch (${sign}${v})`;
    }
    if (key.includes('ResistanceReduction')) return `Giảm ${sign}${v}% kháng ${dtvi} của địch`;
    if (key.includes('TotalDamageModifier')) return `Tăng ${sign}${v}% tổng sát thương`;
    if (key.includes('Confusion')) return key.includes('Chance') ? `${sign}${v}% cơ hội gây Bối rối` : `Gây Bối rối ${sign}${v}`;
    if (key.includes('Freeze')) return key.includes('Chance') ? `${sign}${v}% cơ hội làm Đóng băng` : `Làm Đóng băng ${sign}${v}`;
    if (key.includes('Stun')) return key.includes('Chance') ? `${sign}${v}% cơ hội làm Choáng` : `Làm Choáng ${sign}${v}`;
    if (dt) {
      if (key.endsWith('Modifier')) return `Tăng ${sign}${v}% sát thương ${dtvi}`;
      if (key.endsWith('Min')) return `${sign}${v} sát thương ${dtvi} (flat)`;
      if (key.endsWith('Max')) return `${sign}${v} sát thương ${dtvi} tối đa`;
      if (key.includes('Base')) return `${sign}${v} sát thương ${dtvi} cơ bản`;
    }
    return key;
  }
  if (key.startsWith('defensive')) {
    if (key.includes('Block')) {
      if (key.includes('Chance')) return `${sign}${v}% tỉ lệ Block`;
      if (key.includes('Amount')) return `${sign}${v}% lượng Block`;
      if (key.includes('Recovery')) return `Phục hồi Block ${sign}${v}`;
      return `Block ${sign}${v}%`;
    }
    if (key.includes('Protection')) return key.endsWith('Modifier') ? `Tăng ${sign}${v}% Giáp` : `${sign}${v} Giáp`;
    if (key.includes('Absorption')) return `Tăng ${sign}${v}% Hấp thụ`;
    if (key.includes('BonusProtection')) return `${sign}${v} Giáp cộng thêm`;
    if (key.includes('Petrify')) return `${sign}${v} Kháng Hóa đá`;
    if (key.includes('Trap')) return `${sign}${v} Kháng Bẫy`;
    if (key.includes('Stun')) return `${sign}${v} Kháng Choáng`;
    if (key.includes('Freeze')) return `${sign}${v} Kháng Đóng băng`;
    if (key.includes('Bleeding')) return `${sign}${v} Kháng Chảy máu`;
    if (key.includes('TotalSpeedResistance')) return `${sign}${v}% Kháng làm chậm`;
    if (key.includes('PercentReflectionResistance')) return `${sign}${v}% Kháng Phản chiếu`;
    if (key.includes('SlowLifeLeach')) return `${sign}${v} Hút máu khi chậm`;
    if (dt) {
      if (key.endsWith('MaxResist')) return `${sign}${v} kháng tối đa ${dtvi}`;
      return `${sign}${v} kháng ${dtvi}`;
    }
    return key;
  }
  if (key.startsWith('character')) {
    if (key.includes('OffensiveAbility')) return key.endsWith('Modifier') ? `${sign}${v} Điểm Tấn công (OA)` : `${sign}${v} OA`;
    if (key.includes('DefensiveAbility')) return key.endsWith('Modifier') ? `${sign}${v} Điểm Phòng thủ (DA)` : `${sign}${v} DA`;
    if (key.includes('Life')) {
      if (key.includes('Regen')) return key.includes('Modifier') ? `Hồi ${sign}${v} máu/giây` : `Hồi sinh ${sign}${v}`;
      return key.endsWith('Modifier') ? `Tăng ${sign}${v}% Máu` : `${sign}${v} Máu`;
    }
    if (key.includes('Mana')) {
      if (key.includes('Regen')) return `Hồi ${sign}${v} mana/giây`;
      return key.endsWith('Modifier') ? `Tăng ${sign}${v}% Mana` : `${sign}${v} Mana`;
    }
    if (key.includes('RunSpeed')) return `Tăng ${sign}${v}% tốc độ chạy`;
    if (key.includes('AttackSpeed')) return `Tăng ${sign}${v}% tốc độ đánh`;
    if (key.includes('SpellCastSpeed')) return `Tăng ${sign}${v}% tốc độ niệm`;
    if (key.includes('HealIncreasePercent')) return `Tăng ${sign}${v}% hồi máu`;
    if (key.includes('EnergyAbsorptionPercent')) return `${sign}${v}% hấp thụ năng lượng`;
    if (key.includes('DefensiveBlockRecoveryReduction')) return `Giảm ${sign}${v} phục hồi block`;
    if (key.includes('Strength')) return `${sign}${v} Sức mạnh`;
    if (key.includes('Dexterity')) return `${sign}${v} Nhanh nhẹn`;
    if (key.includes('Intelligence')) return `${sign}${v} Trí tuệ`;
    if (key.includes('Spirit')) return `${sign}${v} Tinh thần`;
    if (key.includes('ConstitutionModifier')) return `Tăng ${sign}${v}% Thể chất`;
    return key;
  }
  if (key.startsWith('retaliation')) {
    if (key === 'retaliationTotalDamageModifier') return `Tăng ${sign}${v}% sát thương phản`;
    if (dt) return `Phản ${sign}${v} sát thương ${dtvi}`;
    return key;
  }
  if (key.startsWith('racial')) {
    if (key.includes('PercentDamage')) return `Tăng ${sign}${v}% sát thương vs loài`;
    if (key.includes('PercentDefense')) return `Tăng ${sign}${v}% phòng thủ vs loài`;
    if (key.includes('Race')) return `Loài: ${val}`;
    return key;
  }
  if (key.startsWith('pet')) {
    if (key.includes('BonusName')) return 'Có chỉ số Pet';
    if (key.includes('Defensive')) return `${sign}${v} phòng thủ Pet`;
    if (key.includes('Avoidance')) return `${sign}${v}% né tránh Pet`;
    return key;
  }
  if (key.startsWith('augment')) {
    if (key.includes('AllLevel')) return `+${val} level tất cả kỹ năng augment`;
    if (key.includes('MasteryLevel')) return `+${val} level mastery augment`;
    if (key.includes('MasteryName')) return `Mastery augment: ${val}`;
    if (key.includes('SkillLevel')) return `+${val} level kỹ năng augment`;
    return key;
  }
  if (key.startsWith('itemSkill')) {
    if (key.includes('Name')) return `Kỹ năng: ${val}`;
    if (key.includes('LevelEq')) return `Yêu cầu level kỹ năng: ${val}`;
    return key;
  }
  if (key.startsWith('modified')) {
    if (key.includes('Name')) return `Kỹ năng sửa đổi: ${val}`;
    if (key.includes('Level')) return `+${val} level kỹ năng sửa đổi`;
    return key;
  }
  return key;
}

export { DMG_KEYS };
