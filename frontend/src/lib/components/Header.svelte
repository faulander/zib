<script>
	import { onMount } from 'svelte';
	import { Rss } from '@lucide/svelte';
	import { isMobile, toggleSidebar, isSidebarOpen } from '$lib/stores/sidebar.js';
	
	// Use stores for mobile and sidebar state
	let mobileState = $derived($isMobile);
	let sidebarState = $derived($isSidebarOpen);
	
	onMount(() => {
		// Always use dark mode - we're opinionated
		document.documentElement.classList.add('dark');
	});
</script>

<header class="bg-gray-800 border-b border-gray-700 px-4 md:px-6 py-3 md:py-4">
	<div class="flex items-center space-x-3 w-full">
		<!-- Mobile Hamburger Menu Button -->
		{#if mobileState}
			<button
				class="hamburger-menu p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors md:hidden flex-shrink-0"
				onclick={toggleSidebar}
				aria-label="Toggle sidebar"
			>
				<svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					{#if sidebarState}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					{:else}
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
					{/if}
				</svg>
			</button>
		{/if}
		
		<!-- RSS Logo -->
		<div class="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
			<Rss class="w-5 h-5 text-white" />
		</div>
		
		<!-- Title (hidden on mobile) or Search (full width on mobile) -->
		{#if mobileState}
			<!-- Mobile Search Bar -->
			<div class="relative flex-1">
				<input
					type="text"
					placeholder="Search articles..."
					class="w-full px-3 py-2 pr-10 border border-gray-600 rounded-lg bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm"
				/>
				<svg class="w-4 h-4 absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
		{:else}
			<!-- Desktop Title -->
			<div>
				<h1 class="text-xl font-semibold text-white">Zib RSS Reader</h1>
				<p class="text-sm text-gray-400">Zeit im Bild</p>
			</div>
			
			<!-- Desktop Search -->
			<div class="flex-1 max-w-md ml-8">
				<div class="relative">
					<input
						type="text"
						placeholder="Search articles..."
						class="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
					/>
					<svg class="w-4 h-4 absolute right-3 top-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
				</div>
			</div>
		{/if}
		
	</div>
</header>