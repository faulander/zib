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
    X,
    ChevronLeft,
    ChevronRight,
    Circle
  } from '@lucide/svelte';
  import { cn } from '$lib/utils';

  const article = $derived(appStore.selectedArticle);

  const publishedDate = $derived(
    article?.published_at
      ? new Date(article.published_at).toLocaleDateString(undefined, {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      : ''
  );

  // Content state - use RSS content initially, then load full content
  let extractedContent = $state<string | null>(null);
  let isExtracting = $state(false);
  let lastExtractedId = $state<number | null>(null);

  const content = $derived(
    extractedContent && lastExtractedId === article?.id
      ? extractedContent
      : article?.full_content || article?.rss_content || ''
  );

  // Extract full content when modal opens with an article that doesn't have it
  $effect(() => {
    const currentArticle = article;
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
    if (!article) return;
    const newValue = !article.is_starred;

    await fetch(`/api/articles/${article.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_starred: newValue })
    });

    appStore.updateArticleInList(article.id, { is_starred: newValue });
  }

  async function toggleRead() {
    if (!article) return;
    const newValue = !article.is_read;

    await fetch(`/api/articles/${article.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_read: newValue })
    });

    appStore.updateArticleInList(article.id, { is_read: newValue });
    window.dispatchEvent(new CustomEvent('reload-counts'));
  }

  async function sendToInstapaper() {
    if (!article) return;

    try {
      const res = await fetch(`/api/articles/${article.id}/instapaper`, {
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
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<Dialog.Root open={appStore.articleModalOpen} onOpenChange={handleOpenChange}>
  <Dialog.Content
    class="max-w-4xl h-[90vh] flex flex-col p-0 overflow-hidden"
    showCloseButton={false}
  >
    {#if article}
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
            title={article.is_read ? 'Mark as unread' : 'Mark as read'}
          >
            <Circle
              class={cn(
                'h-4 w-4',
                article.is_read ? 'text-muted-foreground' : 'fill-primary text-primary'
              )}
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onclick={toggleStar}
            title={article.is_starred ? 'Remove star' : 'Star'}
          >
            <Star class={cn('h-4 w-4', article.is_starred && 'fill-yellow-400 text-yellow-400')} />
          </Button>
          <Button variant="ghost" size="icon" onclick={sendToInstapaper} title="Send to Instapaper">
            <BookmarkPlus class="h-4 w-4" />
          </Button>
          {#if article.url}
            <Button
              variant="ghost"
              size="icon"
              onclick={() => window.open(article.url!, '_blank')}
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
            <h1 class="text-2xl font-bold mb-2">{article.title}</h1>
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              {#if article.feed_title}
                <span>{article.feed_title}</span>
              {/if}
              {#if article.author}
                <span>·</span>
                <span>{article.author}</span>
              {/if}
              {#if publishedDate}
                <span>·</span>
                <span>{publishedDate}</span>
              {/if}
            </div>
          </header>

          <div class="prose prose-neutral dark:prose-invert max-w-none">
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
        </article>
      </div>
    {/if}
  </Dialog.Content>
</Dialog.Root>
