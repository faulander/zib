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

      // Load articles
      await loadArticles();
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      appStore.setIsLoading(false);
    }
  }

  const ARTICLES_PER_PAGE = 50;

  function buildArticleParams(cursor?: { date: string; id: number }): URLSearchParams {
    const params = new URLSearchParams();

    if (appStore.selectedFeedId) {
      params.set('feed_id', String(appStore.selectedFeedId));
    } else if (appStore.selectedFolderId) {
      params.set('folder_id', String(appStore.selectedFolderId));
    }

    if (appStore.showUnreadOnly || appStore.hideReadArticles) {
      params.set('is_read', 'false');
    }

    if (appStore.showStarredOnly) {
      params.set('is_starred', 'true');
    }

    params.set('limit', String(ARTICLES_PER_PAGE));

    // Cursor-based pagination
    if (cursor) {
      params.set('before_date', cursor.date);
      params.set('before_id', String(cursor.id));
    }

    return params;
  }

  async function loadArticles() {
    const params = buildArticleParams();
    const res = await fetch(`/api/articles?${params}`);
    const articles = await res.json();
    appStore.setArticles(articles);
    appStore.setHasMoreArticles(articles.length >= ARTICLES_PER_PAGE);
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
        id: lastArticle.id
      };
      const params = buildArticleParams(cursor);
      const res = await fetch(`/api/articles?${params}`);
      const newArticles = await res.json();
      appStore.appendArticles(newArticles);
      appStore.setHasMoreArticles(newArticles.length >= ARTICLES_PER_PAGE);
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

    loadArticles();
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

<Seo title="RSS Reader" description="A modern RSS reader" />

<div class="h-screen flex flex-col">
  <!-- Mobile header -->
  <header class="lg:hidden flex items-center justify-between px-4 py-2 border-b">
    <Button variant="ghost" size="icon" onclick={() => appStore.setSidebarOpen(true)}>
      <Menu class="h-5 w-5" />
    </Button>

    <h1 class="font-semibold">RSS Reader</h1>

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
