<script>
	import { onMount } from 'svelte';
	import { feedsStore, categoriesStore, apiActions, isLoading, error } from '$lib/stores/api.js';
	import { settings } from '$lib/stores/settings.js';
	import { opml, api } from '$lib/api.js';
	import { Plus, Trash2, Download, Upload, RefreshCw, Settings, Rss, FolderOpen, FileText, ChevronDown, ChevronRight } from '@lucide/svelte';
	
	// Use Svelte 5 runes
	let feeds = $derived($feedsStore);
	let categories = $derived($categoriesStore);
	let loading = $derived($isLoading);
	let apiError = $derived($error);
	
	// Settings - use reactive state for binding
	let autoRefreshFeeds = $state(false);
	let showUnreadCountInTitle = $state(false);
	let markReadScrollBatchSize = $state(5);
	let markReadScrollDelay = $state(1000);
	
	// Subscribe to settings changes and update local state
	$effect(() => {
		const currentSettings = $settings;
		autoRefreshFeeds = currentSettings.autoRefreshFeeds;
		showUnreadCountInTitle = currentSettings.showUnreadCountInTitle;
		markReadScrollBatchSize = currentSettings.markReadScrollBatchSize;
		markReadScrollDelay = currentSettings.markReadScrollDelay;
	});
	
	
	// Settings navigation
	let selectedSection = $state('categories');
	
	// Expandable categories state
	let expandedCategories = $state(new Set());
	
	// Delete confirmation modal state
	let showDeleteModal = $state(false);
	let deleteTarget = $state(null); // { type: 'category'|'feed', item: object }
	
	// Form states
	let showAddFeed = $state(false);
	let showAddFeedForCategory = $state(null); // ID of category to show add feed form for
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
		{ id: 'categories', name: 'Feeds & Categories', icon: FolderOpen },
		{ id: 'general', name: 'General Settings', icon: Settings },
		{ id: 'import-export', name: 'Import/Export', icon: FileText }
	];
	
	// Category expansion functions
	function toggleCategory(categoryId) {
		if (expandedCategories.has(categoryId)) {
			expandedCategories.delete(categoryId);
		} else {
			expandedCategories.add(categoryId);
		}
		expandedCategories = new Set(expandedCategories);
	}
	
	// Feed management functions
	async function handleAddFeed(categoryId = null) {
		if (!newFeedUrl.trim()) return;
		
		try {
			const feedData = {
				url: newFeedUrl.trim(),
				title: newFeedTitle.trim() || undefined,
				category_id: categoryId || (newFeedCategoryId ? parseInt(newFeedCategoryId) : undefined)
			};
			
			const newFeed = await apiActions.addFeed(feedData);
			
			// Immediately refresh the newly created feed to fetch articles
			if (newFeed && newFeed.id) {
				try {
					await apiActions.refreshFeed(newFeed.id);
				} catch (refreshErr) {
					console.error('Failed to refresh new feed:', refreshErr);
					// Don't throw - the feed was created successfully, refresh just failed
				}
			}
			
			// Reset form
			newFeedUrl = '';
			newFeedTitle = '';
			newFeedCategoryId = '';
			showAddFeed = false;
			showAddFeedForCategory = null;
		} catch (err) {
			console.error('Failed to add feed:', err);
		}
	}
	
	// Delete confirmation functions
	function confirmDeleteCategory(category) {
		const categoryFeeds = feeds.filter(f => f.category_id === category.id);
		deleteTarget = { 
			type: 'category', 
			item: category, 
			feedCount: categoryFeeds.length,
			feeds: categoryFeeds
		};
		showDeleteModal = true;
	}
	
	function confirmDeleteFeed(feed) {
		deleteTarget = { 
			type: 'feed', 
			item: feed 
		};
		showDeleteModal = true;
	}
	
	async function handleConfirmDelete() {
		if (!deleteTarget) return;
		
		try {
			if (deleteTarget.type === 'category') {
				// Delete category and all its feeds
				await api.request(`/api/categories/${deleteTarget.item.id}`, {
					method: 'DELETE'
				});
				// Reload data
				await apiActions.loadCategories();
				await apiActions.loadFeeds();
			} else if (deleteTarget.type === 'feed') {
				// Delete single feed
				await api.request(`/api/feeds/${deleteTarget.item.id}`, {
					method: 'DELETE'
				});
				// Reload data
				await apiActions.loadFeeds();
			}
		} catch (err) {
			console.error(`Failed to delete ${deleteTarget.type}:`, err);
		} finally {
			showDeleteModal = false;
			deleteTarget = null;
		}
	}
	
	function cancelDelete() {
		showDeleteModal = false;
		deleteTarget = null;
	}
	
	async function handleDeleteFeed(feedId) {
		const feed = feeds.find(f => f.id === feedId);
		if (feed) {
			confirmDeleteFeed(feed);
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
		<div class="p-6">
		
		{#if selectedSection === 'categories'}
		<!-- Feeds & Categories Section -->
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
					<button
						onclick={handleRefreshAllFeeds}
						disabled={isRefreshing || loading}
						class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
					>
						<RefreshCw class="h-4 w-4 mr-1 {isRefreshing ? 'animate-spin' : ''}" />
						Refresh All Feeds
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

			<!-- Expandable Categories List -->
			<div class="space-y-2">
				{#each categories as category}
					{@const categoryFeeds = feeds.filter(f => f.category_id === category.id)}
					{@const isExpanded = expandedCategories.has(category.id)}
					
					<div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
						<!-- Category Header -->
						<div 
							class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600 rounded-lg"
							onclick={() => toggleCategory(category.id)}
						>
							<div class="flex items-center space-x-3">
								<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
									{#if isExpanded}
										<ChevronDown class="h-4 w-4" />
									{:else}
										<ChevronRight class="h-4 w-4" />
									{/if}
								</button>
								<div>
									<h3 class="font-medium text-gray-900 dark:text-white">{category.name}</h3>
									{#if category.description}
										<p class="text-sm text-gray-600 dark:text-gray-400">{category.description}</p>
									{/if}
								</div>
							</div>
							<div class="flex items-center space-x-4">
								<span class="text-sm text-gray-500 dark:text-gray-400">
									{categoryFeeds.length} feeds
								</span>
								<div class="flex items-center space-x-2">
									<button
										onclick={(e) => {
											e.stopPropagation();
											
											// Make sure category is expanded
											if (!expandedCategories.has(category.id)) {
												expandedCategories.add(category.id);
												expandedCategories = new Set(expandedCategories);
											}
											
											showAddFeedForCategory = category.id;
										}}
										class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
										title="Add feed to this category"
									>
										<Plus class="h-4 w-4" />
									</button>
									<button
										onclick={(e) => {
											e.stopPropagation();
											confirmDeleteCategory(category);
										}}
										class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
										title="Delete category"
									>
										<Trash2 class="h-4 w-4" />
									</button>
								</div>
							</div>
						</div>

						<!-- Expanded Category Content -->
						{#if isExpanded}
							<div class="border-t border-gray-200 dark:border-gray-600">
								<!-- Add Feed Form for this Category -->
								{#if showAddFeedForCategory === category.id}
									<div class="p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-600">
										<h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">Add Feed to {category.name}</h4>
										<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
											<div>
												<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
													Feed URL *
												</label>
												<input
													type="url"
													bind:value={newFeedUrl}
													placeholder="https://example.com/feed.xml"
													class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
												/>
											</div>
											<div>
												<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
													Title (optional)
												</label>
												<input
													type="text"
													bind:value={newFeedTitle}
													placeholder="Feed title"
													class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
												/>
											</div>
										</div>
										<div class="flex justify-end space-x-2 mt-4">
											<button
												onclick={() => showAddFeedForCategory = null}
												class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
											>
												Cancel
											</button>
											<button
												onclick={() => handleAddFeed(category.id)}
												disabled={!newFeedUrl.trim() || loading}
												class="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
											>
												Add Feed
											</button>
										</div>
									</div>
								{/if}

								<!-- Feeds in this Category -->
								{#if categoryFeeds.length > 0}
									<div class="p-4 space-y-2">
										{#each categoryFeeds as feed}
											<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
												<div class="flex-1">
													<h4 class="font-medium text-gray-900 dark:text-white text-sm">{feed.title}</h4>
													<p class="text-xs text-gray-600 dark:text-gray-400">{feed.url}</p>
												</div>
												<div class="flex items-center space-x-1">
													<button
														onclick={() => handleRefreshFeed(feed.id)}
														disabled={loading}
														class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50"
														title="Refresh feed"
													>
														<RefreshCw class="h-3 w-3" />
													</button>
													<button
														onclick={() => handleDeleteFeed(feed.id)}
														disabled={loading}
														class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50"
														title="Delete feed"
													>
														<Trash2 class="h-3 w-3" />
													</button>
												</div>
											</div>
										{/each}
									</div>
								{:else}
									<div class="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
										No feeds in this category yet.
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</section>

		{:else if selectedSection === 'general'}
		<!-- General Settings Section -->
		<section class="space-y-4">
			<div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Application Settings</h3>
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<div>
							<label class="text-sm font-medium text-gray-900 dark:text-white">Auto-refresh feeds</label>
							<p class="text-xs text-gray-600 dark:text-gray-400">Automatically refresh all feeds periodically</p>
						</div>
						<input 
							type="checkbox" 
							bind:checked={autoRefreshFeeds}
							onchange={() => settings.setSetting('autoRefreshFeeds', autoRefreshFeeds)}
							class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
						/>
					</div>
					<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
						<h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Mark as Read on Scroll</h4>
						<p class="text-xs text-gray-600 dark:text-gray-400 mb-4">Articles are automatically marked as read when scrolling past them. Configure the behavior below.</p>
						<div class="space-y-3">
							<div class="flex items-center justify-between">
								<div>
									<label class="text-sm font-medium text-gray-900 dark:text-white">Batch size</label>
									<p class="text-xs text-gray-600 dark:text-gray-400">Number of articles to batch before marking as read</p>
								</div>
								<input 
									type="number" 
									min="1" 
									max="20"
									bind:value={markReadScrollBatchSize}
									onchange={() => settings.setSetting('markReadScrollBatchSize', markReadScrollBatchSize)}
									class="w-16 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500" 
								/>
							</div>
							<div class="flex items-center justify-between">
								<div>
									<label class="text-sm font-medium text-gray-900 dark:text-white">Scroll delay (ms)</label>
									<p class="text-xs text-gray-600 dark:text-gray-400">Delay after article leaves viewport before adding to batch</p>
								</div>
								<input 
									type="number" 
									min="500" 
									max="5000"
									step="100"
									bind:value={markReadScrollDelay}
									onchange={() => settings.setSetting('markReadScrollDelay', markReadScrollDelay)}
									class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500" 
								/>
							</div>
						</div>
					</div>
					<div class="flex items-center justify-between">
						<div>
							<label class="text-sm font-medium text-gray-900 dark:text-white">Show unread count in title</label>
							<p class="text-xs text-gray-600 dark:text-gray-400">Display unread article count in browser tab title</p>
						</div>
						<input 
							type="checkbox" 
							bind:checked={showUnreadCountInTitle}
							onchange={() => settings.setSetting('showUnreadCountInTitle', showUnreadCountInTitle)}
							class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
						/>
					</div>
				</div>
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

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && deleteTarget}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
				{#if deleteTarget.type === 'category'}
					Delete Category
				{:else}
					Delete Feed
				{/if}
			</h3>
			
			<div class="mb-4">
				{#if deleteTarget.type === 'category'}
					<p class="text-gray-700 dark:text-gray-300">
						Are you sure you want to delete the category <strong>"{deleteTarget.item.name}"</strong>?
					</p>
					{#if deleteTarget.feedCount > 0}
						<div class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
							<p class="text-red-800 dark:text-red-200 text-sm font-medium">
								⚠️ This will also delete {deleteTarget.feedCount} feed{deleteTarget.feedCount === 1 ? '' : 's'} and all their articles:
							</p>
							<ul class="mt-2 text-red-700 dark:text-red-300 text-sm list-disc list-inside">
								{#each deleteTarget.feeds as feed}
									<li>{feed.title || feed.url}</li>
								{/each}
							</ul>
						</div>
					{/if}
				{:else}
					<p class="text-gray-700 dark:text-gray-300">
						Are you sure you want to delete the feed <strong>"{deleteTarget.item.title}"</strong>?
					</p>
					<div class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
						<p class="text-red-800 dark:text-red-200 text-sm">
							⚠️ This will also delete all articles from this feed.
						</p>
					</div>
				{/if}
				
				<p class="text-gray-600 dark:text-gray-400 text-sm mt-3">
					This action cannot be undone.
				</p>
			</div>

			<div class="flex justify-end space-x-3">
				<button
					onclick={cancelDelete}
					class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
				>
					Cancel
				</button>
				<button
					onclick={handleConfirmDelete}
					class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
				>
					{#if deleteTarget.type === 'category'}
						Delete Category & {deleteTarget.feedCount} Feed{deleteTarget.feedCount === 1 ? '' : 's'}
					{:else}
						Delete Feed
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}