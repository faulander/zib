<script>
	import { onMount } from 'svelte';
	import ArticleList from '$lib/components/ArticleList.svelte';
	import { articlesStore, isLoading, isLoadingMore, hasMoreArticles, apiActions } from '$lib/stores/api.js';
	
	// Use real articles from API with Svelte 5 runes
	let articles = $derived($articlesStore);
	let loading = $derived($isLoading);
	let loadingMore = $derived($isLoadingMore);
	let moreAvailable = $derived($hasMoreArticles);
	
	let scrollContainer;
	
	async function handleMarkRead(article) {
		try {
			const newReadStatus = !article.read_status?.is_read;
			await apiActions.markArticleRead(article.id, newReadStatus);
		} catch (err) {
			console.error('Failed to mark article as read:', err);
		}
	}
	
	async function handleToggleStar(article) {
		try {
			const newStarStatus = !article.read_status?.is_starred;
			await apiActions.starArticle(article.id, newStarStatus);
		} catch (err) {
			console.error('Failed to star article:', err);
		}
	}
	
	async function handleMarkAllRead() {
		try {
			await apiActions.markAllRead();
		} catch (err) {
			console.error('Failed to mark all as read:', err);
		}
	}

	// Infinite scroll logic
	function handleScroll() {
		if (!scrollContainer || loadingMore || !moreAvailable) return;
		
		const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
		const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
		
		// Load more when scrolled 80% down
		if (scrollPercentage > 0.8) {
			apiActions.loadMoreArticles().catch(err => {
				console.error('Failed to load more articles:', err);
			});
		}
	}

	onMount(() => {
		// Set up scroll listener
		if (scrollContainer) {
			scrollContainer.addEventListener('scroll', handleScroll);
			return () => {
				scrollContainer.removeEventListener('scroll', handleScroll);
			};
		}
	});
</script>

<div class="h-full flex flex-col">
	<!-- Content Header -->
	<div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4 bg-white dark:bg-gray-800">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">All Articles</h1>
			</div>
			<div class="flex items-center space-x-2">
				<!-- View Options -->
				<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
					<button class="px-3 py-1 text-sm font-medium bg-white dark:bg-gray-600 text-gray-900 dark:text-white rounded shadow-sm">
						All
					</button>
					<button class="px-3 py-1 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
						Unread
					</button>
					<button class="px-3 py-1 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">
						Starred
					</button>
				</div>
				
				<!-- Mark All Read -->
				<button 
					onclick={handleMarkAllRead}
					class="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors"
				>
					Mark All Read
				</button>
			</div>
		</div>
	</div>
	
	<!-- Article List -->
	<div class="flex-1 overflow-y-auto" bind:this={scrollContainer}>
		{#if loading}
			<div class="flex items-center justify-center h-64">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>
		{:else}
			<ArticleList 
				{articles} 
				onMarkRead={handleMarkRead}
				onToggleStar={handleToggleStar}
			/>
			
			<!-- Loading More Indicator -->
			{#if loadingMore}
				<div class="flex items-center justify-center py-4">
					<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
					<span class="ml-2 text-sm text-gray-500 dark:text-gray-400">Loading more articles...</span>
				</div>
			{:else if !moreAvailable && articles.length > 0}
				<div class="flex items-center justify-center py-4">
					<span class="text-sm text-gray-500 dark:text-gray-400">No more articles to load</span>
				</div>
			{/if}
		{/if}
	</div>
</div>
