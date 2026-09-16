import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8783/";
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});
await page.goto(base, { waitUntil: "networkidle" });
await page.waitForTimeout(2500);
await page.click("text=Matchups");
await page.waitForTimeout(800);
// Scroll to bottom for category breakdown
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
await page.waitForTimeout(500);
await page.screenshot({ path: "matchups-bottom.png", fullPage: false });
await browser.close();
console.log("done");
