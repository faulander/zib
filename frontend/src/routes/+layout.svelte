<script>
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import { initializeApp } from '$lib/stores/api.js';
	import { error, isLoading } from '$lib/stores/api.js';
	import { autoRefreshService } from '$lib/services/autoRefreshService.js';
	import { settings } from '$lib/stores/settings.js';
	import { articles } from '$lib/api.js';
	import { isMobile, isSidebarOpen, toggleSidebar, closeSidebar, checkMobile } from '$lib/stores/sidebar.js';
	import { initializeFontScale } from '$lib/fontScale.js';
	
	let { children } = $props();
	let initError = $state(null);
	let isInitialized = $state(false);
	let unreadCount = $state(0);
	let unreadCountInterval;
	
	// Use stores for mobile and sidebar state
	let mobileState = $derived($isMobile);
	let sidebarState = $derived($isSidebarOpen);
	
	// Check if we're on the settings page
	let isSettingsPage = $derived($page.url.pathname.startsWith('/settings'));
	
	// Dynamic title based on unread count and settings
	let pageTitle = $derived.by(() => {
		const baseTitle = 'Zib RSS Reader';
		if ($settings.showUnreadCountInTitle && unreadCount > 0) {
			return `(${unreadCount}) ${baseTitle}`;
		}
		return baseTitle;
	});

	// Update unread count periodically (use filtered count)
	async function updateUnreadCount() {
		try {
			const response = await articles.getFilteredCounts();
			// Use total unread from the filtered counts endpoint
			unreadCount = response.total_unread || 0;
		} catch (err) {
			console.error('Failed to get unread count:', err);
		}
	}
	
	
	// Close sidebar when clicking outside on mobile
	function handleOutsideClick(event) {
		if (mobileState && sidebarState) {
			const sidebar = event.target.closest('aside');
			const hamburger = event.target.closest('.hamburger-menu');
			if (!sidebar && !hamburger) {
				closeSidebar();
			}
		}
	}
	
	// Touch handling for swipe gestures
	let touchStartX = 0;
	let touchEndX = 0;
	
	function handleTouchStart(e) {
		if (mobileState) {
			touchStartX = e.touches[0].clientX;
		}
	}
	
	function handleTouchEnd(e) {
		if (mobileState) {
			touchEndX = e.changedTouches[0].clientX;
			handleSwipe();
		}
	}
	
	function handleSwipe() {
		const swipeDistance = touchEndX - touchStartX;
		const swipeThreshold = 75; // Minimum swipe distance
		
		if (Math.abs(swipeDistance) > swipeThreshold) {
			if (swipeDistance > 0 && touchStartX < 50) {
				// Swipe right from left edge - open sidebar
				$isSidebarOpen = true;
			} else if (swipeDistance < 0 && sidebarState) {
				// Swipe left - close sidebar
				closeSidebar();
			}
		}
	}
	
	onMount(async () => {
		try {
			// Initialize font scale from localStorage/settings
			initializeFontScale();
			
			// Check if mobile on mount
			checkMobile();
			window.addEventListener('resize', checkMobile);
			
			await initializeApp();
			// Start auto-refresh service after app initialization
			await autoRefreshService.start();
			// Initial unread count update
			await updateUnreadCount();
			// Update unread count every 30 seconds
			unreadCountInterval = setInterval(updateUnreadCount, 30000);
			isInitialized = true;
		} catch (err) {
			initError = err.message;
			isInitialized = true; // Still show UI with error message
		}
	});

	onDestroy(() => {
		autoRefreshService.stop();
		if (unreadCountInterval) {
			clearInterval(unreadCountInterval);
		}
		// Only run in browser environment
	if (browser) {
		window.removeEventListener('resize', checkMobile);
	}
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
		<div 
			class="flex flex-1 overflow-hidden relative" 
			onclick={handleOutsideClick}
			ontouchstart={handleTouchStart}
			ontouchend={handleTouchEnd}
		>
			<!-- Sidebar (responsive) -->
			{#if !isSettingsPage}
				<div class="{mobileState ? 'fixed inset-y-0 left-0 z-40 transition-transform duration-300 transform ' + (sidebarState ? 'translate-x-0' : '-translate-x-full') : 'relative'}">
					<Sidebar isMobile={mobileState} onClose={closeSidebar} />
				</div>
				
				<!-- Mobile Overlay -->
				{#if mobileState && sidebarState}
					<div class="fixed inset-0 z-30 bg-black bg-opacity-50 md:hidden" onclick={closeSidebar}></div>
				{/if}
			{/if}
			
			<!-- Main Content -->
			<main class="flex-1 overflow-y-auto {isSettingsPage ? '' : 'bg-white dark:bg-gray-800'}">
				{@render children?.()}
			</main>
		</div>
	{/if}
</div>
