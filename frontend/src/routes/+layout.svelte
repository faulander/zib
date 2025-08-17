<script>
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	
	let { children } = $props();
</script>

<svelte:head>
	<title>Zib RSS Reader</title>
	<meta name="description" content="An opinionated RSS reader inspired by Austrian news culture" />
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
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
</div>
