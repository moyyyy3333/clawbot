const puppeteer = require('puppeteer-core');
const GIFEncoder = require('gif-encoder-2');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const OUTPUT = path.join(__dirname, 'clawbot-promo.gif');
const FRAMES_DIR = path.join(__dirname, 'frames');
const HTML_PATH = path.join(__dirname, 'clawbot-promo.html');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  if (fs.existsSync(FRAMES_DIR)) fs.rmSync(FRAMES_DIR, { recursive: true });
  fs.mkdirSync(FRAMES_DIR, { recursive: true });

  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (!fs.existsSync(chromePath)) { console.error('Chrome not found'); process.exit(1); }

  console.log('Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 393, height: 852, deviceScaleFactor: 2 });

  console.log('Loading HTML...');
  await page.goto('file://' + HTML_PATH, { waitUntil: 'networkidle0' });

  // Speed up animation by overriding CSS delays — 25s → 4s total
  await page.evaluate(() => {
    // Find all nth-child based delays and override to total ~4s
    const msgs = document.querySelectorAll('.msg');
    const n = msgs.length;
    const total = 4000; // 4 seconds
    const interval = total / (n + 1);
    let idx = 0;
    msgs.forEach(msg => {
      idx++;
      const delay = interval * idx;
      msg.style.animationDelay = (delay / 1000) + 's';
    });
    
    // Typing indicators
    const typings = document.querySelectorAll('.typing');
    idx = 0;
    typings.forEach(t => {
      idx++;
      const delay = interval * idx - 400;
      t.style.animationDelay = Math.max(0, delay / 1000) + 's';
    });
    
    // Overlay appears right after last message
    const overlay = document.getElementById('overlay');
    if (overlay) {
      overlay.style.animationDelay = (total / 1000 + 0.5) + 's';
    }
  });

  // Wait for animation to initialize
  await sleep(200);

  // Capture frames at high rate during the 4.5s of animation
  const CAPTURE_MS = 5500;
  const INTERVAL_MS = 50; // 50ms = 20fps
  const TOTAL_FRAMES = Math.ceil(CAPTURE_MS / INTERVAL_MS);
  
  console.log(`Capturing ${TOTAL_FRAMES} frames...`);
  
  for (let i = 0; i < TOTAL_FRAMES; i++) {
    const filename = String(i).padStart(4, '0') + '.png';
    await page.screenshot({
      path: path.join(FRAMES_DIR, filename),
      clip: { x: 0, y: 0, width: 393, height: 852 },
    });
    
    if (i % 20 === 0) process.stdout.write(`\r  ${Math.round((i / TOTAL_FRAMES) * 100)}%`);
    await sleep(INTERVAL_MS);
  }
  process.stdout.write('\r  100%\n');
  await browser.close();

  // Create GIF
  console.log('Encoding GIF...');
  const frames = fs.readdirSync(FRAMES_DIR).filter(f => f.endsWith('.png')).sort();
  const gifW = 393, gifH = 852;

  const encoder = new GIFEncoder(gifW, gifH, 'octree', false);
  encoder.setRepeat(0);
  encoder.setDelay(50);

  const fileStream = fs.createWriteStream(OUTPUT);
  encoder.createReadStream().pipe(fileStream);

  // Sample every 3rd frame (reduces file size) = ~7fps
  for (let i = 0; i < frames.length; i += 3) {
    const buffer = await sharp(path.join(FRAMES_DIR, frames[i])).raw().toBuffer();
    const rgb = Buffer.alloc(gifW * gifH * 3);
    for (let j = 0; j < gifW * gifH; j++) {
      rgb[j * 3] = buffer[j * 4];
      rgb[j * 3 + 1] = buffer[j * 4 + 1];
      rgb[j * 3 + 2] = buffer[j * 4 + 2];
    }
    encoder.addFrame(rgb);
    if (i % 90 === 0) process.stdout.write(`\r  GIF: ${Math.round((i / frames.length) * 100)}%`);
  }
  
  encoder.finish();
  await new Promise(resolve => fileStream.on('close', resolve));
  process.stdout.write('\r  GIF: 100%\n');
  
  fs.rmSync(FRAMES_DIR, { recursive: true });
  
  const stats = fs.statSync(OUTPUT);
  console.log(`\n✅ ${OUTPUT}`);
  console.log(`   ${(stats.size / 1024).toFixed(0)} KB, ${Math.ceil(TOTAL_FRAMES / 3)} frames`);
}

main().catch(e => { console.error(e); process.exit(1); });
