<script>
	import { onMount } from 'svelte';
	import ArticleList from '$lib/components/ArticleList.svelte';
	import { articlesStore, isLoading, isLoadingMore, hasMoreArticles, selectedCategory, selectedFeed, selectedFilter, apiActions } from '$lib/stores/api.js';
	import { userSettings, articles as articlesApi } from '$lib/api.js';
	import { isMobile, isSidebarOpen, toggleSidebar } from '$lib/stores/sidebar.js';
	import { scrollTracker } from '$lib/services/scrollTracker.js';
	
	// Use stores for mobile and sidebar state
	let mobileState = $derived($isMobile);
	let sidebarState = $derived($isSidebarOpen);
	
	// View mode state (list or card) - will be loaded from user settings
	let viewMode = $state('list'); // 'list' or 'card'
	
	// Use real articles from API with Svelte 5 runes
	let allArticles = $derived($articlesStore);
	
	// Filter articles based on current filter to handle local filtering
	// This complements backend filtering and handles articles marked as read locally
	let articles = $derived.by(() => {
		if (currentFilter === 'unread') {
			return allArticles.filter(article => !article.read_status?.is_read);
		} else if (currentFilter === 'starred') {
			return allArticles.filter(article => article.read_status?.is_starred);
		}
		return allArticles; // 'all' filter shows everything
	});
	
	let loading = $derived($isLoading);
	let loadingMore = $derived($isLoadingMore);
	let moreAvailable = $derived($hasMoreArticles);
	let currentCategory = $derived($selectedCategory);
	let currentFeed = $derived($selectedFeed);
	let currentFilter = $derived($selectedFilter);
	
	// Dynamic header title
	let headerTitle = $derived.by(() => {
		if (currentFeed) {
			return `All ${currentFeed.title} Articles`;
		} else if (currentCategory) {
			return `All ${currentCategory.name} Articles`;
		} else {
			return 'All Articles';
		}
	});

	// Debug category and article loading
	$effect(() => {
		console.log('=== PAGE STATE DEBUG ===');
		console.log('Selected Category:', currentCategory);
		console.log('Selected Feed:', currentFeed);
		console.log('Header Title:', headerTitle);
		console.log('Articles Length:', articles.length);
		console.log('Loading:', loading);
		console.log('More Available:', moreAvailable);
		if (articles.length > 0) {
			console.log('First article feed:', articles[0].feed?.title);
			console.log('First article category:', articles[0].feed?.category?.name);
		}
		console.log('========================');
	});
	
	let scrollContainer;

	// Track when end message is visible to show mark-as-read button
	let endMessageVisible = $state(false);
	let showMarkAllReadButton = $state(false);
	
	$effect(() => {
		// Show mark-as-read button when we reach the end and there are unread articles
		if (articles.length > 0 && !moreAvailable && !loadingMore && endMessageVisible) {
			const hasUnreadArticles = articles.some(article => !article.read_status?.is_read);
			showMarkAllReadButton = hasUnreadArticles;
		} else {
			showMarkAllReadButton = false;
		}
	});
	
	// Function to mark all articles in current view as read
	async function markAllCurrentRead() {
		try {
			console.log('markAllCurrentRead called');
			console.log('Selected category:', $selectedCategory);
			console.log('Articles length:', articles.length);
			
			// If we're viewing a specific category, mark the entire category as read
			if ($selectedCategory) {
				console.log('Marking category as read:', $selectedCategory.id);
				await apiActions.markCategoryAsRead($selectedCategory.id);
			} else {
				// Mark all currently loaded articles as read
				const unreadArticleIds = articles
					.filter(article => !article.read_status?.is_read)
					.map(article => article.id);
				
				console.log('Marking individual articles as read:', unreadArticleIds.length, 'articles');
				
				if (unreadArticleIds.length > 0) {
					await articlesApi.bulkMarkRead(unreadArticleIds);
				}
			}
			
			// Reload articles to refresh the view
			await apiActions.loadArticles();
			
			// Reload unread counts to update the sidebar
			await apiActions.loadUnreadCounts();
			
			// Hide the button after successful action
			showMarkAllReadButton = false;
			
		} catch (error) {
			console.error('Failed to mark articles as read:', error);
		}
	}

	// Intersection observer action to detect when "No more articles to load" is visible
	function endMessageObserver(element) {
		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					endMessageVisible = entry.isIntersecting;
					if (entry.isIntersecting) {
						console.log('"No more articles to load" message is now visible');
					}
				});
			},
			{ threshold: 0.1 }
		);

		observer.observe(element);

		return {
			destroy() {
				observer.disconnect();
			}
		};
	}

	// Filter handlers
	function setFilter(filter) {
		selectedFilter.set(filter);
		// Reload articles with new filter
		apiActions.loadArticles();
	}
	
	// View mode handlers
	async function setViewMode(mode) {
		viewMode = mode;
		// Save preference to backend
		try {
			const currentSettings = await userSettings.get();
			await userSettings.update({
				...currentSettings,
				preferred_view_mode: mode
			});
		} catch (error) {
			console.error('Failed to save view mode preference:', error);
		}
	}

	async function loadUserSettings() {
		try {
			const settings = await userSettings.get();
			viewMode = settings.preferred_view_mode || 'list';
		} catch (error) {
			console.error('Failed to load user settings:', error);
		}
	}
	
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

	onMount(async () => {
		// Load user settings
		await loadUserSettings();
		
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
	<div class="border-b border-gray-200 dark:border-gray-700 px-4 md:px-6 py-3 md:py-4 bg-white dark:bg-gray-800">
		<div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
			<div>
				<h1 class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white">{headerTitle}</h1>
			</div>
			<div class="flex items-center space-x-2 md:space-x-3">
				<!-- Filter Buttons with Icons -->
				<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5 md:p-1">
					<button 
						onclick={() => setFilter('all')}
						class="p-1.5 md:p-2 rounded transition-colors {currentFilter === 'all' ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}"
						title="All Articles"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14-7H3a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z"/>
						</svg>
					</button>
					<button 
						onclick={() => setFilter('unread')}
						class="p-1.5 md:p-2 rounded transition-colors {currentFilter === 'unread' ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}"
						title="Unread Articles"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<circle cx="12" cy="12" r="10"/>
							<path d="m9 12 2 2 4-4"/>
						</svg>
					</button>
					<button 
						onclick={() => setFilter('starred')}
						class="p-1.5 md:p-2 rounded transition-colors {currentFilter === 'starred' ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}"
						title="Starred Articles"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
						</svg>
					</button>
				</div>

				<!-- View Mode Toggle -->
				<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5 md:p-1">
					<button 
						onclick={() => setViewMode('list')}
						class="p-1.5 md:p-2 rounded transition-colors {viewMode === 'list' ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}"
						title="List View"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
						</svg>
					</button>
					<button 
						onclick={() => setViewMode('card')}
						class="p-1.5 md:p-2 rounded transition-colors {viewMode === 'card' ? 'bg-orange-500 text-white shadow-sm' : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'}"
						title="Card View"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
						</svg>
					</button>
				</div>
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
				{viewMode}
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
				<div 
					class="flex flex-col items-center justify-center py-4 space-y-3"
					use:endMessageObserver
				>
					<span class="text-sm text-gray-500 dark:text-gray-400">No more articles to load</span>
					
					{#if showMarkAllReadButton}
						<button
							onclick={markAllCurrentRead}
							class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors duration-200 flex items-center gap-2"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
							</svg>
							Want to mark all read?
						</button>
					{/if}
				</div>
			{/if}
		{/if}
	</div>
</div>
