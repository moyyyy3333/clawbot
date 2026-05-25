const puppeteer = require('puppeteer-core');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const FRAMES_DIR = path.join(__dirname, 'frames');
const HTML_PATH = path.join(__dirname, 'clawbot-promo.html');
const OUTPUT = path.join(__dirname, 'clawbot-promo.mp4');
const FFMPEG = '/tmp/ffmpeg';

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

  // Speed up animation to run in ~4s
  await page.evaluate(() => {
    const msgs = document.querySelectorAll('.msg, .typing');
    const total = 4000, interval = total / (msgs.length + 2);
    msgs.forEach((m, i) => m.style.animationDelay = ((i + 1) * interval / 1000) + 's');
    
    // Move overlay timing
    const overlay = document.getElementById('overlay');
    if (overlay) overlay.style.animationDelay = ((total + 500) / 1000) + 's';
    
    // Speed up the typing animation
    const style = document.createElement('style');
    style.textContent = `
      .typing span { animation-duration: 0.6s !important; }
      @keyframes popIn { 0% { opacity: 0; transform: translateY(8px); } 100% { opacity: 1; transform: translateY(0); } }
      @keyframes showOverlay { 0% { opacity: 0; } 100% { opacity: 1; } }
    `;
    document.head.appendChild(style);
  });

  await sleep(300);

  // Take screenshots at a smoother rate
  const DURATION = 6000; // 6 seconds total
  const FPS = 12;
  const TOTAL_FRAMES = DURATION / 1000 * FPS;
  const INTERVAL = 1000 / FPS;

  console.log(`Capturing ${TOTAL_FRAMES} frames @ ${FPS}fps...`);

  for (let i = 0; i < TOTAL_FRAMES; i++) {
    const filename = String(i).padStart(4, '0') + '.png';
    await page.screenshot({
      path: path.join(FRAMES_DIR, filename),
      clip: { x: 0, y: 0, width: 393, height: 852 },
    });
    if (i % 12 === 0) process.stdout.write(`\r  ${Math.round((i / TOTAL_FRAMES) * 100)}%`);
    await sleep(INTERVAL);
  }
  process.stdout.write('\r  100%\n');
  await browser.close();

  // Create MP4 with ffmpeg
  console.log('Encoding MP4...');
  execSync(
    `${FFMPEG} -y -framerate 12 -i ${FRAMES_DIR}/%04d.png ` +
    `-c:v libx264 -pix_fmt yuv420p -vf "scale=786:1704:flags=lanczos" ` +
    `-b:v 2M -maxrate 2M -bufsize 4M -movflags +faststart ` +
    `"${OUTPUT}"`,
    { stdio: 'inherit' }
  );
  
  // Also create a shorter 30-second looping version
  console.log('Creating looping version...');
  execSync(
    `${FFMPEG} -y -stream_loop 2 -i "${OUTPUT}" -c copy -t 18 -movflags +faststart "${OUTPUT.replace('.mp4', '-loop.mp4')}"`,
    { stdio: 'inherit', timeout: 30000 }
  );

  fs.rmSync(FRAMES_DIR, { recursive: true });

  const stats = fs.statSync(OUTPUT);
  console.log(`\n✅ MP4: ${OUTPUT} (${(stats.size / 1024 / 1024).toFixed(1)} MB)`);
}

main().catch(e => { console.error('Error:', e); process.exit(1); });
