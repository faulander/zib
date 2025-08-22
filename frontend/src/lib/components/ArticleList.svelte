<script>
	import { onMount, onDestroy } from 'svelte';
	import { scrollTracker } from '../services/scrollTracker.js';
	import { userSettings } from '$lib/api.js';
	import ArticleModal from './ArticleModal.svelte';
	import DOMPurify from 'dompurify';
	
	let { articles, viewMode = 'list', onMarkRead, onToggleStar } = $props();
	
	// Check if mobile
	let isMobile = $state(false);
	
	function checkMobile() {
		isMobile = window.innerWidth < 768;
	}
	
	// Modal state
	let isModalOpen = $state(false);
	let selectedArticle = $state(null);
	
	// User settings
	let userSettingsData = $state({
		open_webpage_for_short_articles: false,
		short_article_threshold: 500,
		show_timestamps_in_list: true
	});
	
	// Current time for reactive timestamps
	let currentTime = $state(new Date());
	
	// Track article elements for scroll detection
	let articleElements = new Map(); // Map of article.id -> element

	function formatDate(dateString) {
		const date = new Date(dateString);
		const now = new Date();
		const diffTime = Math.abs(now - date);
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays === 1) return 'Today';
		if (diffDays === 2) return 'Yesterday';
		if (diffDays <= 7) return `${diffDays - 1} days ago`;

		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
		});
	}

	function formatTime(dateString) {
		// Treat the date as UTC if it doesn't have timezone info
		const date = dateString.includes('Z') || dateString.includes('+') || dateString.includes('-')
			? new Date(dateString)  // Already has timezone info
			: new Date(dateString + 'Z');  // Add UTC indicator
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}
	
	// Format relative timestamp (reactive to currentTime)
	function formatRelativeTimestamp(dateString) {
		if (!dateString) return '';
		
		// Parse the date - handle both old format (naive) and new format (with timezone)
		let date;
		if (dateString.includes('Z') || dateString.includes('+') || dateString.includes('-')) {
			// Already has timezone info, parse directly
			date = new Date(dateString);
		} else {
			// Naive datetime from backend, treat as UTC
			date = new Date(dateString + 'Z');
		}
		
		const diffMs = currentTime - date;
		const diffMins = Math.floor(diffMs / 60000);
		const diffHours = Math.floor(diffMs / 3600000);
		const diffDays = Math.floor(diffMs / 86400000);
		
		if (diffMins < 1) return 'now';
		if (diffMins < 60) return `${diffMins}m`;
		if (diffHours < 24) {
			const remainingMins = diffMins % 60;
			return remainingMins > 0 ? `${diffHours}h${remainingMins}m` : `${diffHours}h`;
		}
		
		const remainingHours = diffHours % 24;
		const remainingMins = diffMins % 60;
		if (remainingHours > 0 && remainingMins > 0) {
			return `${diffDays}d${remainingHours}h${remainingMins}m`;
		} else if (remainingHours > 0) {
			return `${diffDays}d${remainingHours}h`;
		}
		return `${diffDays}d`;
	}

	async function loadUserSettings() {
		try {
			userSettingsData = await userSettings.get();
		} catch (err) {
			console.error('Failed to load user settings:', err);
		}
	}

	function getContentLength(article) {
		// Strip HTML tags and count text characters
		const textContent = article.content?.replace(/<[^>]*>/g, '') || '';
		return textContent.length;
	}

	function handleArticleClick(article) {
		// Mark as read when clicked (if not already read)
		if (!article.read_status?.is_read) {
			onMarkRead(article);
		}

		// Check if we should open webpage instead of modal for short articles
		if (userSettingsData.open_webpage_for_short_articles) {
			const contentLength = getContentLength(article);
			if (contentLength < userSettingsData.short_article_threshold) {
				// Open webpage in new tab
				window.open(article.url, '_blank');
				return;
			}
		}

		// Open article in modal (default behavior)
		selectedArticle = article;
		isModalOpen = true;
	}
	
	function closeModal() {
		isModalOpen = false;
		selectedArticle = null;
	}
	
	// Start tracking an article element for scroll detection
	function trackArticle(element, article) {
		if (!element || !article) return;
		
		articleElements.set(article.id, element);
		scrollTracker.trackArticle(element, article);
	}
	
	// Stop tracking an article element
	function untrackArticle(article) {
		if (!article) return;
		
		const element = articleElements.get(article.id);
		if (element) {
			scrollTracker.untrackArticle(element);
			articleElements.delete(article.id);
		}
	}
	
	// Svelte action to track article elements
	function trackElement(element, params) {
		const { article } = params;
		
		// Start tracking when element is mounted
		trackArticle(element, article);
		
		return {
			update(newParams) {
				// If article changes, untrack old and track new
				const { article: newArticle } = newParams;
				if (newArticle.id !== article.id) {
					untrackArticle(article);
					trackArticle(element, newArticle);
				}
			},
			destroy() {
				// Stop tracking when element is destroyed
				untrackArticle(article);
			}
		};
	}
	
	// Load user settings on component mount
	let timeUpdateInterval;
	
	onMount(async () => {
		await loadUserSettings();
		
		// Check if mobile
		checkMobile();
		window.addEventListener('resize', checkMobile);
		
		// Update current time every minute for reactive timestamps
		timeUpdateInterval = setInterval(() => {
			currentTime = new Date();
		}, 60000);
		
		return () => {
			window.removeEventListener('resize', checkMobile);
		};
	});

	// Clean up tracking when component is destroyed
	onDestroy(() => {
		// Clean up all tracked articles
		for (const [articleId, element] of articleElements) {
			scrollTracker.untrackArticle(element);
		}
		articleElements.clear();
		
		// Clean up time update interval
		if (timeUpdateInterval) {
			clearInterval(timeUpdateInterval);
		}
	});
</script>

{#if articles.length === 0}
	<div class="flex flex-col items-center justify-center py-12 px-4">
		<div class="text-center">
			<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
			</svg>
			<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No articles yet</h3>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Articles will appear here once feeds are fetched. This may take a few minutes after adding feeds.
			</p>
		</div>
	</div>
{:else if viewMode === 'card'}
	<!-- Card View -->
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4">
		{#each articles as article (article.id)}
			<article
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow cursor-pointer group {article.read_status?.is_read ? 'opacity-60' : ''} flex flex-col h-full"
				onclick={() => handleArticleClick(article)}
				use:trackElement={{ article }}
				data-article-id={article.id}
			>
				<!-- Image Container -->
				<div class="h-32 bg-gray-100 dark:bg-gray-700 relative overflow-hidden flex-shrink-0">
					{#if article.image_url && article.image_url.trim() !== '' && article.image_url.startsWith('http') && !article.image_url.includes('www.china-gadgets.de/www.china-gadgets.de')}
						{@const imageId = `img-${article.id}`}
						{@const placeholderId = `placeholder-${article.id}`}
						<img 
							id={imageId}
							src={article.image_url} 
							alt="{article.title}" 
							class="w-full h-full object-cover"
							style="object-position: center;"
							onerror={(e) => {
								e.target.style.display = 'none';
								document.getElementById(placeholderId).style.display = 'flex';
							}}
						/>
						<!-- Fallback placeholder (hidden by default) -->
						<div id={placeholderId} class="w-full h-full flex items-center justify-center absolute inset-0" style="display: none;">
							<svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
					{:else}
						<!-- Placeholder -->
						<div class="w-full h-full flex items-center justify-center">
							<svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
					{/if}
					
					<!-- Read Status Indicator -->
					<div class="absolute top-2 left-2 w-2 h-2 {article.read_status?.is_read ? 'bg-transparent' : 'bg-orange-500'} rounded-full"></div>
					
					<!-- Star if starred -->
					{#if article.read_status?.is_starred}
						<div class="absolute top-2 right-2">
							<svg class="w-4 h-4 text-yellow-500 fill-current" viewBox="0 0 24 24">
								<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
							</svg>
						</div>
					{/if}
				</div>
				
				<!-- Content -->
				<div class="p-3 flex-1 flex flex-col">
					<!-- Title -->
					<h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2 line-clamp-2 {article.read_status?.is_read ? 'text-gray-500 dark:text-gray-500 line-through' : ''}">
						{article.title}
					</h3>
					
					<!-- Summary -->
					{#if article.summary}
						<div class="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
							{@html DOMPurify.sanitize(article.summary, { 
								ALLOWED_TAGS: ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'span'],
								FORBID_TAGS: ['img', 'picture', 'figure'],
								REMOVE_TAGS: ['img', 'picture', 'figure']
							})}
						</div>
					{/if}
					
					<!-- Footer -->
					<div class="flex items-center justify-between mt-auto">
						<!-- Feed and Date Info -->
						<div class="flex items-center space-x-1 text-xs text-gray-400 dark:text-gray-500 truncate">
							<span class="truncate">
								{article.feed?.title || 'Unknown'}
							</span>
							<span>•</span>
							<span class="whitespace-nowrap">
								{userSettingsData.show_timestamps_in_list ? formatRelativeTimestamp(article.published_date || article.created_at) : formatTime(article.published_date || article.created_at)}
							</span>
						</div>
						
						<!-- Article Actions -->
						<div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
							<!-- Mark Read/Unread -->
							<button
								onclick={(e) => { e.stopPropagation(); onMarkRead(article); }}
								class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
								title={article.read_status?.is_read ? 'Mark as unread' : 'Mark as read'}
							>
								{#if article.read_status?.is_read}
									<svg class="w-3 h-3 text-green-600" fill="currentColor" viewBox="0 0 24 24">
										<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
									</svg>
								{:else}
									<svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
									</svg>
								{/if}
							</button>
							
							<!-- Star/Unstar -->
							<button
								onclick={(e) => { e.stopPropagation(); onToggleStar(article); }}
								class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
								title={article.read_status?.is_starred ? 'Remove from starred' : 'Add to starred'}
							>
								{#if article.read_status?.is_starred}
									<svg class="w-3 h-3 text-yellow-500 fill-current" viewBox="0 0 24 24">
										<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
									</svg>
								{:else}
									<svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
									</svg>
								{/if}
							</button>
						</div>
					</div>
				</div>
			</article>
		{/each}
	</div>
{:else}
	<!-- List View -->
	<div class="divide-y divide-gray-200 dark:divide-gray-700">
		{#each articles as article (article.id)}
			<article
				class="px-4 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer group {article.read_status?.is_read ? 'opacity-50 bg-gray-25 dark:bg-gray-800/30' : ''}"
				onclick={() => handleArticleClick(article)}
				use:trackElement={{ article }}
				data-article-id={article.id}
			>
				<div class="flex items-center justify-between w-full pr-2">
					<!-- Left side: Read indicator + Title -->
					<div class="flex items-center space-x-2 flex-1 min-w-0">
						<!-- Read Status Indicator -->
						<div class="w-1.5 h-1.5 {article.read_status?.is_read ? 'bg-transparent' : 'bg-orange-500'} rounded-full flex-shrink-0"></div>

						<!-- Article Title -->
						<h3 class="{isMobile ? 'text-xs' : 'text-sm'} font-medium text-gray-900 dark:text-white group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors truncate {article.read_status?.is_read ? 'text-gray-500 dark:text-gray-500 line-through' : ''}">
							{article.title}
						</h3>
					</div>

					<!-- Right side: Star -->
					{#if article.read_status?.is_starred}
						<svg class="w-4 h-4 text-yellow-500 fill-current flex-shrink-0" viewBox="0 0 24 24">
							<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
						</svg>
					{/if}

					<!-- Feed and Date Info -->
					<div class="flex items-center space-x-1 text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
						{#if !isMobile}
							<span class="truncate max-w-16 sm:max-w-20 text-xs">
								{article.feed?.title || 'Unknown'}
							</span>
							<span class="text-xs">•</span>
						{/if}
						<span class="whitespace-nowrap text-xs">
							{userSettingsData.show_timestamps_in_list ? formatRelativeTimestamp(article.published_date || article.created_at) : formatTime(article.published_date || article.created_at)}
						</span>
					</div>

					<!-- Article Actions -->
					<div class="flex items-center space-x-0.5 {isMobile ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'} transition-opacity flex-shrink-0">
						<!-- Mark Read/Unread -->
						<button
							onclick={(e) => { e.stopPropagation(); onMarkRead(article); }}
							class="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
							title={article.read_status?.is_read ? 'Mark as unread' : 'Mark as read'}
						>
							{#if article.read_status?.is_read}
								<svg class="w-2.5 h-2.5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
									<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
								</svg>
							{:else}
								<svg class="w-2.5 h-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
							{/if}
						</button>

						<!-- Star/Unstar -->
						<button
							onclick={(e) => { e.stopPropagation(); onToggleStar(article); }}
							class="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
							title={article.read_status?.is_starred ? 'Remove from starred' : 'Add to starred'}
						>
							{#if article.read_status?.is_starred}
								<svg class="w-2.5 h-2.5 text-yellow-500 fill-current" viewBox="0 0 24 24">
									<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
								</svg>
							{:else}
								<svg class="w-2.5 h-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
									</svg>
							{/if}
						</button>
					</div>
				</div>
			</article>
		{/each}
	</div>
{/if}

<!-- Article Modal -->
<ArticleModal 
	isOpen={isModalOpen} 
	article={selectedArticle} 
	onClose={closeModal}
	{onMarkRead}
	{onToggleStar}
/>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
