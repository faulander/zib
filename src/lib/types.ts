// Database row types
export interface FolderRow {
  id: number;
  name: string;
  position: number;
  created_at: string;
}

export interface FeedRow {
  id: number;
  folder_id: number | null;
  title: string;
  feed_url: string;
  site_url: string | null;
  description: string | null;
  favicon_url: string | null;
  last_fetched_at: string | null;
  last_new_article_at: string | null;
  last_error: string | null;
  error_count: number;
  fetch_priority: number;
  ttl_minutes: number | null;
  position: number;
  created_at: string;
}

export interface ArticleRow {
  id: number;
  feed_id: number;
  guid: string;
  title: string;
  url: string | null;
  author: string | null;
  published_at: string | null;
  rss_content: string | null;
  full_content: string | null;
  image_url: string | null;
  is_read: number;
  is_starred: number;
  created_at: string;
}

// API types with computed fields
export interface Folder extends FolderRow {
  unread_count?: number;
  feeds?: Feed[];
}

export interface Feed extends FeedRow {
  unread_count?: number;
  folder_name?: string | null;
}

export interface Article extends Omit<ArticleRow, 'is_read' | 'is_starred'> {
  is_read: boolean;
  is_starred: boolean;
  feed_title?: string | null;
  feed_favicon?: string | null;
  // Similarity grouping metadata (added when grouping is enabled)
  similar_count?: number;
  similar_ids?: number[];
}

// Similar articles grouping
export interface ArticleGroup {
  main: Article;
  similar: Article[];
}

// Input types for creating/updating
export interface CreateFolder {
  name: string;
  position?: number;
}

export interface UpdateFolder {
  name?: string;
  position?: number;
}

export interface CreateFeed {
  folder_id?: number | null;
  title: string;
  feed_url: string;
  site_url?: string;
  description?: string;
}

export interface UpdateFeed {
  folder_id?: number | null;
  title?: string;
  feed_url?: string;
  site_url?: string;
  description?: string;
  position?: number;
}

export interface UpdateArticle {
  is_read?: boolean;
  is_starred?: boolean;
}

// Filter types for querying
export interface ArticleFilters {
  feed_id?: number;
  folder_id?: number;
  is_read?: boolean;
  is_starred?: boolean;
  limit?: number;
  offset?: number; // deprecated, use cursor-based pagination
  before_date?: string; // cursor: fetch articles before this date
  before_id?: number; // cursor: for tie-breaking when dates are equal
}

export interface MarkReadFilters {
  feed_id?: number;
  folder_id?: number;
  older_than?: 'day' | 'week' | 'month' | 'all';
}

// OPML types
export interface OPMLOutline {
  title: string;
  xmlUrl?: string;
  htmlUrl?: string;
  children?: OPMLOutline[];
}

// Settings
export interface Settings {
  instapaper_username?: string;
  instapaper_password?: string;
  refresh_interval_minutes?: number;
  view_mode?: 'list' | 'cards';
}

// Filter types
export interface Filter {
  id: number;
  name: string;
  rule: string;
  is_enabled: boolean;
  created_at: string;
}

export interface CreateFilter {
  name: string;
  rule: string;
  is_enabled?: boolean;
}

export interface UpdateFilter {
  name?: string;
  rule?: string;
  is_enabled?: boolean;
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface UnreadCounts {
  total: number;
  by_folder: Record<number, number>;
  by_feed: Record<number, number>;
}

// Feed statistics for adaptive refresh rates
export interface FeedStatistics {
  feed_id: number;
  avg_articles_per_day: number;
  articles_last_7_days: number;
  articles_last_30_days: number;
  avg_publish_gap_hours: number | null;
  total_articles_fetched: number;
  total_articles_read: number;
  total_articles_starred: number;
  read_rate: number;
  calculated_ttl_minutes: number | null;
  ttl_override_minutes: number | null;
  ttl_calculation_reason: string | null;
  last_calculated_at: string | null;
}
