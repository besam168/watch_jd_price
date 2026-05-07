const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const outDir = path.resolve(__dirname, '..', 'output');
const output = path.join(outDir, 'huawei-auto-consulting-final.pptx');
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_WIDE';
pres.author = '沈万三';
pres.company = 'OpenClaw';
pres.subject = '华为汽车PPT｜咨询公司终稿版';
pres.title = 'Huawei Automotive Consulting Final';
pres.lang = 'zh-CN';
pres.theme = { headFontFace: 'Aptos', bodyFontFace: 'Aptos', lang: 'zh-CN' };

const IMG_COVER = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_073036.png');
const IMG_DETAIL = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_072300.png');
const IMG_DRIVE = path.resolve(outDir, '..', '..', 'ppt-image-bridge', 'output-v2-test', 'v2-test_20260507_064842.png');

const C = {
  bg: 'F7F4EE',
  card: 'FBFAF7',
  text: '191919',
  body: '383838',
  sub: '6B6B6B',
  line: 'DDD6CC',
  accent: '8A1F25',
  dark: '181818',
  white: 'FAFAF8'
};

function cover(slide, img, x, y, w, h) {
  slide.addImage({ path: img, x, y, w, h, sizing: { type: 'cover', x, y, w, h } });
}
function contain(slide, img, x, y, w, h) {
  slide.addImage({ path: img, x, y, w, h, sizing: { type: 'contain', x, y, w, h } });
}
function footer(slide, text, dark=false) {
  slide.addText(text, { x: 0.75, y: 6.72, w: 5.5, h: 0.18, fontSize: 8, color: dark ? 'A8A29E' : C.sub, margin: 0, charSpace: 0.4 });
}
function page(slide, n, dark=false) {
  slide.addText(String(n).padStart(2,'0'), { x: 11.65, y: 6.72, w: 0.45, h: 0.18, align: 'right', fontSize: 8, color: dark ? '9CA3AF' : C.sub, margin: 0 });
}
function topRule(slide, dark=false) {
  slide.addShape(pres.ShapeType.line, { x: 0.7, y: 0.58, w: 10.95, h: 0, line: { color: dark ? '3A3A3A' : C.line, pt: 1 } });
}
function title(slide, main, sub, dark=false) {
  slide.addText(main, { x: 0.8, y: 0.85, w: 6.2, h: 0.45, fontSize: 23, bold: true, color: dark ? C.white : C.text, margin: 0 });
  if (sub) slide.addText(sub, { x: 0.82, y: 1.35, w: 7.8, h: 0.24, fontSize: 10.5, color: dark ? 'BDBDBD' : C.sub, italic: true, margin: 0 });
}
function card(slide, x, y, w, h, dark=false, accent=false) {
  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h,
    line: { color: accent ? C.accent : (dark ? '3E3E3E' : C.line), pt: 1 },
    fill: { color: dark ? '202020' : C.card }
  });
}
function bullets(slide, items, x, y, w, h, fontSize=15.5, dark=false) {
  const arr = [];
  items.forEach(item => arr.push({ text: item + '\n', options: { bullet: { indent: 13 } } }));
  slide.addText(arr, {
    x, y, w, h,
    fontSize,
    color: dark ? 'ECE7E1' : C.body,
    margin: 0.03,
    paraSpaceAfterPt: 8,
    breakLine: false,
    valign: 'top'
  });
}

const W169_1 = { w: 5.7, h: 3.20625 };
const W169_2 = { w: 5.95, h: 3.346875 };

// 1 cover
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  cover(s, IMG_COVER, 4.82, 0, 8.51, 7.5);
  s.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 5.4, h: 7.5, line: { color: C.dark, transparency: 100 }, fill: { color: C.dark, transparency: 6 } });
  s.addShape(pres.ShapeType.rect, { x: 0.82, y: 0.88, w: 0.12, h: 1.45, line: { color: C.accent, transparency: 100 }, fill: { color: C.accent } });
  s.addText('华为汽车', { x: 1.12, y: 0.92, w: 3.2, h: 0.55, fontSize: 27, bold: true, color: C.white, margin: 0 });
  s.addText('咨询公司终稿版', { x: 1.12, y: 1.52, w: 2.5, h: 0.3, fontSize: 13, color: 'D6D3D1', margin: 0 });
  s.addText('HARMONY INTELLIGENT MOBILITY / FINAL EXECUTIVE DECK', { x: 1.12, y: 2.04, w: 4.1, h: 0.22, fontSize: 8, color: 'A8A29E', charSpace: 1, margin: 0 });
  s.addText('核心结论：华为并非单纯参与汽车制造，而是在高端智能汽车的系统层占据更高价值位。', { x: 1.12, y: 3.08, w: 3.7, h: 1.15, fontSize: 15, color: 'ECE7E1', margin: 0.02 });
  footer(s, 'EXECUTIVE PRESENTATION', true); page(s, 1, true);
}

// 2 exec summary
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '执行摘要', 'Executive summary');
  card(s, 0.86, 1.95, 10.4, 3.95, false, true);
  const pts = [
    '市场竞争正从硬件参数，转向智能体验、品牌信任与生态协同。',
    '华为的核心优势，在于座舱、智驾、终端生态与品牌触点的复合整合。',
    '若生态矩阵持续扩张，华为有机会长期占据高端智能汽车价值链上层。'
  ];
  bullets(s, pts, 1.18, 2.45, 9.5, 2.35, 17);
  s.addText('一句话结论', { x: 1.16, y: 5.1, w: 1.5, h: 0.24, fontSize: 11, bold: true, color: C.accent, margin: 0 });
  s.addText('华为卖的不只是车，而是一整套高端智能出行体验。', { x: 2.42, y: 5.05, w: 5.9, h: 0.3, fontSize: 15, color: C.body, margin: 0 });
  footer(s, 'EXECUTIVE SUMMARY'); page(s, 2);
}

// 3 thesis + hero image
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '投资判断', 'Investment thesis');
  s.addText('华为正在占据智能汽车最具溢价能力的系统层。', { x: 0.9, y: 1.92, w: 4.95, h: 0.75, fontSize: 22, bold: true, color: C.text, margin: 0.01 });
  bullets(s, [
    '高端竞争的核心，已由单点配置转向整体体验。',
    '华为的优势来自跨终端协同与系统级能力。',
    '这一模式更接近平台型放大器，而非传统整车逻辑。'
  ], 0.95, 2.95, 4.55, 2.15, 15.5);
  contain(s, IMG_COVER, 6.0, 1.92, W169_2.w, W169_2.h);
  s.addShape(pres.ShapeType.rect, { x: 5.86, y: 1.78, w: W169_2.w + 0.28, h: W169_2.h + 0.28, line: { color: C.accent, pt: 1 }, fill: { color: C.bg, transparency: 100 } });
  footer(s, 'INVESTMENT THESIS'); page(s, 3);
}

// 4 value pool
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topRule(s, true); title(s, '价值池迁移', 'Where premium value is accumulating', true);
  const items = [
    ['传统价值', '发动机、机械性能、制造效率'],
    ['迁移方向', '操作系统、辅助驾驶、交互体验'],
    ['新增价值', '生态连接、品牌信任、持续 OTA']
  ];
  let x = 0.92;
  items.forEach((it, i) => {
    card(s, x, 2.15, 3.2, 2.95, true, i===1);
    s.addText(it[0], { x: x+0.22, y: 2.48, w: 1.2, h: 0.25, fontSize: 16, bold: true, color: i===1 ? 'F0D7D9' : C.white, margin: 0 });
    s.addText(it[1], { x: x+0.22, y: 3.02, w: 2.55, h: 1.05, fontSize: 14, color: 'E5E5E5', margin: 0.02 });
    x += 3.52;
  });
  footer(s, 'VALUE POOL SHIFT', true); page(s, 4, true);
}

// 5 cockpit
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '鸿蒙座舱：体验层的关键抓手', 'Cockpit is where differentiation becomes visible');
  card(s, 0.82, 1.95, 4.85, 3.95, false, false);
  bullets(s, [
    '把车机体验拉到高端消费电子水准。',
    '多设备无缝联动，提高用户迁移成本。',
    '顺滑交互与生态延展，共同支撑品牌溢价。'
  ], 1.05, 2.35, 4.05, 2.15, 15.5);
  contain(s, IMG_DETAIL, 6.0, 2.1, W169_2.w, W169_2.h);
  s.addShape(pres.ShapeType.rect, { x: 5.86, y: 1.96, w: W169_2.w + 0.28, h: W169_2.h + 0.28, line: { color: C.line, pt: 1 }, fill: { color: C.bg, transparency: 100 } });
  footer(s, 'HARMONY COCKPIT'); page(s, 5);
}

// 6 adas
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topRule(s, true); title(s, '智能驾驶：高端溢价的第二支柱', 'ADAS is becoming a defining premium layer', true);
  contain(s, IMG_DRIVE, 0.88, 2.0, W169_1.w, W169_1.h);
  s.addShape(pres.ShapeType.rect, { x: 0.74, y: 1.86, w: W169_1.w + 0.28, h: W169_1.h + 0.28, line: { color: '3D3D3D', pt: 1 }, fill: { color: C.dark, transparency: 100 } });
  bullets(s, [
    '用户最终购买的是“安全感”和“持续可用性”。',
    '真正重要的不是单次演示，而是日常体验稳定。',
    '高阶智驾一旦建立信任，将持续抬升产品价格带。'
  ], 7.0, 2.28, 3.65, 2.45, 15.2, true);
  footer(s, 'ADVANCED DRIVING'); page(s, 6, true);
}

// 7 ecosystem
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '生态矩阵：平台故事能否变成规模故事', 'Ecosystem breadth determines scale potential');
  const cols = [
    ['问界', '当前最强的销量与认知支点'],
    ['智界', '补充年轻化与运动化定位'],
    ['享界', '切入高端商务区间'],
    ['尊界', '抬升价格与品牌天花板']
  ];
  let x = 0.86;
  cols.forEach((c, i) => {
    card(s, x, 2.0, 2.65, 2.45, false, i===0);
    s.addText(c[0], { x: x+0.22, y: 2.35, w: 1.1, h: 0.28, fontSize: 20, bold: true, color: C.text, margin: 0 });
    s.addText(c[1], { x: x+0.22, y: 2.95, w: 2.0, h: 0.75, fontSize: 13.5, color: C.body, margin: 0.01 });
    x += 2.8;
  });
  s.addText('判断标准不只是“品牌是否增加”，而是生态是否真的把系统能力转成多层级品牌势能。', { x: 0.9, y: 5.05, w: 10.0, h: 0.38, fontSize: 14.5, color: C.body, margin: 0 });
  footer(s, 'ECOSYSTEM MATRIX'); page(s, 7);
}

// 8 moat
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '护城河拆解', 'Why the advantage is systemic');
  const rows = [
    ['技术', '座舱、智驾、车云协同的系统整合能力'],
    ['品牌', '高端科技品牌心智可向汽车外溢'],
    ['渠道', '零售触点强，用户教育效率更高'],
    ['生态', '手机、IoT、服务与汽车形成联动']
  ];
  let y = 1.95;
  rows.forEach((r, i) => {
    s.addShape(pres.ShapeType.rect, { x: 0.95, y: y+0.04, w: 0.1, h: 0.32, line: { color: i===0 ? C.accent : C.line, transparency:100 }, fill: { color: i===0 ? C.accent : C.line } });
    s.addText(r[0], { x: 1.22, y, w: 0.72, h: 0.24, fontSize: 16, bold: true, color: i===0 ? C.accent : C.text, margin: 0 });
    s.addText(r[1], { x: 2.22, y: y-0.01, w: 6.4, h: 0.26, fontSize: 14.5, color: C.body, margin: 0 });
    y += 0.78;
  });
  card(s, 8.95, 1.9, 2.02, 2.95, false, true);
  s.addText('结论', { x: 9.27, y: 2.2, w: 0.8, h: 0.22, fontSize: 15, bold: true, color: C.accent, margin: 0 });
  s.addText('优势并非单点领先，而是系统层协同。', { x: 9.18, y: 2.72, w: 1.5, h: 1.0, fontSize: 13.5, color: C.body, align: 'center', valign: 'mid', margin: 0.02 });
  footer(s, 'SYSTEMIC MOAT'); page(s, 8);
}

// 9 risks
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topRule(s, true); title(s, '关键风险', 'Key risks to monitor', true);
  const risks = [
    '价格竞争若长期延续，盈利改善节奏可能放缓。',
    '生态矩阵扩张后，品牌协同与资源分配难度上升。',
    '高阶智驾仍受监管、舆论与安全事件影响。',
    '交付、供应链与市场预期管理仍需保持平衡。'
  ];
  let x = 0.9;
  risks.forEach((r, i) => {
    card(s, x, 2.2, 2.58, 2.25, true, i===0);
    s.addText('0' + (i+1), { x: x+0.22, y: 2.45, w: 0.4, h: 0.2, fontSize: 10, color: 'A8A8A8', margin: 0 });
    s.addText(r, { x: x+0.22, y: 2.9, w: 2.05, h: 1.05, fontSize: 14, color: C.white, margin: 0.02, valign: 'mid' });
    x += 2.8;
  });
  footer(s, 'RISKS'); page(s, 9, true);
}

// 10 close
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  topRule(s); title(s, '结论', 'Closing statement');
  card(s, 0.9, 1.9, 10.0, 3.65, false, false);
  s.addText('华为汽车真正值得重视的，不只是销量，而是它正在重构高端智能汽车的价值表达方式。', {
    x: 1.18, y: 2.45, w: 8.9, h: 0.98, fontSize: 23, bold: true, color: C.text, margin: 0.01, valign: 'mid'
  });
  s.addText('后续重点跟踪：生态扩张速度、智驾稳定落地、高端品牌心智形成。', { x: 1.18, y: 4.2, w: 7.8, h: 0.32, fontSize: 14.5, color: C.sub, margin: 0 });
  footer(s, 'CLOSING'); page(s, 10);
}

fs.mkdirSync(outDir, { recursive: true });
pres.writeFile({ fileName: output }).then(() => console.log(output));
