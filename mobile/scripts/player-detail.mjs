// Screenshot the player detail screens directly by route.
import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8781/";
const browser = await chromium.launch();

for (const route of ["player/matthews", "player/demko"]) {
  const page = await browser.newPage({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
  });
  await page.goto(base + route, { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `detail-${route.split("/")[1]}.png`, fullPage: true });
  await page.close();
  console.log("saved", route);
}

await browser.close();
console.log("done");
