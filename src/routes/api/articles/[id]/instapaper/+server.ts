import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getArticleById, updateArticle } from '$lib/server/articles';
import { getSetting } from '$lib/server/settings';
import { logger } from '$lib/server/logger';

export const POST: RequestHandler = async ({ params }) => {
  const id = parseInt(params.id);

  if (isNaN(id)) {
    return json({ error: 'Invalid article ID' }, { status: 400 });
  }

  const article = getArticleById(id);

  if (!article) {
    return json({ error: 'Article not found' }, { status: 404 });
  }

  if (!article.url) {
    return json({ error: 'Article has no URL' }, { status: 400 });
  }

  const username = getSetting('instapaperUsername');
  const password = getSetting('instapaperPassword');

  if (!username) {
    return json(
      { error: 'Instapaper is not configured. Go to Settings to add your credentials.' },
      { status: 400 }
    );
  }

  try {
    const params = new URLSearchParams();
    params.append('username', username);
    if (password) {
      params.append('password', password);
    }
    params.append('url', article.url);
    params.append('title', article.title);

    const response = await fetch('https://www.instapaper.com/api/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params.toString()
    });

    if (response.status === 201) {
      logger.info('system', `Saved to Instapaper: ${article.title}`);
      updateArticle(id, { is_sent_to_instapaper: true });
      return json({ success: true });
    } else if (response.status === 403) {
      logger.error('system', 'Instapaper authentication failed');
      return json({ error: 'Invalid Instapaper credentials' }, { status: 403 });
    } else if (response.status === 500) {
      logger.error('system', 'Instapaper service error');
      return json({ error: 'Instapaper service error' }, { status: 500 });
    } else {
      const text = await response.text();
      logger.error('system', `Instapaper error: ${response.status}`, { response: text });
      return json({ error: `Instapaper returned ${response.status}` }, { status: response.status });
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Unknown error';
    logger.error('system', 'Failed to save to Instapaper', { error: errorMsg });
    return json({ error: 'Failed to connect to Instapaper' }, { status: 500 });
  }
};
