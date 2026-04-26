const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
const slide = pres.addSlide();
slide.background = { color: 'F7F7F7' };
slide.addText('PPTX Generator Smoke Test', {
  x: 0.5, y: 1.2, w: 9, h: 0.8,
  fontSize: 28, bold: true, color: '1F2937', align: 'center'
});
slide.addText('OpenClaw + MiniMax skill wiring is working on this machine.', {
  x: 0.8, y: 2.2, w: 8.4, h: 0.8,
  fontSize: 16, color: '374151', align: 'center'
});
slide.addText('Generated: 2026-04-26', {
  x: 3.6, y: 4.8, w: 2.8, h: 0.3,
  fontSize: 10, color: '6B7280', align: 'center'
});
pres.writeFile({ fileName: 'C:/Users/besam/.openclaw/workspace/_tmp/pptx-smoke-test.pptx' });
