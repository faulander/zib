<script>
	import { onMount, onDestroy } from 'svelte';
	import { Settings, CheckCircle, ChevronRight, ChevronDown } from '@lucide/svelte';
	import { 
		categoriesStore, 
		feedsStore, 
		selectedCategory, 
		selectedFeed, 
		unreadCounts,
		searchQuery,
		apiActions 
	} from '../stores/api.js';
	import { closeSidebar } from '../stores/sidebar.js';
	import { refreshStatus, refreshStatusService } from '../services/refreshStatusService.js';
	
	let { isMobile = false, onClose = closeSidebar } = $props();
	
	// Local state for UI
	let showAllArticles = $state(true);
	let hoveredCategory = $state(null);
	let expandedCategories = $state(new Set()); // Track which categories are expanded
	let currentTime = $state(new Date()); // Track current time for relative timestamps
	
	// Use stores with Svelte 5 runes
	let categories = $derived($categoriesStore);
	let feeds = $derived($feedsStore);
	let counts = $derived($unreadCounts);
	
	// Use the store directly with $ syntax for proper reactivity
	let refreshData = $derived($refreshStatus);
	
	// Derive individual values from the store for cleaner template access
	let refreshingStatus = $derived(refreshData?.is_refreshing || false);
	let secondsUntilRefresh = $derived(refreshData?.seconds_until_refresh || null);
	let intervalMinutes = $derived(refreshData?.interval_minutes || 5);
	let lastRefreshCompleted = $derived(refreshData?.last_refresh_completed || null);
	
	
	// Reload counters when search changes
	$effect(() => {
		const currentSearch = $searchQuery;
		// Debounce the counter reload to avoid too many API calls
		const timeoutId = setTimeout(() => {
			if (categories && feeds && categories.length > 0 && feeds.length > 0) {
				console.log('Search changed, reloading counters:', currentSearch);
				apiActions.loadUnreadCounts();
			}
		}, 500); // 500ms debounce
		
		return () => clearTimeout(timeoutId);
	});
	
	
	function selectCategoryHandler(category) {
		if ($selectedCategory?.id === category.id) {
			selectedCategory.set(null);
		} else {
			selectedCategory.set(category);
		}
		selectedFeed.set(null);
		showAllArticles = false;
		
		// Load fresh articles for this category (resets infinite scroll)
		console.log('Loading articles for category:', category);
		apiActions.loadArticles().catch(err => {
			console.error('Failed to load articles:', err);
		});
		
		// Close sidebar on mobile after selection
		if (isMobile) {
			onClose();
		}
	}
	
	function toggleCategoryExpansion(categoryId) {
		const newExpanded = new Set(expandedCategories);
		if (newExpanded.has(categoryId)) {
			newExpanded.delete(categoryId);
		} else {
			newExpanded.add(categoryId);
		}
		expandedCategories = newExpanded;
	}
	
	function selectFeedHandler(feed) {
		if ($selectedFeed?.id === feed.id) {
			selectedFeed.set(null);
		} else {
			selectedFeed.set(feed);
		}
		selectedCategory.set(null);
		showAllArticles = false;
		
		// Load fresh articles for this feed (resets infinite scroll)
		apiActions.loadArticles();
		
		// Close sidebar on mobile after selection
		if (isMobile) {
			onClose();
		}
	}
	
	function showAll() {
		selectedCategory.set(null);
		selectedFeed.set(null);
		showAllArticles = true;
		
		// Load fresh articles (resets infinite scroll)
		apiActions.loadArticles();
		
		// Close sidebar on mobile after selection
		if (isMobile) {
			onClose();
		}
	}
	
	
	// Calculate total unread count from all categories
	let totalUnread = $derived(
		Object.values(counts.categories).reduce((sum, count) => sum + count, 0)
	);
	
	// Get feeds for a category
	function getCategoryFeeds(categoryId) {
		return feeds.filter(feed => feed.category_id === categoryId);
	}
	
	// Format last updated time (reactive to currentTime)
	function formatLastUpdated(lastFetched) {
		if (!lastFetched) return 'Never';
		
		const date = new Date(lastFetched);
		const diffMs = currentTime - date;
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);
		
		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		return `${diffDays}d ago`;
	}
	
	// Update timestamp every minute and countdown every second
	let timeUpdateInterval;
	let countdownInterval;
	
	onMount(() => {
		// Update current time every minute
		timeUpdateInterval = setInterval(() => {
			currentTime = new Date();
		}, 60000); // Update every minute
		
		// Update countdown every second
		countdownInterval = setInterval(() => {
			// Update the countdown by decrementing seconds_until_refresh
			if (status.seconds_until_refresh && status.seconds_until_refresh > 0) {
				refreshStatus.update(s => ({
					...s,
					seconds_until_refresh: Math.max(0, s.seconds_until_refresh - 1)
				}));
			}
		}, 1000); // Update every second
		
		// Listen for backend refresh completion
		const handleRefreshCompleted = () => {
			// Reload feeds, categories and articles
			apiActions.loadFeeds();
			apiActions.loadCategories();
			apiActions.loadArticles();
			apiActions.loadUnreadCounts();
		};
		
		window.addEventListener('backend-refresh-completed', handleRefreshCompleted);
		
		return () => {
			window.removeEventListener('backend-refresh-completed', handleRefreshCompleted);
		};
	});
	
	onDestroy(() => {
		if (timeUpdateInterval) {
			clearInterval(timeUpdateInterval);
		}
		if (countdownInterval) {
			clearInterval(countdownInterval);
		}
	});
	
	// Mark all articles in a category as read
	async function markCategoryAsRead(categoryId) {
		try {
			await apiActions.markCategoryAsRead(categoryId);
		} catch (err) {
			console.error('Failed to mark category as read:', err);
		}
	}
</script>

<aside class="w-80 h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col {isMobile ? 'shadow-2xl' : ''}">
	<!-- Sidebar Header -->
	<div class="p-2 border-b border-gray-200 dark:border-gray-700">
		<h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">Feeds</h2>
		
		<!-- Settings and Status (at the very top) -->
		<div class="mb-2 space-y-2">
			<!-- Settings Link -->
			<a 
				href="/settings"
				class="w-full flex items-center space-x-2 p-1.5 rounded transition-colors text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
			>
				<Settings class="w-3 h-3" />
				<span class="text-xs font-medium">Settings</span>
			</a>
			
			<!-- Refresh Status -->
			<div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
				<span>
					{#if refreshingStatus === true}
						<span class="flex items-center space-x-1">
							<svg class="w-3 h-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
							</svg>
							<span>Refreshing...</span>
						</span>
					{:else if secondsUntilRefresh && secondsUntilRefresh > 0}
						Next: {refreshStatusService.formatTimeUntilRefresh(secondsUntilRefresh)}
					{:else}
						Auto-refresh ready
					{/if}
				</span>
				{#if lastRefreshCompleted}
					<span class="text-gray-400 dark:text-gray-500">
						Last: {formatLastUpdated(new Date(lastRefreshCompleted).getTime())}
					</span>
				{/if}
			</div>
		</div>
		
		<!-- Divider -->
		<div class="border-t border-gray-200 dark:border-gray-700 my-2"></div>
		
		<!-- All Articles -->
		<button
			onclick={showAll}
			class="w-full flex items-center justify-between p-1.5 rounded transition-colors {showAllArticles ? 'bg-orange-500 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
		>
			<div class="flex items-center space-x-1.5">
				<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14-7l-7 7-7-7" />
				</svg>
				<span class="text-xs font-medium">All Articles</span>
			</div>
			<span class="text-xs bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded-full">
				{totalUnread}
			</span>
		</button>
	</div>
	
	<!-- Categories and Feeds -->
	<div class="flex-1 overflow-y-auto p-2 space-y-0.5">
		{#each categories as category}
			<div class="space-y-1">
				<!-- Category Header -->
				<div class="flex items-center space-x-1">
					<!-- Chevron for expanding/collapsing feeds -->
					<button
						onclick={() => toggleCategoryExpansion(category.id)}
						class="p-0.5 rounded transition-colors text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
					>
						{#if expandedCategories.has(category.id)}
							<ChevronDown class="w-3 h-3" />
						{:else}
							<ChevronRight class="w-3 h-3" />
						{/if}
					</button>
					
					<!-- Category name button -->
					<button
						onclick={() => selectCategoryHandler(category)}
						class="flex-1 flex items-center space-x-1.5 p-1.5 rounded transition-colors {$selectedCategory?.id === category.id ? 'bg-orange-500 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
					>
						<span class="text-xs font-medium truncate">{category.name}</span>
					</button>
					
					<!-- Unread count / Mark as read button -->
					<div 
						class="text-xs px-1 py-0.5 rounded-full cursor-pointer hover:bg-red-100 dark:hover:bg-red-900 transition-colors flex-shrink-0 {$selectedCategory?.id === category.id ? 'bg-orange-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
						onmouseenter={() => hoveredCategory = category.id}
						onmouseleave={() => hoveredCategory = null}
						onclick={() => markCategoryAsRead(category.id)}
						title="Mark all articles in this category as read"
					>
						{#if hoveredCategory === category.id && (counts.categories[category.id] || 0) > 0}
							<CheckCircle class="w-3 h-3" />
						{:else}
							{counts.categories[category.id] || 0}
						{/if}
					</div>
				</div>
				
				<!-- Category Feeds -->
				{#if expandedCategories.has(category.id)}
					<div class="ml-4 space-y-0.5">
						{#each getCategoryFeeds(category.id) as feed}
							<button
								onclick={() => selectFeedHandler(feed)}
								class="w-full flex items-center justify-between p-1 rounded text-left transition-colors {$selectedFeed?.id === feed.id ? 'bg-orange-500 text-white' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
							>
								<div class="flex-1 min-w-0">
									<p class="text-xs font-normal truncate">{feed.title}</p>
								</div>
								<span class="text-xs px-1 py-0.5 rounded-full ml-1 {$selectedFeed?.id === feed.id ? 'bg-orange-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}">
									{counts.feeds[feed.id] || 0}
								</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
</aside>