<script lang="ts">
  import { onMount } from 'svelte';
  import { appStore } from '$lib/stores/app.svelte';
  import { Sheet, SheetContent } from '$lib/components/ui/sheet';
  import { Button } from '$lib/components/ui/button';
  import Sidebar from '$lib/components/sidebar/sidebar.svelte';
  import ArticleList from '$lib/components/articles/article-list.svelte';
  import ArticleModal from '$lib/components/articles/article-modal.svelte';
  import ToolsPanel from '$lib/components/tools-panel.svelte';
  import ThemeToggle from '$lib/components/theme-toggle.svelte';
  import Seo from '$lib/components/seo.svelte';
  import KeyboardHelp from '$lib/components/keyboard-help.svelte';

  let awaitingG = $state(false);
  let gTimeout: ReturnType<typeof setTimeout> | undefined;

  function handleGlobalKeydown(e: KeyboardEvent) {
    if (appStore.articleModalOpen) return;

    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    if (awaitingG) {
      awaitingG = false;
      clearTimeout(gTimeout);
      if (e.key === 'a') {
        e.preventDefault();
        appStore.selectFolder(null);
        appStore.selectFeed(null);
        return;
      }
      if (e.key === 's') {
        e.preventDefault();
        appStore.setShowStarredOnly(true);
        return;
      }
      return;
    }

    const articles = appStore.articles;
    const idx = appStore.focusedArticleIndex;

    switch (e.key) {
      case 'j':
      case 'ArrowDown':
        e.preventDefault();
        appStore.setFocusedArticleIndex(Math.min(idx + 1, articles.length - 1));
        break;
      case 'k':
      case 'ArrowUp':
        e.preventDefault();
        appStore.setFocusedArticleIndex(Math.max(idx - 1, 0));
        break;
      case 'Enter':
      case 'o': {
        if (idx >= 0 && idx < articles.length) {
          e.preventDefault();
          const art = articles[idx];
          if (!art.is_read) {
            fetch(`/api/articles/${art.id}`, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ is_read: true })
            });
            appStore.updateArticleInList(art.id, { is_read: true });
            window.dispatchEvent(new CustomEvent('reload-counts'));
          }
          appStore.selectArticle(art.id);
        }
        break;
      }
      case 's': {
        if (idx >= 0 && idx < articles.length) {
          e.preventDefault();
          const art = articles[idx];
          const starred = !art.is_starred;
          fetch(`/api/articles/${art.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_starred: starred })
          });
          appStore.updateArticleInList(art.id, { is_starred: starred });
          window.dispatchEvent(new CustomEvent('reload-counts'));
        }
        break;
      }
      case 'm': {
        if (idx >= 0 && idx < articles.length) {
          e.preventDefault();
          const art = articles[idx];
          const read = !art.is_read;
          fetch(`/api/articles/${art.id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_read: read })
          });
          appStore.updateArticleInList(art.id, { is_read: read });
          window.dispatchEvent(new CustomEvent('reload-counts'));
        }
        break;
      }
      case 'v':
        if (idx >= 0 && idx < articles.length) {
          e.preventDefault();
          const url = articles[idx].url;
          if (url) window.open(url, '_blank');
        }
        break;
      case 'r':
        e.preventDefault();
        window.dispatchEvent(new CustomEvent('reload-data'));
        break;
      case 'g':
        e.preventDefault();
        awaitingG = true;
        gTimeout = setTimeout(() => { awaitingG = false; }, 500);
        break;
      case '?':
        e.preventDefault();
        appStore.setKeyboardHelpOpen(!appStore.keyboardHelpOpen);
        break;
      case 'Escape':
        e.preventDefault();
        if (appStore.keyboardHelpOpen) {
          appStore.setKeyboardHelpOpen(false);
        } else {
          appStore.setFocusedArticleIndex(-1);
        }
        break;
    }
  }
  import { Menu } from '@lucide/svelte';

  async function loadData() {
    appStore.setIsLoading(true);

    try {
      // Load folders, feeds, and settings
      const [foldersRes, feedsRes, countsRes, settingsRes] = await Promise.all([
        fetch('/api/folders'),
        fetch('/api/feeds'),
        fetch('/api/articles?counts=true'),
        fetch('/api/settings')
      ]);

      const [folders, feeds, counts, settings] = await Promise.all([
        foldersRes.json(),
        feedsRes.json(),
        countsRes.json(),
        settingsRes.json()
      ]);

      appStore.setFolders(folders);
      appStore.setFeeds(feeds);
      appStore.setUnreadCounts(counts);
      appStore.initSettings(settings);

      // Skip article reload while modal is open — replacing the list would blank it
      if (!appStore.articleModalOpen) {
        await loadArticles();
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      appStore.setIsLoading(false);
    }
  }

  const ARTICLES_PER_PAGE = 50;

  function buildArticleParams(cursor?: { date: string; id: number; highlightRank?: number }): URLSearchParams {
    const params = new URLSearchParams();

    if (appStore.selectedFeedId) {
      params.set('feed_id', String(appStore.selectedFeedId));
    } else if (appStore.selectedFolderId) {
      params.set('folder_id', String(appStore.selectedFolderId));
    }

    if ((appStore.showUnreadOnly || appStore.hideReadArticles) && !appStore.showSavedOnly) {
      params.set('is_read', 'false');
    }

    if (appStore.showStarredOnly) {
      params.set('is_starred', 'true');
    }

    if (appStore.showSavedOnly) {
      params.set('is_saved', 'true');
    }

    params.set('limit', String(ARTICLES_PER_PAGE));

    // Cursor-based pagination
    if (cursor) {
      params.set('before_date', cursor.date);
      params.set('before_id', String(cursor.id));
      if (cursor.highlightRank !== undefined) {
        params.set('before_highlight_rank', String(cursor.highlightRank));
      }
    }

    // Similar articles grouping
    if (appStore.similarityThreshold > 0) {
      params.set('group_similar', 'true');
      params.set('similarity_threshold', String(appStore.similarityThreshold));
    }

    if (appStore.searchQuery) params.set('search', appStore.searchQuery);

    return params;
  }

  async function loadArticles() {
    const params = buildArticleParams();
    const res = await fetch(`/api/articles?${params}`);
    const data = await res.json();
    appStore.setArticles(data.articles);
    appStore.setHasMoreArticles(data.hasMore);
  }

  async function loadMoreArticles() {
    if (appStore.isLoadingMore || !appStore.hasMoreArticles) return;

    // Get the last article to use as cursor
    const lastArticle = appStore.articles[appStore.articles.length - 1];
    if (!lastArticle) return;

    appStore.setIsLoadingMore(true);
    try {
      const cursor = {
        date: lastArticle.published_at || lastArticle.created_at,
        id: lastArticle.id,
        highlightRank: lastArticle.is_feed_highlighted ? 0 : 1
      };
      const params = buildArticleParams(cursor);
      const res = await fetch(`/api/articles?${params}`);
      const data = await res.json();
      appStore.appendArticles(data.articles);
      appStore.setHasMoreArticles(data.hasMore);
    } finally {
      appStore.setIsLoadingMore(false);
    }
  }

  async function loadCounts() {
    const res = await fetch('/api/articles?counts=true');
    const counts = await res.json();
    appStore.setUnreadCounts(counts);
  }

  // React to filter changes
  $effect(() => {
    // Access dependencies
    appStore.selectedFeedId;
    appStore.selectedFolderId;
    appStore.showUnreadOnly;
    appStore.showStarredOnly;
    appStore.hideReadArticles;
    appStore.similarityThreshold;
    appStore.searchQuery;
    appStore.showSavedOnly;
    appStore.highlightMode;

    loadArticles();
  });

  // Reload articles when the article modal closes (background refreshes may have been skipped)
  let wasModalOpen = false;
  $effect(() => {
    const isOpen = appStore.articleModalOpen;
    if (wasModalOpen && !isOpen) {
      loadArticles();
    }
    wasModalOpen = isOpen;
  });

  onMount(() => {
    loadData();

    // Listen for reload events
    const handleReload = () => loadData();
    const handleReloadCounts = () => loadCounts();
    const handleLoadMore = () => loadMoreArticles();

    window.addEventListener('reload-data', handleReload);
    window.addEventListener('reload-counts', handleReloadCounts);
    window.addEventListener('load-more-articles', handleLoadMore);

    // Connect to Server-Sent Events for real-time updates
    let eventSource: EventSource | null = null;

    function connectSSE() {
      eventSource = new EventSource('/api/events');

      eventSource.addEventListener('connected', () => {
        console.log('[SSE] Connected to server events');
      });

      eventSource.addEventListener('feeds-refreshed', (event) => {
        const data = JSON.parse(event.data);
        console.log(`[SSE] Feeds refreshed, ${data.added} new articles`);
        loadData();
      });

      eventSource.addEventListener('articles-updated', () => {
        console.log('[SSE] Articles updated');
        loadData();
      });

      eventSource.onerror = () => {
        console.log('[SSE] Connection error, reconnecting in 5s...');
        eventSource?.close();
        setTimeout(connectSSE, 5000);
      };
    }

    connectSSE();

    return () => {
      window.removeEventListener('reload-data', handleReload);
      window.removeEventListener('reload-counts', handleReloadCounts);
      window.removeEventListener('load-more-articles', handleLoadMore);
      eventSource?.close();
    };
  });
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<Seo title="ZiB" description="ZiB - a modern RSS reader" />

<div class="h-screen flex flex-col">
  <!-- Mobile header -->
  <header class="lg:hidden flex items-center justify-between px-4 py-2 border-b">
    <Button variant="ghost" size="icon" onclick={() => appStore.setSidebarOpen(true)}>
      <Menu class="h-5 w-5" />
    </Button>

    <h1 class="font-semibold">ZiB</h1>

    <ThemeToggle />
  </header>

  <!-- Mobile sidebar sheet -->
  <Sheet open={appStore.sidebarOpen} onOpenChange={(open) => appStore.setSidebarOpen(open)}>
    <SheetContent side="left" class="w-72 p-0">
      <Sidebar />
    </SheetContent>
  </Sheet>

  <div class="flex flex-1 overflow-hidden">
    <!-- Desktop sidebar -->
    <aside class="hidden lg:flex w-72 border-r flex-col">
      <Sidebar />
    </aside>

    <!-- Main content -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <ToolsPanel />
      <div class="flex-1 overflow-hidden">
        <ArticleList />
      </div>
    </main>
  </div>

  <!-- Desktop theme toggle -->
  <div class="hidden lg:block fixed bottom-4 right-4">
    <ThemeToggle />
  </div>
</div>

<ArticleModal />
<KeyboardHelp />
