<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import Spinner from '$lib/components/spinner.svelte';
  import { toast } from 'svelte-sonner';
  import {
    Star,
    ExternalLink,
    BookmarkPlus,
    Bookmark,
    X,
    ChevronLeft,
    ChevronRight,
    Circle,
    Layers
  } from '@lucide/svelte';
  import { cn } from '$lib/utils';
  import type { Article } from '$lib/types';

  const article = $derived(appStore.selectedArticle);

  // Content state - use RSS content initially, then load full content
  let extractedContent = $state<string | null>(null);
  let isExtracting = $state(false);
  let lastExtractedId = $state<number | null>(null);

  // Similar articles state
  let similarArticles = $state<Article[]>([]);
  let isLoadingSimilar = $state(false);
  let lastSimilarLoadedId = $state<number | null>(null);

  // Store the current article data when viewing a similar article not in the main list
  let currentSimilarArticle = $state<Article | null>(null);

  // Use either the article from the main list or the similar article we're viewing
  const displayArticle = $derived(article || currentSimilarArticle);

  const publishedDate = $derived(
    displayArticle?.published_at
      ? new Date(displayArticle.published_at).toLocaleDateString(undefined, {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      : ''
  );

  const content = $derived(
    extractedContent && lastExtractedId === displayArticle?.id
      ? extractedContent
      : displayArticle?.full_content || displayArticle?.rss_content || ''
  );

  // Extract full content when modal opens with an article that doesn't have it
  $effect(() => {
    const currentArticle = displayArticle;
    const isOpen = appStore.articleModalOpen;

    if (
      currentArticle &&
      isOpen &&
      !currentArticle.full_content &&
      currentArticle.url &&
      lastExtractedId !== currentArticle.id
    ) {
      extractFullContent(currentArticle.id);
    }
  });

  // Mark article as opened for engagement tracking
  $effect(() => {
    const currentArticle = displayArticle;
    const isOpen = appStore.articleModalOpen;

    if (currentArticle && isOpen && !currentArticle.is_opened) {
      fetch(`/api/articles/${currentArticle.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_opened: true })
      });
      appStore.updateArticleInList(currentArticle.id, { is_opened: true });
    }
  });

  // Load similar articles when modal opens
  $effect(() => {
    // Access reactive values to ensure effect tracks them
    const currentArticle = displayArticle;
    const isOpen = appStore.articleModalOpen;
    const threshold = appStore.similarityThreshold;
    const alreadyLoaded = lastSimilarLoadedId;

    if (currentArticle && isOpen && threshold > 0 && alreadyLoaded !== currentArticle.id) {
      // Check if we already have similar_ids from the grouping
      if (currentArticle.similar_ids && currentArticle.similar_ids.length > 0) {
        // Fetch the similar articles by their IDs
        loadSimilarArticlesByIds(currentArticle.similar_ids);
        lastSimilarLoadedId = currentArticle.id;
      } else {
        // Fall back to API search for similar articles
        loadSimilarArticles(currentArticle.id, threshold);
      }
    } else if (!isOpen) {
      similarArticles = [];
      lastSimilarLoadedId = null;
      currentSimilarArticle = null;
    }
  });

  async function extractFullContent(articleId: number) {
    isExtracting = true;
    try {
      const res = await fetch(`/api/articles/${articleId}/extract`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.content) {
        extractedContent = data.content;
        lastExtractedId = articleId;
      }
    } catch {
      // Silently fail, use RSS content
    } finally {
      isExtracting = false;
    }
  }

  async function loadSimilarArticlesByIds(ids: number[]) {
    isLoadingSimilar = true;
    try {
      // Fetch each article by ID
      const promises = ids.map((id) =>
        fetch(`/api/articles/${id}`).then((res) => (res.ok ? res.json() : null))
      );
      const results = await Promise.all(promises);
      similarArticles = results.filter((a): a is Article => a !== null);
    } catch {
      similarArticles = [];
    } finally {
      isLoadingSimilar = false;
    }
  }

  async function loadSimilarArticles(articleId: number, threshold: number) {
    isLoadingSimilar = true;
    try {
      const res = await fetch(`/api/articles/${articleId}/similar?threshold=${threshold}`);
      if (res.ok) {
        similarArticles = await res.json();
        lastSimilarLoadedId = articleId;
      }
    } catch {
      // Silently fail
      similarArticles = [];
    } finally {
      isLoadingSimilar = false;
    }
  }

  function openSimilarArticle(similarArticle: Article) {
    // Mark as read
    if (!similarArticle.is_read) {
      fetch(`/api/articles/${similarArticle.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: true })
      });
      appStore.updateArticleInList(similarArticle.id, { is_read: true });
      window.dispatchEvent(new CustomEvent('reload-counts'));
    }

    // Reset states for new article
    extractedContent = null;
    lastExtractedId = null;
    similarArticles = [];
    lastSimilarLoadedId = null;

    // Store the similar article data since it might not be in the main list
    currentSimilarArticle = { ...similarArticle, is_read: true };

    // Also try to select it in the store (in case it IS in the main list)
    appStore.selectArticle(similarArticle.id);
  }

  // Find prev/next article indices
  const currentIndex = $derived(
    appStore.articles.findIndex((a) => a.id === appStore.selectedArticleId)
  );
  const hasPrev = $derived(currentIndex > 0);
  const hasNext = $derived(currentIndex < appStore.articles.length - 1);

  function handleOpenChange(open: boolean) {
    if (!open) {
      appStore.closeArticleModal();
    }
  }

  function goToPrev() {
    if (hasPrev) {
      const prevArticle = appStore.articles[currentIndex - 1];
      appStore.selectArticle(prevArticle.id);

      // Mark as read
      if (!prevArticle.is_read) {
        fetch(`/api/articles/${prevArticle.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_read: true })
        });
        appStore.updateArticleInList(prevArticle.id, { is_read: true });
        window.dispatchEvent(new CustomEvent('reload-counts'));
      }
    }
  }

  function goToNext() {
    if (hasNext) {
      const nextArticle = appStore.articles[currentIndex + 1];
      appStore.selectArticle(nextArticle.id);

      // Mark as read
      if (!nextArticle.is_read) {
        fetch(`/api/articles/${nextArticle.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_read: true })
        });
        appStore.updateArticleInList(nextArticle.id, { is_read: true });
        window.dispatchEvent(new CustomEvent('reload-counts'));
      }
    }
  }

  async function toggleStar() {
    if (!displayArticle) return;
    const newValue = !displayArticle.is_starred;

    await fetch(`/api/articles/${displayArticle.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_starred: newValue })
    });

    appStore.updateArticleInList(displayArticle.id, { is_starred: newValue });

    // Also update currentSimilarArticle if we're viewing one
    if (currentSimilarArticle && currentSimilarArticle.id === displayArticle.id) {
      currentSimilarArticle = { ...currentSimilarArticle, is_starred: newValue };
    }
  }

  async function toggleRead() {
    if (!displayArticle) return;
    const newValue = !displayArticle.is_read;

    await fetch(`/api/articles/${displayArticle.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_read: newValue })
    });

    appStore.updateArticleInList(displayArticle.id, { is_read: newValue });
    window.dispatchEvent(new CustomEvent('reload-counts'));

    // Also update currentSimilarArticle if we're viewing one
    if (currentSimilarArticle && currentSimilarArticle.id === displayArticle.id) {
      currentSimilarArticle = { ...currentSimilarArticle, is_read: newValue };
    }
  }

  async function toggleSaved() {
    if (!displayArticle) return;
    const newValue = !displayArticle.is_saved;
    await fetch(`/api/articles/${displayArticle.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_saved: newValue })
    });
    appStore.updateArticleInList(displayArticle.id, { is_saved: newValue });
    if (currentSimilarArticle && currentSimilarArticle.id === displayArticle.id) {
      currentSimilarArticle = { ...currentSimilarArticle, is_saved: newValue };
    }
  }

  async function sendToInstapaper() {
    if (!displayArticle) return;

    try {
      const res = await fetch(`/api/articles/${displayArticle.id}/instapaper`, {
        method: 'POST'
      });

      const data = await res.json();

      if (res.ok) {
        toast.success('Sent to Instapaper');
      } else {
        toast.error(data.error || 'Failed to send to Instapaper');
      }
    } catch {
      toast.error('Failed to send to Instapaper');
    }
  }

  // Keyboard navigation
  function handleKeydown(e: KeyboardEvent) {
    if (!appStore.articleModalOpen) return;

    if (e.key === 'ArrowLeft' || e.key === 'k') {
      e.preventDefault();
      goToPrev();
    } else if (e.key === 'ArrowRight' || e.key === 'j') {
      e.preventDefault();
      goToNext();
    } else if (e.key === 's') {
      e.preventDefault();
      toggleStar();
    } else if (e.key === 'm') {
      e.preventDefault();
      toggleRead();
    } else if (e.key === 'l') {
      e.preventDefault();
      toggleSaved();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<Dialog.Root open={appStore.articleModalOpen} onOpenChange={handleOpenChange}>
  <Dialog.Content
    class="max-w-4xl h-[90vh] flex flex-col p-0 overflow-hidden"
    showCloseButton={false}
  >
    {#if displayArticle}
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b shrink-0">
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="icon" onclick={goToPrev} disabled={!hasPrev}>
            <ChevronLeft class="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onclick={goToNext} disabled={!hasNext}>
            <ChevronRight class="h-4 w-4" />
          </Button>
        </div>

        <div class="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onclick={toggleRead}
            title={displayArticle.is_read ? 'Mark as unread' : 'Mark as read'}
          >
            <Circle
              class={cn(
                'h-4 w-4',
                displayArticle.is_read ? 'text-muted-foreground' : 'fill-primary text-primary'
              )}
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onclick={toggleStar}
            title={displayArticle.is_starred ? 'Remove star' : 'Star'}
          >
            <Star
              class={cn('h-4 w-4', displayArticle.is_starred && 'fill-yellow-400 text-yellow-400')}
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onclick={toggleSaved}
            title={displayArticle.is_saved ? 'Remove from saved' : 'Save for later'}
          >
            <Bookmark class={cn('h-4 w-4', displayArticle.is_saved && 'fill-current')} />
          </Button>
          <Button variant="ghost" size="icon" onclick={sendToInstapaper} title="Send to Instapaper">
            <BookmarkPlus class="h-4 w-4" />
          </Button>
          {#if displayArticle.url}
            <Button
              variant="ghost"
              size="icon"
              onclick={() => window.open(displayArticle.url!, '_blank')}
              title="Open original"
            >
              <ExternalLink class="h-4 w-4" />
            </Button>
          {/if}
          <Button variant="ghost" size="icon" onclick={() => appStore.closeArticleModal()}>
            <X class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto">
        <article class="px-6 py-6 max-w-3xl mx-auto">
          <header class="mb-6">
            <h1 class="text-2xl font-bold mb-2">{displayArticle.title}</h1>
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              {#if displayArticle.feed_title}
                <span>{displayArticle.feed_title}</span>
              {/if}
              {#if displayArticle.author}
                <span>·</span>
                <span>{displayArticle.author}</span>
              {/if}
              {#if publishedDate}
                <span>·</span>
                <span>{publishedDate}</span>
              {/if}
            </div>
          </header>

          <div class="prose prose-neutral dark:prose-invert max-w-none" style="font-family: 'Source Serif 4', Georgia, serif;">
            {#if isExtracting && !content}
              <div class="flex items-center justify-center py-8">
                <Spinner />
                <span class="ml-2 text-muted-foreground">Loading full article...</span>
              </div>
            {:else}
              {@html content}
            {/if}
            {#if isExtracting && content}
              <div class="text-xs text-muted-foreground mt-4">Loading full article...</div>
            {/if}
          </div>

          <!-- Similar Articles Section -->
          {#if appStore.similarityThreshold > 0}
            <div class="mt-8 pt-6 border-t">
              <h2 class="flex items-center gap-2 text-lg font-semibold mb-4">
                <Layers class="h-5 w-5" />
                Similar Articles
              </h2>

              {#if isLoadingSimilar}
                <div class="flex items-center gap-2 text-muted-foreground">
                  <Spinner size="sm" />
                  <span>Finding similar articles...</span>
                </div>
              {:else if similarArticles.length > 0}
                <div class="space-y-2">
                  {#each similarArticles as similar}
                    <button
                      type="button"
                      class="w-full text-left p-3 rounded-lg border hover:bg-muted transition-colors"
                      onclick={() => openSimilarArticle(similar)}
                    >
                      <div class="font-medium text-sm">{similar.title}</div>
                      <div class="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                        {#if similar.feed_title}
                          <span>{similar.feed_title}</span>
                        {/if}
                        {#if similar.published_at}
                          <span>·</span>
                          <span>{new Date(similar.published_at).toLocaleDateString()}</span>
                        {/if}
                      </div>
                    </button>
                  {/each}
                </div>
              {:else}
                <p class="text-muted-foreground text-sm">No similar articles found.</p>
              {/if}
            </div>
          {/if}
        </article>
      </div>
    {/if}
  </Dialog.Content>
</Dialog.Root>
