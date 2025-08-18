<script>
	import Modal from './Modal.svelte';
	import { Star, ExternalLink, Clock, User } from '@lucide/svelte';
	import DOMPurify from 'dompurify';
	
	let { isOpen = false, article = null, onClose, onMarkRead, onToggleStar } = $props();
	
	function formatDate(dateString) {
		if (!dateString) return '';
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	function handleMarkRead() {
		if (article && onMarkRead) {
			onMarkRead(article);
		}
	}
	
	function handleToggleStar() {
		if (article && onToggleStar) {
			onToggleStar(article);
		}
	}
	
	function openOriginal() {
		if (article?.url) {
			window.open(article.url, '_blank', 'noopener,noreferrer');
		}
	}
	
	// Sanitize HTML content using DOMPurify
	function sanitizeContent(html) {
		if (!html) return '';
		
		// Configure DOMPurify to allow basic formatting tags while removing ALL attributes except href
		const cleanHtml = DOMPurify.sanitize(html, {
			ALLOWED_TAGS: ['p', 'br', 'a', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre', 'img'],
			ALLOWED_ATTR: ['href', 'src', 'alt'],
			FORBID_ATTR: ['style', 'class', 'id', 'color', 'bgcolor', 'face', 'size'],
			FORBID_TAGS: ['font', 'center'],
			SANITIZE_DOM: true,
			KEEP_CONTENT: true,
			ALLOW_DATA_ATTR: false,
			ALLOW_UNKNOWN_PROTOCOLS: false
		});
		
		// Post-process to ensure all links open in new window and remove any remaining style attributes
		const temp = document.createElement('div');
		temp.innerHTML = cleanHtml;
		
		// Remove ALL style attributes that might have slipped through
		temp.querySelectorAll('*').forEach(element => {
			element.removeAttribute('style');
			element.removeAttribute('color');
			element.removeAttribute('bgcolor');
			element.removeAttribute('face');
			element.removeAttribute('size');
			element.removeAttribute('align');
		});
		
		// Ensure all links open in new window with proper security
		const links = temp.querySelectorAll('a[href]');
		links.forEach(link => {
			link.setAttribute('target', '_blank');
			link.setAttribute('rel', 'noopener noreferrer');
		});
		
		// Limit image sizes
		const images = temp.querySelectorAll('img');
		images.forEach(img => {
			img.removeAttribute('style');
			img.removeAttribute('width');
			img.removeAttribute('height');
		});
		
		return temp.innerHTML;
	}
</script>

<Modal {isOpen} title={article?.title || ''} onclose={onClose}>
	{#snippet children()}
		{#if article}
			<div class="px-6 py-4">
				<!-- Article Meta -->
				<div class="mb-6 space-y-3">
					<!-- Feed and Date -->
					<div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
						<div class="flex items-center space-x-2">
							<span class="font-medium">{article.feed?.title || 'Unknown Feed'}</span>
							{#if article.feed?.category}
								<span>•</span>
								<span>{article.feed.category.name}</span>
							{/if}
						</div>
						<div class="flex items-center space-x-1">
							<Clock size={14} />
							<span>{formatDate(article.published_date)}</span>
						</div>
					</div>
					
					<!-- Author if available -->
					{#if article.author}
						<div class="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400">
							<User size={14} />
							<span>By {article.author}</span>
						</div>
					{/if}
					
					<!-- Reading time -->
					{#if article.estimated_reading_time}
						<div class="text-sm text-gray-600 dark:text-gray-400">
							<span>{article.estimated_reading_time} min read</span>
						</div>
					{/if}
				</div>
				
				<!-- Article Content -->
				<div class="prose prose-sm dark:prose-invert max-w-none article-content">
					{#if article.content}
						{@html sanitizeContent(article.content)}
					{:else if article.summary}
						<p class="text-gray-600 dark:text-gray-400 italic">
							{article.summary}
						</p>
						<p class="text-sm text-gray-500 dark:text-gray-500 mt-4">
							Full content not available. <button onclick={openOriginal} class="text-blue-600 dark:text-blue-400 hover:underline">Read on original site</button>
						</p>
					{:else}
						<p class="text-gray-600 dark:text-gray-400 italic">
							No content available. <button onclick={openOriginal} class="text-blue-600 dark:text-blue-400 hover:underline">Read on original site</button>
						</p>
					{/if}
				</div>
				
				<!-- Article Actions -->
				<div class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
					<div class="flex items-center space-x-2">
						<button
							onclick={handleMarkRead}
							class="flex items-center space-x-1 px-3 py-1.5 text-sm rounded-md border transition-colors {article.read_status?.is_read 
								? 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400' 
								: 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700'}"
						>
							<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
								<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
							</svg>
							<span>{article.read_status?.is_read ? 'Mark Unread' : 'Mark Read'}</span>
						</button>
						
						<button
							onclick={handleToggleStar}
							class="flex items-center space-x-1 px-3 py-1.5 text-sm rounded-md border transition-colors {article.read_status?.is_starred 
								? 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-400' 
								: 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700'}"
						>
							<Star size={16} fill={article.read_status?.is_starred ? 'currentColor' : 'none'} />
							<span>{article.read_status?.is_starred ? 'Unstar' : 'Star'}</span>
						</button>
						
						<button
							onclick={openOriginal}
							class="flex items-center space-x-1 px-3 py-1.5 text-sm rounded-md border bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
						>
							<ExternalLink size={16} />
							<span>Open Original</span>
						</button>
					</div>
				</div>
				
				<!-- Tags if available -->
				{#if article.tags && article.tags.length > 0}
					<div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
						<div class="flex flex-wrap gap-2">
							{#each article.tags as tag}
								<span class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-full">
									{tag}
								</span>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}
</Modal>

<style>
	/* Reset all inherited colors first */
	:global(.article-content.prose) {
		color: rgb(55 65 81) !important; /* gray-700 */
	}
	
	:global(.dark .article-content.prose) {
		color: rgb(209 213 219) !important; /* gray-300 */
	}
	
	/* Enhance prose styling for article content */
	:global(.article-content.prose h1) {
		@apply text-xl font-bold text-gray-900 dark:text-white mb-4 !important;
	}
	
	:global(.article-content.prose h2) {
		@apply text-lg font-semibold text-gray-900 dark:text-white mb-3 mt-6 !important;
	}
	
	:global(.article-content.prose h3) {
		@apply text-base font-medium text-gray-900 dark:text-white mb-2 mt-4 !important;
	}
	
	:global(.article-content.prose p) {
		@apply text-gray-700 dark:text-gray-300 mb-3 leading-relaxed !important;
	}
	
	:global(.article-content.prose a) {
		@apply text-blue-600 dark:text-blue-400 hover:underline !important;
	}
	
	:global(.article-content.prose img) {
		@apply rounded-lg max-w-full h-auto my-4;
		max-height: 400px;
		object-fit: contain;
	}
	
	:global(.article-content.prose blockquote) {
		@apply border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-600 dark:text-gray-400 !important;
	}
	
	:global(.article-content.prose ul) {
		@apply list-disc list-inside mb-3 space-y-1;
	}
	
	:global(.article-content.prose ol) {
		@apply list-decimal list-inside mb-3 space-y-1;
	}
	
	:global(.article-content.prose li) {
		@apply text-gray-700 dark:text-gray-300 !important;
	}
	
	:global(.article-content.prose code) {
		@apply bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono text-gray-900 dark:text-gray-100 !important;
	}
	
	:global(.article-content.prose pre) {
		@apply bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto text-sm text-gray-900 dark:text-gray-100 !important;
	}
	
	/* Force dark mode colors for any text elements */
	:global(.article-content.prose *) {
		color: inherit !important;
		@apply dark:text-gray-300 !important;
	}
	
	/* Override specific elements that should be darker in dark mode */
	:global(.article-content.prose h1, .article-content.prose h2, .article-content.prose h3, .article-content.prose h4, .article-content.prose h5, .article-content.prose h6) {
		@apply dark:text-white !important;
	}
	
	/* Force specific text elements to use proper dark mode colors */
	:global(.article-content.prose span, .article-content.prose div, .article-content.prose section) {
		@apply dark:text-gray-300 !important;
	}
	
	/* Ensure strong/bold text is visible */
	:global(.article-content.prose strong, .article-content.prose b) {
		@apply dark:text-gray-100 !important;
	}
	
	/* Ensure em/italic text is visible */
	:global(.article-content.prose em, .article-content.prose i) {
		@apply dark:text-gray-300 !important;
	}
</style>