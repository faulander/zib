<script>
	import { onMount, onDestroy } from 'svelte';
	
	let { isOpen = false, title = '', children, onclose } = $props();
	
	let modalElement;
	
	function closeModal() {
		if (onclose) {
			onclose();
		}
	}
	
	function handleKeydown(event) {
		if (event.key === 'Escape') {
			closeModal();
		}
	}
	
	function handleBackdropClick(event) {
		if (event.target === event.currentTarget) {
			closeModal();
		}
	}
	
	// Focus management
	onMount(() => {
		if (isOpen) {
			document.addEventListener('keydown', handleKeydown);
			// Focus the modal for accessibility
			modalElement?.focus();
			// Prevent body scroll
			document.body.style.overflow = 'hidden';
		}
	});
	
	onDestroy(() => {
		document.removeEventListener('keydown', handleKeydown);
		// Restore body scroll
		document.body.style.overflow = '';
	});
	
	// Update event listeners when isOpen changes
	$effect(() => {
		if (isOpen) {
			document.addEventListener('keydown', handleKeydown);
			modalElement?.focus();
			document.body.style.overflow = 'hidden';
		} else {
			document.removeEventListener('keydown', handleKeydown);
			document.body.style.overflow = '';
		}
		
		return () => {
			document.removeEventListener('keydown', handleKeydown);
			document.body.style.overflow = '';
		};
	});
</script>

{#if isOpen}
	<div 
		class="fixed inset-0 z-50 overflow-y-auto"
		onclick={handleBackdropClick}
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
	>
		<!-- Backdrop -->
		<div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
		
		<!-- Modal container -->
		<div class="flex min-h-full items-center justify-center p-4">
			<div 
				bind:this={modalElement}
				class="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-lg shadow-xl overflow-hidden"
				tabindex="-1"
			>
				<!-- Header -->
				<div class="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
					<div class="flex items-center justify-between">
						<h2 id="modal-title" class="text-lg font-semibold text-gray-900 dark:text-white truncate pr-4">
							{title}
						</h2>
						<button
							onclick={closeModal}
							class="p-2 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0"
							aria-label="Close modal"
						>
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
				</div>
				
				<!-- Content -->
				<div class="overflow-y-auto max-h-[calc(90vh-80px)]">
					{@render children()}
				</div>
			</div>
		</div>
	</div>
{/if}