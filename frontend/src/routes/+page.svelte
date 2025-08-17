<script>
	import ArticleList from '$lib/components/ArticleList.svelte';
	
	// Mock articles data for now
	let articles = $state([
		{
			id: 1,
			title: 'Revolutionary AI Breakthrough Changes Everything',
			summary: 'Scientists at MIT have developed a new artificial intelligence system that can understand and generate human-like text with unprecedented accuracy...',
			author: 'Dr. Sarah Johnson',
			publishedDate: '2025-08-16T10:30:00Z',
			readAt: null,
			starred: false,
			estimatedReadingTime: 5,
			feed: { title: 'TechCrunch', color: '#3B82F6' },
			tags: ['AI', 'Technology', 'Science']
		},
		{
			id: 2,
			title: 'Climate Summit Reaches Historic Agreement',
			summary: 'World leaders have reached a consensus on new climate policies that will significantly reduce global carbon emissions...',
			author: 'Michael Chen',
			publishedDate: '2025-08-16T09:15:00Z',
			readAt: '2025-08-16T11:00:00Z',
			starred: true,
			estimatedReadingTime: 8,
			feed: { title: 'BBC News', color: '#EF4444' },
			tags: ['Climate', 'Politics', 'Environment']
		},
		{
			id: 3,
			title: 'New Quantum Computer Achieves 1000-Qubit Milestone',
			summary: 'IBM announces their latest quantum computer has successfully demonstrated stable operation with over 1000 qubits...',
			author: 'Dr. Lisa Park',
			publishedDate: '2025-08-16T08:45:00Z',
			readAt: null,
			starred: false,
			estimatedReadingTime: 6,
			feed: { title: 'Nature', color: '#10B981' },
			tags: ['Quantum', 'Computing', 'Research']
		},
		{
			id: 4,
			title: 'Breakthrough in Fusion Energy Announced',
			summary: 'Researchers have achieved a net energy gain in nuclear fusion for the third consecutive experiment...',
			author: 'Robert Williams',
			publishedDate: '2025-08-16T07:20:00Z',
			readAt: null,
			starred: false,
			estimatedReadingTime: 7,
			feed: { title: 'Science Daily', color: '#8B5CF6' },
			tags: ['Energy', 'Physics', 'Innovation']
		}
	]);
	
	let loading = $state(false);
	
	function handleMarkRead(article) {
		article.readAt = article.readAt ? null : new Date().toISOString();
	}
	
	function handleToggleStar(article) {
		article.starred = !article.starred;
	}
</script>

<div class="h-full flex flex-col">
	<!-- Content Header -->
	<div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4 bg-white dark:bg-gray-800">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">All Articles</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
					{articles.filter(a => !a.readAt).length} unread of {articles.length} total
				</p>
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
				<button class="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900 transition-colors">
					Mark All Read
				</button>
			</div>
		</div>
	</div>
	
	<!-- Article List -->
	<div class="flex-1 overflow-y-auto">
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
		{/if}
	</div>
</div>
