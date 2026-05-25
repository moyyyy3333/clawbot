const puppeteer = require('puppeteer-core');
const GIFEncoder = require('gif-encoder-2');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');
const OUTPUT = path.join(__dirname, 'clawbot-promo.gif');
const FRAMES_DIR = path.join(__dirname, 'frames');
const HTML_PATH = path.join(__dirname, 'clawbot-promo.html');

// Timing: when to capture each frame (in seconds from start)
const CAPTURE_POINTS = [
  { t: 0.0, label: 'welcome' },
  { t: 3.0, label: 'start_typing' },
  { t: 4.5, label: 'start_msg' },
  { t: 5.5, label: 'confirm_typing' },
  { t: 7.0, label: 'confirm_msg' },
  { t: 8.0, label: 'aws_typing' },
  { t: 9.5, label: 'aws_msg' },
  { t: 10.5, label: 'created_typing' },
  { t: 12.0, label: 'created_msg' },
  { t: 13.0, label: 'ec2_typing' },
  { t: 14.5, label: 'ec2_msg' },
  { t: 15.5, label: 'launched_typing' },
  { t: 17.0, label: 'launched_msg' },
  { t: 18.0, label: 'termius_typing' },
  { t: 19.5, label: 'termius_msg' },
  { t: 20.5, label: 'installed_typing' },
  { t: 22.0, label: 'installed_msg' },
  { t: 25.0, label: 'final_msg' },
  { t: 27.0, label: 'price_overlay' },
];

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  // Clean up
  if (fs.existsSync(FRAMES_DIR)) {
    fs.rmSync(FRAMES_DIR, { recursive: true });
  }
  fs.mkdirSync(FRAMES_DIR, { recursive: true });

  // Find Chrome
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (!fs.existsSync(chromePath)) {
    console.error('Chrome not found at', chromePath);
    process.exit(1);
  }

  console.log('Launching Chrome...');
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 393, height: 852, deviceScaleFactor: 2 });

  // Load the HTML
  console.log('Loading HTML...');
  await page.goto('file://' + HTML_PATH, { waitUntil: 'networkidle0' });

  // Wait a moment for initial render
  await sleep(1500);

  // Set animation speed to match our capture points
  // The HTML uses 0.5s delay + increments of ~2s per message
  // We'll just take screenshots at the right timings

  console.log('Capturing frames...');
  for (let i = 0; i < CAPTURE_POINTS.length; i++) {
    const pt = CAPTURE_POINTS[i];
    let waitFor = 0;
    
    if (i === 0) {
      waitFor = 0;
    } else {
      // Wait the difference in time
      waitFor = (CAPTURE_POINTS[i].t - CAPTURE_POINTS[i-1].t) * 1000;
    }

    await sleep(waitFor);
    
    const filename = String(i).padStart(3, '0') + '-' + pt.label + '.png';
    await page.screenshot({
      path: path.join(FRAMES_DIR, filename),
      clip: { x: 0, y: 0, width: 393, height: 852 },
    });
    console.log(`  Captured ${filename}`);
  }

  await browser.close();

  // Now create animated GIF from frames
  console.log('\nCreating animated GIF...');
  
  const frames = fs.readdirSync(FRAMES_DIR)
    .filter(f => f.endsWith('.png'))
    .sort();
  
  if (frames.length === 0) {
    console.error('No frames captured!');
    process.exit(1);
  }

  // Read first frame for dimensions
  const firstFrame = await sharp(path.join(FRAMES_DIR, frames[0])).metadata();
  const width = firstFrame.width;
  const height = firstFrame.height;

  // Create GIF encoder
  const encoder = new GIFEncoder(width, height, 'octree', true);
  encoder.setRepeat(0); // loop forever
  encoder.setTransparent(0x000000);
  
  const fileStream = fs.createWriteStream(OUTPUT);
  encoder.createReadStream().pipe(fileStream);

  // Frame durations (in ms) - hold each frame for 0.5s = 500ms
  // Last frame (price) held longer
  encoder.setDelay(800);

  for (let i = 0; i < frames.length; i++) {
    const framePath = path.join(FRAMES_DIR, frames[i]);
    const buffer = await sharp(framePath)
      .resize(width, height)
      .raw()
      .toBuffer();
    
    // Convert RGBA to RGB for GIF (GIF doesn't support alpha well)
    const rgb = Buffer.alloc((width * height) * 3);
    for (let j = 0; j < width * height; j++) {
      rgb[j * 3] = buffer[j * 4];       // R
      rgb[j * 3 + 1] = buffer[j * 4 + 1]; // G
      rgb[j * 3 + 2] = buffer[j * 4 + 2]; // B
    }
    
    encoder.addFrame(rgb);
    
    if (i % 5 === 0) {
      const pct = Math.round((i / frames.length) * 100);
      process.stdout.write(`\r  Encoding: ${pct}%`);
    }
  }

  encoder.finish();
  
  await new Promise(resolve => fileStream.on('close', resolve));
  
  console.log('\r  Encoding: 100%');
  
  const stats = fs.statSync(OUTPUT);
  console.log(`\n✅ GIF created: ${OUTPUT}`);
  console.log(`   Size: ${(stats.size / 1024 / 1024).toFixed(1)} MB`);
  console.log(`   Frames: ${frames.length}`);

  // Clean up frames
  fs.rmSync(FRAMES_DIR, { recursive: true });
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
