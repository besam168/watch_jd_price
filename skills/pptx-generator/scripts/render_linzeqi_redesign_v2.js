const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const input = path.resolve(process.argv[2] || 'skills/pptx-generator/output/linzeqi-totoro-redesign-v2.json');
const output = path.resolve(process.argv[3] || 'skills/pptx-generator/output/linzeqi-totoro-redesign-v2.pptx');
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
  primary: cfg.theme?.title || '24351F',
  secondary: cfg.theme?.text || '5B6B50',
  accent: cfg.theme?.accent || 'D89B52',
  light: cfg.theme?.muted || '95A186',
  bg: cfg.theme?.bg || 'FDF8EE'
};

const baseDir = path.resolve('skills/pptx-generator/output');

function addPageBadge(slide, n) {
  slide.addShape('roundRect', {
    x: 9.08, y: 5.05, w: 0.5, h: 0.3,
    rectRadius: 0.14,
    line: { color: theme.primary, pt: 0 },
    fill: { color: theme.primary }
  });
  slide.addText(String(n).padStart(2, '0'), {
    x: 9.08, y: 5.08, w: 0.5, h: 0.18,
    fontFace: 'Arial', fontSize: 9, bold: true, color: 'FFFFFF', align: 'center', margin: 0
  });
}

function addFooter(slide) {
  if (!cfg.footer) return;
  slide.addText(cfg.footer, {
    x: 0.58, y: 5.12, w: 4.8, h: 0.16,
    fontFace: 'Microsoft YaHei', fontSize: 8, color: theme.light, margin: 0
  });
}

function addImageIfExists(slide, imagePath, x, y, w, h, extra = {}) {
  if (!imagePath) return;
  const img = path.resolve(baseDir, imagePath);
  if (!fs.existsSync(img)) return;
  slide.addImage({ path: img, x, y, w, h, ...extra });
}

function renderCoverV2(slide, s) {
  slide.background = { color: theme.bg };
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 5.625, line: { color: 'F6EFD9', pt: 0 }, fill: { color: theme.bg } });
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 0.22, line: { color: theme.primary, pt: 0 }, fill: { color: theme.primary } });
  slide.addShape('rect', { x: 0.68, y: 0.72, w: 2.55, h: 4.1, line: { color: 'EFE5CF', pt: 0.8 }, fill: { color: 'F7F1DE' } });
  slide.addText(s.title || '', {
    x: 0.95, y: 1.02, w: 1.7, h: 1.0,
    fontFace: 'Microsoft YaHei', fontSize: 30, bold: true, color: theme.primary, margin: 0, fit: 'shrink'
  });
  slide.addText(s.subtitle || '', {
    x: 1.0, y: 2.18, w: 1.3, h: 0.6,
    fontFace: 'Microsoft YaHei', fontSize: 17, color: theme.secondary, margin: 0
  });
  slide.addShape('line', { x: 0.98, y: 3.0, w: 0.95, h: 0, line: { color: theme.accent, pt: 1.6 } });
  slide.addText(s.meta || '', {
    x: 1.0, y: 4.18, w: 1.6, h: 0.28,
    fontFace: 'Microsoft YaHei', fontSize: 9, color: theme.light, margin: 0
  });
  addImageIfExists(slide, s.imagePath, 3.05, 0.5, 6.25, 4.2);
  slide.addShape('roundRect', { x: 6.65, y: 0.78, w: 2.2, h: 0.4, rectRadius: 0.14, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'FFFFFF', transparency: 20 } });
  slide.addText('GROWTH MEMORIES · 2019—2025', {
    x: 6.9, y: 0.9, w: 1.7, h: 0.12,
    fontFace: 'Arial', fontSize: 7.5, bold: true, color: theme.primary, margin: 0, align: 'center'
  });
  slide.addShape('roundRect', { x: 3.48, y: 4.45, w: 4.75, h: 0.62, rectRadius: 0.12, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'FFFFFF', transparency: 18 } });
  slide.addText('“' + (s.quote || '') + '”', {
    x: 3.75, y: 4.65, w: 4.15, h: 0.18,
    fontFace: 'Microsoft YaHei', fontSize: 11, italic: true, color: theme.primary, margin: 0, align: 'center'
  });
}

function renderTocV2(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.72, y: 0.55, w: 2.5, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 23, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.75, y: 0.98, w: 4.6, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  const sections = s.sections || [];
  const positions = [
    [0.95, 1.55, 'F7F1DE'], [3.45, 1.35, 'EEF2E3'], [6.1, 1.58, 'F7F1DE'],
    [1.25, 3.1, 'EEF2E3'], [3.95, 2.9, 'F7F1DE'], [6.45, 3.18, 'EEF2E3']
  ];
  sections.forEach((sec, i) => {
    const [x, y, fill] = positions[i] || [1, 1, 'F7F1DE'];
    const [num, label] = sec.split('｜');
    slide.addShape('roundRect', { x, y, w: 2.15, h: 1.05, rectRadius: 0.12, line: { color: theme.light, pt: 0.8 }, fill: { color: fill } });
    slide.addText(num || '', { x: x + 0.15, y: y + 0.14, w: 0.52, h: 0.22, fontFace: 'Arial', fontSize: 14, bold: true, color: theme.accent, margin: 0 });
    slide.addText(label || sec, { x: x + 0.18, y: y + 0.48, w: 1.62, h: 0.25, fontFace: 'Microsoft YaHei', fontSize: 13, bold: true, color: theme.primary, margin: 0, fit: 'shrink' });
  });
  slide.addShape('line', { x: 8.9, y: 1.2, w: 0, h: 3.0, line: { color: 'E7DFC9', pt: 1.2, dash: 'dash' } });
  slide.addText('Chapter\nMap', { x: 8.35, y: 2.0, w: 0.7, h: 0.7, fontFace: 'Arial', fontSize: 14, bold: true, color: theme.primary, margin: 0, align: 'center' });
  addFooter(slide);
  addPageBadge(slide, idx + 1);
}

function renderGradeHeroV2(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('roundRect', { x: 0.6, y: 0.72, w: 3.75, h: 4.25, rectRadius: 0.1, line: { color: 'ECE3CF', pt: 0.8 }, fill: { color: 'FBF7EC' } });
  slide.addText(s.title || '', { x: 0.88, y: 0.96, w: 2.95, h: 0.42, fontFace: 'Microsoft YaHei', fontSize: 20.5, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.9, y: 1.38, w: 2.98, h: 0.3, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  slide.addShape('roundRect', { x: 0.9, y: 1.8, w: 1.55, h: 0.28, rectRadius: 0.12, line: { color: theme.accent, pt: 0 }, fill: { color: 'F3E4CA' } });
  slide.addText(s.tag || '', { x: 1.0, y: 1.88, w: 1.34, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: theme.primary, margin: 0, align: 'center' });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addText(runs, { x: 0.98, y: 2.18, w: 2.95, h: 1.45, fontFace: 'Microsoft YaHei', fontSize: 12, color: theme.secondary, paraSpaceAfterPt: 6, margin: 0 });
  slide.addShape('roundRect', { x: 0.92, y: 3.95, w: 2.95, h: 0.72, rectRadius: 0.1, line: { color: 'E8DFC9', pt: 0.6 }, fill: { color: 'F5EFDE' } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.1, y: 4.14, w: 2.55, h: 0.28, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0 });
  addImageIfExists(slide, s.imagePath, 4.65, 0.65, 4.45, 4.2);
  slide.addShape('line', { x: 4.42, y: 0.9, w: 0, h: 3.8, line: { color: 'E8DFC8', pt: 1.0 } });
  addFooter(slide);
  addPageBadge(slide, idx + 1);
}

function renderGrade4FeatureV2(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('rect', { x: 0.62, y: 0.78, w: 2.85, h: 3.95, line: { color: 'EDE3CE', pt: 0.8 }, fill: { color: 'F7F1DE' } });
  slide.addText('04', { x: 0.85, y: 0.92, w: 0.9, h: 0.42, fontFace: 'Arial', fontSize: 26, bold: true, color: theme.accent, margin: 0 });
  slide.addText(s.title || '', { x: 0.88, y: 1.42, w: 2.0, h: 0.58, fontFace: 'Microsoft YaHei', fontSize: 21, bold: true, color: theme.primary, margin: 0, fit: 'shrink' });
  slide.addText(s.subtitle || '', { x: 0.9, y: 2.18, w: 2.08, h: 0.44, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0, fit: 'shrink' });
  slide.addShape('roundRect', { x: 0.9, y: 2.8, w: 1.48, h: 0.28, rectRadius: 0.12, line: { color: theme.accent, pt: 0 }, fill: { color: 'F2E2C5' } });
  slide.addText(s.tag || '', { x: 1.0, y: 2.88, w: 1.28, h: 0.12, fontFace: 'Microsoft YaHei', fontSize: 8, bold: true, color: theme.primary, align: 'center', margin: 0 });
  slide.addText('“' + (s.quote || '') + '”', { x: 0.92, y: 3.38, w: 2.1, h: 0.6, fontFace: 'Microsoft YaHei', fontSize: 10, italic: true, color: theme.primary, margin: 0, fit: 'shrink' });

  const cards = [
    { x: 3.95, y: 0.95, w: 2.1, h: 1.15, title: '学习状态', text: '更稳、更均衡\n能持续进入状态' },
    { x: 6.28, y: 0.78, w: 2.45, h: 1.42, title: '活动实践', text: '校园活动 / 实践体验\n可替换真实照片' },
    { x: 4.18, y: 2.35, w: 1.88, h: 1.52, title: '证书占位', text: '荣誉 / 奖状 / 作品' },
    { x: 6.35, y: 2.48, w: 2.32, h: 1.65, title: '成长轨迹', text: '规划\n总结\n调整\n坚持' }
  ];
  cards.forEach((c, i) => {
    const fill = i % 2 === 0 ? 'EEF2E3' : 'FBF5E8';
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.1, line: { color: theme.light, pt: 0.8 }, fill: { color: fill } });
    slide.addText(c.title, { x: c.x + 0.16, y: c.y + 0.16, w: c.w - 0.3, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 12.5, bold: true, color: theme.primary, margin: 0 });
    slide.addText(c.text, { x: c.x + 0.16, y: c.y + 0.48, w: c.w - 0.32, h: c.h - 0.58, fontFace: 'Microsoft YaHei', fontSize: 9.5, color: theme.secondary, margin: 0, valign: 'mid', fit: 'shrink' });
  });
  const runs = (s.bullets || []).map(b => ({ text: b, options: { breakLine: true, bullet: { indent: 14 } } }));
  slide.addText(runs, { x: 3.98, y: 4.38, w: 4.95, h: 0.6, fontFace: 'Microsoft YaHei', fontSize: 10.5, color: theme.secondary, paraSpaceAfterPt: 4, margin: 0 });
  addFooter(slide);
  addPageBadge(slide, idx + 1);
}

function renderKeywordsV2(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addText(s.title || '', { x: 0.72, y: 0.62, w: 2.6, h: 0.36, fontFace: 'Microsoft YaHei', fontSize: 22, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.75, y: 1.0, w: 4.8, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.light, margin: 0 });
  const items = s.keywords || [];
  const cards = [
    { x: 0.98, y: 1.72, w: 2.45, h: 1.18, rot: -3, fill: 'F7F1DE' },
    { x: 3.85, y: 1.55, w: 2.4, h: 1.16, rot: 2, fill: 'EEF2E3' },
    { x: 1.28, y: 3.08, w: 2.42, h: 1.18, rot: 2, fill: 'EEF2E3' },
    { x: 4.22, y: 2.92, w: 2.58, h: 1.25, rot: -2, fill: 'F7F1DE' }
  ];
  cards.forEach((c, i) => {
    const [k, d] = (items[i] || '').split('｜');
    slide.addShape('roundRect', { x: c.x, y: c.y, w: c.w, h: c.h, rectRadius: 0.1, rotate: c.rot, line: { color: theme.light, pt: 0.8 }, fill: { color: c.fill } });
    slide.addText(k || '', { x: c.x + 0.18, y: c.y + 0.2, w: c.w - 0.36, h: 0.22, fontFace: 'Microsoft YaHei', fontSize: 16, bold: true, color: theme.primary, align: 'center', margin: 0 });
    slide.addText(d || '', { x: c.x + 0.2, y: c.y + 0.58, w: c.w - 0.4, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10, color: theme.secondary, align: 'center', margin: 0 });
  });
  slide.addShape('line', { x: 7.6, y: 1.6, w: 0, h: 2.5, line: { color: 'E6DECA', pt: 1.2, dash: 'dash' } });
  slide.addText('KEYWORDS', { x: 7.15, y: 2.35, w: 0.9, h: 0.2, fontFace: 'Arial', fontSize: 12, bold: true, color: theme.primary, rotate: 90, margin: 0 });
  addFooter(slide);
  addPageBadge(slide, idx + 1);
}

function renderEndingV2(slide, s, idx) {
  slide.background = { color: theme.bg };
  slide.addShape('rect', { x: 0, y: 0, w: 10, h: 5.625, line: { color: theme.bg, pt: 0 }, fill: { color: theme.bg } });
  slide.addText(s.title || '', { x: 0.85, y: 0.82, w: 2.1, h: 0.35, fontFace: 'Microsoft YaHei', fontSize: 23, bold: true, color: theme.primary, margin: 0 });
  slide.addText(s.subtitle || '', { x: 0.88, y: 1.25, w: 3.9, h: 0.24, fontFace: 'Microsoft YaHei', fontSize: 10.5, color: theme.light, margin: 0 });
  slide.addShape('line', { x: 0.9, y: 1.72, w: 1.05, h: 0, line: { color: theme.accent, pt: 1.6 } });
  slide.addText('“' + (s.quote || '') + '”', { x: 1.15, y: 2.02, w: 4.8, h: 0.95, fontFace: 'Microsoft YaHei', fontSize: 21, italic: true, color: theme.primary, margin: 0, fit: 'shrink' });
  slide.addText(s.body || '', { x: 1.18, y: 3.35, w: 3.95, h: 0.32, fontFace: 'Microsoft YaHei', fontSize: 11, color: theme.secondary, margin: 0 });
  addImageIfExists(slide, s.imagePath, 6.2, 1.12, 2.9, 2.9, { transparency: 10 });
  slide.addShape('roundRect', { x: 6.0, y: 4.18, w: 3.05, h: 0.58, rectRadius: 0.16, line: { color: 'FFFFFF', transparency: 100, pt: 0 }, fill: { color: 'F6F0DE' } });
  slide.addText('愿你一直自由生长，始终眼里有光', { x: 6.25, y: 4.4, w: 2.55, h: 0.16, fontFace: 'Microsoft YaHei', fontSize: 8.5, color: theme.primary, margin: 0, align: 'center' });
  slide.addShape('line', { x: 8.95, y: 0.95, w: 0, h: 3.2, line: { color: 'E6DEC9', pt: 1.0, dash: 'dash' } });
  slide.addText('END', { x: 8.55, y: 2.1, w: 0.7, h: 0.18, fontFace: 'Arial', fontSize: 12, bold: true, color: theme.primary, rotate: 90, margin: 0, align: 'center' });
  addFooter(slide);
  addPageBadge(slide, idx + 1);
}

(cfg.slides || []).forEach((s, idx) => {
  const slide = pres.addSlide();
  switch (s.type) {
    case 'cover-v2':
      renderCoverV2(slide, s);
      break;
    case 'toc-v2':
      renderTocV2(slide, s, idx);
      break;
    case 'grade4-feature-v2':
      renderGrade4FeatureV2(slide, s, idx);
      break;
    case 'keywords-v2':
      renderKeywordsV2(slide, s, idx);
      break;
    case 'ending-v2':
      renderEndingV2(slide, s, idx);
      break;
    default:
      renderGradeHeroV2(slide, s, idx);
      break;
  }
});

pres.writeFile({ fileName: output })
  .then(() => console.log('PPTX_OK ' + output))
  .catch(err => { console.error(err); process.exit(1); });
