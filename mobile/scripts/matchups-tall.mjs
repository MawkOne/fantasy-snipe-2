import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8786/";
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 390, height: 1600 }, // tall viewport to see full scroll content
  deviceScaleFactor: 2,
});
await page.goto(base, { waitUntil: "networkidle" });
await page.waitForTimeout(2500);
await page.click("text=Matchups");
await page.waitForTimeout(900);
await page.screenshot({ path: "matchups-tall.png", fullPage: false });
await browser.close();
console.log("done");
