const puppeteer = require('puppeteer-core');
const path = require('path');
const { execSync } = require('child_process');

const HTML_PATH = path.join(__dirname, 'profile-avatar.html');
const OUTPUT = path.join(__dirname, 'profile-pic.png');
const OUTPUT_SMALL = path.join(__dirname, 'profile-pic-400.png');

async function main() {
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (!fs.existsSync(chromePath)) { console.error('Chrome not found'); process.exit(1); }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 600, height: 600, deviceScaleFactor: 2 });

  console.log('Loading avatar...');
  await page.goto('file://' + HTML_PATH, { waitUntil: 'networkidle0' });

  // Wait for animations to settle at a good frame
  await sleep(1500);

  // Screenshot just the avatar element (400x400)
  const avatar = await page.$('.avatar');
  
  console.log('Capturing at 2x...');
  await avatar.screenshot({
    path: OUTPUT,
    omitBackground: false,
  });

  // Also capture at 400x400 (resize via ffmpeg)
  const ffmpeg = '/tmp/ffmpeg';
  execSync(
    `${ffmpeg} -y -i "${OUTPUT}" -vf "scale=400:400:flags=lanczos" "${OUTPUT_SMALL}"`,
    { stdio: 'ignore' }
  );

  await browser.close();

  const stats = fs.statSync(OUTPUT);
  const statsSmall = fs.statSync(OUTPUT_SMALL);
  console.log(`\n✅ High-res: ${OUTPUT} (${(stats.size / 1024).toFixed(0)} KB)`);
  console.log(`✅ 400x400: ${OUTPUT_SMALL} (${(statsSmall.size / 1024).toFixed(0)} KB)`);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
const fs = require('fs');
main().catch(e => { console.error(e); process.exit(1); });
