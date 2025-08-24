# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-24-search-functionality/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Technical Requirements

- **Search input state management** - Connect search inputs to searchQuery store with proper reactivity
- **Debounced search execution** - Implement search with debouncing to prevent excessive API calls  
- **Layout positioning fix** - Correct header CSS to right-align search input on desktop
- **Search result integration** - Ensure search results work with existing pagination and filtering
- **Search history management** - Store recent searches in localStorage for user convenience
- **Search clearing functionality** - Provide easy ways to clear search and return to normal view

## Approach Options

**Option A: Simple Input Binding with Store**
- Pros: Minimal changes, uses existing store system, straightforward implementation
- Cons: No advanced features, basic search experience

**Option B: Enhanced Search Component** (Selected)
- Pros: Better user experience, search suggestions, history, proper debouncing
- Cons: More complex implementation, additional state management

**Option C: Advanced Search System**
- Pros: Powerful search capabilities, filters, operators
- Cons: Over-engineered for current needs, requires backend changes

**Rationale:** Option B provides the best balance of user experience improvements while leveraging existing backend infrastructure.

## External Dependencies

- **No new major dependencies** - Use existing Svelte stores and browser APIs

## Implementation Architecture

### Header Layout Fix

#### Current Desktop Header Structure (BROKEN)
```svelte
<div class="flex items-center space-x-3 w-full">
  <!-- Logo -->
  <div class="w-8 h-8 bg-orange-500 rounded-lg">...</div>
  
  <!-- Title -->
  <div>...</div>
  
  <!-- Search (WRONG POSITION) -->
  <div class="flex-1 max-w-md ml-8">
    <input ... />
  </div>
</div>
```

#### Fixed Desktop Header Structure
```svelte
<div class="flex items-center justify-between w-full">
  <!-- Left Section: Logo + Title -->
  <div class="flex items-center space-x-3">
    <div class="w-8 h-8 bg-orange-500 rounded-lg">...</div>
    <div>
      <h1 class="text-xl font-semibold text-white">Zib RSS Reader</h1>
      <p class="text-sm text-gray-400">Zeit im Bild</p>
    </div>
  </div>
  
  <!-- Right Section: Search -->
  <div class="max-w-md w-96">
    <SearchComponent />
  </div>
</div>
```

### Search Component Implementation

#### SearchComponent.svelte
```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import { searchQuery } from '$lib/stores/api.js';
  import { apiActions } from '$lib/stores/api.js';
  import { Search, X } from '@lucide/svelte';
  
  let searchInput = '';
  let isSearching = false;
  let showSuggestions = false;
  let recentSearches = $state([]);
  let searchTimeout;
  
  // Reactive search query from store
  let currentSearchQuery = $derived($searchQuery);
  
  // Load recent searches from localStorage
  onMount(() => {
    const saved = localStorage.getItem('zib-recent-searches');
    if (saved) {
      try {
        recentSearches = JSON.parse(saved);
      } catch (e) {
        recentSearches = [];
      }
    }
  });
  
  // Debounced search function
  function handleSearchInput(event) {
    searchInput = event.target.value;
    
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Debounce search execution
    searchTimeout = setTimeout(() => {
      executeSearch(searchInput);
    }, 300); // 300ms debounce
  }
  
  function executeSearch(query) {
    const trimmedQuery = query.trim();
    
    if (trimmedQuery) {
      // Update search store
      searchQuery.set(trimmedQuery);
      
      // Add to recent searches
      addToRecentSearches(trimmedQuery);
      
      // Trigger article reload with search
      apiActions.loadArticles();
      
    } else {
      // Clear search
      clearSearch();
    }
    
    showSuggestions = false;
  }
  
  function clearSearch() {
    searchInput = '';
    searchQuery.set('');
    apiActions.loadArticles(); // Reload without search
  }
  
  function addToRecentSearches(query) {
    // Remove if already exists
    recentSearches = recentSearches.filter(s => s !== query);
    
    // Add to beginning
    recentSearches.unshift(query);
    
    // Keep only last 5 searches
    recentSearches = recentSearches.slice(0, 5);
    
    // Save to localStorage
    localStorage.setItem('zib-recent-searches', JSON.stringify(recentSearches));
  }
  
  function selectRecentSearch(query) {
    searchInput = query;
    executeSearch(query);
  }
  
  function handleFocus() {
    if (recentSearches.length > 0 && !searchInput) {
      showSuggestions = true;
    }
  }
  
  function handleBlur() {
    // Delay hiding suggestions to allow click on suggestions
    setTimeout(() => {
      showSuggestions = false;
    }, 200);
  }
  
  function handleKeydown(event) {
    if (event.key === 'Escape') {
      clearSearch();
      event.target.blur();
    } else if (event.key === 'Enter') {
      executeSearch(searchInput);
      event.target.blur();
    }
  }
  
  // Cleanup timeout on destroy
  onDestroy(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
  });
</script>

<div class="relative">
  <div class="relative">
    <input
      type="text"
      bind:value={searchInput}
      placeholder="Search articles..."
      class="w-full px-4 py-2 pr-10 border border-gray-600 rounded-lg bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
      oninput={handleSearchInput}
      onfocus={handleFocus}
      onblur={handleBlur}
      onkeydown={handleKeydown}
    />
    
    <!-- Search or Clear Icon -->
    <div class="absolute right-3 top-1/2 transform -translate-y-1/2">
      {#if searchInput}
        <button 
          onclick={clearSearch}
          class="text-gray-400 hover:text-white transition-colors"
          title="Clear search"
        >
          <X size={16} />
        </button>
      {:else}
        <Search size={16} class="text-gray-400" />
      {/if}
    </div>
  </div>
  
  <!-- Search Suggestions Dropdown -->
  {#if showSuggestions && recentSearches.length > 0}
    <div class="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50">
      <div class="p-2">
        <div class="text-xs text-gray-400 mb-2">Recent searches</div>
        {#each recentSearches as search}
          <button
            class="block w-full text-left px-3 py-2 text-sm text-white hover:bg-gray-700 rounded"
            onclick={() => selectRecentSearch(search)}
          >
            {search}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>
```

### Mobile Search Integration

#### Update Header.svelte Mobile Section
```svelte
{#if mobileState}
  <!-- Mobile Search Bar -->
  <div class="flex-1">
    <SearchComponent />
  </div>
{:else}
  <!-- Desktop Layout -->
  <div class="flex items-center justify-between w-full">
    <!-- Left: Logo + Title -->
    <div class="flex items-center space-x-3">
      <div class="w-8 h-8 bg-orange-500 rounded-lg">...</div>
      <div>
        <h1 class="text-xl font-semibold text-white">Zib RSS Reader</h1>
        <p class="text-sm text-gray-400">Zeit im Bild</p>
      </div>
    </div>
    
    <!-- Right: Search -->
    <div class="max-w-md w-96">
      <SearchComponent />
    </div>
  </div>
{/if}
```

### Search State Integration

#### Enhanced Store Integration
```javascript
// In stores/api.js - ensure search triggers article reload
export const apiActions = {
  async loadArticles(isAutoRefresh = false) {
    try {
      isLoading.set(true);
      
      // Build query parameters including search
      const queryParams = {};
      
      // Include search query
      const currentSearch = get(searchQuery);
      if (currentSearch) {
        queryParams.search = currentSearch;
        console.log('Loading articles with search:', currentSearch);
      }
      
      // ... rest of existing loadArticles logic
    } catch (err) {
      // ... error handling
    }
  },
  
  // Add dedicated search action
  async performSearch(query) {
    searchQuery.set(query);
    await this.loadArticles();
  },
  
  async clearSearch() {
    searchQuery.set('');
    await this.loadArticles();
  }
};
```

### Search Result Display

#### Search Status Indicator
```svelte
<!-- In main article view component -->
{#if $searchQuery}
  <div class="search-status bg-blue-900 border-b border-blue-700 px-4 py-2">
    <div class="flex items-center justify-between">
      <span class="text-blue-200 text-sm">
        Searching for: <strong>"{$searchQuery}"</strong>
      </span>
      <button 
        onclick={() => apiActions.clearSearch()}
        class="text-blue-300 hover:text-white text-sm underline"
      >
        Clear search
      </button>
    </div>
  </div>
{/if}
```

### Keyboard Shortcuts Integration

#### Search Shortcuts
```javascript
// Global keyboard shortcut for search focus
function handleGlobalKeydown(event) {
  if (event.key === '/' && !event.target.matches('input, textarea')) {
    event.preventDefault();
    
    // Focus search input
    const searchInput = document.querySelector('[data-search-input]');
    if (searchInput) {
      searchInput.focus();
    }
  }
}

// Add to document
document.addEventListener('keydown', handleGlobalKeydown);
```

### Performance Optimizations

#### Search Debouncing
- 300ms debounce delay to prevent excessive API calls
- Cancel previous requests when new search is typed
- Loading states during search execution

#### Local Storage Management
- Store max 5 recent searches
- Clear old searches periodically
- Handle localStorage failures gracefully

#### Memory Management
- Clear search timeouts on component destroy
- Efficient suggestion dropdown rendering
- Minimal re-renders with proper reactive patterns