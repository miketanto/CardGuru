// Render a replay_studio page to video with headless Chromium.
//
// mage-bench records a live JavaFX observer through FFmpeg; we render the
// finished game from its log instead: the page is opened at 1920x1080 in
// presentation mode, Playwright's built-in recorder captures the tab, and
// the script steps the replay's own API (window.__replay) so every frame
// is shown for the duration the page assigns it (searches and plans
// linger, auto-passes are skipped). Output is WebM (VP8), which YouTube
// accepts directly; convert with ffmpeg if you want MP4.
//
// Usage:
//   NODE_PATH=./node_modules node benchmark/replay_video.js --html replay.html --out replay.webm \
//        [--speed 1] [--max-frames N] [--chromium /path/to/chrome]
// Needs `npm install playwright` (browser download can be skipped when a
// Chromium is passed with --chromium or PLAYWRIGHT_BROWSERS_PATH is set).
// Export the page with --images-dir/--embed-images (fetch_card_images.py)
// so the capture does not depend on Scryfall; the recorder waits for the
// board's images before each frame's clock starts (window.__replay.ready).
const path = require('path');
const fs = require('fs');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : def;
}

(async () => {
  const { chromium } = require('playwright');
  const html = path.resolve(arg('html'));
  const out = path.resolve(arg('out', 'replay.webm'));
  const speed = parseFloat(arg('speed', '1'));
  const maxFrames = parseInt(arg('max-frames', '0'), 10);
  const exe = arg('chromium', process.env.CHROMIUM_PATH || undefined);
  if (!fs.existsSync(html)) throw new Error('no such file: ' + html);

  const tmpDir = fs.mkdtempSync(path.join(path.dirname(out), '.rec-'));
  const browser = await chromium.launch(exe ? { executablePath: exe } : {});
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: tmpDir, size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();
  await page.goto('file://' + html + '?present=1');
  await page.waitForTimeout(1500);           // first paint
  const ready = () => page.evaluate(() => window.__replay.ready ? window.__replay.ready() : null);
  await page.evaluate((s) => { document.getElementById('speed').value = String(s); }, speed);
  const total = await page.evaluate(() => window.__replay.total);
  let shown = 0;
  await page.evaluate(() => window.__replay.goto(0, false));
  await ready();                              // card images (Scryfall / cache) before the clock starts
  await page.waitForTimeout(await page.evaluate(() => window.__replay.duration()));
  while (true) {
    const i = await page.evaluate(() => window.__replay.next());
    if (i === null) break;
    shown++;
    await ready();
    const ms = await page.evaluate(() => window.__replay.duration());
    await page.waitForTimeout(ms);
    if (shown % 25 === 0) process.stderr.write(`  frame ${i + 1}/${total}\n`);
    if (maxFrames && shown >= maxFrames) break;
  }
  await page.waitForTimeout(1500);
  const video = page.video();
  await context.close();
  const recorded = await video.path();
  fs.renameSync(recorded, out);
  fs.rmSync(tmpDir, { recursive: true, force: true });
  await browser.close();
  console.log(`wrote ${out} (${shown} frames shown of ${total})`);
})().catch((e) => { console.error(e); process.exit(1); });
