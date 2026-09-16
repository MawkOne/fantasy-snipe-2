// Screenshot the exported web build at iPhone size for design review.
import { chromium } from "playwright";

const url = process.argv[2] || "http://localhost:8765/";
const out = process.argv[3] || "preview.png";

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 390, height: 844 }, // iPhone 14 size
  deviceScaleFactor: 2,
});
await page.goto(url, { waitUntil: "networkidle" });
await page.waitForTimeout(2500); // let images/fonts settle

// optional: click elements before screenshot (comma-separated)
if (process.argv[4]) {
  for (const target of process.argv[4].split(",")) {
    await page.click(`text=${target.trim()}`).catch(() => console.log(`not found: ${target}`));
    await page.waitForTimeout(500);
  }
}

await page.screenshot({ path: out, fullPage: true });
await browser.close();
console.log(`Saved ${out}`);
