<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import { initializeApp } from '$lib/stores/api.js';
	import { error, isLoading } from '$lib/stores/api.js';
	
	let { children } = $props();
	let initError = $state(null);
	let isInitialized = $state(false);
	
	onMount(async () => {
		try {
			await initializeApp();
			isInitialized = true;
		} catch (err) {
			initError = err.message;
			isInitialized = true; // Still show UI with error message
		}
	});
</script>

<svelte:head>
	<title>Zib RSS Reader</title>
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
			<!-- Sidebar -->
			<Sidebar />
			
			<!-- Main Content -->
			<main class="flex-1 overflow-y-auto bg-white dark:bg-gray-800">
				{@render children?.()}
			</main>
		</div>
	{/if}
</div>
