<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';
  import { READ_WRITE_HEADERS } from '$lib/client-version';
  import { Sheet, SheetContent } from '$lib/components/ui/sheet';
  import { Button } from '$lib/components/ui/button';
  import Sidebar from '$lib/components/sidebar/sidebar.svelte';
  import ArticleList from '$lib/components/articles/article-list.svelte';
  import { markReadOnOpen } from '$lib/components/articles/mark-read-on-open';
  import ArticleModal from '$lib/components/articles/article-modal.svelte';
  import ToolsPanel from '$lib/components/tools-panel.svelte';
  import ThemeToggle from '$lib/components/theme-toggle.svelte';
  import Seo from '$lib/components/seo.svelte';
  import KeyboardHelp from '$lib/components/keyboard-help.svelte';

  let awaitingG = $state(false);
  let gTimeout: ReturnType<typeof setTimeout> | undefined;
  let settingsReady = $state(false);
  let dataRequestId = 0;
  let lastFilterKey = '';
  let wasModalOpen = false;
  let modalListDirty = false;

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
          markReadOnOpen(art);
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
            headers: READ_WRITE_HEADERS,
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

  let lastLoadAt = 0;

  async function loadData() {
    lastLoadAt = Date.now();
    const requestId = ++dataRequestId;
    const countsId = ++countsRequestId;
    if (!settingsReady) appStore.setIsLoading(true);

    try {
      const [foldersRes, feedsRes, countsRes, settingsRes] = await Promise.all([
        fetch('/api/folders'),
        fetch('/api/feeds'),
        fetch('/api/articles?counts=true'),
        fetch('/api/settings')
      ]);
      if (![foldersRes, feedsRes, countsRes, settingsRes].every((res) => res.ok)) {
        throw new Error('Failed to fetch reader data');
      }

      const [folders, feeds, counts, settings] = await Promise.all([
        foldersRes.json(),
        feedsRes.json(),
        countsRes.json(),
        settingsRes.json()
      ]);
      if (requestId !== dataRequestId) return;

      const previousFilterKey = currentFilterKey();
      const wasReady = settingsReady;
      appStore.setFolders(folders);
      appStore.setFeeds(feeds);
      if (countsId === countsRequestId) appStore.setUnreadCounts(counts);
      appStore.initSettings(settings);
      settingsReady = true;

      if (appStore.articleModalOpen) {
        modalListDirty = true;
      } else if (wasReady && previousFilterKey === currentFilterKey()) {
        // No filter effect will run; refresh the rows without tearing them down.
        void loadArticles(true);
      }
    } catch (err) {
      if (requestId === dataRequestId) {
        console.error('Failed to load data:', err);
        toast.error('Could not load reader data', { id: 'reader-load-error' });
      }
    } finally {
      if (requestId === dataRequestId && !settingsReady) appStore.setIsLoading(false);
    }
  }

  const ARTICLES_PER_PAGE = 50;
  let nextCursor: { date: string; id: number; highlightRank: number } | null = null;
  let articlesRequestId = 0;

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

    // Similar articles grouping (thresholds are read server-side from settings)
    if (appStore.similarityThreshold > 0) {
      params.set('group_similar', 'true');
    }

    if (appStore.searchQuery) params.set('search', appStore.searchQuery);

    return params;
  }

  function currentFilterKey(): string {
    return `${buildArticleParams()}|${appStore.similarityThreshold}|${appStore.highlightMode}`;
  }

  async function loadArticles(keepList = false) {
    const requestId = ++articlesRequestId;
    appStore.setIsLoading(!keepList || appStore.articles.length === 0);
    appStore.setIsLoadingMore(false);
    try {
      const params = buildArticleParams();
      const res = await fetch(`/api/articles?${params}`);
      if (!res.ok) throw new Error(`Failed to load articles: ${res.status}`);
      const data = await res.json();
      if (requestId !== articlesRequestId) return;
      if (appStore.articleModalOpen) {
        modalListDirty = true;
        return;
      }
      appStore.setArticles(data.articles);
      appStore.setHasMoreArticles(data.hasMore);
      nextCursor = data.nextCursor;
    } catch (err) {
      if (requestId === articlesRequestId) {
        console.error('Failed to load articles:', err);
        toast.error('Could not load articles', { id: 'articles-load-error' });
      }
    } finally {
      if (requestId === articlesRequestId) appStore.setIsLoading(false);
    }
  }

  async function loadMoreArticles() {
    if (appStore.isLoading || appStore.isLoadingMore || !appStore.hasMoreArticles) return;

    // Grouping hides some results inside a displayed row. The server cursor
    // tracks the last raw result rather than the last visible representative.
    const cursor = nextCursor;
    if (!cursor) return;

    const requestId = articlesRequestId;
    appStore.setIsLoadingMore(true);
    try {
      const params = buildArticleParams(cursor);
      const res = await fetch(`/api/articles?${params}`);
      const data = await res.json();
      if (requestId !== articlesRequestId) return;
      appStore.appendArticles(data.articles);
      appStore.setHasMoreArticles(data.hasMore);
      nextCursor = data.nextCursor;
    } finally {
      if (requestId === articlesRequestId) appStore.setIsLoadingMore(false);
    }
  }

  let countsRequestId = 0;
  async function loadCounts() {
    const requestId = ++countsRequestId;
    const res = await fetch('/api/articles?counts=true');
    const counts = await res.json();
    // Discard stale responses that resolve after a newer request
    if (requestId !== countsRequestId) return;
    appStore.setUnreadCounts(counts);
  }

  // Only the current filter or a modal close can start a list request.
  // Keep background refreshes and open/close transitions from tearing down
  // the rows (and the scroll observer) while an article is being read.
  $effect(() => {
    if (!settingsReady) return;
    const filterKey = currentFilterKey();
    const isOpen = appStore.articleModalOpen;
    if (isOpen) {
      if (filterKey !== lastFilterKey) modalListDirty = true;
      wasModalOpen = true;
      return;
    }

    const closing = wasModalOpen;
    wasModalOpen = false;
    const unchangedList = filterKey === lastFilterKey;
    const needsUnreadRefresh = appStore.hideReadArticles || appStore.showUnreadOnly;
    if (closing && unchangedList && !modalListDirty && !needsUnreadRefresh) return;

    const keepList = unchangedList && closing;
    lastFilterKey = filterKey;
    modalListDirty = false;
    // Fetching reads store state synchronously; don't make the effect depend
    // on the current rows or loading flags as well as its explicit filter.
    untrack(() => {
      void loadArticles(keepList);
    });
  });

  const POLL_INTERVAL = 60 * 1000;
  const RECENT_LOAD_MS = 5 * 1000;

  // Cheap poll independent of SSE and the counts store: fetch the head of the
  // list for the current filters and reload only when it holds an article the
  // list doesn't show (new arrivals, or an empty/stale list). Never marks
  // anything read and keeps deep pages when nothing new exists.
  async function pollForNewArticles() {
    if (!settingsReady || document.visibilityState !== 'visible') return;
    if (appStore.articleModalOpen || appStore.isLoading || appStore.isLoadingMore) return;
    try {
      const requestId = articlesRequestId;
      const params = buildArticleParams();
      params.set('limit', '1');
      const res = await fetch(`/api/articles?${params}`);
      if (!res.ok) return;
      const data = await res.json();
      // A list load started meanwhile (filters changed etc.); it is fresher.
      if (requestId !== articlesRequestId || appStore.articleModalOpen) return;
      const head = data.articles?.[0];
      if (head && !appStore.articles.some((a) => a.id === head.id)) void loadData();
    } catch {
      // Network hiccup; try again next tick.
    }
  }

  onMount(() => {
    loadData();

    // Listen for reload events
    const handleReload = () => loadData();
    const handleReloadCounts = () => loadCounts();
    const handleLoadMore = () => loadMoreArticles();

    window.addEventListener('reload-data', handleReload);
    window.addEventListener('reload-counts', handleReloadCounts);
    window.addEventListener('load-more-articles', handleLoadMore);

    // Native EventSource reconnects automatically; resync on every connection
    // to recover updates missed while offline (including before the first connection).
    const eventSource = new EventSource('/api/events');
    let reloadTimeout: ReturnType<typeof setTimeout> | undefined;
    const queueReload = () => {
      clearTimeout(reloadTimeout);
      reloadTimeout = setTimeout(() => {
        reloadTimeout = undefined;
        void loadData();
      }, 1000);
    };

    // A (re)connect only resyncs when nothing loaded recently; real events always reload.
    eventSource.addEventListener('connected', () => {
      if (Date.now() - lastLoadAt > RECENT_LOAD_MS) queueReload();
    });
    eventSource.addEventListener('feeds-refreshed', queueReload);
    eventSource.addEventListener('articles-updated', queueReload);

    const pollTimer = setInterval(() => void pollForNewArticles(), POLL_INTERVAL);
    let hiddenAt = 0;
    const handleVisibility = () => {
      if (document.visibilityState === 'hidden') {
        hiddenAt = Date.now();
      } else if (hiddenAt && Date.now() - lastLoadAt > RECENT_LOAD_MS) {
        hiddenAt = 0;
        queueReload();
      }
    };
    const handleFocus = () => {
      if (Date.now() - lastLoadAt > POLL_INTERVAL) queueReload();
    };
    document.addEventListener('visibilitychange', handleVisibility);
    window.addEventListener('focus', handleFocus);

    return () => {
      window.removeEventListener('reload-data', handleReload);
      window.removeEventListener('reload-counts', handleReloadCounts);
      window.removeEventListener('load-more-articles', handleLoadMore);
      clearTimeout(reloadTimeout);
      clearInterval(pollTimer);
      document.removeEventListener('visibilitychange', handleVisibility);
      window.removeEventListener('focus', handleFocus);
      eventSource.close();
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
