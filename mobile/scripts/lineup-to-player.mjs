// Verify tapping a Lineup player row opens Player Detail.
import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8782/";
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});
await page.goto(base, { waitUntil: "networkidle" });
await page.waitForTimeout(2500);

// Tap Bobrovsky (a goalie with real detail data)
await page.click("text=S. Bobrovsky").catch(() => console.log("bobrovsky not found"));
await page.waitForTimeout(900);
await page.screenshot({ path: "lineup-tap-goalie.png", fullPage: true });

await browser.close();
console.log("done");
