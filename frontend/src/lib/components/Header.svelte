<script>
	import { onMount } from 'svelte';
	
	onMount(() => {
		// Always use dark mode - we're opinionated
		document.documentElement.classList.add('dark');
	});
</script>

<header class="bg-gray-800 border-b border-gray-700 px-6 py-4">
	<div class="flex items-center justify-between">
		<!-- Logo/Title -->
		<div class="flex items-center space-x-3">
			<div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
				<span class="text-white font-bold text-sm">Z</span>
			</div>
			<div>
				<h1 class="text-xl font-semibold text-white">Zib RSS Reader</h1>
				<p class="text-sm text-gray-400">Zeit im Bild</p>
			</div>
		</div>
		
		<!-- Header Actions -->
		<div class="flex items-center space-x-4">
			<!-- Search -->
			<div class="relative">
				<input
					type="text"
					placeholder="Search articles..."
					class="w-64 px-4 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
				<svg class="w-4 h-4 absolute right-3 top-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
			</div>
			
		</div>
	</div>
</header>