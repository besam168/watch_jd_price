const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const input = path.resolve(process.argv[2] || 'skills/pptx-generator/output/linzeqi-totoro-redesign.json');
const output = path.resolve(process.argv[3] || 'skills/pptx-generator/output/linzeqi-totoro-redesign.pptx');
const cfg = JSON.parse(fs.readFileSync(input, 'utf8'));
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_WIDE';
pres.author = cfg.author || '';
pres.company = cfg.company || '';
pres.subject = cfg.subject || '';
pres.title = cfg.title || '';
pres.lang = cfg.lang || 'zh-CN';
pres.theme = { headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei', lang: 'zh-CN' };

const theme = {
  primary: cfg.theme?.title || '283618',
  secondary: cfg.theme?.text || '606C38',
  accent: cfg.theme?.accent || 'DDA15E',
  light: cfg.theme?.muted || 'A3B18A',
  bg: cfg.theme?.bg || 'FEFAE0'
};

const baseDir = path.resolve('skills/pptx-generator/output');

function addFooter(slide, text) {
  if (!text) return;
  slide.addText(text, {
    x: 0.55, y: 5.12, w: 4.4, h: 0.16,
    fontFace: 'Microsoft YaHei', fontSize: 8, color: theme.light, margin: 0
  });
}

function addPageBadge(slide, n) {
  slide.addShape('roundRect', {
    x: 9.08, y: 5.05, w: 0.48, h: 0.3,
    rectRadius: 0.12,
    line: { color: theme.accent, pt: 0 },
    fill: { color: theme.accent }
  });
  slide.addText(String(n).padStart(2, '0'), {
    x: 9.08, y: 5.08, w: 0.48, h: 0.2,
    fontFace: 'Arial', fontSize: 9, bold: true, color: 'FFFFFF', align: 'center', margin: 0
  });
}

function addImageIfExists(slide, imagePath, x, y, w, h, opts = {}) {
  if (!imagePath) return;
  const img = path.resolve(baseDir, imagePath);
  if (!fs.existsSync(img)) return;
  slide.addImage({ path: img, x, y, w, h, ...opts });
}

function renderCover(slide, s) {
  slide.background = { color: theme.bg };
  slide.addShape('rect', { x: 0, y: 0, w: 3.1, h: 5.625, line: { color: theme.primary, pt: 0 }, fill: { color: 'F4EFD9' } });
  slide.addShape('line', { x: 2.7, y: 0.55, w: 0, h: 4.45, line: { color: theme.accent, pt: 1.5 } });
  slide.addText(s.title || '', {
    x: 0.65, y: 1.0, w: 2.0, h: 0.95,
    fontFace: 'Microsoft YaHei', fontSize: 28, bold: true, color: theme.primary, margin: 0
  });
  slide.addText(s.subtitle || '', {
    x: 0.68, y: 2.08, w: 1.6, h: 0.5,
    fontFace: 'Microsoft YaHei', fontSize: 16, color: theme.secondary, margin: 0
  });
  slide.addText(s.meta || '', {
    x: 0.7, y: 4.68, w: 1.7, h: 0.22,
    fontFace: 'Microsoft YaHei', fontSize: 9, color: theme.light, margin: 0
  });
  slide.addText(s.quote || '', {
    x: 3.2, y: 4.55, w: 5.9, h: 0.35,
    fontFace: 'Microsoft YaHei', fontSize: 12, italic: true, color: theme.secondary, margin: 0, align: 'left'
  });
  addImageIfExists(slide, s.imagePath, 3.15, 0.42, 6.25, 3.8);
  slide.addShape('roundRect', {
    x: 6.9, y: 0.7, w: 2.0, h: 0.38,
    rectRadius: 0.12,
    line: { color: 'FFFFFF', transparency: 100, pt: 0 },
    fill: { color: 'FFFFFF', transparency: 25 }
  });
  slide.addText('GROWTH ALBUM · 2019—2025', {
    x: 7.08, y: 0.8, w: 1.7, h: 0.14,
    fontFace: 'Arial', fontSize: 7, bold: true, color: theme.primary, margin: 0, align: 'center'
  });
}

function renderTocCards(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.7, y: 0.55, w: 2.6, h: 0.35, fontFace: 'Microsoft YaHei', fontSize: 22, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.72, y: 0.95, w: 3.8, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  const sections = s.sections || [];
  const cardW = 2.75, cardH = 1.25;
  const startX = 0.78, startY = 1.45, gapX = 0.32, gapY = 0.35;
  sections.forEach((sec, i) => {
    const row = Math.floor(i / 3), col = i % 3;
    const x = startX + col * (cardW + gapX) + (row % 2 ? 0.08 : 0);
    const y = startY + row * (cardH + gapY);
    const fill = i % 2 === 0 ? 'F7F1DE' : 'EEF2E3';
    slide.addShape('roundRect', { x, y, w: cardW, h: cardH, rectRadius: 0.1, line: { color: theme.light, pt: 0.8 }, fill: { color: fill } });
    const parts = sec.split('｜');
    slide.addText(parts[0] || '', { x: x + 0.18, y: y + 0.16, w: 0.8, h: 0.2, fontFace: 'Arial', fontSize: 14, bold: true, color: theme.accent, margin: 0 });
    slide.addText(parts[1] || sec, { x: x + 0.18, y: y + 0.5, w: 2.15, h: 0.3, fontFace: 'Microsoft YaHei', fontSize: 13, bold: true, color: theme.primary, margin: 0 });
  });
  slide.addText(s.body || '', { x: 0.82, y: 4.85, w: 6.8, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 9, color: theme.secondary, margin: 0 });
  addFooter(slide, cfg.footer);
  addPageBadge(slide, idx + 1);
}

function renderGradeHero(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('roundRect', { x: 0.55, y: 0.55, w: 3.95, h: 4.45, rectRadius: 0.08, line: { color: 'EFE7CF', pt: 0.8 }, fill: { color: 'FBF7EA' } });
  slide.addText(s.title || '', { x: 0.82, y: 0.8, w: 3.15, h: 0.42, fontFace: 'Microsoft YaHei', fontSize: 21, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.84, y: 1.28, w: 3.0, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  slide.addShape('roundRect', { x: 0.84, y: 1.72, w: 1.95, h: 0.28, rectRadius: 0.12, line: { color: theme.accent, pt: 0 }, fill: { color: 'F3E3C7' } });
  slide.addText(s.tag || '', { x: 0.98, y: 1.8, w: 1.65, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: theme.primary, margin: 0, align: 'center' });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addText(runs, { x: 0.92, y: 2.12, w: 2.95, h: 1.52, fontFace: 'Microsoft YaHei', fontSize: 12, color: theme.secondary, paraSpaceAfterPt: 6, margin: 0 });
  slide.addShape('roundRect', { x: 0.84, y: 3.9, w: 3.1, h: 0.72, rectRadius: 0.08, line: { color: 'E7DFC5', pt: 0.6 }, fill: { color: 'F6F0DE' } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.02, y: 4.1, w: 2.72, h: 0.28, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0, align: 'left' });
  addImageIfExists(slide, s.imagePath, 4.85, 0.72, 4.25, 3.95);
  slide.addShape('roundRect', { x: 5.15, y: 4.35, w: 3.45, h: 0.46, rectRadius: 0.12, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'FFFFFF', transparency: 18 } });
  slide.addText(s.designHint || '', { x: 5.3, y: 4.48, w: 3.1, h: 0.16, fontFace: 'Microsoft YaHei', fontSize: 7.5, color: theme.primary, margin: 0, align: 'center' });
  addFooter(slide, cfg.footer);
  addPageBadge(slide, idx + 1);
}

function renderGradeCollage(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.7, y: 0.65, w: 3.2, h: 0.38, fontFace: 'Microsoft YaHei', fontSize: 23, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.72, y: 1.08, w: 3.5, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  slide.addShape('roundRect', { x: 0.72, y: 1.45, w: 2.1, h: 0.28, rectRadius: 0.12, line: { color: theme.accent, pt: 0 }, fill: { color: 'F3E3C7' } });
  slide.addText(s.tag || '', { x: 0.88, y: 1.52, w: 1.78, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: theme.primary, margin: 0, align: 'center' });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addText(runs, { x: 0.84, y: 1.95, w: 3.2, h: 1.72, fontFace: 'Microsoft YaHei', fontSize: 12, color: theme.secondary, paraSpaceAfterPt: 6, margin: 0 });
  slide.addShape('roundRect', { x: 0.82, y: 4.12, w: 3.25, h: 0.72, rectRadius: 0.08, line: { color: 'E7DFC5', pt: 0.6 }, fill: { color: 'F6F0DE' } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.02, y: 4.28, w: 2.86, h: 0.28, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0 });
  const cards = [
    { x: 4.55, y: 0.9, w: 2.1, h: 1.35, title: '学习能力', txt: '更稳、更均衡' },
    { x: 6.9, y: 1.1, w: 2.0, h: 1.2, title: '活动实践', txt: '丰富校园体验' },
    { x: 4.7, y: 2.55, w: 1.95, h: 1.3, title: '证书占位', txt: '可放荣誉证书' },
    { x: 6.85, y: 2.75, w: 2.15, h: 1.45, title: '成长轨迹', txt: '规划 / 总结 / 调整' }
  ];
  cards.forEach((c, i) => {
    const fill = i % 2 === 0 ? 'EEF2E3' : 'F7F1DE';
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.08, line: { color: theme.light, pt: 0.8 }, fill: { color: fill } });
    slide.addText(c.title, { x: c.x + 0.16, y: c.y + 0.18, w: c.w - 0.3, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 12, bold: true, color: theme.primary, margin: 0 });
    slide.addText(c.txt, { x: c.x + 0.16, y: c.y + 0.58, w: c.w - 0.3, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 9.5, color: theme.secondary, margin: 0 });
  });
  slide.addText(s.designHint || '', { x: 4.72, y: 4.56, w: 4.05, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 7.5, color: theme.light, italic: true, margin: 0, align: 'center' });
  addFooter(slide, cfg.footer);
  addPageBadge(slide, idx + 1);
}

function renderKeywords(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.72, y: 0.62, w: 2.6, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 22, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.75, y: 1.0, w: 4.6, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  const items = s.keywords || [];
  const cards = [
    { x: 0.95, y: 1.6, w: 2.6, h: 1.25, rot: -3, fill: 'F7F1DE' },
    { x: 3.95, y: 1.48, w: 2.55, h: 1.22, rot: 2, fill: 'EEF2E3' },
    { x: 1.25, y: 3.05, w: 2.55, h: 1.22, rot: 2, fill: 'EEF2E3' },
    { x: 4.25, y: 2.92, w: 2.7, h: 1.3, rot: -2, fill: 'F7F1DE' }
  ];
  cards.forEach((c, i) => {
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.08, rotate: c.rot, line: { color: theme.light, pt: 0.8 }, fill: { color: c.fill } });
    const [k, d] = (items[i] || '').split('｜');
    slide.addText(k || '', { x: c.x + 0.2, y: c.y + 0.22, w: c.w - 0.4, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 16, bold: true, color: theme.primary, margin: 0, align: 'center' });
    slide.addText(d || '', { x: c.x + 0.22, y: c.y + 0.62, w: c.w - 0.44, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.secondary, margin: 0, align: 'center' });
  });
  slide.addText(s.body || '', { x: 7.35, y: 2.05, w: 1.55, h: 1.55, fontFace: 'Microsoft YaHei', fontSize: 11, color: theme.secondary, margin: 0, valign: 'mid', fit: 'shrink' });
  addFooter(slide, cfg.footer);
  addPageBadge(slide, idx + 1);
}

function renderEnding(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.85, y: 0.85, w: 2.2, h: 0.35, fontFace: 'Microsoft YaHei', fontSize: 22, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.88, y: 1.28, w: 3.6, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10.5, color: theme.light, margin: 0 });
  slide.addShape('line', { x: 0.88, y: 1.72, w: 1.1, h: 0, line: { color: theme.accent, pt: 1.5 } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.2, y: 2.2, w: 4.5, h: 0.8, fontFace: 'Microsoft YaHei', fontSize: 20, bold: false, italic: true, color: theme.primary, margin: 0, align: 'left', valign: 'mid' });
  slide.addText(s.body || '', { x: 1.22, y: 3.45, w: 4.1, h: 0.42, fontFace: 'Microsoft YaHei', fontSize: 11.5, color: theme.secondary, margin: 0 });
  addImageIfExists(slide, s.imagePath, 6.25, 1.15, 2.75, 2.75, { transparency: 8 });
  slide.addShape('roundRect', { x: 6.05, y: 4.2, w: 2.95, h: 0.55, rectRadius: 0.14, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'F4EFD9' } });
  slide.addText('愿你永远温暖、明亮、自由生长', { x: 6.25, y: 4.4, w: 2.55, h: 0.16, fontFace: 'Microsoft YaHei', fontSize: 8.5, color: theme.primary, margin: 0, align: 'center' });
  addFooter(slide, cfg.footer);
  addPageBadge(slide, idx + 1);
}

(cfg.slides || []).forEach((s, idx) => {
  const slide = pres.addSlide();
  switch (s.type) {
    case 'cover-redesign':
      renderCover(slide, s);
      break;
    case 'toc-cards':
      renderTocCards(slide, s, idx);
      break;
    case 'grade-collage':
      renderGradeCollage(slide, s, idx);
      break;
    case 'keywords-collage':
      renderKeywords(slide, s, idx);
      break;
    case 'ending-quote':
      renderEnding(slide, s, idx);
      break;
    default:
      renderGradeHero(slide, s, idx);
      break;
  }
});

pres.writeFile({ fileName: output })
  .then(() => console.log('PPTX_OK ' + output))
  .catch(err => { console.error(err); process.exit(1); });
