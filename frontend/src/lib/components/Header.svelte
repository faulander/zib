<script>
	import { onMount } from 'svelte';
	
	let darkMode = $state(false);
	
	onMount(() => {
		// Check if user has a theme preference in localStorage
		const stored = localStorage.getItem('theme');
		const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
		
		darkMode = stored === 'dark' || (!stored && prefersDark);
		updateTheme();
	});
	
	function toggleTheme() {
		darkMode = !darkMode;
		updateTheme();
		localStorage.setItem('theme', darkMode ? 'dark' : 'light');
	}
	
	function updateTheme() {
		if (darkMode) {
			document.documentElement.classList.add('dark');
		} else {
			document.documentElement.classList.remove('dark');
		}
	}
</script>

<header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
	<div class="flex items-center justify-between">
		<!-- Logo/Title -->
		<div class="flex items-center space-x-3">
			<div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
				<span class="text-white font-bold text-sm">Z</span>
			</div>
			<div>
				<h1 class="text-xl font-semibold text-gray-900 dark:text-white">Zib RSS Reader</h1>
				<p class="text-sm text-gray-500 dark:text-gray-400">Zeit im Bild</p>
			</div>
		</div>
		
		<!-- Header Actions -->
		<div class="flex items-center space-x-4">
			<!-- Search -->
			<div class="relative">
				<input
					type="text"
					placeholder="Search articles..."
					class="w-64 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
				<svg class="w-4 h-4 absolute right-3 top-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
			
			<!-- Theme Toggle -->
			<button
				onclick={toggleTheme}
				class="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
				title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
			>
				{#if darkMode}
					<!-- Sun icon for light mode -->
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
					</svg>
				{:else}
					<!-- Moon icon for dark mode -->
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
					</svg>
				{/if}
			</button>
			
		</div>
	</div>
</header>