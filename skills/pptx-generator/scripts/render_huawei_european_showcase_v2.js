const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const outDir = path.resolve(__dirname, '..', 'output');
const output = path.join(outDir, 'huawei-auto-european-showcase-v2.pptx');
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_WIDE';
pres.author = '沈万三';
pres.company = 'OpenClaw';
pres.subject = '华为汽车PPT｜欧洲高端发布会风｜顶级视觉版V2';
pres.title = 'Huawei Automotive / Harmony Intelligent Mobility';
pres.lang = 'zh-CN';
pres.theme = { headFontFace: 'Aptos', bodyFontFace: 'Aptos', lang: 'zh-CN' };

const IMG_COVER = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_073036.png');
const IMG_DETAIL = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_072300.png');
const IMG_DRIVE = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_064842.png');

const COLORS = {
  ivory: 'F5F3EF',
  ivory2: 'FBFAF7',
  sand: 'E8E1D8',
  ink: '111111',
  body: '2F2F2F',
  muted: '6E6A64',
  wine: '8B1E24',
  charcoal: '171717',
  white: 'FAFAF8',
  line: 'D8D1C7'
};

function addImageContain(slide, imgPath, x, y, w, h) {
  slide.addImage({ path: imgPath, x, y, w, h, sizing: { type: 'contain', x, y, w, h } });
}
function addImageCover(slide, imgPath, x, y, w, h) {
  slide.addImage({ path: imgPath, x, y, w, h, sizing: { type: 'cover', x, y, w, h } });
}
function addPageNo(slide, n, dark=false) {
  slide.addText(String(n).padStart(2, '0'), {
    x: 11.7, y: 6.72, w: 0.4, h: 0.18,
    fontSize: 8, color: dark ? '9CA3AF' : COLORS.muted, align: 'right', margin: 0
  });
}
function addFooter(slide, text, dark=false) {
  slide.addText(text, {
    x: 0.7, y: 6.72, w: 6.5, h: 0.18,
    fontSize: 8, color: dark ? 'A8A29E' : COLORS.muted, margin: 0, charSpace: 0.4
  });
}
function addHeaderRule(slide) {
  slide.addShape(pres.ShapeType.line, { x: 0.65, y: 0.55, w: 11.0, h: 0, line: { color: COLORS.line, pt: 1 } });
}
function addTitle(slide, title, sub) {
  slide.addText(title, { x: 0.75, y: 0.88, w: 5.8, h: 0.45, fontSize: 24, bold: true, color: COLORS.ink, margin: 0 });
  if (sub) slide.addText(sub, { x: 0.78, y: 1.38, w: 5.6, h: 0.28, fontSize: 11, color: COLORS.muted, italic: true, margin: 0 });
}
function addBulletList(slide, items, x, y, w, h=2.8, fontSize=17, color=COLORS.body) {
  const runs = [];
  items.forEach((item) => runs.push({ text: item + '\n', options: { bullet: { indent: 14 } } }));
  slide.addText(runs, { x, y, w, h, fontSize, color, breakLine: false, paraSpaceAfterPt: 10, margin: 0.03, valign: 'top' });
}
function card(slide, x, y, w, h, dark=false, accent=false) {
  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h,
    line: { color: accent ? COLORS.wine : (dark ? '3F3F46' : COLORS.sand), pt: 1 },
    fill: { color: dark ? '202225' : COLORS.ivory2 }
  });
}

// Common 16:9 boxes
const BOX_WIDE_W = 5.2;
const BOX_WIDE_H = 2.925; // 16:9 exact
const BOX_TALL_W = 5.6;
const BOX_TALL_H = 3.15;  // 16:9 exact
const BOX_LARGE_W = 6.0;
const BOX_LARGE_H = 3.375; // 16:9 exact

// 1 Cover
{
  const s = pres.addSlide();
  s.background = { color: COLORS.charcoal };
  addImageCover(s, IMG_COVER, 4.95, 0, 8.38, 7.5);
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 5.45, h: 7.5, line: { color: COLORS.charcoal, transparency: 100 }, fill: { color: COLORS.charcoal, transparency: 4 } });
  s.addShape(pres.ShapeType.rect, { x: 0.78, y: 0.82, w: 0.14, h: 1.6, line: { color: COLORS.wine, transparency: 100 }, fill: { color: COLORS.wine } });
  s.addText('华为汽车', { x: 1.12, y: 0.86, w: 3.8, h: 0.7, fontSize: 28, bold: true, color: COLORS.white, margin: 0 });
  s.addText('鸿蒙智行｜欧洲高端发布会终极视觉版', { x: 1.12, y: 1.58, w: 4.2, h: 0.45, fontSize: 14, color: 'D6D3D1', margin: 0 });
  s.addText('SMART MOBILITY / HAUTE PRESENTATION / EXECUTIVE SHOWCASE', { x: 1.12, y: 2.12, w: 4.3, h: 0.25, fontSize: 8, color: 'A8A29E', margin: 0, charSpace: 1.05 });
  s.addText('以平台能力、生态协同与高端品牌心智，重构智能汽车时代的价值表达方式。', { x: 1.12, y: 3.1, w: 3.75, h: 1.15, fontSize: 15, color: 'E7E5E4', margin: 0.02, valign: 'mid' });
  addFooter(s, 'HUAWEI AUTOMOTIVE / EUROPEAN SHOWCASE', true);
  addPageNo(s, 1, true);
}

// 2 Opening thesis
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  addHeaderRule(s);
  addTitle(s, '核心判断', 'Huawei is shaping the premium intelligent mobility layer, not merely participating in auto manufacturing.');
  card(s, 0.82, 2.05, 10.5, 3.05, false, true);
  s.addText('真正的价值，不在“造一辆车”，而在占据智能汽车最有溢价、最能形成长期认知的那一层。', {
    x: 1.1, y: 2.45, w: 9.8, h: 0.72, fontSize: 21, bold: true, color: COLORS.body, margin: 0.02
  });
  addBulletList(s, [
    '鸿蒙座舱、智能驾驶、车云协同与终端生态，构成平台型护城河。',
    '华为模式更接近“高端系统整合者”，而不是传统整车制造者。',
    '高端新能源竞争的本质，正在转向体验、信任与审美的复合竞争。'
  ], 1.12, 3.45, 9.4, 1.7, 17);
  addFooter(s, 'INVESTMENT THESIS'); addPageNo(s, 2);
}

// 3 Market + image
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  addHeaderRule(s);
  addTitle(s, '市场已经从参数竞争转向体验竞争', 'The premium moat is shifting from hardware specs to software, trust and total experience.');
  addBulletList(s, [
    '消费者对高端新能源车的期待，已经从续航和马力，转向完整智能体验。',
    '品牌认知、交互流畅度与系统一致性，正成为新的溢价来源。',
    '这恰好是华为最容易建立差异化的战场。'
  ], 0.92, 2.15, 4.85, 2.6, 16);
  addImageContain(s, IMG_COVER, 6.15, 2.05, BOX_TALL_W, BOX_TALL_H);
  s.addShape(pres.ShapeType.rect, { x: 6.0, y: 1.9, w: BOX_TALL_W + 0.3, h: BOX_TALL_H + 0.3, line: { color: COLORS.wine, pt: 1.2 }, fill: { color: COLORS.ivory, transparency: 100 } });
  addFooter(s, 'MARKET SHIFT'); addPageNo(s, 3);
}

// 4 Positioning dark
{
  const s = pres.addSlide();
  s.background = { color: COLORS.charcoal };
  s.addText('华为汽车业务定位', { x: 0.82, y: 0.82, w: 4.0, h: 0.5, fontSize: 25, bold: true, color: COLORS.white, margin: 0 });
  s.addText('PLATFORM / ECOSYSTEM / EXPERIENCE', { x: 0.85, y: 1.38, w: 3.5, h: 0.22, fontSize: 8, color: 'A8A29E', charSpace: 1.1, margin: 0 });
  card(s, 0.82, 2.02, 3.2, 3.0, true, true);
  s.addText('不直接造车\n而是掌握\n增量价值层', { x: 1.12, y: 2.5, w: 2.55, h: 1.2, fontSize: 22, bold: true, color: COLORS.white, align: 'center', valign: 'mid' });
  card(s, 4.45, 2.02, 2.7, 3.0, true, false);
  addBulletList(s, ['智能驾驶', '鸿蒙座舱', '车云协同', '品牌零售触点'], 4.72, 2.42, 2.15, 2.1, 16, 'E7E5E4');
  card(s, 7.45, 2.02, 4.0, 3.0, true, false);
  addBulletList(s, ['解决方案供应商 + 品牌放大器', '避开重资产整车压力', '把技术能力直接转成市场心智'], 7.72, 2.42, 3.35, 2.1, 16, 'E7E5E4');
  addFooter(s, 'POSITIONING', true); addPageNo(s, 4, true);
}

// 5 Cockpit with strict 16:9
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  card(s, 0.6, 0.75, 5.25, 4.95, false, false);
  s.addText('鸿蒙座舱', { x: 0.95, y: 1.0, w: 2.2, h: 0.45, fontSize: 24, bold: true, color: COLORS.ink, margin: 0 });
  s.addText('欧式高级感的关键不是堆屏，而是秩序、材质、光感与交互节奏。', { x: 0.95, y: 1.55, w: 4.25, h: 0.65, fontSize: 15, color: COLORS.body, margin: 0.01 });
  addBulletList(s, [
    '多设备无缝流转，强化“人车家”连续体验。',
    '交互、语音、应用生态共同形成留存。',
    '座舱体验更接近高级消费电子，而非传统车机。'
  ], 0.98, 2.42, 4.3, 2.3, 16);
  addImageContain(s, IMG_DETAIL, 6.15, 1.28, BOX_LARGE_W, BOX_LARGE_H);
  s.addShape(pres.ShapeType.rect, { x: 6.0, y: 1.13, w: BOX_LARGE_W + 0.3, h: BOX_LARGE_H + 0.3, line: { color: COLORS.sand, pt: 1 }, fill: { color: COLORS.ivory, transparency: 100 } });
  addFooter(s, 'HARMONY COCKPIT'); addPageNo(s, 5);
}

// 6 Driving with strict 16:9
{
  const s = pres.addSlide();
  s.background = { color: COLORS.charcoal };
  addImageContain(s, IMG_DRIVE, 0.75, 1.32, BOX_TALL_W, BOX_TALL_H);
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 1.17, w: BOX_TALL_W + 0.3, h: BOX_TALL_H + 0.3, line: { color: '3F3F46', pt: 1 }, fill: { color: COLORS.charcoal, transparency: 100 } });
  s.addText('智能驾驶', { x: 6.65, y: 1.2, w: 2.5, h: 0.45, fontSize: 24, bold: true, color: COLORS.white, margin: 0 });
  s.addText('A premium brand wins only when assistance feels safe, calm and consistently usable.', { x: 6.67, y: 1.76, w: 4.45, h: 0.48, fontSize: 12, color: 'CFCFCF', italic: true, margin: 0 });
  addBulletList(s, [
    '安全、稳定、可用性比单次炫技更重要。',
    '高阶智驾是中高端车型溢价的重要来源。',
    '持续 OTA 让能力具备复利式进化空间。'
  ], 6.7, 2.55, 4.2, 2.2, 16, 'E7E5E4');
  addFooter(s, 'ADVANCED DRIVING', true); addPageNo(s, 6, true);
}

// 7 Ecosystem matrix visual
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  addHeaderRule(s);
  addTitle(s, '合作生态决定规模上限', 'A platform story becomes powerful only when it turns into a brand matrix.');
  const cards = [ ['问界','最具销量与认知基础'], ['智界','年轻化与运动化定位'], ['享界','高端商务市场延展'], ['尊界','抬升品牌天花板'] ];
  let x = 0.88;
  cards.forEach(([t,d], i) => {
    card(s, x, 2.02, 2.65, 2.25, false, i===0);
    s.addText(t, { x: x+0.22, y: 2.35, w: 1.5, h: 0.35, fontSize: 22, bold: true, color: COLORS.ink, margin: 0 });
    s.addText(d, { x: x+0.22, y: 2.95, w: 2.05, h: 0.62, fontSize: 13, color: COLORS.body, margin: 0.01 });
    x += 2.82;
  });
  s.addText('生态矩阵的意义，不只是多品牌覆盖，而是把技术平台真正转成规模化品牌势能。', { x: 0.92, y: 5.08, w: 10.0, h: 0.45, fontSize: 15, color: COLORS.body, margin: 0 });
  addFooter(s, 'ECOSYSTEM MATRIX'); addPageNo(s, 7);
}

// 8 Why win visual bars
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  addHeaderRule(s);
  addTitle(s, '为什么它有机会长期占位', 'The competitive advantage is systemic, not isolated.');
  const items = [
    ['技术','座舱、智驾、车云、系统协同'],
    ['品牌','高端科技消费电子心智外溢'],
    ['渠道','零售触点强，教育成本更低'],
    ['生态','手机、IoT、服务与汽车联动']
  ];
  let y = 1.95;
  items.forEach(([a,b], idx) => {
    s.addShape(pres.ShapeType.rect, { x: 0.95, y, w: 0.12, h: 0.42, line: { color: idx===0 ? COLORS.wine : COLORS.sand, transparency:100 }, fill: { color: idx===0 ? COLORS.wine : COLORS.sand } });
    s.addText(a, { x: 1.22, y: y-0.01, w: 0.9, h: 0.28, fontSize: 17, bold: true, color: idx===0 ? COLORS.wine : COLORS.ink, margin: 0 });
    s.addText(b, { x: 2.35, y: y-0.02, w: 6.4, h: 0.3, fontSize: 15, color: COLORS.body, margin: 0 });
    y += 0.78;
  });
  card(s, 8.85, 1.78, 2.2, 2.95, false, true);
  s.addText('结论', { x: 9.18, y: 2.08, w: 0.9, h: 0.3, fontSize: 16, bold: true, color: COLORS.wine, margin: 0 });
  s.addText('华为不是在卖单个车型，而是在卖一整套高端智能出行体验。', { x: 9.08, y: 2.55, w: 1.55, h: 1.5, fontSize: 13, color: COLORS.body, align: 'center', valign: 'mid', margin: 0.02 });
  addFooter(s, 'WHY IT CAN WIN'); addPageNo(s, 8);
}

// 9 Risks
{
  const s = pres.addSlide();
  s.background = { color: COLORS.charcoal };
  s.addText('风险与约束', { x: 0.82, y: 0.88, w: 2.8, h: 0.42, fontSize: 24, bold: true, color: COLORS.white, margin: 0 });
  s.addText('Scale does not remove execution complexity.', { x: 0.85, y: 1.42, w: 3.6, h: 0.25, fontSize: 11, color: 'B4B4B4', italic: true, margin: 0 });
  const risks = ['价格战长期存在，利润率承压','生态扩张后，协同复杂度明显上升','智能驾驶监管与安全舆论风险持续存在','供应链、交付节奏与市场预期需要平衡'];
  let x = 0.9;
  risks.forEach((r, i) => {
    card(s, x, 2.35, 2.58, 2.2, true, i===0);
    s.addText(String(i+1).padStart(2,'0'), { x: x+0.2, y: 2.58, w: 0.45, h: 0.25, fontSize: 10, color: 'A8A29E', margin: 0 });
    s.addText(r, { x: x+0.2, y: 3.02, w: 2.05, h: 1.02, fontSize: 14, color: COLORS.white, margin: 0.02, valign: 'mid' });
    x += 2.78;
  });
  addFooter(s, 'RISKS & CONSTRAINTS', true); addPageNo(s, 9, true);
}

// 10 Closing
{
  const s = pres.addSlide();
  s.background = { color: COLORS.ivory };
  card(s, 0.7, 0.9, 10.3, 4.95, false, false);
  s.addText('最终一句话', { x: 1.08, y: 1.35, w: 2.0, h: 0.4, fontSize: 22, bold: true, color: COLORS.ink, margin: 0 });
  s.addText('华为汽车真正值得重视的，不只是销量，而是它正在重构高端智能汽车的价值表达方式。', { x: 1.08, y: 2.03, w: 8.95, h: 0.95, fontSize: 24, bold: true, color: COLORS.body, margin: 0.01, align: 'left', valign: 'mid' });
  s.addText('持续关注：鸿蒙智行生态扩张、高阶智驾稳定落地、高端品牌心智形成速度。', { x: 1.1, y: 3.58, w: 8.7, h: 0.48, fontSize: 15, color: COLORS.muted, margin: 0 });
  s.addText('THANK YOU', { x: 1.08, y: 5.15, w: 1.5, h: 0.25, fontSize: 9, color: COLORS.wine, charSpace: 1.2, margin: 0 });
  addFooter(s, 'CLOSING STATEMENT'); addPageNo(s, 10);
}

fs.mkdirSync(outDir, { recursive: true });
pres.writeFile({ fileName: output }).then(() => console.log(output));
