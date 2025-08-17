<script>
	import { onMount } from 'svelte';
	import { feedsStore, categoriesStore, apiActions, isLoading, error } from '$lib/stores/api.js';
	import { opml } from '$lib/api.js';
	import { Plus, Trash2, Download, Upload, RefreshCw, Settings, Rss, FolderOpen, FileText } from '@lucide/svelte';
	
	// Use Svelte 5 runes
	let feeds = $derived($feedsStore);
	let categories = $derived($categoriesStore);
	let loading = $derived($isLoading);
	let apiError = $derived($error);
	
	// Settings navigation
	let selectedSection = $state('feeds');
	
	// Form states
	let showAddFeed = $state(false);
	let showAddCategory = $state(false);
	let newFeedUrl = $state('');
	let newFeedTitle = $state('');
	let newFeedCategoryId = $state('');
	let newCategoryName = $state('');
	let newCategoryDescription = $state('');
	
	// OPML states
	let importFile = $state(null);
	let isRefreshing = $state(false);
	let isImporting = $state(false);
	let importJobId = $state(null);
	let importStatus = $state(null);
	
	// Settings sections
	const settingsSections = [
		{ id: 'feeds', name: 'Feed Management', icon: Rss },
		{ id: 'categories', name: 'Categories', icon: FolderOpen },
		{ id: 'import-export', name: 'Import/Export', icon: FileText }
	];
	
	// Feed management functions
	async function handleAddFeed() {
		if (!newFeedUrl.trim()) return;
		
		try {
			const feedData = {
				url: newFeedUrl.trim(),
				title: newFeedTitle.trim() || undefined,
				category_id: newFeedCategoryId ? parseInt(newFeedCategoryId) : undefined
			};
			
			await apiActions.addFeed(feedData);
			
			// Reset form
			newFeedUrl = '';
			newFeedTitle = '';
			newFeedCategoryId = '';
			showAddFeed = false;
		} catch (err) {
			console.error('Failed to add feed:', err);
		}
	}
	
	async function handleDeleteFeed(feedId) {
		if (!confirm('Are you sure you want to delete this feed?')) return;
		
		try {
			await apiActions.deleteFeed(feedId);
		} catch (err) {
			console.error('Failed to delete feed:', err);
		}
	}
	
	async function handleRefreshFeed(feedId) {
		try {
			await apiActions.refreshFeed(feedId);
		} catch (err) {
			console.error('Failed to refresh feed:', err);
		}
	}
	
	async function handleRefreshAllFeeds() {
		isRefreshing = true;
		try {
			await apiActions.refreshAllFeeds();
		} catch (err) {
			console.error('Failed to refresh all feeds:', err);
		} finally {
			isRefreshing = false;
		}
	}
	
	// Category management functions
	async function handleAddCategory() {
		if (!newCategoryName.trim()) return;
		
		try {
			const categoryData = {
				name: newCategoryName.trim(),
				description: newCategoryDescription.trim() || undefined
			};
			
			await apiActions.addCategory(categoryData);
			
			// Reset form
			newCategoryName = '';
			newCategoryDescription = '';
			showAddCategory = false;
		} catch (err) {
			console.error('Failed to add category:', err);
		}
	}
	
	// OPML functions
	async function handleImportOpml() {
		if (!importFile) return;
		
		try {
			isImporting = true;
			importStatus = null;
			
			const options = {
				duplicate_strategy: 'skip',
				validate_feeds: true,
				merge_categories: true
			};
			
			const result = await opml.import(importFile, options);
			importJobId = result.job_id;
			
			// Start polling for status
			pollImportStatus();
			
		} catch (err) {
			console.error('Failed to import OPML:', err);
			isImporting = false;
		}
	}
	
	async function pollImportStatus() {
		if (!importJobId) return;
		
		try {
			const status = await opml.getImportStatus(importJobId);
			importStatus = status;
			
			if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
				isImporting = false;
				if (status.status === 'completed') {
					// Reload feeds and categories
					await apiActions.loadFeeds();
					await apiActions.loadCategories();
				}
			} else {
				// Continue polling
				setTimeout(pollImportStatus, 2000);
			}
		} catch (err) {
			console.error('Failed to get import status:', err);
			isImporting = false;
		}
	}
	
	async function handleExportOpml() {
		try {
			const result = await opml.export();
			
			// Create blob and download
			const blob = new Blob([result], { type: 'application/xml' });
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `zib-feeds-${new Date().toISOString().split('T')[0]}.opml`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);
		} catch (err) {
			console.error('Failed to export OPML:', err);
		}
	}
</script>

<div class="h-full flex">
	<!-- Settings Sidebar -->
	<aside class="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
		<!-- Settings Header -->
		<div class="p-4 border-b border-gray-200 dark:border-gray-700">
			<div class="flex items-center space-x-2">
				<Settings class="h-5 w-5 text-gray-600 dark:text-gray-300" />
				<h1 class="text-lg font-semibold text-gray-900 dark:text-white">Settings</h1>
			</div>
			<p class="mt-1 text-xs text-gray-600 dark:text-gray-400">
				Manage your RSS reader
			</p>
		</div>
		
		<!-- Settings Navigation -->
		<div class="flex-1 overflow-y-auto p-2 space-y-1">
			{#each settingsSections as section}
				<button
					onclick={() => selectedSection = section.id}
					class="w-full flex items-center space-x-2 p-2 rounded transition-colors text-left {selectedSection === section.id ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
				>
					<svelte:component this={section.icon} class="h-4 w-4" />
					<span class="text-sm font-medium">{section.name}</span>
				</button>
			{/each}
		</div>
	</aside>

	<!-- Settings Content -->
	<main class="flex-1 overflow-y-auto bg-white dark:bg-gray-800">
		<!-- Content Header -->
		<div class="border-b border-gray-200 dark:border-gray-700 px-6 py-4 bg-white dark:bg-gray-800">
			<div class="flex items-center justify-between">
				<div>
					<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
						{settingsSections.find(s => s.id === selectedSection)?.name || 'Settings'}
					</h2>
				</div>
				<div>
					<a 
						href="/"
						class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
					>
						← Back to Articles
					</a>
				</div>
			</div>
		</div>

		<!-- Error Display -->
		{#if apiError}
			<div class="mx-6 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
				<p class="text-red-700 dark:text-red-300">{apiError}</p>
			</div>
		{/if}

		<!-- Content Area -->
		<div class="p-6">{#if selectedSection === 'feeds'}

		<!-- Feed Management Section -->
		<section class="space-y-4">
			<div class="flex items-center justify-between mb-4">
				<div class="flex space-x-2">
				<button
					onclick={() => showAddFeed = !showAddFeed}
					class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
				>
					<Plus class="h-4 w-4 mr-1" />
					Add Feed
				</button>
				<button
					onclick={handleRefreshAllFeeds}
					disabled={isRefreshing || loading}
					class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
				>
					<RefreshCw class="h-4 w-4 mr-1 {isRefreshing ? 'animate-spin' : ''}" />
					Refresh All
				</button>
				</div>
			</div>

		<!-- Add Feed Form -->
		{#if showAddFeed}
			<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
				<h3 class="text-lg font-medium text-gray-900 dark:text-white">Add New Feed</h3>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="feed-url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Feed URL *
						</label>
						<input
							id="feed-url"
							type="url"
							bind:value={newFeedUrl}
							placeholder="https://example.com/feed.xml"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
					<div>
						<label for="feed-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Title (optional)
						</label>
						<input
							id="feed-title"
							type="text"
							bind:value={newFeedTitle}
							placeholder="Feed title"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
					<div>
						<label for="feed-category" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Category (optional)
						</label>
						<select
							id="feed-category"
							bind:value={newFeedCategoryId}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						>
							<option value="">No category</option>
							{#each categories as category}
								<option value={category.id}>{category.name}</option>
							{/each}
						</select>
					</div>
				</div>
				<div class="flex justify-end space-x-2">
					<button
						onclick={() => showAddFeed = false}
						class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
					>
						Cancel
					</button>
					<button
						onclick={handleAddFeed}
						disabled={!newFeedUrl.trim() || loading}
						class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
					>
						Add Feed
					</button>
				</div>
			</div>
		{/if}

		<!-- Feeds List -->
		<div class="space-y-2">
			{#each feeds as feed}
				<div class="flex items-center justify-between p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
					<div class="flex-1">
						<h3 class="font-medium text-gray-900 dark:text-white">{feed.title}</h3>
						<p class="text-sm text-gray-600 dark:text-gray-400">{feed.url}</p>
						{#if feed.category}
							<span class="inline-block mt-1 px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
								{feed.category.name}
							</span>
						{/if}
					</div>
					<div class="flex items-center space-x-2">
						<button
							onclick={() => handleRefreshFeed(feed.id)}
							disabled={loading}
							class="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50"
							title="Refresh feed"
						>
							<RefreshCw class="h-4 w-4" />
						</button>
						<button
							onclick={() => handleDeleteFeed(feed.id)}
							disabled={loading}
							class="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50"
							title="Delete feed"
						>
							<Trash2 class="h-4 w-4" />
						</button>
					</div>
				</div>
			{/each}
		</div>
	</section>

{:else if selectedSection === 'categories'}
	<!-- Category Management Section -->
	<section class="space-y-4">
		<div class="flex items-center justify-between mb-4">
			<div class="flex space-x-2">
				<button
					onclick={() => showAddCategory = !showAddCategory}
					class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
				>
					<Plus class="h-4 w-4 mr-1" />
					Add Category
				</button>
			</div>
		</div>

		<!-- Add Category Form -->
		{#if showAddCategory}
			<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4">
				<h3 class="text-lg font-medium text-gray-900 dark:text-white">Add New Category</h3>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="category-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Name *
						</label>
						<input
							id="category-name"
							type="text"
							bind:value={newCategoryName}
							placeholder="Category name"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
					<div>
						<label for="category-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Description (optional)
						</label>
						<input
							id="category-description"
							type="text"
							bind:value={newCategoryDescription}
							placeholder="Category description"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
						/>
					</div>
				</div>
				<div class="flex justify-end space-x-2">
					<button
						onclick={() => showAddCategory = false}
						class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
					>
						Cancel
					</button>
					<button
						onclick={handleAddCategory}
						disabled={!newCategoryName.trim() || loading}
						class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
					>
						Add Category
					</button>
				</div>
			</div>
		{/if}

		<!-- Categories List -->
		<div class="space-y-2">
			{#each categories as category}
				<div class="flex items-center justify-between p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
					<div class="flex-1">
						<h3 class="font-medium text-gray-900 dark:text-white">{category.name}</h3>
						{#if category.description}
							<p class="text-sm text-gray-600 dark:text-gray-400">{category.description}</p>
						{/if}
					</div>
					<div class="flex items-center space-x-2">
						<span class="text-sm text-gray-500 dark:text-gray-400">
							{feeds.filter(f => f.category?.id === category.id).length} feeds
						</span>
					</div>
				</div>
			{/each}
		</div>
	</section>

{:else if selectedSection === 'import-export'}
	<!-- OPML Import/Export Section -->
	<section class="space-y-4">
		
		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<!-- Import OPML -->
			<div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Import OPML</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
					Import feeds from an OPML file
				</p>
				<div class="space-y-3">
					<input
						type="file"
						accept=".opml,.xml"
						onchange={(e) => importFile = e.target.files[0]}
						class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
					/>
					<button
						onclick={handleImportOpml}
						disabled={!importFile || loading || isImporting}
						class="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
					>
						<Upload class="h-4 w-4 mr-2" />
						{isImporting ? 'Importing...' : 'Import OPML'}
					</button>
					
					<!-- Import Status -->
					{#if isImporting && importStatus}
						<div class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
							<div class="flex items-center justify-between mb-2">
								<span class="text-sm font-medium text-blue-900 dark:text-blue-100">
									{importStatus.current_phase || 'Processing'}...
								</span>
								<span class="text-xs text-blue-700 dark:text-blue-300">
									{Math.round(importStatus.progress_percentage || 0)}%
								</span>
							</div>
							<div class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
								<div 
									class="bg-blue-600 h-2 rounded-full transition-all duration-300"
									style="width: {importStatus.progress_percentage || 0}%"
								></div>
							</div>
							{#if importStatus.feeds_imported > 0 || importStatus.categories_created > 0}
								<div class="mt-2 text-xs text-blue-700 dark:text-blue-300">
									Created {importStatus.categories_created} categories, imported {importStatus.feeds_imported} feeds
									{#if importStatus.feeds_failed > 0}
										({importStatus.feeds_failed} failed)
									{/if}
								</div>
							{/if}
						</div>
					{:else if importStatus && (importStatus.status === 'completed' || importStatus.status === 'failed')}
						<div class="mt-3 p-3 {importStatus.status === 'completed' ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'} rounded-lg">
							<div class="text-sm font-medium {importStatus.status === 'completed' ? 'text-green-900 dark:text-green-100' : 'text-red-900 dark:text-red-100'}">
								{#if importStatus.status === 'completed'}
									Import completed successfully!
									<div class="text-xs mt-1 {importStatus.status === 'completed' ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}">
										Created {importStatus.categories_created} categories, imported {importStatus.feeds_imported} feeds
									</div>
								{:else}
									Import failed: {importStatus.error_message}
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- Export OPML -->
			<div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Export OPML</h3>
				<p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
					Export your feeds to an OPML file
				</p>
				<button
					onclick={handleExportOpml}
					disabled={loading}
					class="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
				>
					<Download class="h-4 w-4 mr-2" />
					Export OPML
				</button>
			</div>
		</div>
	</section>
{/if}
		</div>
	</main>
</div>