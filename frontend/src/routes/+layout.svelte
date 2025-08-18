<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import { initializeApp } from '$lib/stores/api.js';
	import { error, isLoading } from '$lib/stores/api.js';
	import { autoRefreshService } from '$lib/services/autoRefreshService.js';
	import { settings } from '$lib/stores/settings.js';
	import { articles } from '$lib/api.js';
	
	let { children } = $props();
	let initError = $state(null);
	let isInitialized = $state(false);
	let unreadCount = $state(0);
	
	// Check if we're on the settings page
	let isSettingsPage = $derived($page.url.pathname.startsWith('/settings'));
	
	// Dynamic title based on unread count and settings
	let pageTitle = $derived(() => {
		const baseTitle = 'Zib RSS Reader';
		if ($settings.showUnreadCountInTitle && unreadCount > 0) {
			return `(${unreadCount}) ${baseTitle}`;
		}
		return baseTitle;
	});

	// Update unread count periodically
	async function updateUnreadCount() {
		try {
			const response = await articles.getAll({ read_status: 'unread', limit: 1 });
			unreadCount = response.pagination?.total || 0;
		} catch (err) {
			console.error('Failed to get unread count:', err);
		}
	}
	
	onMount(async () => {
		try {
			await initializeApp();
			// Start auto-refresh service after app initialization
			await autoRefreshService.start();
			// Initial unread count update
			await updateUnreadCount();
			// Update unread count every 30 seconds
			const unreadCountInterval = setInterval(updateUnreadCount, 30000);
			isInitialized = true;
		} catch (err) {
			initError = err.message;
			isInitialized = true; // Still show UI with error message
		}
	});

	onDestroy(() => {
		autoRefreshService.stop();
	});
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content="An opinionated RSS reader inspired by Austrian news culture" />
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
	<!-- Loading State -->
	{#if !isInitialized}
		<div class="flex-1 flex items-center justify-center">
			<div class="text-center">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
				<p class="text-gray-600 dark:text-gray-400">Loading Zib RSS Reader...</p>
			</div>
		</div>
	{:else}
		<!-- Error Banner -->
		{#if initError || $error}
			<div class="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 p-4">
				<div class="flex">
					<div class="flex-shrink-0">
						<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
						</svg>
					</div>
					<div class="ml-3">
						<p class="text-sm text-red-700 dark:text-red-300">
							{initError || $error}
						</p>
					</div>
				</div>
			</div>
		{/if}
		
		<!-- Header -->
		<Header />
		
		<!-- Main Content Area -->
		<div class="flex flex-1 overflow-hidden">
			<!-- Sidebar (only show on non-settings pages) -->
			{#if !isSettingsPage}
				<Sidebar />
			{/if}
			
			<!-- Main Content -->
			<main class="flex-1 overflow-y-auto {isSettingsPage ? '' : 'bg-white dark:bg-gray-800'}">
				{@render children?.()}
			</main>
		</div>
	{/if}
</div>
