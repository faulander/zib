import type { Folder, Feed, Article, UnreadCounts } from '$lib/types';

// Settings (persisted)
let hideReadArticles = $state(false);
let compactListView = $state(false);
let highlightColorLight = $state('#fef3c7');
let highlightColorDark = $state('#422006');
let instapaperEnabled = $state(false);

// View state
let viewMode = $state<'list' | 'cards'>('list');
let selectedFolderId = $state<number | null>(null);
let selectedFeedId = $state<number | null>(null);
let selectedArticleId = $state<number | null>(null);
let showUnreadOnly = $state(false);
let showStarredOnly = $state(false);
let sidebarOpen = $state(false);
let articleModalOpen = $state(false);

// Data
let folders = $state<Folder[]>([]);
let feeds = $state<Feed[]>([]);
let articles = $state<Article[]>([]);
let unreadCounts = $state<UnreadCounts>({ total: 0, by_folder: {}, by_feed: {} });
let isLoading = $state(false);
let isRefreshing = $state(false);
let isLoadingMore = $state(false);
let hasMoreArticles = $state(true);

// Computed
const selectedArticle = $derived(articles.find((a) => a.id === selectedArticleId) || null);

const filteredFeeds = $derived(() => {
  if (selectedFolderId === null) return feeds;
  return feeds.filter((f) => f.folder_id === selectedFolderId);
});

const currentFilter = $derived(() => {
  if (showStarredOnly) return 'starred';
  if (selectedFeedId) return `feed:${selectedFeedId}`;
  if (selectedFolderId) return `folder:${selectedFolderId}`;
  return 'all';
});

// Actions
function setViewMode(mode: 'list' | 'cards') {
  viewMode = mode;
}

function selectFolder(id: number | null) {
  selectedFolderId = id;
  selectedFeedId = null;
  showStarredOnly = false;
  // Close sidebar on mobile
  if (typeof window !== 'undefined' && window.innerWidth < 768) {
    sidebarOpen = false;
  }
}

function selectFeed(id: number | null) {
  selectedFeedId = id;
  showStarredOnly = false;
  // Close sidebar on mobile
  if (typeof window !== 'undefined' && window.innerWidth < 768) {
    sidebarOpen = false;
  }
}

function selectArticle(id: number | null) {
  selectedArticleId = id;
  if (id !== null) {
    articleModalOpen = true;
  }
}

function closeArticleModal() {
  articleModalOpen = false;
}

function toggleSidebar() {
  sidebarOpen = !sidebarOpen;
}

function setSidebarOpen(open: boolean) {
  sidebarOpen = open;
}

function setShowUnreadOnly(value: boolean) {
  showUnreadOnly = value;
}

function setShowStarredOnly(value: boolean) {
  showStarredOnly = value;
  if (value) {
    selectedFolderId = null;
    selectedFeedId = null;
  }
}

function setFolders(data: Folder[]) {
  folders = data;
}

function setFeeds(data: Feed[]) {
  feeds = data;
}

function setArticles(data: Article[]) {
  articles = data;
}

function setUnreadCounts(data: UnreadCounts) {
  unreadCounts = data;
}

function setIsLoading(value: boolean) {
  isLoading = value;
}

function setIsRefreshing(value: boolean) {
  isRefreshing = value;
}

function setIsLoadingMore(value: boolean) {
  isLoadingMore = value;
}

function setHasMoreArticles(value: boolean) {
  hasMoreArticles = value;
}

function appendArticles(newArticles: Article[]) {
  articles = [...articles, ...newArticles];
}

function updateArticleInList(id: number, updates: Partial<Article>) {
  articles = articles.map((a) => (a.id === id ? { ...a, ...updates } : a));
}

function removeArticleFromList(id: number) {
  articles = articles.filter((a) => a.id !== id);
}

function setHideReadArticles(value: boolean) {
  hideReadArticles = value;
}

function setCompactListView(value: boolean) {
  compactListView = value;
}

function setHighlightColorLight(value: string) {
  highlightColorLight = value;
}

function setHighlightColorDark(value: string) {
  highlightColorDark = value;
}

function setInstapaperEnabled(value: boolean) {
  instapaperEnabled = value;
}

function initSettings(settings: {
  hideReadArticles: boolean;
  compactListView: boolean;
  highlightColorLight: string;
  highlightColorDark: string;
  instapaperEnabled?: boolean;
}) {
  hideReadArticles = settings.hideReadArticles;
  compactListView = settings.compactListView;
  highlightColorLight = settings.highlightColorLight;
  highlightColorDark = settings.highlightColorDark;
  instapaperEnabled = settings.instapaperEnabled ?? false;
}

// Export reactive getters and setters
export const appStore = {
  // Getters (reactive)
  get hideReadArticles() {
    return hideReadArticles;
  },
  get compactListView() {
    return compactListView;
  },
  get highlightColorLight() {
    return highlightColorLight;
  },
  get highlightColorDark() {
    return highlightColorDark;
  },
  get instapaperEnabled() {
    return instapaperEnabled;
  },
  get viewMode() {
    return viewMode;
  },
  get selectedFolderId() {
    return selectedFolderId;
  },
  get selectedFeedId() {
    return selectedFeedId;
  },
  get selectedArticleId() {
    return selectedArticleId;
  },
  get showUnreadOnly() {
    return showUnreadOnly;
  },
  get showStarredOnly() {
    return showStarredOnly;
  },
  get sidebarOpen() {
    return sidebarOpen;
  },
  get articleModalOpen() {
    return articleModalOpen;
  },
  get folders() {
    return folders;
  },
  get feeds() {
    return feeds;
  },
  get articles() {
    return articles;
  },
  get unreadCounts() {
    return unreadCounts;
  },
  get isLoading() {
    return isLoading;
  },
  get isRefreshing() {
    return isRefreshing;
  },
  get isLoadingMore() {
    return isLoadingMore;
  },
  get hasMoreArticles() {
    return hasMoreArticles;
  },
  get selectedArticle() {
    return selectedArticle;
  },
  get filteredFeeds() {
    return filteredFeeds;
  },
  get currentFilter() {
    return currentFilter;
  },

  // Actions
  setViewMode,
  selectFolder,
  selectFeed,
  selectArticle,
  closeArticleModal,
  toggleSidebar,
  setSidebarOpen,
  setShowUnreadOnly,
  setShowStarredOnly,
  setFolders,
  setFeeds,
  setArticles,
  setUnreadCounts,
  setIsLoading,
  setIsRefreshing,
  setIsLoadingMore,
  setHasMoreArticles,
  appendArticles,
  updateArticleInList,
  removeArticleFromList,
  setHideReadArticles,
  setCompactListView,
  setHighlightColorLight,
  setHighlightColorDark,
  setInstapaperEnabled,
  initSettings
};
