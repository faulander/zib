import { env } from '$env/dynamic/private';

const INSTAPAPER_USERNAME = env.INSTAPAPER_USERNAME || '';
const INSTAPAPER_PASSWORD = env.INSTAPAPER_PASSWORD || '';

const INSTAPAPER_API_URL = 'https://www.instapaper.com/api';

export interface InstapaperResult {
  success: boolean;
  bookmark_id?: number;
  error?: string;
}

export async function addToInstapaper(
  url: string,
  title?: string,
  selection?: string
): Promise<InstapaperResult> {
  if (!INSTAPAPER_USERNAME || !INSTAPAPER_PASSWORD) {
    return {
      success: false,
      error: 'Instapaper credentials not configured'
    };
  }

  const params = new URLSearchParams({
    username: INSTAPAPER_USERNAME,
    password: INSTAPAPER_PASSWORD,
    url
  });

  if (title) {
    params.append('title', title);
  }

  if (selection) {
    params.append('selection', selection);
  }

  try {
    const response = await fetch(`${INSTAPAPER_API_URL}/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params.toString()
    });

    // Instapaper returns 201 on success
    if (response.status === 201) {
      const text = await response.text();
      // Response format: bookmark_id\ttitle\turl
      const parts = text.split('\t');
      const bookmarkId = parts[0] ? parseInt(parts[0]) : undefined;

      return {
        success: true,
        bookmark_id: bookmarkId
      };
    }

    // Handle error codes
    if (response.status === 403) {
      return {
        success: false,
        error: 'Invalid Instapaper username or password'
      };
    }

    if (response.status === 500) {
      return {
        success: false,
        error: 'Instapaper service error'
      };
    }

    return {
      success: false,
      error: `Unexpected response: ${response.status}`
    };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : 'Failed to connect to Instapaper'
    };
  }
}

export function isInstapaperConfigured(): boolean {
  return Boolean(INSTAPAPER_USERNAME && INSTAPAPER_PASSWORD);
}
