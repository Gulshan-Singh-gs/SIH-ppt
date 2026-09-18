/**
 * Sovereign AI Workbench — Smart India Hackathon Presentation Exporter
 * Generates an exact 6-page 1920x1080 PDF using Puppeteer.
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_PATH = path.resolve(__dirname, 'index.html');
const EXPORT_DIR = path.resolve(__dirname, 'export');
const OUTPUT_PDF = path.join(EXPORT_DIR, 'Sovereign_AI_Workbench_SIH_PSC26117_Deck.pdf');

// Ensure export directory exists
if (!fs.existsSync(EXPORT_DIR)) {
  fs.mkdirSync(EXPORT_DIR, { recursive: true });
}

async function exportDeck() {
  console.log('============================================================');
  console.log('🚀 SOVEREIGN AI WORKBENCH — SIH PRESENTATION PDF EXPORTER');
  console.log('============================================================');
  console.log(`📄 Source HTML : ${HTML_PATH}`);
  console.log(`📁 Target PDF  : ${OUTPUT_PDF}`);

  let browser;
  try {
    // Try system Chrome first, fallback to bundled Puppeteer Chromium
    const possibleChromePaths = [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      process.env.CHROME_PATH
    ].filter(Boolean);

    let executablePath = possibleChromePaths.find(p => fs.existsSync(p));

    const launchOptions = {
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security',
        '--allow-file-access-from-files',
        '--force-device-scale-factor=1.5'
      ]
    };

    if (executablePath) {
      console.log(`🔍 Using system Chrome: ${executablePath}`);
      launchOptions.executablePath = executablePath;
    } else {
      console.log('🔍 Using Puppeteer default Chromium...');
    }

    browser = await puppeteer.launch(launchOptions);
    const page = await browser.newPage();

    // Set 1920x1080 viewport
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });

    // Open index.html
    const fileUrl = `file:///${HTML_PATH.replace(/\\/g, '/')}`;
    console.log(`🌐 Navigating to ${fileUrl}...`);
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

    // Wait for fonts and styles to settle
    await new Promise(r => setTimeout(r, 1500));

    // Emulate print media
    await page.emulateMediaType('print');

    console.log('🖨️  Rendering PDF (1920x1080 logical pixels per slide)...');
    await page.pdf({
      path: OUTPUT_PDF,
      width: '1920px',
      height: '1080px',
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' }
    });

    console.log(`✅ PDF successfully generated at:\n   ${OUTPUT_PDF}\n`);

    // Verify PDF page count
    const stats = fs.statSync(OUTPUT_PDF);
    console.log(`📊 Output File Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);

    // Quick regex scan for page count in PDF stream
    const pdfBuffer = fs.readFileSync(OUTPUT_PDF);
    const pdfText = pdfBuffer.toString('binary');
    const pageMatches = pdfText.match(/\/Type\s*\/Page\b/g);
    const pageCount = pageMatches ? pageMatches.length : 'Unknown';
    console.log(`📑 Validated Slide/Page Count: ${pageCount} (Expected: 6)`);

    if (pageCount === 6) {
      console.log('🎯 SUCCESS: Verified exact 6-page SIH presentation deck requirement!');
    } else {
      console.log(`⚠️  Notice: Detected ${pageCount} pages. Verify visual rendering.`);
    }

    console.log('============================================================\n');
  } catch (err) {
    console.error('❌ PDF Export Error:', err);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
}

exportDeck();
