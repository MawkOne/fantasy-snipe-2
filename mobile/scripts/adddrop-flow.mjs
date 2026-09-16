// Drive the Add/Drop flow end-to-end and screenshot each step.
import { chromium } from "playwright";

const base = process.argv[2] || "http://localhost:8780/";
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
});
await page.goto(base, { waitUntil: "networkidle" });
await page.waitForTimeout(2500);

// Go to Players tab
await page.click('text=Players');
await page.waitForTimeout(800);

// Click first "+ Add" button (Add is the visible text on the button)
const addButtons = page.locator('text=Add');
await addButtons.first().click();
await page.waitForTimeout(800);
await page.screenshot({ path: "flow-1-dropselect.png", fullPage: true });

// Select a drop target (David Pastrnak row)
await page.click("text=David Pastrnak").catch(() => console.log("pastrnak not found"));
await page.waitForTimeout(500);
await page.screenshot({ path: "flow-2-selected.png", fullPage: true });

// Continue
await page.click("text=Continue").catch(() => console.log("continue not found"));
await page.waitForTimeout(800);
await page.screenshot({ path: "flow-3-review.png", fullPage: true });

// Confirm
await page.click("text=Confirm Add / Drop").catch(() => console.log("confirm not found"));
await page.waitForTimeout(800);
await page.screenshot({ path: "flow-4-success.png", fullPage: true });

await browser.close();
console.log("done");
