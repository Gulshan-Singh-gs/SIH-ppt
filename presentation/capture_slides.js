/**
 * Capture screenshots of all 6 slides at 1920x1080 to visually verify rendering.
 */
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, 'index.html');
const EXPORT_DIR = path.resolve(__dirname, 'export');

(async () => {
  const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: CHROME_PATH,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  for (let i = 1; i <= 6; i++) {
    const url = `file:///${HTML_PATH.replace(/\\/g, '/')}#slide-${i}`;
    await page.goto(url, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 600));

    // Force exact slide active
    await page.evaluate((slideNum) => {
      document.querySelectorAll('.slide').forEach(s => {
        const num = parseInt(s.dataset.slide, 10);
        s.classList.toggle('active', num === slideNum);
      });
    }, i);

    const outPath = path.join(EXPORT_DIR, `slide_${i}.png`);
    await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
    console.log(`Captured Slide ${i} -> ${outPath}`);
  }

  await browser.close();
  console.log('All 6 slides captured successfully!');
})();
