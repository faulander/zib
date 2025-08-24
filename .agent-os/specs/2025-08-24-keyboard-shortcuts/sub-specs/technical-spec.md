# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-24-keyboard-shortcuts/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Technical Requirements

- **Global keyboard event handling** - Capture keyboard events at document level while respecting input focus states
- **Focus management system** - Track and control focus states between feeds, articles, and interface elements
- **Accessible navigation** - Follow ARIA guidelines and screen reader compatibility
- **Contextual shortcuts** - Different shortcuts based on current interface state (article modal vs main view)
- **Visual feedback system** - Show keyboard shortcuts in tooltips and help overlays
- **Mobile keyboard support** - Handle external keyboard input on tablets and mobile devices with keyboards

## Approach Options

**Option A: Global Event Listener with State Management**
- Pros: Centralized control, easy to maintain, consistent behavior
- Cons: Risk of conflicts with other components, complex state tracking

**Option B: Component-Level Keyboard Handlers** (Selected)
- Pros: Scoped to relevant components, easier testing, clear ownership
- Cons: Risk of duplicate handlers, coordination between components needed

**Option C: Browser Accesskey Attributes**
- Pros: Native browser support, automatic visual indicators
- Cons: Limited key combinations, browser inconsistencies, poor UX

**Rationale:** Option B provides the best balance of maintainability and functionality. Each component can handle its relevant shortcuts while a coordination service manages global state and prevents conflicts.

## External Dependencies

- **No new dependencies required** - Use native browser APIs and existing Svelte event handling

## Keyboard Shortcut Map

### Global Shortcuts (Available Anywhere)
- `?` - Show help overlay with all shortcuts
- `/` - Focus search bar
- `r` - Refresh all feeds
- `g + a` - Go to All Articles
- `g + s` - Go to Starred Articles
- `g + u` - Go to Unread Articles

### Feed Navigation
- `↑/↓` - Navigate between feeds in sidebar
- `Enter` - Select highlighted feed
- `Space` - Toggle feed expansion
- `Escape` - Return focus to main content area

### Article Navigation
- `j/k` - Next/Previous article in list
- `o` or `Enter` - Open selected article
- `m` - Mark article as read/unread
- `s` - Star/Unstar article
- `u` - Mark all visible articles as read
- `n` - Next unread article
- `p` - Previous unread article

### Article Modal
- `Escape` - Close article modal
- `←/→` - Previous/Next article
- `m` - Toggle read status
- `s` - Toggle star status
- `Space` - Scroll down in article
- `Shift + Space` - Scroll up in article

### Filter and Search
- `f` - Toggle filter dropdown
- `Escape` - Close filter dropdown or clear search
- `Enter` - Apply current filter or search

## Implementation Architecture

### KeyboardService
Central service for managing keyboard shortcuts:
- Register/unregister shortcut handlers
- Handle global shortcuts and help system
- Prevent conflicts between components
- Track current focus context

### Component Integration
Each component registers its relevant shortcuts:
- Sidebar component handles feed navigation
- ArticleList component handles article navigation
- ArticleModal component handles modal shortcuts
- Header component handles search shortcuts

### Focus Management
- Track active component and interface state
- Provide focus indicators with CSS classes
- Handle focus trapping in modals
- Restore focus when closing overlays

### Help System
- Overlay showing all available shortcuts
- Context-sensitive help based on current view
- Keyboard shortcut hints in tooltips
- Progressive disclosure of advanced shortcuts