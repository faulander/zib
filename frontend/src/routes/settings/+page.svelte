<script>
    import { onMount } from "svelte";
    import {
        feedsStore,
        categoriesStore,
        apiActions,
        isLoading,
        error,
    } from "$lib/stores/api.js";
    import { settings } from "$lib/stores/settings.js";
    import {
        opml,
        api,
        filters,
        userSettings,
        feeds as feedsApi,
    } from "$lib/api.js";
    import { autoRefreshService } from "$lib/services/autoRefreshService.js";
    import {
        isMobile,
        isSidebarOpen,
        toggleSidebar,
        closeSidebar,
    } from "$lib/stores/sidebar.js";
    import { FONT_SCALES, applyFontScale, getCurrentFontScale, getFontScaleLevel } from "$lib/fontScale.js";
    import {
        Plus,
        Trash2,
        Download,
        Upload,
        RefreshCw,
        Settings,
        Rss,
        FolderOpen,
        FileText,
        ChevronDown,
        ChevronRight,
        Filter,
        Edit3,
        Activity,
        CheckCircle,
        Menu,
    } from "@lucide/svelte";

    // Use Svelte 5 runes
    let feeds = $derived($feedsStore);
    let categories = $derived($categoriesStore);
    let loading = $derived($isLoading);
    let apiError = $derived($error);

    // Mobile and sidebar state
    let mobileState = $derived($isMobile);
    let sidebarState = $derived($isSidebarOpen);

    // Settings - use reactive state for binding
    let autoRefreshFeeds = $state(false);
    let autoRefreshInterval = $state(30);
    let showUnreadCountInTitle = $state(false);
    let openWebpageForShortArticles = $state(false);
    let shortArticleThreshold = $state(500);
    let defaultView = $state("unread");
    let showTimestampsInList = $state(true);
    let fontScale = $state(1.0);

    // Subscribe to settings changes and update local state
    $effect(() => {
        const currentSettings = $settings;
        autoRefreshFeeds = currentSettings.autoRefreshFeeds;
        showUnreadCountInTitle = currentSettings.showUnreadCountInTitle;
    });

    // Settings navigation
    let selectedSection = $state("categories");

    // Expandable categories state
    let expandedCategories = $state(new Set());

    // Delete confirmation modal state
    let showDeleteModal = $state(false);
    let deleteTarget = $state(null); // { type: 'category'|'feed', item: object }

    // Form states
    let showAddFeed = $state(false);
    let showAddFeedForCategory = $state(null); // ID of category to show add feed form for
    let showAddCategory = $state(false);
    let newFeedUrl = $state("");
    let newFeedTitle = $state("");
    let newFeedCategoryId = $state("");
    let newCategoryName = $state("");
    let newCategoryDescription = $state("");

    // OPML states
    let importFile = $state(null);
    let isRefreshing = $state(false);
    let isImporting = $state(false);
    let importJobId = $state(null);
    let importStatus = $state(null);

    // Filter states
    let userFilters = $state([]);
    let showAddFilter = $state(false);
    let newFilterName = $state("");
    let newFilterType = $state("title_contains");
    let newFilterValue = $state("");
    let newFilterCategory = $state("");
    let newFilterCaseSensitive = $state(false);

    // Edit filter states
    let editingFilter = $state(null);
    let editFilterName = $state("");
    let editFilterType = $state("title_contains");
    let editFilterValue = $state("");
    let editFilterCategory = $state("");
    let editFilterCaseSensitive = $state(false);

    // Feed health checking states
    let checkingFeeds = $state(new Set()); // Set of category IDs being checked
    let checkSessions = $state(new Map()); // Map of sessionId -> progress data
    let brokenFeedsModal = $state({
        show: false,
        categoryId: null,
        categoryName: "",
        feeds: [],
    });
    let selectedBrokenFeeds = $state(new Set());

    // Settings sections
    const settingsSections = [
        { id: "categories", name: "Feeds & Categories", icon: FolderOpen },
        { id: "filters", name: "Content Filters", icon: Filter },
        { id: "general", name: "General Settings", icon: Settings },
        { id: "import-export", name: "Import/Export", icon: FileText },
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
                category_id:
                    categoryId ||
                    (newFeedCategoryId
                        ? parseInt(newFeedCategoryId)
                        : undefined),
            };

            const newFeed = await apiActions.addFeed(feedData);

            // Immediately refresh the newly created feed to fetch articles
            if (newFeed && newFeed.id) {
                try {
                    await apiActions.refreshFeed(newFeed.id);
                } catch (refreshErr) {
                    console.error("Failed to refresh new feed:", refreshErr);
                    // Don't throw - the feed was created successfully, refresh just failed
                }
            }

            // Reset form
            newFeedUrl = "";
            newFeedTitle = "";
            newFeedCategoryId = "";
            showAddFeed = false;
            showAddFeedForCategory = null;
        } catch (err) {
            console.error("Failed to add feed:", err);
        }
    }

    // Delete confirmation functions
    function confirmDeleteCategory(category) {
        const categoryFeeds = feeds.filter(
            (f) => f.category_id === category.id,
        );
        deleteTarget = {
            type: "category",
            item: category,
            feedCount: categoryFeeds.length,
            feeds: categoryFeeds,
        };
        showDeleteModal = true;
    }

    function confirmDeleteFeed(feed) {
        deleteTarget = {
            type: "feed",
            item: feed,
        };
        showDeleteModal = true;
    }

    async function handleConfirmDelete() {
        if (!deleteTarget) return;

        try {
            if (deleteTarget.type === "category") {
                // Delete category and all its feeds
                await api.request(`/api/categories/${deleteTarget.item.id}`, {
                    method: "DELETE",
                });
                // Reload data
                await apiActions.loadCategories();
                await apiActions.loadFeeds();
            } else if (deleteTarget.type === "feed") {
                // Delete single feed
                await api.request(`/api/feeds/${deleteTarget.item.id}`, {
                    method: "DELETE",
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
        const feed = feeds.find((f) => f.id === feedId);
        if (feed) {
            confirmDeleteFeed(feed);
        }
    }

    async function handleRefreshFeed(feedId) {
        try {
            await apiActions.refreshFeed(feedId);
        } catch (err) {
            console.error("Failed to refresh feed:", err);
        }
    }

    async function handleRefreshAllFeeds() {
        isRefreshing = true;
        try {
            await apiActions.refreshAllFeeds();
        } catch (err) {
            console.error("Failed to refresh all feeds:", err);
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
                description: newCategoryDescription.trim() || undefined,
            };

            await apiActions.addCategory(categoryData);

            // Reset form
            newCategoryName = "";
            newCategoryDescription = "";
            showAddCategory = false;
        } catch (err) {
            console.error("Failed to add category:", err);
        }
    }

    // OPML functions
    async function handleImportOpml() {
        if (!importFile) return;

        try {
            isImporting = true;
            importStatus = null;

            const options = {
                duplicate_strategy: "skip",
                validate_feeds: true,
                merge_categories: true,
            };

            const result = await opml.import(importFile, options);
            importJobId = result.job_id;

            // Start polling for status
            pollImportStatus();
        } catch (err) {
            console.error("Failed to import OPML:", err);
            isImporting = false;
        }
    }

    async function pollImportStatus() {
        if (!importJobId) return;

        try {
            const status = await opml.getImportStatus(importJobId);
            importStatus = status;

            if (
                status.status === "completed" ||
                status.status === "failed" ||
                status.status === "cancelled"
            ) {
                isImporting = false;
                if (status.status === "completed") {
                    // Reload feeds and categories
                    await apiActions.loadFeeds();
                    await apiActions.loadCategories();
                }
            } else {
                // Continue polling
                setTimeout(pollImportStatus, 2000);
            }
        } catch (err) {
            console.error("Failed to get import status:", err);
            isImporting = false;
        }
    }

    async function handleExportOpml() {
        try {
            const result = await opml.export();

            // Create blob and download
            const blob = new Blob([result], { type: "application/xml" });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `zib-feeds-${new Date().toISOString().split("T")[0]}.opml`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error("Failed to export OPML:", err);
        }
    }

    // Filter management functions
    async function loadFilters() {
        try {
            const filtersData = await filters.getAll();
            userFilters = filtersData || [];
        } catch (err) {
            console.error("Failed to load filters:", err);
            userFilters = [];
        }
    }

    async function handleAddFilter() {
        if (!newFilterName.trim() || !newFilterValue.trim()) return;

        try {
            const filterData = {
                name: newFilterName.trim(),
                filter_type: newFilterType,
                filter_value: newFilterValue.trim(),
                category_id: newFilterCategory
                    ? parseInt(newFilterCategory)
                    : null,
                case_sensitive: newFilterCaseSensitive,
            };

            await filters.create(filterData);
            await loadFilters();

            // Reset form
            newFilterName = "";
            newFilterValue = "";
            newFilterCategory = "";
            newFilterCaseSensitive = false;
            showAddFilter = false;
        } catch (err) {
            console.error("Failed to add filter:", err);
        }
    }

    async function deleteFilter(filterId) {
        try {
            await filters.delete(filterId);
            await loadFilters();
        } catch (err) {
            console.error("Failed to delete filter:", err);
        }
    }

    async function toggleFilter(filterId) {
        try {
            await filters.toggle(filterId);
            await loadFilters();
        } catch (err) {
            console.error("Failed to toggle filter:", err);
        }
    }

    function startEditFilter(filter) {
        editingFilter = filter;
        editFilterName = filter.name;
        editFilterType = filter.filter_type;
        editFilterValue = filter.filter_value;
        editFilterCategory = filter.category_id || "";
        editFilterCaseSensitive = filter.case_sensitive;
    }

    function cancelEditFilter() {
        editingFilter = null;
        editFilterName = "";
        editFilterType = "title_contains";
        editFilterValue = "";
        editFilterCategory = "";
        editFilterCaseSensitive = false;
    }

    async function handleEditFilter() {
        if (!editFilterName.trim() || !editFilterValue.trim()) return;

        try {
            const filterData = {
                name: editFilterName.trim(),
                filter_type: editFilterType,
                filter_value: editFilterValue.trim(),
                category_id: editFilterCategory || null,
                case_sensitive: editFilterCaseSensitive,
            };

            await filters.update(editingFilter.id, filterData);
            cancelEditFilter();
            await loadFilters();
        } catch (err) {
            console.error("Failed to update filter:", err);
        }
    }

    // User settings functions
    async function loadUserSettings() {
        try {
            const settingsData = await userSettings.get();
            openWebpageForShortArticles =
                settingsData.open_webpage_for_short_articles;
            shortArticleThreshold = settingsData.short_article_threshold;
            autoRefreshFeeds = settingsData.auto_refresh_feeds;
            autoRefreshInterval = settingsData.auto_refresh_interval_minutes;
            defaultView = settingsData.default_view;
            showTimestampsInList = settingsData.show_timestamps_in_list;
            fontScale = settingsData.font_scale || 1.0;

            // Also update the frontend store
            settings.update((s) => ({
                ...s,
            }));
        } catch (err) {
            console.error("Failed to load user settings:", err);
        }
    }

    async function handleFontScaleChange(scale) {
        fontScale = scale;
        applyFontScale(scale);
        await saveUserSettings();
    }

    async function saveUserSettings() {
        try {
            const settingsData = {
                feeds_per_page: 50, // Keep existing default
                default_view: defaultView,
                open_webpage_for_short_articles: openWebpageForShortArticles,
                short_article_threshold: shortArticleThreshold,
                auto_refresh_feeds: autoRefreshFeeds,
                auto_refresh_interval_minutes: autoRefreshInterval,
                show_timestamps_in_list: showTimestampsInList,
                font_scale: fontScale,
            };

            await userSettings.update(settingsData);

            // Also update localStorage settings for frontend-only settings
            settings.setSetting("autoRefreshFeeds", autoRefreshFeeds);

            // Update auto-refresh service with new settings
            await autoRefreshService.updateSettings(settingsData);
        } catch (err) {
            console.error("Failed to save user settings:", err);
        }
    }

    // Load filters when filters section is selected
    $effect(() => {
        if (selectedSection === "filters") {
            loadFilters();
        }
    });

    // Load user settings when general section is selected
    $effect(() => {
        if (selectedSection === "general") {
            loadUserSettings();
        }
    });
    
    // Initialize font scale on mount
    $effect(() => {
        // Apply current font scale from localStorage
        fontScale = getCurrentFontScale();
    });

    // Feed health checking functions
    async function handleCheckFeeds(category) {
        try {
            // Start checking
            checkingFeeds.add(category.id);
            checkingFeeds = new Set(checkingFeeds);

            const response = await feedsApi.checkCategory(category.id);
            const sessionId = response.session_id;

            // Store session data
            checkSessions.set(sessionId, {
                categoryId: category.id,
                categoryName: category.name,
                status: "running",
                progress: {
                    completed: 0,
                    total: response.total_feeds,
                    percentage: 0,
                },
                results: {
                    accessible: 0,
                    inaccessible: 0,
                    pending: response.total_feeds,
                },
            });
            checkSessions = new Map(checkSessions);

            // Poll for progress
            pollCheckProgress(sessionId);
        } catch (err) {
            console.error("Failed to start feed check:", err);
            checkingFeeds.delete(category.id);
            checkingFeeds = new Set(checkingFeeds);
        }
    }

    async function pollCheckProgress(sessionId) {
        try {
            const status = await feedsApi.getCheckStatus(sessionId);

            // Update session data
            checkSessions.set(sessionId, status);
            checkSessions = new Map(checkSessions);

            if (status.status === "completed") {
                // Check completed, remove from checking set
                checkingFeeds.delete(status.progress.categoryId);
                checkingFeeds = new Set(checkingFeeds);

                // Show results - either broken feeds or success message
                if (status.results.inaccessible > 0) {
                    await showBrokenFeeds(status.progress.categoryId);
                } else {
                    // All feeds are healthy, show success notification
                    await showHealthyFeedsResult(
                        status.progress.categoryId,
                        status.results.accessible,
                    );
                }

                // Clean up session after 30 seconds
                setTimeout(() => {
                    checkSessions.delete(sessionId);
                    checkSessions = new Map(checkSessions);
                }, 30000);
            } else {
                // Continue polling
                setTimeout(() => pollCheckProgress(sessionId), 2000);
            }
        } catch (err) {
            console.error("Failed to get check status:", err);
            // Remove from checking set on error
            const sessionData = checkSessions.get(sessionId);
            if (sessionData && sessionData.progress) {
                checkingFeeds.delete(sessionData.progress.categoryId);
                checkingFeeds = new Set(checkingFeeds);
            }
        }
    }

    async function showBrokenFeeds(categoryId) {
        try {
            const category = categories.find((c) => c.id === categoryId);
            const response = await feedsApi.getBrokenFeeds(categoryId);

            brokenFeedsModal = {
                show: true,
                categoryId: categoryId,
                categoryName: category?.name || "Unknown",
                feeds: response.broken_feeds,
            };
            selectedBrokenFeeds = new Set();
        } catch (err) {
            console.error("Failed to get broken feeds:", err);
        }
    }

    async function showHealthyFeedsResult(categoryId, accessibleCount) {
        const category = categories.find((c) => c.id === categoryId);

        brokenFeedsModal = {
            show: true,
            categoryId: categoryId,
            categoryName: category?.name || "Unknown",
            feeds: [],
            healthyMessage: `All ${accessibleCount} feeds in this category are working correctly! ✅`,
        };
    }

    function toggleBrokenFeed(feedId) {
        if (selectedBrokenFeeds.has(feedId)) {
            selectedBrokenFeeds.delete(feedId);
        } else {
            selectedBrokenFeeds.add(feedId);
        }
        selectedBrokenFeeds = new Set(selectedBrokenFeeds);
    }

    function selectAllBrokenFeeds() {
        selectedBrokenFeeds = new Set(brokenFeedsModal.feeds.map((f) => f.id));
    }

    function deselectAllBrokenFeeds() {
        selectedBrokenFeeds = new Set();
    }

    async function deleteBrokenFeeds() {
        try {
            const feedIds = Array.from(selectedBrokenFeeds);
            if (feedIds.length === 0) return;

            const result = await feedsApi.bulkDelete(feedIds);

            // Update the broken feeds modal
            brokenFeedsModal.feeds = brokenFeedsModal.feeds.filter(
                (f) => !feedIds.includes(f.id),
            );
            selectedBrokenFeeds = new Set();

            // Refresh feeds and categories
            await Promise.all([
                apiActions.loadFeeds(),
                apiActions.loadCategories(),
            ]);

            console.log(`Deleted ${result.deleted_count} feeds`);
        } catch (err) {
            console.error("Failed to delete broken feeds:", err);
        }
    }

    function closeBrokenFeedsModal() {
        brokenFeedsModal = {
            show: false,
            categoryId: null,
            categoryName: "",
            feeds: [],
        };
        selectedBrokenFeeds = new Set();
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
</script>

<div
    class="h-full flex relative"
    ontouchstart={handleTouchStart}
    ontouchend={handleTouchEnd}
>
    <!-- Mobile Overlay -->
    {#if mobileState && sidebarState}
        <div
            class="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
            onclick={() => closeSidebar()}
        ></div>
    {/if}

    <!-- Settings Sidebar -->
    <aside
        class="
		{mobileState
            ? 'fixed left-0 top-0 h-full z-40 transform transition-transform duration-300'
            : 'relative'}
		{mobileState && !sidebarState ? '-translate-x-full' : 'translate-x-0'}
		w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col
		md:relative md:translate-x-0 md:z-auto
	"
    >
        <!-- Settings Header -->
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
                <Settings class="h-5 w-5 text-gray-600 dark:text-gray-300" />
                <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
                    Settings
                </h1>
            </div>
            <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">
                Manage your RSS reader
            </p>
        </div>

        <!-- Settings Navigation -->
        <div class="flex-1 overflow-y-auto p-2 space-y-1">
            {#each settingsSections as section}
                <button
                    onclick={() => {
                        selectedSection = section.id;
                        // Close sidebar on mobile after selection
                        if (mobileState) {
                            closeSidebar();
                        }
                    }}
                    class="w-full flex items-center space-x-2 p-2 rounded transition-colors text-left {selectedSection ===
                    section.id
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
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
        <div
            class="border-b border-gray-200 dark:border-gray-700 px-4 md:px-6 py-4 bg-white dark:bg-gray-800"
        >
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <!-- Hamburger Menu (Mobile Only) -->
                    {#if mobileState}
                        <button
                            onclick={() => toggleSidebar()}
                            class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            aria-label="Toggle menu"
                        >
                            <Menu
                                class="h-5 w-5 text-gray-600 dark:text-gray-300"
                            />
                        </button>
                    {/if}
                    <h2
                        class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white"
                    >
                        {settingsSections.find((s) => s.id === selectedSection)
                            ?.name || "Settings"}
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
            <div
                class="mx-6 mt-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
                <p class="text-red-700 dark:text-red-300">{apiError}</p>
            </div>
        {/if}

        <!-- Content Area -->
        <div class="p-6">
            {#if selectedSection === "categories"}
                <!-- Feeds & Categories Section -->
                <section class="space-y-4">
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex space-x-2">
                            <button
                                onclick={() =>
                                    (showAddCategory = !showAddCategory)}
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
                                <RefreshCw
                                    class="h-4 w-4 mr-1 {isRefreshing
                                        ? 'animate-spin'
                                        : ''}"
                                />
                                Refresh All Feeds
                            </button>
                        </div>
                    </div>

                    <!-- Add Category Form -->
                    {#if showAddCategory}
                        <div
                            class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-4"
                        >
                            <h3
                                class="text-lg font-medium text-gray-900 dark:text-white"
                            >
                                Add New Category
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label
                                        for="category-name"
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
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
                                    <label
                                        for="category-description"
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
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
                                    onclick={() => (showAddCategory = false)}
                                    class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                                >
                                    Cancel
                                </button>
                                <button
                                    onclick={handleAddCategory}
                                    disabled={!newCategoryName.trim() ||
                                        loading}
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
                            {@const categoryFeeds = feeds.filter(
                                (f) => f.category_id === category.id,
                            )}
                            {@const isExpanded = expandedCategories.has(
                                category.id,
                            )}

                            <div
                                class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600"
                            >
                                <!-- Category Header -->
                                <div
                                    class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600 rounded-lg"
                                    onclick={() => toggleCategory(category.id)}
                                >
                                    <div class="flex items-center space-x-3">
                                        <button
                                            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                        >
                                            {#if isExpanded}
                                                <ChevronDown class="h-4 w-4" />
                                            {:else}
                                                <ChevronRight class="h-4 w-4" />
                                            {/if}
                                        </button>
                                        <div>
                                            <h3
                                                class="font-medium text-gray-900 dark:text-white"
                                            >
                                                {category.name}
                                            </h3>
                                            {#if category.description}
                                                <p
                                                    class="text-sm text-gray-600 dark:text-gray-400"
                                                >
                                                    {category.description}
                                                </p>
                                            {/if}
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-4">
                                        <span
                                            class="text-sm text-gray-500 dark:text-gray-400"
                                        >
                                            {categoryFeeds.length} feeds
                                        </span>
                                        <div
                                            class="flex items-center space-x-2"
                                        >
                                            <button
                                                onclick={(e) => {
                                                    e.stopPropagation();

                                                    // Make sure category is expanded
                                                    if (
                                                        !expandedCategories.has(
                                                            category.id,
                                                        )
                                                    ) {
                                                        expandedCategories.add(
                                                            category.id,
                                                        );
                                                        expandedCategories =
                                                            new Set(
                                                                expandedCategories,
                                                            );
                                                    }

                                                    showAddFeedForCategory =
                                                        category.id;
                                                }}
                                                class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                                title="Add feed to this category"
                                            >
                                                <Plus class="h-4 w-4" />
                                            </button>
                                            <button
                                                onclick={(e) => {
                                                    e.stopPropagation();
                                                    handleCheckFeeds(category);
                                                }}
                                                disabled={checkingFeeds.has(
                                                    category.id,
                                                ) || categoryFeeds.length === 0}
                                                class="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300 disabled:opacity-50 disabled:cursor-not-allowed"
                                                title={categoryFeeds.length ===
                                                0
                                                    ? "No feeds to check"
                                                    : checkingFeeds.has(
                                                            category.id,
                                                        )
                                                      ? "Checking feeds..."
                                                      : "Check feed accessibility"}
                                            >
                                                {#if checkingFeeds.has(category.id)}
                                                    <RefreshCw
                                                        class="h-4 w-4 animate-spin"
                                                    />
                                                {:else}
                                                    <Activity class="h-4 w-4" />
                                                {/if}
                                            </button>
                                            <button
                                                onclick={(e) => {
                                                    e.stopPropagation();
                                                    confirmDeleteCategory(
                                                        category,
                                                    );
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
                                    <div
                                        class="border-t border-gray-200 dark:border-gray-600"
                                    >
                                        <!-- Add Feed Form for this Category -->
                                        {#if showAddFeedForCategory === category.id}
                                            <div
                                                class="p-4 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-600"
                                            >
                                                <h4
                                                    class="text-md font-medium text-gray-900 dark:text-white mb-3"
                                                >
                                                    Add Feed to {category.name}
                                                </h4>
                                                <div
                                                    class="grid grid-cols-1 md:grid-cols-2 gap-4"
                                                >
                                                    <div>
                                                        <label
                                                            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                        >
                                                            Feed URL *
                                                        </label>
                                                        <input
                                                            type="url"
                                                            bind:value={
                                                                newFeedUrl
                                                            }
                                                            placeholder="https://example.com/feed.xml"
                                                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                                        />
                                                    </div>
                                                    <div>
                                                        <label
                                                            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                        >
                                                            Title (optional)
                                                        </label>
                                                        <input
                                                            type="text"
                                                            bind:value={
                                                                newFeedTitle
                                                            }
                                                            placeholder="Feed title"
                                                            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                                        />
                                                    </div>
                                                </div>
                                                <div
                                                    class="flex justify-end space-x-2 mt-4"
                                                >
                                                    <button
                                                        onclick={() =>
                                                            (showAddFeedForCategory =
                                                                null)}
                                                        class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                                                    >
                                                        Cancel
                                                    </button>
                                                    <button
                                                        onclick={() =>
                                                            handleAddFeed(
                                                                category.id,
                                                            )}
                                                        disabled={!newFeedUrl.trim() ||
                                                            loading}
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
                                                    <div
                                                        class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                                                    >
                                                        <div class="flex-1">
                                                            <h4
                                                                class="font-medium text-gray-900 dark:text-white text-sm"
                                                            >
                                                                {feed.title}
                                                            </h4>
                                                            <p
                                                                class="text-xs text-gray-600 dark:text-gray-400"
                                                            >
                                                                {feed.url}
                                                            </p>
                                                        </div>
                                                        <div
                                                            class="flex items-center space-x-1"
                                                        >
                                                            <button
                                                                onclick={() =>
                                                                    handleRefreshFeed(
                                                                        feed.id,
                                                                    )}
                                                                disabled={loading}
                                                                class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50"
                                                                title="Refresh feed"
                                                            >
                                                                <RefreshCw
                                                                    class="h-3 w-3"
                                                                />
                                                            </button>
                                                            <button
                                                                onclick={() =>
                                                                    handleDeleteFeed(
                                                                        feed.id,
                                                                    )}
                                                                disabled={loading}
                                                                class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50"
                                                                title="Delete feed"
                                                            >
                                                                <Trash2
                                                                    class="h-3 w-3"
                                                                />
                                                            </button>
                                                        </div>
                                                    </div>
                                                {/each}
                                            </div>
                                        {:else}
                                            <div
                                                class="p-4 text-center text-gray-500 dark:text-gray-400 text-sm"
                                            >
                                                No feeds in this category yet.
                                            </div>
                                        {/if}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </section>
            {:else if selectedSection === "filters"}
                <!-- Content Filters Section -->
                <section class="space-y-4">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3
                                class="text-lg font-medium text-gray-900 dark:text-white"
                            >
                                Content Filters
                            </h3>
                            <p class="text-sm text-gray-600 dark:text-gray-400">
                                Hide articles based on title, author, or other
                                criteria
                            </p>
                        </div>
                        <button
                            onclick={() => (showAddFilter = !showAddFilter)}
                            class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            <Filter class="h-4 w-4 mr-1" />
                            Add Filter
                        </button>
                    </div>

                    <!-- Add Filter Form -->
                    {#if showAddFilter}
                        <div
                            class="bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 p-4 mb-4"
                        >
                            <h4
                                class="text-sm font-medium text-gray-900 dark:text-white mb-3"
                            >
                                Create New Filter
                            </h4>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <!-- Filter Name -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
                                        Filter Name
                                    </label>
                                    <input
                                        type="text"
                                        bind:value={newFilterName}
                                        placeholder="e.g., Hide Sports News"
                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>

                                <!-- Filter Type -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
                                        Filter Type
                                    </label>
                                    <select
                                        bind:value={newFilterType}
                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="title_contains"
                                            >Title contains</option
                                        >
                                        <option value="title_not_contains"
                                            >Title does not contain</option
                                        >
                                        <option value="title_exact"
                                            >Title matches exactly</option
                                        >
                                        <option value="author_contains"
                                            >Author contains</option
                                        >
                                    </select>
                                </div>

                                <!-- Filter Value -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
                                        Filter Value
                                    </label>
                                    <input
                                        type="text"
                                        bind:value={newFilterValue}
                                        placeholder="e.g., Django, &quot;React Native&quot; OR Vue, sports AND football"
                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                    <div
                                        class="mt-2 text-xs text-gray-500 dark:text-gray-400"
                                    >
                                        <p class="font-medium mb-1">
                                            Advanced syntax:
                                        </p>
                                        <ul class="space-y-1">
                                            <li>
                                                • Simple: <code>Django</code>
                                            </li>
                                            <li>
                                                • Phrase: <code
                                                    >"Django Rest Framework"</code
                                                >
                                            </li>
                                            <li>
                                                • OR logic: <code
                                                    >"Django Rest Framework" OR
                                                    DRF</code
                                                >
                                            </li>
                                            <li>
                                                • AND logic: <code
                                                    >Python AND tutorial</code
                                                >
                                            </li>
                                        </ul>
                                    </div>
                                </div>

                                <!-- Category Selection -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                    >
                                        Apply to Category
                                    </label>
                                    <select
                                        bind:value={newFilterCategory}
                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    >
                                        <option value="">All categories</option>
                                        {#each categories as category}
                                            <option value={category.id}
                                                >{category.name}</option
                                            >
                                        {/each}
                                    </select>
                                </div>
                            </div>

                            <!-- Case Sensitive Checkbox -->
                            <div class="mt-4">
                                <label class="flex items-center">
                                    <input
                                        type="checkbox"
                                        bind:checked={newFilterCaseSensitive}
                                        class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-700"
                                    />
                                    <span
                                        class="ml-2 text-sm text-gray-700 dark:text-gray-300"
                                        >Case sensitive</span
                                    >
                                </label>
                            </div>

                            <!-- Form Actions -->
                            <div class="flex justify-end space-x-2 mt-4">
                                <button
                                    onclick={() => (showAddFilter = false)}
                                    class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-md hover:bg-gray-50 dark:hover:bg-gray-500"
                                >
                                    Cancel
                                </button>
                                <button
                                    onclick={handleAddFilter}
                                    disabled={!newFilterName.trim() ||
                                        !newFilterValue.trim()}
                                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                                >
                                    Create Filter
                                </button>
                            </div>
                        </div>
                    {/if}

                    <!-- Filters List -->
                    <div class="space-y-2">
                        {#if userFilters.length === 0}
                            <div class="text-center py-8">
                                <Filter
                                    class="mx-auto h-12 w-12 text-gray-400"
                                />
                                <h3
                                    class="mt-2 text-sm font-medium text-gray-900 dark:text-white"
                                >
                                    No filters yet
                                </h3>
                                <p
                                    class="mt-1 text-sm text-gray-500 dark:text-gray-400"
                                >
                                    Create your first filter to hide unwanted
                                    articles.
                                </p>
                            </div>
                        {:else}
                            {#each userFilters as filter}
                                <div
                                    class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                                >
                                    {#if editingFilter && editingFilter.id === filter.id}
                                        <!-- Edit Form -->
                                        <div class="space-y-4">
                                            <div class="grid grid-cols-2 gap-4">
                                                <!-- Filter Name -->
                                                <div>
                                                    <label
                                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                    >
                                                        Filter Name
                                                    </label>
                                                    <input
                                                        type="text"
                                                        bind:value={
                                                            editFilterName
                                                        }
                                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                    />
                                                </div>

                                                <!-- Filter Type -->
                                                <div>
                                                    <label
                                                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                    >
                                                        Filter Type
                                                    </label>
                                                    <select
                                                        bind:value={
                                                            editFilterType
                                                        }
                                                        class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                    >
                                                        <option
                                                            value="title_contains"
                                                            >Title contains</option
                                                        >
                                                        <option
                                                            value="title_not_contains"
                                                            >Title does not
                                                            contain</option
                                                        >
                                                        <option
                                                            value="title_exact"
                                                            >Title exact match</option
                                                        >
                                                        <option
                                                            value="author_contains"
                                                            >Author contains</option
                                                        >
                                                    </select>
                                                </div>
                                            </div>

                                            <!-- Filter Value -->
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                >
                                                    Filter Value
                                                </label>
                                                <textarea
                                                    bind:value={editFilterValue}
                                                    placeholder="e.g., Django, &quot;React Native&quot; OR Vue, sports AND football"
                                                    rows="3"
                                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                ></textarea>
                                            </div>

                                            <!-- Category Selection -->
                                            <div>
                                                <label
                                                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                                >
                                                    Apply to Category
                                                </label>
                                                <select
                                                    bind:value={
                                                        editFilterCategory
                                                    }
                                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                >
                                                    <option value=""
                                                        >All categories</option
                                                    >
                                                    {#each categories as category}
                                                        <option
                                                            value={category.id}
                                                            >{category.name}</option
                                                        >
                                                    {/each}
                                                </select>
                                            </div>

                                            <!-- Case Sensitive Checkbox -->
                                            <div>
                                                <label
                                                    class="flex items-center"
                                                >
                                                    <input
                                                        type="checkbox"
                                                        bind:checked={
                                                            editFilterCaseSensitive
                                                        }
                                                        class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-700"
                                                    />
                                                    <span
                                                        class="ml-2 text-sm text-gray-700 dark:text-gray-300"
                                                        >Case sensitive</span
                                                    >
                                                </label>
                                            </div>

                                            <!-- Form Actions -->
                                            <div
                                                class="flex justify-end space-x-2"
                                            >
                                                <button
                                                    onclick={cancelEditFilter}
                                                    class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded-md hover:bg-gray-50 dark:hover:bg-gray-500"
                                                >
                                                    Cancel
                                                </button>
                                                <button
                                                    onclick={handleEditFilter}
                                                    disabled={!editFilterName.trim() ||
                                                        !editFilterValue.trim()}
                                                    class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                                                >
                                                    Save Changes
                                                </button>
                                            </div>
                                        </div>
                                    {:else}
                                        <!-- Display Mode -->
                                        <div
                                            class="flex items-center justify-between"
                                        >
                                            <div class="flex-1">
                                                <div
                                                    class="flex items-center space-x-2"
                                                >
                                                    <h4
                                                        class="font-medium text-gray-900 dark:text-white"
                                                    >
                                                        {filter.name}
                                                    </h4>
                                                    <span
                                                        class="px-2 py-1 text-xs rounded-full {filter.is_active
                                                            ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                                                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}"
                                                    >
                                                        {filter.is_active
                                                            ? "Active"
                                                            : "Inactive"}
                                                    </span>
                                                </div>
                                                <p
                                                    class="text-sm text-gray-600 dark:text-gray-400 mt-1"
                                                >
                                                    {filter.filter_type.replace(
                                                        "_",
                                                        " ",
                                                    )}: "{filter.filter_value}"
                                                    {#if filter.category_name}
                                                        • Category: {filter.category_name}
                                                    {:else}
                                                        • All categories
                                                    {/if}
                                                    {#if filter.case_sensitive}
                                                        • Case sensitive
                                                    {/if}
                                                </p>
                                            </div>
                                            <div
                                                class="flex items-center space-x-2"
                                            >
                                                <button
                                                    onclick={() =>
                                                        toggleFilter(filter.id)}
                                                    class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                                    title={filter.is_active
                                                        ? "Deactivate filter"
                                                        : "Activate filter"}
                                                >
                                                    {#if filter.is_active}
                                                        <svg
                                                            class="w-4 h-4 text-green-600"
                                                            fill="currentColor"
                                                            viewBox="0 0 24 24"
                                                        >
                                                            <path
                                                                d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"
                                                            />
                                                        </svg>
                                                    {:else}
                                                        <svg
                                                            class="w-4 h-4"
                                                            fill="none"
                                                            stroke="currentColor"
                                                            viewBox="0 0 24 24"
                                                        >
                                                            <path
                                                                stroke-linecap="round"
                                                                stroke-linejoin="round"
                                                                stroke-width="2"
                                                                d="M6 18L18 6M6 6l12 12"
                                                            />
                                                        </svg>
                                                    {/if}
                                                </button>
                                                <button
                                                    onclick={() =>
                                                        startEditFilter(filter)}
                                                    class="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                                                    title="Edit filter"
                                                >
                                                    <Edit3 class="h-4 w-4" />
                                                </button>
                                                <button
                                                    onclick={() =>
                                                        deleteFilter(filter.id)}
                                                    class="p-2 text-red-400 hover:text-red-600"
                                                    title="Delete filter"
                                                >
                                                    <Trash2 class="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    {/if}
                                </div>
                            {/each}
                        {/if}
                    </div>
                </section>
            {:else if selectedSection === "general"}
                <!-- General Settings Section -->
                <section class="space-y-4">
                    <div
                        class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                    >
                        <h3
                            class="text-lg font-medium text-gray-900 dark:text-white mb-4"
                        >
                            Application Settings
                        </h3>
                        <div class="space-y-4">
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Auto-refresh feeds</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Automatically refresh all feeds
                                        periodically
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    bind:checked={autoRefreshFeeds}
                                    onchange={saveUserSettings}
                                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Auto-refresh interval (minutes)</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        How often to automatically refresh feeds
                                    </p>
                                </div>
                                <input
                                    type="number"
                                    min="5"
                                    max="1440"
                                    step="5"
                                    bind:value={autoRefreshInterval}
                                    onchange={saveUserSettings}
                                    class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Show unread count in title</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Display unread article count in browser
                                        tab title
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    bind:checked={showUnreadCountInTitle}
                                    onchange={() =>
                                        settings.setSetting(
                                            "showUnreadCountInTitle",
                                            showUnreadCountInTitle,
                                        )}
                                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                    </div>

                    <!-- Article Display Settings -->
                    <div
                        class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                    >
                        <h3
                            class="text-lg font-medium text-gray-900 dark:text-white mb-4"
                        >
                            Article Display
                        </h3>
                        <div class="space-y-4">
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Open webpage instead of RSS feeds for
                                        short articles</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Click short articles to open original
                                        webpage in new tab instead of modal
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    bind:checked={openWebpageForShortArticles}
                                    onchange={saveUserSettings}
                                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Short article threshold (characters)</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Articles shorter than this will open
                                        webpage instead of modal
                                    </p>
                                </div>
                                <input
                                    type="number"
                                    min="50"
                                    max="2000"
                                    step="50"
                                    bind:value={shortArticleThreshold}
                                    onchange={saveUserSettings}
                                    class="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Default view</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Which view to show when opening the app
                                    </p>
                                </div>
                                <select
                                    bind:value={defaultView}
                                    onchange={saveUserSettings}
                                    class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-blue-500 focus:border-blue-500"
                                >
                                    <option value="all">All Articles</option>
                                    <option value="unread"
                                        >Unread Articles</option
                                    >
                                    <option value="starred"
                                        >Starred Articles</option
                                    >
                                </select>
                            </div>
                            <div class="flex items-center justify-between">
                                <div>
                                    <label
                                        class="text-sm font-medium text-gray-900 dark:text-white"
                                        >Show timestamps in article list</label
                                    >
                                    <p
                                        class="text-xs text-gray-600 dark:text-gray-400"
                                    >
                                        Display relative time (20m, 3h20m,
                                        3d3h20m) for each article
                                    </p>
                                </div>
                                <input
                                    type="checkbox"
                                    bind:checked={showTimestampsInList}
                                    onchange={saveUserSettings}
                                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                    </div>
                    
                    <!-- Accessibility Settings -->
                    <div
                        class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                    >
                        <h3
                            class="text-lg font-medium text-gray-900 dark:text-white mb-4"
                        >
                            Accessibility
                        </h3>
                        <div class="space-y-4">
                            <div>
                                <label
                                    class="text-sm font-medium text-gray-900 dark:text-white block mb-2"
                                    >Font Size</label
                                >
                                <p
                                    class="text-xs text-gray-600 dark:text-gray-400 mb-3"
                                >
                                    Adjust the font size across the entire interface
                                </p>
                                <div class="flex items-center gap-2">
                                    {#each Object.entries(FONT_SCALES) as [key, scale]}
                                        <button
                                            onclick={() => handleFontScaleChange(scale.value)}
                                            class="px-3 py-2 text-sm rounded-lg border transition-colors
                                                   {fontScale === scale.value 
                                                    ? 'bg-blue-600 text-white border-blue-600' 
                                                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                                            title={scale.label}
                                        >
                                            {scale.label}
                                        </button>
                                    {/each}
                                </div>
                                <div class="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                    <p class="text-sm text-gray-700 dark:text-gray-300" style="font-size: calc(1rem * {fontScale})">
                                        Preview: This is how text will appear with your selected font size.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            {:else if selectedSection === "import-export"}
                <!-- OPML Import/Export Section -->
                <section class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- Import OPML -->
                        <div
                            class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                        >
                            <h3
                                class="text-lg font-medium text-gray-900 dark:text-white mb-2"
                            >
                                Import OPML
                            </h3>
                            <p
                                class="text-sm text-gray-600 dark:text-gray-400 mb-4"
                            >
                                Import feeds from an OPML file
                            </p>
                            <div class="space-y-3">
                                <input
                                    type="file"
                                    accept=".opml,.xml"
                                    onchange={(e) =>
                                        (importFile = e.target.files[0])}
                                    class="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                />
                                <button
                                    onclick={handleImportOpml}
                                    disabled={!importFile ||
                                        loading ||
                                        isImporting}
                                    class="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                                >
                                    <Upload class="h-4 w-4 mr-2" />
                                    {isImporting
                                        ? "Importing..."
                                        : "Import OPML"}
                                </button>

                                <!-- Import Status -->
                                {#if isImporting && importStatus}
                                    <div
                                        class="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg"
                                    >
                                        <div
                                            class="flex items-center justify-between mb-2"
                                        >
                                            <span
                                                class="text-sm font-medium text-blue-900 dark:text-blue-100"
                                            >
                                                {importStatus.current_phase ||
                                                    "Processing"}...
                                            </span>
                                            <span
                                                class="text-xs text-blue-700 dark:text-blue-300"
                                            >
                                                {Math.round(
                                                    importStatus.progress_percentage ||
                                                        0,
                                                )}%
                                            </span>
                                        </div>
                                        <div
                                            class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2"
                                        >
                                            <div
                                                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                                style="width: {importStatus.progress_percentage ||
                                                    0}%"
                                            ></div>
                                        </div>
                                        {#if importStatus.feeds_imported > 0 || importStatus.categories_created > 0}
                                            <div
                                                class="mt-2 text-xs text-blue-700 dark:text-blue-300"
                                            >
                                                Created {importStatus.categories_created}
                                                categories, imported {importStatus.feeds_imported}
                                                feeds
                                                {#if importStatus.feeds_failed > 0}
                                                    ({importStatus.feeds_failed}
                                                    failed)
                                                {/if}
                                            </div>
                                        {/if}
                                    </div>
                                {:else if importStatus && (importStatus.status === "completed" || importStatus.status === "failed")}
                                    <div
                                        class="mt-3 p-3 {importStatus.status ===
                                        'completed'
                                            ? 'bg-green-50 dark:bg-green-900/20'
                                            : 'bg-red-50 dark:bg-red-900/20'} rounded-lg"
                                    >
                                        <div
                                            class="text-sm font-medium {importStatus.status ===
                                            'completed'
                                                ? 'text-green-900 dark:text-green-100'
                                                : 'text-red-900 dark:text-red-100'}"
                                        >
                                            {#if importStatus.status === "completed"}
                                                Import completed successfully!
                                                <div
                                                    class="text-xs mt-1 {importStatus.status ===
                                                    'completed'
                                                        ? 'text-green-700 dark:text-green-300'
                                                        : 'text-red-700 dark:text-red-300'}"
                                                >
                                                    Created {importStatus.categories_created}
                                                    categories, imported {importStatus.feeds_imported}
                                                    feeds
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
                        <div
                            class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                        >
                            <h3
                                class="text-lg font-medium text-gray-900 dark:text-white mb-2"
                            >
                                Export OPML
                            </h3>
                            <p
                                class="text-sm text-gray-600 dark:text-gray-400 mb-4"
                            >
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
    <div
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
        <div
            class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4"
        >
            <h3
                class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
            >
                {#if deleteTarget.type === "category"}
                    Delete Category
                {:else}
                    Delete Feed
                {/if}
            </h3>

            <div class="mb-4">
                {#if deleteTarget.type === "category"}
                    <p class="text-gray-700 dark:text-gray-300">
                        Are you sure you want to delete the category <strong
                            >"{deleteTarget.item.name}"</strong
                        >?
                    </p>
                    {#if deleteTarget.feedCount > 0}
                        <div
                            class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                        >
                            <p
                                class="text-red-800 dark:text-red-200 text-sm font-medium"
                            >
                                ⚠️ This will also delete {deleteTarget.feedCount}
                                feed{deleteTarget.feedCount === 1 ? "" : "s"} and
                                all their articles:
                            </p>
                            <ul
                                class="mt-2 text-red-700 dark:text-red-300 text-sm list-disc list-inside"
                            >
                                {#each deleteTarget.feeds as feed}
                                    <li>{feed.title || feed.url}</li>
                                {/each}
                            </ul>
                        </div>
                    {/if}
                {:else}
                    <p class="text-gray-700 dark:text-gray-300">
                        Are you sure you want to delete the feed <strong
                            >"{deleteTarget.item.title}"</strong
                        >?
                    </p>
                    <div
                        class="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                    >
                        <p class="text-red-800 dark:text-red-200 text-sm">
                            ⚠️ This will also delete all articles from this
                            feed.
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
                    {#if deleteTarget.type === "category"}
                        Delete Category & {deleteTarget.feedCount} Feed{deleteTarget.feedCount ===
                        1
                            ? ""
                            : "s"}
                    {:else}
                        Delete Feed
                    {/if}
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Broken Feeds Modal -->
{#if brokenFeedsModal.show}
    <div
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
        <div
            class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col"
        >
            <div
                class="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-600"
            >
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {brokenFeedsModal.feeds.length > 0
                        ? `Broken Feeds in "${brokenFeedsModal.categoryName}"`
                        : `Feed Check Results - "${brokenFeedsModal.categoryName}"`}
                </h3>
                <button
                    onclick={closeBrokenFeedsModal}
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                    <svg
                        class="w-6 h-6"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M6 18L18 6m0-12L6 6"
                        />
                    </svg>
                </button>
            </div>

            {#if brokenFeedsModal.feeds.length === 0}
                <div class="flex-1 flex items-center justify-center">
                    <div class="text-center">
                        <CheckCircle
                            class="mx-auto h-16 w-16 text-green-500 mb-4"
                        />
                        <h3
                            class="text-lg font-medium text-gray-900 dark:text-white mb-2"
                        >
                            All feeds are accessible!
                        </h3>
                        <p class="text-gray-600 dark:text-gray-400">
                            {brokenFeedsModal.healthyMessage ||
                                "No broken feeds found in this category."}
                        </p>
                    </div>
                </div>
            {:else}
                <div class="mb-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        Found {brokenFeedsModal.feeds.length} feed{brokenFeedsModal
                            .feeds.length === 1
                            ? ""
                            : "s"} that have been inaccessible for 7+ days. Select
                        feeds to delete permanently.
                    </p>

                    <!-- Selection Controls -->
                    <div class="flex items-center space-x-4 mb-4">
                        <button
                            onclick={selectAllBrokenFeeds}
                            class="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                            Select All
                        </button>
                        <button
                            onclick={deselectAllBrokenFeeds}
                            class="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300"
                        >
                            Deselect All
                        </button>
                        <span class="text-sm text-gray-500 dark:text-gray-400">
                            {selectedBrokenFeeds.size} of {brokenFeedsModal
                                .feeds.length} selected
                        </span>
                    </div>
                </div>

                <!-- Broken Feeds List -->
                <div
                    class="flex-1 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg"
                >
                    <div class="divide-y divide-gray-200 dark:divide-gray-600">
                        {#each brokenFeedsModal.feeds as feed}
                            <div
                                class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700"
                            >
                                <div class="flex items-start space-x-3">
                                    <input
                                        type="checkbox"
                                        checked={selectedBrokenFeeds.has(
                                            feed.id,
                                        )}
                                        onchange={() =>
                                            toggleBrokenFeed(feed.id)}
                                        class="mt-1 rounded border-gray-300 dark:border-gray-600 text-red-600 focus:ring-red-500"
                                    />
                                    <div class="flex-1 min-w-0">
                                        <div
                                            class="flex items-center space-x-2 mb-1"
                                        >
                                            <h4
                                                class="font-medium text-gray-900 dark:text-white text-sm truncate"
                                            >
                                                {feed.title}
                                            </h4>
                                            <span
                                                class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
                                            >
                                                {feed.consecutive_failures} failures
                                            </span>
                                        </div>
                                        <p
                                            class="text-xs text-gray-600 dark:text-gray-400 mb-2 break-all"
                                        >
                                            {feed.url}
                                        </p>

                                        <div
                                            class="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400"
                                        >
                                            {#if feed.last_checked}
                                                <span
                                                    >Last checked: {new Date(
                                                        feed.last_checked,
                                                    ).toLocaleDateString()}</span
                                                >
                                            {/if}
                                            {#if feed.last_success}
                                                <span
                                                    >Last success: {new Date(
                                                        feed.last_success,
                                                    ).toLocaleDateString()}</span
                                                >
                                            {/if}
                                        </div>

                                        {#if feed.recent_errors && feed.recent_errors.length > 0}
                                            <div class="mt-2">
                                                <details class="text-xs">
                                                    <summary
                                                        class="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-300"
                                                    >
                                                        Recent errors ({feed
                                                            .recent_errors
                                                            .length})
                                                    </summary>
                                                    <div
                                                        class="mt-1 pl-4 space-y-1"
                                                    >
                                                        {#each feed.recent_errors as error}
                                                            <div
                                                                class="flex items-center space-x-2 text-red-600 dark:text-red-400"
                                                            >
                                                                <span
                                                                    >{new Date(
                                                                        error.checked_at,
                                                                    ).toLocaleDateString()}</span
                                                                >
                                                                {#if error.status_code}
                                                                    <span
                                                                        class="font-mono"
                                                                        >HTTP {error.status_code}</span
                                                                    >
                                                                {/if}
                                                                {#if error.error_message}
                                                                    <span
                                                                        class="truncate"
                                                                        >{error.error_message}</span
                                                                    >
                                                                {/if}
                                                            </div>
                                                        {/each}
                                                    </div>
                                                </details>
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}

            <!-- Modal Actions -->
            <div
                class="flex justify-between items-center pt-4 mt-4 border-t border-gray-200 dark:border-gray-600"
            >
                <button
                    onclick={closeBrokenFeedsModal}
                    class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                    Close
                </button>

                {#if brokenFeedsModal.feeds.length > 0}
                    <button
                        onclick={deleteBrokenFeeds}
                        disabled={selectedBrokenFeeds.size === 0}
                        class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Delete {selectedBrokenFeeds.size} Selected Feed{selectedBrokenFeeds.size ===
                        1
                            ? ""
                            : "s"}
                    </button>
                {/if}
            </div>
        </div>
    </div>
{/if}
