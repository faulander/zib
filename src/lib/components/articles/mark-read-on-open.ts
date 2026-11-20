import type { Article } from '$lib/types';
import { appStore } from '$lib/stores/app.svelte';
import { toast } from 'svelte-sonner';
import { READ_WRITE_HEADERS } from '$lib/client-version';

/** Mark the row immediately, then refresh counts once the database write finishes. */
export function markReadOnOpen(article: Article): void {
  if (article.is_read) return;

  appStore.updateArticleInList(article.id, { is_read: true });
  void fetch(`/api/articles/${article.id}`, {
    method: 'PATCH',
    headers: READ_WRITE_HEADERS,
    body: JSON.stringify({ is_read: true })
  }).then((response) => {
    if (!response.ok) throw new Error(`Mark read failed: ${response.status}`);
    window.dispatchEvent(new CustomEvent('reload-counts'));
  }).catch((err) => {
    console.error(`Failed to mark article ${article.id} as read:`, err);
    appStore.updateArticleInList(article.id, { is_read: false });
    toast.error('Could not mark article as read');
  });
}
