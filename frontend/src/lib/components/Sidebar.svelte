<script>
	import { onMount } from 'svelte';
	import { Settings, CheckCircle } from '@lucide/svelte';
	import { 
		categoriesStore, 
		feedsStore, 
		selectedCategory, 
		selectedFeed, 
		unreadCounts,
		apiActions 
	} from '../stores/api.js';
	
	// Local state for UI
	let showAllArticles = $state(true);
	let hoveredCategory = $state(null);
	
	// Use stores with Svelte 5 runes
	let categories = $derived($categoriesStore);
	let feeds = $derived($feedsStore);
	let counts = $derived($unreadCounts);
	
	
	function selectCategoryHandler(category) {
		if ($selectedCategory?.id === category.id) {
			selectedCategory.set(null);
		} else {
			selectedCategory.set(category);
		}
		selectedFeed.set(null);
		showAllArticles = false;
		
		// Load fresh articles for this category (resets infinite scroll)
		apiActions.loadArticles();
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
	}
	
	function showAll() {
		selectedCategory.set(null);
		selectedFeed.set(null);
		showAllArticles = true;
		
		// Load fresh articles (resets infinite scroll)
		apiActions.loadArticles();
	}
	
	async function refreshFeeds() {
		try {
			await apiActions.refreshAllFeeds();
		} catch (err) {
			console.error('Failed to refresh feeds:', err);
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
	
	// Format last updated time
	function formatLastUpdated(lastFetched) {
		if (!lastFetched) return 'Never';
		
		const date = new Date(lastFetched);
		const now = new Date();
		const diffMs = now - date;
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);
		
		if (diffMins < 1) return 'Just now';
		if (diffMins < 60) return `${diffMins}m ago`;
		if (diffHours < 24) return `${diffHours}h ago`;
		return `${diffDays}d ago`;
	}
	
	// Mark all articles in a category as read
	async function markCategoryAsRead(categoryId) {
		try {
			await apiActions.markCategoryAsRead(categoryId);
		} catch (err) {
			console.error('Failed to mark category as read:', err);
		}
	}
</script>

<aside class="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
	<!-- Sidebar Header -->
	<div class="p-2 border-b border-gray-200 dark:border-gray-700">
		<h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">Feeds</h2>
		
		<!-- All Articles -->
		<button
			onclick={showAll}
			class="w-full flex items-center justify-between p-1.5 rounded transition-colors {showAllArticles ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
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
					<button
						onclick={() => selectCategoryHandler(category)}
						class="flex-1 flex items-center space-x-1.5 p-1.5 rounded transition-colors {$selectedCategory?.id === category.id ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
					>
						<div 
							class="w-1.5 h-1.5 rounded-full flex-shrink-0" 
							style="background-color: {category.color || '#6B7280'}"
						></div>
						<span class="text-xs font-medium truncate">{category.name}</span>
					</button>
					<div 
						class="text-xs bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded-full cursor-pointer hover:bg-red-100 dark:hover:bg-red-900 transition-colors flex-shrink-0"
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
				{#if $selectedCategory?.id === category.id}
					<div class="ml-4 space-y-0.5">
						{#each getCategoryFeeds(category.id) as feed}
							<button
								onclick={() => selectFeedHandler(feed)}
								class="w-full flex items-center justify-between p-1 rounded text-left transition-colors {$selectedFeed?.id === feed.id ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
							>
								<div class="flex-1 min-w-0">
									<p class="text-xs font-normal truncate">{feed.title}</p>
								</div>
								<span class="text-xs bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded-full ml-1">
									{counts.feeds[feed.id] || 0}
								</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>
	
	<!-- Sidebar Footer -->
	<div class="p-2 border-t border-gray-200 dark:border-gray-700 space-y-2">
		<!-- Settings Link -->
		<a 
			href="/settings"
			class="w-full flex items-center space-x-2 p-1.5 rounded transition-colors text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
		>
			<Settings class="w-3 h-3" />
			<span class="text-xs font-medium">Settings</span>
		</a>
		
		<!-- Status and Refresh -->
		<div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
			<span>Last: {formatLastUpdated(feeds[0]?.last_fetched)}</span>
			<button 
				onclick={refreshFeeds}
				class="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
				title="Refresh feeds"
			>
				<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
			</button>
		</div>
	</div>
</aside>