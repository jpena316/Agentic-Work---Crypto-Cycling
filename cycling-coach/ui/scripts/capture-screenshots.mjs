// Screenshots /overview, /today, /bikes to /tmp/screenshots for visual QA.
// Precondition: `npm run dev` must already be running (this script does not
// spawn the dev server itself). Override the target with BASE_URL if the
// dev server picked a non-default port.
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:5173";
const OUT_DIR = "/tmp/screenshots";
const ROUTES = ["overview", "today", "bikes"];

mkdirSync(OUT_DIR, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

for (const route of ROUTES) {
  const url = `${BASE_URL}/${route}`;
  await page.goto(url, { waitUntil: "networkidle" });
  await page.waitForTimeout(300);
  const path = `${OUT_DIR}/${route}.png`;
  await page.screenshot({ path, fullPage: true });
  console.log(`Saved ${path}`);
}

await browser.close();
