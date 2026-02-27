import { getSetting } from './settings';
import { logger } from './logger';

export interface EmbeddingResult {
  embedding: number[];
  model: string;
  dimensions: number;
}

interface OllamaEmbeddingResponse {
  embedding: number[];
}

interface OpenAIEmbeddingResponse {
  data: { embedding: number[]; index: number }[];
  model: string;
}

/**
 * Get the effective API key, checking env var as fallback
 */
function getApiKey(): string {
  const settingKey = getSetting('embeddingApiKey');
  if (settingKey) return settingKey;
  return process.env.EMBEDDING_API_KEY || '';
}

/**
 * Generate an embedding for the given text using the configured provider.
 * Returns null if no provider is configured or on error.
 */
export async function generateEmbedding(text: string): Promise<EmbeddingResult | null> {
  const provider = getSetting('embeddingProvider');
  if (provider === 'none' || !provider) return null;

  const model = getSetting('embeddingModel');
  const apiUrl = getSetting('embeddingApiUrl');

  if (!model || !apiUrl) {
    logger.error('embedding', 'Embedding provider configured but model or API URL is missing');
    return null;
  }

  const apiKey = getApiKey();

  try {
    if (provider === 'ollama') {
      return await generateOllamaEmbedding(apiUrl, model, text, apiKey);
    } else {
      // openai and openai-compatible use the same endpoint format
      return await generateOpenAIEmbedding(apiUrl, model, text, apiKey);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error('embedding', `Failed to generate embedding: ${msg}`);
    return null;
  }
}

/**
 * Generate embeddings for multiple texts in a batch.
 * Returns an array of results (null entries for failures).
 */
export async function generateEmbeddings(texts: string[]): Promise<(EmbeddingResult | null)[]> {
  const provider = getSetting('embeddingProvider');
  if (provider === 'none' || !provider) return texts.map(() => null);

  const model = getSetting('embeddingModel');
  const apiUrl = getSetting('embeddingApiUrl');

  if (!model || !apiUrl) return texts.map(() => null);

  const apiKey = getApiKey();

  if (provider === 'ollama') {
    // Ollama doesn't support batch — process sequentially
    const results: (EmbeddingResult | null)[] = [];
    for (const text of texts) {
      try {
        results.push(await generateOllamaEmbedding(apiUrl, model, text, apiKey));
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        logger.error('embedding', `Ollama embedding failed: ${msg}`);
        results.push(null);
      }
    }
    return results;
  }

  // OpenAI / OpenAI-compatible: use batch endpoint
  try {
    return await generateOpenAIEmbeddingBatch(apiUrl, model, texts, apiKey);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error('embedding', `Batch embedding failed: ${msg}`);
    return texts.map(() => null);
  }
}

async function generateOllamaEmbedding(
  apiUrl: string,
  model: string,
  text: string,
  apiKey: string
): Promise<EmbeddingResult> {
  const url = `${apiUrl.replace(/\/$/, '')}/api/embeddings`;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ model, prompt: text })
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Ollama API error ${response.status}: ${body}`);
  }

  const data = (await response.json()) as OllamaEmbeddingResponse;

  return {
    embedding: data.embedding,
    model,
    dimensions: data.embedding.length
  };
}

async function generateOpenAIEmbedding(
  apiUrl: string,
  model: string,
  text: string,
  apiKey: string
): Promise<EmbeddingResult> {
  const url = `${apiUrl.replace(/\/$/, '')}/v1/embeddings`;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ model, input: text })
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenAI API error ${response.status}: ${body}`);
  }

  const data = (await response.json()) as OpenAIEmbeddingResponse;
  const embedding = data.data[0].embedding;

  return {
    embedding,
    model: data.model || model,
    dimensions: embedding.length
  };
}

async function generateOpenAIEmbeddingBatch(
  apiUrl: string,
  model: string,
  texts: string[],
  apiKey: string
): Promise<(EmbeddingResult | null)[]> {
  const url = `${apiUrl.replace(/\/$/, '')}/v1/embeddings`;

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ model, input: texts })
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenAI batch API error ${response.status}: ${body}`);
  }

  const data = (await response.json()) as OpenAIEmbeddingResponse;

  // Sort by index to match input order
  const sorted = data.data.sort((a, b) => a.index - b.index);

  return sorted.map((item) => ({
    embedding: item.embedding,
    model: data.model || model,
    dimensions: item.embedding.length
  }));
}

/**
 * Test the embedding provider connection by generating a test embedding.
 */
export async function testEmbeddingConnection(): Promise<{
  success: boolean;
  dimensions?: number;
  model?: string;
  error?: string;
  latencyMs?: number;
}> {
  const start = Date.now();
  try {
    const result = await generateEmbedding('test connection');
    if (!result) {
      return { success: false, error: 'No embedding provider configured' };
    }
    return {
      success: true,
      dimensions: result.dimensions,
      model: result.model,
      latencyMs: Date.now() - start
    };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : String(err),
      latencyMs: Date.now() - start
    };
  }
}

/**
 * Serialize a number[] embedding to a Float32Array BLOB for SQLite storage.
 */
export function embeddingToBlob(embedding: number[]): Buffer {
  const float32 = new Float32Array(embedding);
  return Buffer.from(float32.buffer);
}

/**
 * Deserialize a BLOB from SQLite back to a number[].
 */
export function blobToEmbedding(blob: Buffer): number[] {
  const float32 = new Float32Array(blob.buffer, blob.byteOffset, blob.byteLength / 4);
  return Array.from(float32);
}

/**
 * Compute cosine similarity between two embedding vectors.
 * Returns a value between -1 and 1 (typically 0 to 1 for normalized embeddings).
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  const denominator = Math.sqrt(normA) * Math.sqrt(normB);
  if (denominator === 0) return 0;

  return dotProduct / denominator;
}
