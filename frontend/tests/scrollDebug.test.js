import { test, expect } from '@playwright/test';

test.describe('Debug Scroll Tracker', () => {
  test('analyze intersection observer behavior in article list', async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for app to load - wait for any article to appear
    await page.waitForSelector('article', { timeout: 30000 });
    console.log('✅ App loaded, articles visible');
    
    // Wait a bit more for everything to settle
    await page.waitForTimeout(2000);
    
    // Enable console logging
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ScrollTracker]') || text.includes('[DEBUG')) {
        console.log('📋 Browser:', text);
      }
    });
    
    // Find ALL potential scrollable containers
    const allContainers = await page.evaluate(() => {
      const results = [];
      
      // Check main element
      const main = document.querySelector('main');
      if (main) {
        results.push({
          selector: 'main',
          className: main.className,
          scrollHeight: main.scrollHeight,
          clientHeight: main.clientHeight,
          isScrollable: main.scrollHeight > main.clientHeight,
          hasArticles: !!main.querySelector('article')
        });
      }
      
      // Check all elements with overflow classes
      const overflowElements = document.querySelectorAll('[class*="overflow"]');
      overflowElements.forEach((el, index) => {
        const computed = window.getComputedStyle(el);
        results.push({
          selector: `overflow-element-${index}`,
          className: el.className,
          scrollHeight: el.scrollHeight,
          clientHeight: el.clientHeight,
          overflowY: computed.overflowY,
          isScrollable: el.scrollHeight > el.clientHeight,
          hasArticles: !!el.querySelector('article')
        });
      });
      
      // Check the actual article list container
      const articleContainer = document.querySelector('.divide-y')?.parentElement;
      if (articleContainer) {
        results.push({
          selector: 'article-container-parent',
          className: articleContainer.className,
          scrollHeight: articleContainer.scrollHeight,
          clientHeight: articleContainer.clientHeight,
          isScrollable: articleContainer.scrollHeight > articleContainer.clientHeight,
          hasArticles: true
        });
      }
      
      return results;
    });
    
    console.log('📦 All potential scroll containers:', allContainers);
    
    // Find the actual scrollable container with articles
    const scrollableContainer = await page.evaluate(() => {
      // Try different strategies to find the scrollable element
      
      // Strategy 1: Find the parent of .divide-y that's scrollable
      const divideY = document.querySelector('.divide-y');
      if (divideY) {
        let parent = divideY.parentElement;
        while (parent) {
          if (parent.scrollHeight > parent.clientHeight) {
            return {
              found: true,
              strategy: 'divide-y parent',
              selector: parent.className || parent.tagName,
              scrollHeight: parent.scrollHeight,
              clientHeight: parent.clientHeight,
              scrollTop: parent.scrollTop
            };
          }
          parent = parent.parentElement;
        }
      }
      
      // Strategy 2: Find main element if it's scrollable
      const main = document.querySelector('main');
      if (main && main.scrollHeight > main.clientHeight) {
        return {
          found: true,
          strategy: 'main element',
          selector: 'main',
          scrollHeight: main.scrollHeight,
          clientHeight: main.clientHeight,
          scrollTop: main.scrollTop
        };
      }
      
      // Strategy 3: Find any overflow-y-auto that contains articles
      const overflowElements = document.querySelectorAll('[class*="overflow-y-auto"]');
      for (const el of overflowElements) {
        if (el.querySelector('article') && el.scrollHeight > el.clientHeight) {
          return {
            found: true,
            strategy: 'overflow-y-auto',
            selector: el.className,
            scrollHeight: el.scrollHeight,
            clientHeight: el.clientHeight,
            scrollTop: el.scrollTop
          };
        }
      }
      
      return { found: false, message: 'No scrollable container found' };
    });
    
    console.log('🎯 Scrollable container search result:', scrollableContainer);
    
    if (!scrollableContainer.found) {
      console.log('⚠️ No scrollable container found. The content might fit in the viewport.');
      console.log('Let\'s check the viewport and article dimensions...');
      
      const dimensions = await page.evaluate(() => {
        const articles = document.querySelectorAll('article');
        const firstArticle = articles[0];
        const lastArticle = articles[articles.length - 1];
        
        return {
          viewportHeight: window.innerHeight,
          bodyHeight: document.body.scrollHeight,
          articlesCount: articles.length,
          firstArticleTop: firstArticle?.getBoundingClientRect().top,
          lastArticleBottom: lastArticle?.getBoundingClientRect().bottom,
          totalArticleHeight: lastArticle?.getBoundingClientRect().bottom - firstArticle?.getBoundingClientRect().top
        };
      });
      
      console.log('📏 Dimensions:', dimensions);
    }
    
    // Inject our debug code
    await page.evaluate(() => {
      console.log('[DEBUG] Injecting intersection observer debug code...');
      
      // Store original IntersectionObserver
      const OriginalIO = window.IntersectionObserver;
      let observerCount = 0;
      
      // Replace with debug version
      window.IntersectionObserver = class DebugIO extends OriginalIO {
        constructor(callback, options) {
          observerCount++;
          const id = observerCount;
          
          console.log(`[DEBUG IO-${id}] New observer created with options:`, JSON.stringify(options));
          
          const wrappedCallback = (entries, observer) => {
            entries.forEach(entry => {
              const title = entry.target.querySelector('h3')?.textContent?.substring(0, 30) || 'Unknown';
              const rect = entry.boundingClientRect;
              const viewportHeight = window.innerHeight;
              
              // Determine position relative to viewport
              let position = '';
              if (rect.bottom < 0) {
                position = 'ABOVE viewport';
              } else if (rect.top > viewportHeight) {
                position = 'BELOW viewport';
              } else {
                position = 'IN viewport';
              }
              
              console.log(`[DEBUG IO-${id}] "${title}" | Intersecting: ${entry.isIntersecting} | Position: ${position} | Top: ${rect.top.toFixed(0)}, Bottom: ${rect.bottom.toFixed(0)}`);
            });
            
            return callback(entries, observer);
          };
          
          super(wrappedCallback, options);
        }
      };
      
      console.log('[DEBUG] Intersection Observer wrapped successfully');
    });
    
    // Try to scroll whatever is scrollable
    console.log('\n🚀 Attempting to scroll...');
    
    // First try: Scroll the main element
    await page.evaluate(() => {
      const main = document.querySelector('main');
      if (main) {
        console.log(`[DEBUG] Main element before scroll: scrollTop=${main.scrollTop}, scrollHeight=${main.scrollHeight}, clientHeight=${main.clientHeight}`);
        main.scrollBy(0, 300);
        console.log(`[DEBUG] Main element after scroll: scrollTop=${main.scrollTop}`);
      }
    });
    
    await page.waitForTimeout(1000);
    
    // Second try: Scroll any overflow container with articles
    await page.evaluate(() => {
      const containers = document.querySelectorAll('[class*="overflow-y-auto"]');
      containers.forEach((container, index) => {
        if (container.querySelector('article')) {
          console.log(`[DEBUG] Container ${index} before scroll: scrollTop=${container.scrollTop}, scrollHeight=${container.scrollHeight}, clientHeight=${container.clientHeight}`);
          container.scrollBy(0, 300);
          console.log(`[DEBUG] Container ${index} after scroll: scrollTop=${container.scrollTop}`);
        }
      });
    });
    
    await page.waitForTimeout(1000);
    
    // Third try: Scroll the window itself
    await page.evaluate(() => {
      console.log(`[DEBUG] Window before scroll: scrollY=${window.scrollY}, document height=${document.body.scrollHeight}`);
      window.scrollBy(0, 300);
      console.log(`[DEBUG] Window after scroll: scrollY=${window.scrollY}`);
    });
    
    await page.waitForTimeout(2000);
    
    // Check if ScrollTracker is even initialized
    const trackerCheck = await page.evaluate(() => {
      const checks = {
        scrollTrackerExists: typeof window.scrollTracker !== 'undefined',
        scrollTrackerType: typeof window.scrollTracker,
        hasTrackArticle: window.scrollTracker && typeof window.scrollTracker.trackArticle === 'function',
        observersSize: window.scrollTracker?.observers?.size || 0,
        pendingSize: window.scrollTracker?.pendingReadArticles?.size || 0
      };
      
      // Try to manually call trackArticle to see if it works
      if (window.scrollTracker && window.scrollTracker.trackArticle) {
        const firstArticle = document.querySelector('article');
        if (firstArticle) {
          const articleData = {
            id: 999,
            title: 'Test Article',
            read_status: { is_read: false }
          };
          console.log('[DEBUG] Manually calling trackArticle with test data');
          window.scrollTracker.trackArticle(firstArticle, articleData);
        }
      }
      
      return checks;
    });
    
    console.log('\n📌 ScrollTracker availability check:', trackerCheck);
    
    // Keep browser open for a bit to see all console logs
    await page.waitForTimeout(5000);
  });
});