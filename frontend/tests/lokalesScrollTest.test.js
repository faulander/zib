import { test, expect } from '@playwright/test';

test.describe('Lokales Category Scroll Test', () => {
  test('test scroll tracking in Lokales category', async ({ page }) => {
    // Enable console logging before navigation
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ScrollTracker]') || text.includes('[DEBUG]') || text.includes('Article')) {
        console.log('📋', text);
      }
    });
    
    // Navigate to the app
    await page.goto('http://localhost:5173');
    console.log('✅ Navigated to app');
    
    // Wait for the sidebar to load
    await page.waitForSelector('aside', { timeout: 30000 });
    console.log('✅ Sidebar loaded');
    
    // Click on Lokales category
    const lokalesButton = await page.locator('button:has-text("Lokales")').first();
    await lokalesButton.click();
    console.log('✅ Clicked on Lokales category');
    
    // Wait for articles to load
    await page.waitForTimeout(2000);
    
    // Check if scrollTracker exists and is configured
    const trackerInfo = await page.evaluate(() => {
      if (window.scrollTracker) {
        // Log current state
        console.log('[DEBUG] ScrollTracker exists');
        console.log('[DEBUG] ScrollTracker config:', {
          batchSize: window.scrollTracker.batchSize,
          scrollDelay: window.scrollTracker.scrollDelay,
          observersCount: window.scrollTracker.observers?.size || 0,
          pendingCount: window.scrollTracker.pendingReadArticles?.size || 0
        });
        
        return {
          exists: true,
          batchSize: window.scrollTracker.batchSize,
          scrollDelay: window.scrollTracker.scrollDelay,
          observersCount: window.scrollTracker.observers?.size || 0
        };
      }
      return { exists: false };
    });
    console.log('📊 ScrollTracker info:', trackerInfo);
    
    // Find the scrollable container for articles
    const containerInfo = await page.evaluate(() => {
      // Find the container with articles
      const articles = document.querySelectorAll('article');
      console.log(`[DEBUG] Found ${articles.length} articles in DOM`);
      
      // Find the scrollable parent
      let scrollContainer = null;
      if (articles.length > 0) {
        let parent = articles[0].parentElement;
        while (parent) {
          const style = window.getComputedStyle(parent);
          if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
            scrollContainer = parent;
            break;
          }
          parent = parent.parentElement;
        }
      }
      
      if (scrollContainer) {
        return {
          found: true,
          selector: scrollContainer.className,
          scrollHeight: scrollContainer.scrollHeight,
          clientHeight: scrollContainer.clientHeight,
          scrollTop: scrollContainer.scrollTop,
          isScrollable: scrollContainer.scrollHeight > scrollContainer.clientHeight,
          articleCount: articles.length
        };
      }
      
      return { found: false, articleCount: articles.length };
    });
    console.log('📦 Container info:', containerInfo);
    
    // Get info about first few unread articles
    const unreadArticles = await page.evaluate(() => {
      const articles = Array.from(document.querySelectorAll('article'));
      const unread = [];
      
      articles.slice(0, 10).forEach((article, index) => {
        const title = article.querySelector('h3')?.textContent;
        const readIndicator = article.querySelector('.bg-blue-500'); // Unread indicator
        const isUnread = !!readIndicator;
        const rect = article.getBoundingClientRect();
        
        if (isUnread) {
          unread.push({
            index,
            title: title?.substring(0, 40),
            top: rect.top,
            bottom: rect.bottom,
            height: rect.height,
            isVisible: rect.top < window.innerHeight && rect.bottom > 0
          });
        }
      });
      
      return unread;
    });
    console.log('📝 First unread articles:', unreadArticles);
    
    // Check if articles are being tracked
    const trackingStatus = await page.evaluate(() => {
      const articles = Array.from(document.querySelectorAll('article')).slice(0, 5);
      const status = [];
      
      articles.forEach((article, index) => {
        const title = article.querySelector('h3')?.textContent?.substring(0, 30);
        const hasUseAction = article.hasAttribute('use:trackElement');
        
        // Check if observer is attached
        const isTracked = window.scrollTracker?.observers?.has(article) || false;
        
        status.push({
          index,
          title,
          hasUseAction,
          isTracked
        });
      });
      
      return status;
    });
    console.log('🔍 Article tracking status:', trackingStatus);
    
    // Now let's scroll and see what happens
    console.log('\n🚀 Starting scroll test...');
    
    // Scroll the container slowly
    for (let i = 0; i < 5; i++) {
      console.log(`\n📜 Scroll step ${i + 1}/5`);
      
      const scrollResult = await page.evaluate(() => {
        // Find the scrollable container
        const container = Array.from(document.querySelectorAll('[class*="overflow-y-auto"]'))
          .find(el => el.querySelector('article') && el.scrollHeight > el.clientHeight);
        
        if (container) {
          const beforeScroll = container.scrollTop;
          container.scrollBy(0, 200);
          const afterScroll = container.scrollTop;
          
          // Check what articles are now visible
          const visibleArticles = [];
          const articles = container.querySelectorAll('article');
          articles.forEach((article, index) => {
            const rect = article.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
              visibleArticles.push({
                index,
                title: article.querySelector('h3')?.textContent?.substring(0, 30)
              });
            }
          });
          
          return {
            scrolled: true,
            beforeScroll,
            afterScroll,
            actualScroll: afterScroll - beforeScroll,
            visibleCount: visibleArticles.length,
            firstVisible: visibleArticles[0],
            lastVisible: visibleArticles[visibleArticles.length - 1]
          };
        }
        
        return { scrolled: false, message: 'No scrollable container found' };
      });
      
      console.log('Scroll result:', scrollResult);
      
      // Wait for scroll delay
      await page.waitForTimeout(1500);
      
      // Check pending articles
      const pending = await page.evaluate(() => {
        if (window.scrollTracker) {
          return {
            pendingCount: window.scrollTracker.pendingReadArticles?.size || 0,
            observerCount: window.scrollTracker.observers?.size || 0
          };
        }
        return null;
      });
      console.log('Pending after scroll:', pending);
    }
    
    // Final check - what's in the scroll tracker
    const finalState = await page.evaluate(() => {
      if (window.scrollTracker) {
        const pendingIds = Array.from(window.scrollTracker.pendingReadArticles || []);
        return {
          pendingArticles: pendingIds,
          observerCount: window.scrollTracker.observers?.size || 0,
          batchSize: window.scrollTracker.batchSize
        };
      }
      return null;
    });
    console.log('\n📊 Final ScrollTracker state:', finalState);
    
    // Keep browser open briefly
    await page.waitForTimeout(3000);
  });
});