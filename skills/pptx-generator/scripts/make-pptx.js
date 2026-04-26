const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function ensureDirForFile(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function asArray(v) {
  return Array.isArray(v) ? v : [];
}

function normText(v, fallback = '') {
  if (v === undefined || v === null) return fallback;
  return String(v);
}

function parseMarkdownToSpec(text) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  const slides = [];
  let current = null;
  let deckTitle = '';

  function pushCurrent() {
    if (current) {
      current.body = (current.bodyLines || []).join('\n').trim();
      delete current.bodyLines;
      slides.push(current);
    }
  }

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;

    if (line.startsWith('# ')) {
      if (!deckTitle) deckTitle = line.slice(2).trim();
      else {
        pushCurrent();
        current = { title: line.slice(2).trim(), bullets: [], bodyLines: [] };
      }
      continue;
    }

    if (line.startsWith('## ')) {
      pushCurrent();
      current = { title: line.slice(3).trim(), bullets: [], bodyLines: [] };
      continue;
    }

    if (!current) {
      current = { title: deckTitle || 'Untitled', bullets: [], bodyLines: [] };
    }

    if (line.startsWith('- ') || line.startsWith('* ')) {
      current.bullets.push(line.slice(2).trim());
    } else {
      current.bodyLines.push(line);
    }
  }

  pushCurrent();

  if (!slides.length) {
    slides.push({ title: deckTitle || 'Untitled', bullets: [], body: text.trim() });
  }

  return {
    title: deckTitle || slides[0]?.title || 'Untitled Presentation',
    slides: slides.map((s, idx) => ({
      title: s.title || `Slide ${idx + 1}`,
      bullets: s.bullets || [],
      body: s.body || ''
    }))
  };
}

function loadSpec(inputPath) {
  const ext = path.extname(inputPath).toLowerCase();
  if (ext === '.json') return readJson(inputPath);
  if (ext === '.md' || ext === '.markdown' || ext === '.txt') {
    return parseMarkdownToSpec(fs.readFileSync(inputPath, 'utf8'));
  }
  throw new Error(`Unsupported input type: ${ext}`);
}

async function main() {
  const inputPath = process.argv[2];
  const outputPath = process.argv[3];
  if (!inputPath || !outputPath) {
    console.error('Usage: node make-pptx.js <input.(json|md|txt)> <output.pptx>');
    process.exit(2);
  }

  const spec = loadSpec(inputPath);
  const pptx = new pptxgen();
  pptx.layout = spec.layout || 'LAYOUT_WIDE';
  pptx.author = spec.author || 'OpenClaw';
  pptx.company = spec.company || 'OpenClaw';
  pptx.subject = spec.subject || '';
  pptx.title = spec.title || 'Untitled Presentation';
  pptx.lang = spec.lang || 'zh-CN';
  pptx.theme = {
    headFontFace: 'Microsoft YaHei',
    bodyFontFace: 'Microsoft YaHei',
    lang: 'zh-CN'
  };

  const theme = {
    bg: spec.theme?.bg || 'F7F7F7',
    title: spec.theme?.title || '111827',
    text: spec.theme?.text || '374151',
    accent: spec.theme?.accent || '2563EB',
    muted: spec.theme?.muted || '6B7280'
  };

  const slides = asArray(spec.slides);
  for (const slideSpec of slides) {
    const slide = pptx.addSlide();
    slide.background = { color: slideSpec.background || theme.bg };

    slide.addShape(pptx.ShapeType.rect, {
      x: 0.4, y: 0.35, w: 0.18, h: 5.4,
      line: { color: theme.accent, transparency: 100 },
      fill: { color: theme.accent }
    });

    slide.addText(normText(slideSpec.title, ''), {
      x: 0.8, y: 0.5, w: 8.4, h: 0.6,
      fontSize: slideSpec.titleFontSize || 24,
      bold: true,
      color: theme.title,
      margin: 0
    });

    const subtitle = normText(slideSpec.subtitle, '');
    if (subtitle) {
      slide.addText(subtitle, {
        x: 0.82, y: 1.05, w: 8.2, h: 0.4,
        fontSize: 10,
        color: theme.muted,
        margin: 0
      });
    }

    const bullets = asArray(slideSpec.bullets);
    let y = subtitle ? 1.55 : 1.35;
    if (bullets.length) {
      const runs = [];
      bullets.forEach((b) => {
        runs.push({ text: `${normText(b)}\n`, options: { bullet: { indent: 14 } } });
      });
      slide.addText(runs, {
        x: 0.95, y, w: 8.0, h: Math.min(3.5, 0.45 * bullets.length + 0.4),
        fontSize: 16,
        color: theme.text,
        breakLine: false,
        paraSpaceAfterPt: 10,
        valign: 'top',
        margin: 0.03
      });
      y += Math.min(3.5, 0.45 * bullets.length + 0.5);
    }

    const body = normText(slideSpec.body, '');
    if (body) {
      slide.addText(body, {
        x: 0.95, y, w: 8.0, h: 1.6,
        fontSize: 14,
        color: theme.text,
        valign: 'top',
        margin: 0.03
      });
    }

    const footer = normText(slideSpec.footer, spec.footer || '');
    if (footer) {
      slide.addText(footer, {
        x: 0.8, y: 5.05, w: 8.2, h: 0.25,
        fontSize: 9,
        color: theme.muted,
        align: 'right',
        margin: 0
      });
    }
  }

  ensureDirForFile(outputPath);
  await pptx.writeFile({ fileName: outputPath });
  console.log(outputPath);
}

main().catch((err) => {
  console.error(err?.stack || String(err));
  process.exit(1);
});
