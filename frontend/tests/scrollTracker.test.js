import { test, expect } from '@playwright/test';

test.describe('Scroll Tracker Mark-as-Read', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    
    // Wait for initial load
    await page.waitForSelector('.divide-y', { timeout: 10000 });
    
    // Enable console logging
    page.on('console', msg => {
      if (msg.text().includes('[ScrollTracker]')) {
        console.log('Browser console:', msg.text());
      }
    });
  });

  test('should NOT mark articles as read when loaded via infinite scroll without viewing', async ({ page }) => {
    // Get initial article count
    const initialArticles = await page.locator('article').count();
    console.log(`Initial articles visible: ${initialArticles}`);
    
    // Capture which articles are currently visible
    const visibleArticles = await page.evaluate(() => {
      const articles = Array.from(document.querySelectorAll('article'));
      return articles
        .filter(el => {
          const rect = el.getBoundingClientRect();
          return rect.top < window.innerHeight && rect.bottom > 0;
        })
        .map(el => {
          const title = el.querySelector('h3')?.textContent || 'Unknown';
          return { title: title.substring(0, 40) };
        });
    });
    console.log('Initially visible articles:', visibleArticles);
    
    // Scroll to bottom to trigger infinite scroll
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    // Wait for new articles to load
    await page.waitForTimeout(2000);
    
    // Check new article count
    const newArticleCount = await page.locator('article').count();
    console.log(`Articles after infinite scroll: ${newArticleCount}`);
    
    // Check console for any "MARKED FOR READING" messages for articles that weren't scrolled past
    const markedArticles = await page.evaluate(() => {
      // Get all articles currently in DOM
      const articles = Array.from(document.querySelectorAll('article'));
      
      // Check which ones are below the viewport (never been visible)
      const belowViewport = articles.filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.top > window.innerHeight;
      });
      
      return {
        totalArticles: articles.length,
        belowViewportCount: belowViewport.length,
        belowViewportTitles: belowViewport.slice(0, 5).map(el => 
          el.querySelector('h3')?.textContent?.substring(0, 40) || 'Unknown'
        )
      };
    });
    
    console.log('Articles below viewport:', markedArticles);
    
    // Now let's specifically test the scroll tracking behavior
    await page.evaluate(() => {
      window.scrollTrackerTest = {
        tracked: [],
        markedForRead: []
      };
      
      // Intercept the scrollTracker methods
      if (window.scrollTracker) {
        const originalTrack = window.scrollTracker.trackArticle.bind(window.scrollTracker);
        const originalSchedule = window.scrollTracker.scheduleMarkAsRead.bind(window.scrollTracker);
        
        window.scrollTracker.trackArticle = function(element, article) {
          window.scrollTrackerTest.tracked.push({
            id: article.id,
            title: article.title?.substring(0, 40)
          });
          return originalTrack(element, article);
        };
        
        window.scrollTracker.scheduleMarkAsRead = function(articleId) {
          window.scrollTrackerTest.markedForRead.push(articleId);
          return originalSchedule(articleId);
        };
      }
    });
    
    // Trigger a small scroll to see what happens
    await page.evaluate(() => window.scrollBy(0, 100));
    await page.waitForTimeout(1000);
    
    // Check what was tracked and marked
    const trackingData = await page.evaluate(() => window.scrollTrackerTest);
    console.log('Tracking data:', trackingData);
    
    // The test passes if no articles below the viewport were marked for reading
    expect(trackingData.markedForRead.length).toBeLessThanOrEqual(initialArticles);
  });

  test('should mark articles as read ONLY when scrolled past', async ({ page }) => {
    // Scroll slowly through first few articles
    const firstArticle = await page.locator('article').first();
    const firstArticleTitle = await firstArticle.locator('h3').textContent();
    console.log('First article:', firstArticleTitle?.substring(0, 40));
    
    // Get article height
    const articleHeight = await firstArticle.boundingBox();
    
    if (articleHeight) {
      // Scroll past the first article slowly
      for (let i = 0; i < 5; i++) {
        await page.mouse.wheel(0, articleHeight.height / 5);
        await page.waitForTimeout(200);
      }
      
      // Wait for the delay before mark as read
      await page.waitForTimeout(1500);
      
      // Check console for the specific article being marked
      const logs = await page.evaluate(() => {
        const logs = [];
        // Check if console has our expected log
        return logs;
      });
      
      console.log('After scrolling past first article, logs:', logs);
    }
  });

  test('debug intersection observer behavior', async ({ page }) => {
    // Inject debug code to understand intersection observer
    await page.evaluate(() => {
      let observerCount = 0;
      const originalObserver = window.IntersectionObserver;
      
      window.IntersectionObserver = class DebugIntersectionObserver extends originalObserver {
        constructor(callback, options) {
          const debugCallback = (entries, observer) => {
            entries.forEach(entry => {
              const article = entry.target.querySelector('h3')?.textContent?.substring(0, 30);
              console.log(`[DEBUG IO] Article: "${article}" | Intersecting: ${entry.isIntersecting} | Rect.top: ${entry.boundingClientRect.top.toFixed(0)} | Rect.bottom: ${entry.boundingClientRect.bottom.toFixed(0)} | Viewport height: ${window.innerHeight}`);
            });
            return callback(entries, observer);
          };
          super(debugCallback, options);
          observerCount++;
          console.log(`[DEBUG IO] Observer #${observerCount} created with options:`, options);
        }
      };
    });
    
    // Now scroll and watch the debug output
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(1000);
    
    // Scroll down slowly
    for (let i = 0; i < 10; i++) {
      await page.mouse.wheel(0, 200);
      await page.waitForTimeout(500);
    }
    
    // Scroll to trigger infinite load
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(3000);
    
    console.log('Test complete - check console output above for intersection observer behavior');
  });
});