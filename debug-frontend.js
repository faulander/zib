const { chromium } = require('playwright');

async function debugFrontend() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Listen for console messages
  page.on('console', msg => {
    console.log(`[CONSOLE ${msg.type()}]`, msg.text());
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR]`, error.message);
    console.log(error.stack);
  });
  
  // Listen for unhandled promise rejections
  page.on('requestfailed', request => {
    console.log(`[REQUEST FAILED]`, request.url(), request.failure()?.errorText);
  });
  
  try {
    console.log('Navigating to localhost:5173...');
    await page.goto('http://localhost:5174', { waitUntil: 'networkidle' });
    console.log('Page loaded successfully');
    
    // Wait a bit to see what happens
    await page.waitForTimeout(5000);
    
    // Get the page content to see if it's actually white
    const title = await page.title();
    console.log('Page title:', title);
    
    const bodyText = await page.textContent('body');
    console.log('Body text length:', bodyText?.length || 0);
    
  } catch (error) {
    console.log('Error during navigation:', error.message);
  }
  
  console.log('Keeping browser open for inspection...');
  // Keep browser open for manual inspection
  await page.waitForTimeout(30000);
  
  await browser.close();
}

debugFrontend().catch(console.error);