<script>
	let { articles, onMarkRead, onToggleStar } = $props();
	
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
		const date = new Date(dateString);
		return date.toLocaleTimeString('en-US', { 
			hour: 'numeric', 
			minute: '2-digit',
			hour12: true 
		});
	}
	
	function handleArticleClick(article) {
		// For now, just mark as read when clicked
		if (!article.read_status?.is_read) {
			onMarkRead(article);
		}
	}
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
{:else}
<div class="divide-y divide-gray-200 dark:divide-gray-700">
	{#each articles as article (article.id)}
		<article 
			class="px-3 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer group {article.read_status?.is_read ? 'opacity-60' : ''}"
			onclick={() => handleArticleClick(article)}
		>
			<div class="flex items-center space-x-2">
				<!-- Read Status Indicator -->
				<div class="w-1 h-1 {article.read_status?.is_read ? 'bg-transparent' : 'bg-blue-500'} rounded-full flex-shrink-0"></div>
				
				<!-- Article Title -->
				<h3 class="text-xs font-normal text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate flex-1 {article.read_status?.is_read ? 'text-gray-500 dark:text-gray-500' : ''}">
					{article.title}
				</h3>
				
				<!-- Star if starred -->
				{#if article.read_status?.is_starred}
					<svg class="w-2.5 h-2.5 text-yellow-500 fill-current flex-shrink-0" viewBox="0 0 24 24">
						<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
					</svg>
				{/if}
				
				<!-- Feed and Date Info -->
				<div class="flex items-center space-x-1 text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
					<span class="truncate max-w-20 text-xs">
						{article.feed?.title || 'Unknown'}
					</span>
					<span class="text-xs">•</span>
					<span class="whitespace-nowrap text-xs">
						{formatTime(article.published_date)}
					</span>
				</div>
				
				<!-- Article Actions -->
				<div class="flex items-center space-x-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
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

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>