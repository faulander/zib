import type { Folder, Feed, Article, UnreadCounts } from '$lib/types';

// View state
let viewMode = $state<'list' | 'cards'>('list');
let selectedFolderId = $state<number | null>(null);
let selectedFeedId = $state<number | null>(null);
let selectedArticleId = $state<number | null>(null);
let showUnreadOnly = $state(false);
let showStarredOnly = $state(false);
let sidebarOpen = $state(true);
let articleModalOpen = $state(false);

// Data
let folders = $state<Folder[]>([]);
let feeds = $state<Feed[]>([]);
let articles = $state<Article[]>([]);
let unreadCounts = $state<UnreadCounts>({ total: 0, by_folder: {}, by_feed: {} });
let isLoading = $state(false);
let isRefreshing = $state(false);

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
}

function selectFeed(id: number | null) {
  selectedFeedId = id;
  showStarredOnly = false;
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

function updateArticleInList(id: number, updates: Partial<Article>) {
  articles = articles.map((a) => (a.id === id ? { ...a, ...updates } : a));
}

function removeArticleFromList(id: number) {
  articles = articles.filter((a) => a.id !== id);
}

// Export reactive getters and setters
export const appStore = {
  // Getters (reactive)
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
  updateArticleInList,
  removeArticleFromList
};
