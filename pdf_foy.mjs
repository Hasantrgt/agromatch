import { chromium } from 'playwright';

const isler = [
  ['foy/kutu_foyu.html', '/home/claude/AGROMATCH_Kutu_Foyu.pdf', '/tmp/kutu'],
  ['foy/kalibrasyon_karti.html', '/home/claude/AGROMATCH_Kalibrasyon_Karti.pdf', '/tmp/kart'],
];

const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
for (const [kaynak, pdf, png] of isler) {
  const p = await b.newPage({ viewport: { width: 794, height: 1123 } });
  await p.goto(`file:///home/claude/agromatch/${kaynak}`, { waitUntil: 'load' });
  await p.waitForTimeout(400);
  const h = await p.evaluate(() => document.body.scrollHeight);
  console.log(kaynak, 'yükseklik:', h, 'px =', (h / 1123).toFixed(2), 'sayfa');
  await p.pdf({ path: pdf, format: 'A4', printBackground: true,
    margin: { top: '0mm', bottom: '0mm', left: '0mm', right: '0mm' } });
  await p.screenshot({ path: `${png}.png`, fullPage: true });
  await p.close();
}
await b.close();
