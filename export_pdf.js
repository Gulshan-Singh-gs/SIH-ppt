/**
 * Sovereign AI Workbench — High-Quality PDF Exporter
 * Uses Puppeteer to render all 12 slides at 1920×1080 and export as PDF.
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const HTML_FILE = path.resolve(__dirname, 'index.html');
const OUTPUT_PDF = path.resolve(__dirname, 'output', 'Sovereign_AI_Workbench_Presentation.pdf');
const TOTAL_SLIDES = 12;

// Ensure output dir exists
const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

(async () => {
    console.log('\n🚀 Sovereign AI Workbench — PDF Exporter\n');
    console.log(`📄 Source : ${HTML_FILE}`);
    console.log(`📁 Output : ${OUTPUT_PDF}\n`);

    // Use environment variable CHROME_PATH or default platform paths
    const defaultChromePaths = [
        process.env.CHROME_PATH,
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    ].filter(Boolean);

    let CHROME_PATH = defaultChromePaths.find(p => fs.existsSync(p));

    const launchOptions = {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--allow-file-access-from-files',
            '--disable-features=VizDisplayCompositor',
            '--force-device-scale-factor=2'
        ]
    };

    if (CHROME_PATH) {
        launchOptions.executablePath = CHROME_PATH;
    }

    const browser = await puppeteer.launch(launchOptions);
    const page = await browser.newPage();

    // Set high-res viewport: 1920×1080 (16:9 full HD)
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });

    // Load the HTML file
    await page.goto(`file:///${HTML_FILE.replace(/\\/g, '/')}`, {
        waitUntil: 'networkidle0',
        timeout: 30000
    });

    // Wait for fonts and wave canvas to initialise
    await new Promise(r => setTimeout(r, 2000));

    const slideScreenshots = [];

    for (let i = 0; i < TOTAL_SLIDES; i++) {
        console.log(`  📸 Capturing Slide ${i + 1} / ${TOTAL_SLIDES}...`);

        // Navigate to this slide via JS & update full UI (title, counter, progress bar, colors)
        await page.evaluate((idx, total) => {
            const slides = document.querySelectorAll('.slide');
            slides.forEach((s, si) => {
                s.classList.toggle('active', si === idx);
                s.style.opacity = si === idx ? '1' : '0';
                s.style.pointerEvents = si === idx ? 'auto' : 'none';
            });
            const activeSlide = slides[idx];
            if (activeSlide) {
                // Update nav slide title
                const navTitle = document.getElementById('navSlideTitle');
                if (navTitle) navTitle.textContent = activeSlide.dataset.title || '';

                // Update counter
                const counter = document.querySelector('.slide-counter');
                if (counter) counter.textContent = `${idx + 1} / ${total}`;

                // Update progress bar
                const fill = document.querySelector('.progress-fill');
                const pct = ((idx + 1) / total) * 100;
                if (fill) fill.style.width = `${pct}%`;

                // Update accent color & wave opacity
                const accentMap = {
                    'amber': '#f59e0b', 'blue': '#5b6cf9', 'red': '#ef4444',
                    'green': '#10b981', 'purple': '#8b5cf6', 'gold': '#f59e0b', 'electric': '#3b82f6'
                };
                const waveOpacities = [0.75,0.55,0.60,0.50,0.55,0.45,0.45,0.50,0.45,0.60,0.80,0.65];
                const accentKey = activeSlide.dataset.accent || 'blue';
                const color = accentMap[accentKey] || '#5b6cf9';
                document.documentElement.style.setProperty('--slide-accent', color);
                if (fill) fill.style.background = color;

                const canvas = document.getElementById('waveCanvas');
                if (canvas) canvas.style.opacity = waveOpacities[idx] || 0.6;
            }
        }, i, TOTAL_SLIDES);

        await new Promise(r => setTimeout(r, 800));

        const screenshotPath = path.join(outputDir, `slide_${String(i + 1).padStart(2, '0')}.png`);
        await page.screenshot({
            path: screenshotPath,
            fullPage: false,
            type: 'png',
            clip: { x: 0, y: 0, width: 1920, height: 1080 }
        });
        slideScreenshots.push(screenshotPath);
        console.log(`    ✓ Saved: ${path.basename(screenshotPath)}`);
    }

    await browser.close();
    console.log(`\n✅ All ${TOTAL_SLIDES} slides captured as PNG.\n`);

    console.log('📑 Assembling PDF from slide images...\n');

    const browser2 = await puppeteer.launch(launchOptions);
    const page2 = await browser2.newPage();

    const imgTags = slideScreenshots.map((p, i) => {
        const absPath = p.replace(/\\/g, '/');
        return `
        <div class="pdf-slide">
            <img src="file:///${absPath}" alt="Slide ${i + 1}" />
        </div>`;
    }).join('\n');

    const assemblyHtml = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"/>
<style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background:#000; }
    .pdf-slide {
        width: 297mm;
        height: 167.0625mm;
        page-break-after: always;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #e4e9f2;
    }
    .pdf-slide:last-child { page-break-after: avoid; }
    .pdf-slide img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    @page {
        size: 297mm 167.0625mm landscape;
        margin: 0;
    }
</style>
</head><body>${imgTags}</body></html>`;

    const assemblyPath = path.join(outputDir, '_assembly.html');
    fs.writeFileSync(assemblyPath, assemblyHtml);

    await page2.goto(`file:///${assemblyPath.replace(/\\/g, '/')}`, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 1500));

    await page2.pdf({
        path: OUTPUT_PDF,
        width: '297mm',
        height: '167.0625mm',
        printBackground: true,
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });

    await browser2.close();

    fs.unlinkSync(assemblyPath);
    slideScreenshots.forEach(p => { try { fs.unlinkSync(p); } catch(_) {} });

    const stats = fs.statSync(OUTPUT_PDF);
    const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);

    console.log(`\n🎉 PDF exported successfully!`);
    console.log(`   📄 File : ${OUTPUT_PDF}`);
    console.log(`   📦 Size : ${sizeMB} MB`);
    console.log(`   📐 Format: A4 Landscape (16:9 — 297×167mm)`);
    console.log(`   🖼️  Quality: 2× Retina (3840×2160 source render)\n`);

})().catch(err => {
    console.error('\n❌ Export failed:', err.message);
    process.exit(1);
});
