const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const input = path.resolve(process.argv[2] || 'skills/pptx-generator/output/linzeqi-totoro-redesign-v3.json');
const output = path.resolve(process.argv[3] || 'skills/pptx-generator/output/linzeqi-totoro-redesign-v3.pptx');
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
  bg: cfg.theme?.bg || 'F6F1E4',
  primary: cfg.theme?.title || '1F2F1B',
  text: cfg.theme?.text || '4D5D45',
  accent: cfg.theme?.accent || 'B8742F',
  muted: cfg.theme?.muted || '6E7B60',
  panel: cfg.theme?.panel || 'E9DFC7',
  panelAlt: cfg.theme?.panelAlt || 'DCE5D6'
};

const baseDir = path.resolve('skills/pptx-generator/output');

function addImageIfExists(slide, imagePath, x, y, w, h, extra = {}) {
  if (!imagePath) return;
  const img = path.resolve(baseDir, imagePath);
  if (!fs.existsSync(img)) return;
  slide.addImage({ path: img, x, y, w, h, ...extra });
}

function addFooter(slide) {
  if (!cfg.footer) return;
  slide.addText(cfg.footer, {
    x: 0.72, y: 5.12, w: 4.8, h: 0.16,
    fontFace: 'Microsoft YaHei', fontSize: 8, color: theme.muted, margin: 0
  });
}

function addBadge(slide, n) {
  slide.addShape('roundRect', {
    x: 9.02, y: 5.02, w: 0.56, h: 0.32,
    rectRadius: 0.14,
    line: { color: theme.accent, pt: 0 },
    fill: { color: theme.accent }
  });
  slide.addText(String(n).padStart(2, '0'), {
    x: 9.04, y: 5.08, w: 0.5, h: 0.18,
    fontFace: 'Arial', fontSize: 9, bold: true, color: 'FFFFFF', align: 'center', margin: 0
  });
}

function coverV3(slide, s) {
  slide.background = { color: theme.bg };
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 5.625, line: { color: theme.bg, pt: 0 }, fill: { color: theme.bg } });
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 0.24, line: { color: theme.primary, pt: 0 }, fill: { color: theme.primary } });
  slide.addShape('roundRect', { x: 0.95, y: 0.72, w: 2.55, h: 4.18, rectRadius: 0.08, line: { color: theme.panel, pt: 0.8 }, fill: { color: theme.panel } });
  slide.addText(s.title || '', {
    x: 1.2, y: 1.02, w: 1.85, h: 0.9,
    fontFace: 'Microsoft YaHei', fontSize: 31, bold: true, color: theme.primary, margin: 0
  });
  slide.addText(s.subtitle || '', {
    x: 1.22, y: 2.1, w: 1.5, h: 0.5,
    fontFace: 'Microsoft YaHei', fontSize: 17, color: theme.text, margin: 0
  });
  slide.addShape('line', { x: 1.22, y: 2.92, w: 1.2, h: 0, line: { color: theme.accent, pt: 1.8 } });
  slide.addText(s.meta || '', {
    x: 1.24, y: 4.22, w: 1.6, h: 0.24,
    fontFace: 'Microsoft YaHei', fontSize: 9.5, color: theme.muted, margin: 0
  });
  addImageIfExists(slide, s.imagePath, 3.65, 0.62, 5.55, 4.15);
  slide.addShape('roundRect', { x: 4.15, y: 4.38, w: 4.6, h: 0.68, rectRadius: 0.14, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'FFFFFF', transparency: 18 } });
  slide.addText('“' + (s.quote || '') + '”', {
    x: 4.42, y: 4.62, w: 4.05, h: 0.18,
    fontFace: 'Microsoft YaHei', fontSize: 11.5, italic: true, color: theme.primary, margin: 0, align: 'center'
  });
}

function tocV3(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 1.0, y: 0.58, w: 2.6, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 24, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 1.04, y: 0.98, w: 5.2, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10.5, color: theme.muted, margin: 0 });
  const sections = s.sections || [];
  const startX = 1.05, startY = 1.55;
  const cardW = 2.35, cardH = 1.08, gapX = 0.36, gapY = 0.34;
  sections.forEach((sec, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const x = startX + col * (cardW + gapX);
    const y = startY + row * (cardH + gapY) + (col === 1 ? 0.1 : 0);
    const fill = i % 2 === 0 ? theme.panel : theme.panelAlt;
    const [num, label] = sec.split('｜');
    slide.addShape('roundRect', { x, y, w: cardW, h: cardH, rectRadius: 0.1, line: { color: theme.muted, pt: 0.8 }, fill: { color: fill } });
    slide.addText(num || '', { x: x + 0.18, y: y + 0.16, w: 0.56, h: 0.2, fontFace: 'Arial', fontSize: 14, bold: true, color: theme.accent, margin: 0 });
    slide.addText(label || sec, { x: x + 0.2, y: y + 0.5, w: 1.76, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 13.2, bold: true, color: theme.primary, margin: 0, fit: 'shrink' });
  });
  slide.addShape('roundRect', { x: 8.55, y: 1.62, w: 0.5, h: 2.75, rectRadius: 0.14, line: { color: theme.primary, pt: 0 }, fill: { color: theme.primary } });
  slide.addText('CHAPTER\nMAP', { x: 8.61, y: 2.26, w: 0.36, h: 0.72, fontFace: 'Arial', fontSize: 11, bold: true, color: 'FFFFFF', margin: 0, align: 'center' });
  addFooter(slide);
  addBadge(slide, idx + 1);
}

function gradeHeroV3(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('roundRect', { x: 0.95, y: 0.78, w: 3.05, h: 4.12, rectRadius: 0.08, line: { color: theme.panel, pt: 0.8 }, fill: { color: theme.panel } });
  slide.addText(s.title || '', { x: 1.18, y: 1.0, w: 2.4, h: 0.42, fontFace: 'Microsoft YaHei', fontSize: 21, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 1.2, y: 1.42, w: 2.25, h: 0.34, fontFace: 'Microsoft YaHei', fontSize: 10.2, color: theme.muted, margin: 0 });
  slide.addShape('roundRect', { x: 1.2, y: 1.86, w: 1.42, h: 0.3, rectRadius: 0.14, line: { color: theme.accent, pt: 0 }, fill: { color: theme.accent } });
  slide.addText(s.tag || '', { x: 1.28, y: 1.95, w: 1.24, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: 'FFFFFF', margin: 0, align: 'center' });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addText(runs, { x: 1.28, y: 2.28, w: 2.18, h: 1.5, fontFace: 'Microsoft YaHei', fontSize: 12, color: theme.text, paraSpaceAfterPt: 6, margin: 0 });
  slide.addShape('roundRect', { x: 1.18, y: 4.02, w: 2.28, h: 0.68, rectRadius: 0.12, line: { color: theme.bg, pt: 0.6 }, fill: { color: 'F8F4EA' } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.36, y: 4.22, w: 1.92, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0, fit: 'shrink' });
  addImageIfExists(slide, s.imagePath, 4.38, 0.78, 4.75, 4.12);
  slide.addShape('roundRect', { x: 4.64, y: 4.25, w: 4.1, h: 0.45, rectRadius: 0.12, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'FFFFFF', transparency: 18 } });
  slide.addText('成长中的一页，温柔而坚定', { x: 5.0, y: 4.38, w: 3.4, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, color: theme.primary, margin: 0, align: 'center' });
  addFooter(slide);
  addBadge(slide, idx + 1);
}

function grade4FeatureV3(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('roundRect', { x: 0.9, y: 0.82, w: 2.6, h: 3.9, rectRadius: 0.08, line: { color: theme.panel, pt: 0.8 }, fill: { color: theme.panel } });
  slide.addText('04', { x: 1.15, y: 0.98, w: 0.7, h: 0.36, fontFace: 'Arial', fontSize: 24, bold: true, color: theme.accent, margin: 0 });
  slide.addText(s.title || '', { x: 1.18, y: 1.45, w: 1.95, h: 0.56, fontFace: 'Microsoft YaHei', fontSize: 20.5, bold: true, color: theme.primary, margin: 0, fit: 'shrink' });
  slide.addText(s.subtitle || '', { x: 1.2, y: 2.14, w: 1.98, h: 0.42, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.muted, margin: 0, fit: 'shrink' });
  slide.addShape('roundRect', { x: 1.18, y: 2.7, w: 1.3, h: 0.3, rectRadius: 0.14, line: { color: theme.accent, pt: 0 }, fill: { color: theme.accent } });
  slide.addText(s.tag || '', { x: 1.24, y: 2.8, w: 1.18, h: 0.1, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: 'FFFFFF', margin: 0, align: 'center' });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.18, y: 3.32, w: 1.96, h: 0.6, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0, fit: 'shrink' });

  const cards = [
    { x: 3.85, y: 0.92, w: 2.08, h: 1.28, title: '学习状态', text: '更稳、更均衡\n能持续进入状态', fill: theme.panelAlt },
    { x: 6.18, y: 0.92, w: 2.25, h: 1.28, title: '活动实践', text: '校园活动 / 实践体验\n可替换真实照片', fill: theme.panel },
    { x: 4.05, y: 2.42, w: 1.88, h: 1.55, title: '证书占位', text: '荣誉 / 奖状 / 作品', fill: theme.panel },
    { x: 6.18, y: 2.42, w: 2.25, h: 1.55, title: '成长轨迹', text: '规划 / 总结 / 调整 / 坚持', fill: theme.panelAlt }
  ];
  cards.forEach(c => {
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.1, line: { color: theme.muted, pt: 0.8 }, fill: { color: c.fill } });
    slide.addText(c.title, { x: c.x + 0.18, y: c.y + 0.18, w: c.w - 0.3, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 12.5, bold: true, color: theme.primary, margin: 0 });
    slide.addText(c.text, { x: c.x + 0.18, y: c.y + 0.56, w: c.w - 0.36, h: c.h - 0.68, fontFace: 'Microsoft YaHei', fontSize: 9.5, color: theme.text, margin: 0, valign: 'mid', fit: 'shrink' });
  });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addShape('roundRect', { x: 3.88, y: 4.22, w: 4.55, h: 0.68, rectRadius: 0.12, line: { color: theme.panel, pt: 0.8 }, fill: { color: 'F8F4EA' } });
  slide.addText(runs, { x: 4.12, y: 4.36, w: 4.05, h: 0.34, fontFace: 'Microsoft YaHei', fontSize: 10.2, color: theme.text, margin: 0 });
  addFooter(slide);
  addBadge(slide, idx + 1);
}

function keywordsV3(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 1.0, y: 0.62, w: 2.5, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 23, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 1.04, y: 1.0, w: 5.0, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10.4, color: theme.muted, margin: 0 });
  const items = s.keywords || [];
  const cards = [
    { x: 1.2, y: 1.7, w: 2.25, h: 1.15, fill: theme.panel },
    { x: 3.82, y: 1.62, w: 2.25, h: 1.15, fill: theme.panelAlt },
    { x: 2.05, y: 3.02, w: 2.25, h: 1.15, fill: theme.panelAlt },
    { x: 4.7, y: 2.94, w: 2.25, h: 1.15, fill: theme.panel }
  ];
  cards.forEach((c, i) => {
    const [k, d] = (items[i] || '').split('｜');
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.1, line: { color: theme.muted, pt: 0.8 }, fill: { color: c.fill } });
    slide.addText(k || '', { x: c.x + 0.18, y: c.y + 0.22, w: c.w - 0.36, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 15.5, bold: true, color: theme.primary, margin: 0, align: 'center' });
    slide.addText(d || '', { x: c.x + 0.18, y: c.y + 0.58, w: c.w - 0.36, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.text, margin: 0, align: 'center' });
  });
  slide.addShape('roundRect', { x: 7.55, y: 1.58, w: 1.05, h: 2.9, rectRadius: 0.14, line: { color: theme.primary, pt: 0 }, fill: { color: theme.primary } });
  slide.addText('KEYWORDS', { x: 7.74, y: 2.52, w: 0.6, h: 0.18, fontFace: 'Arial', fontSize: 11, bold: true, color: 'FFFFFF', rotate: 90, margin: 0, align: 'center' });
  addFooter(slide);
  addBadge(slide, idx + 1);
}

function endingV3(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 1.0, y: 0.8, w: 2.2, h: 0.35, fontFace: 'Microsoft YaHei', fontSize: 24, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 1.04, y: 1.22, w: 4.2, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10.5, color: theme.muted, margin: 0 });
  slide.addShape('line', { x: 1.04, y: 1.7, w: 1.1, h: 0, line: { color: theme.accent, pt: 1.8 } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.28, y: 2.05, w: 4.95, h: 0.9, fontFace: 'Microsoft YaHei', fontSize: 21.5, italic: true, color: theme.primary, margin: 0, fit: 'shrink' });
  slide.addText(s.body || '', { x: 1.3, y: 3.3, w: 4.0, h: 0.26, fontFace: 'Microsoft YaHei', fontSize: 11.2, color: theme.text, margin: 0 });
  addImageIfExists(slide, s.imagePath, 6.0, 1.0, 3.0, 3.0, { transparency: 8 });
  slide.addShape('roundRect', { x: 5.9, y: 4.12, w: 3.2, h: 0.64, rectRadius: 0.16, line: { color: theme.panel, pt: 0.8 }, fill: { color: theme.panel } });
  slide.addText('愿你一直自由生长，始终眼里有光', { x: 6.2, y: 4.38, w: 2.6, h: 0.14, fontFace: 'Microsoft YaHei', fontSize: 8.6, color: theme.primary, margin: 0, align: 'center' });
  addFooter(slide);
  addBadge(slide, idx + 1);
}

(cfg.slides || []).forEach((s, idx) => {
  const slide = pres.addSlide();
  switch (s.type) {
    case 'cover-v3':
      coverV3(slide, s);
      break;
    case 'toc-v3':
      tocV3(slide, s, idx);
      break;
    case 'grade4-feature-v3':
      grade4FeatureV3(slide, s, idx);
      break;
    case 'keywords-v3':
      keywordsV3(slide, s, idx);
      break;
    case 'ending-v3':
      endingV3(slide, s, idx);
      break;
    default:
      gradeHeroV3(slide, s, idx);
      break;
  }
});

pres.writeFile({ fileName: output })
  .then(() => console.log('PPTX_OK ' + output))
  .catch(err => { console.error(err); process.exit(1); });
