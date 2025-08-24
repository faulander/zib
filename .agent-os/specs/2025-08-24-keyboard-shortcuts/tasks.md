# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-24-keyboard-shortcuts/spec.md

> Created: 2025-08-24
> Status: Ready for Implementation

## Tasks

- [ ] 1. KeyboardService and Global Shortcut System
  - [ ] 1.1 Write tests for KeyboardService class and global shortcut handling
  - [ ] 1.2 Create KeyboardService with shortcut registration and conflict prevention
  - [ ] 1.3 Implement global shortcuts (help, search focus, refresh, navigation)
  - [ ] 1.4 Add keyboard shortcut help overlay component
  - [ ] 1.5 Create focus management system with visual indicators
  - [ ] 1.6 Verify global shortcuts work across all interface states

- [ ] 2. Feed Navigation Shortcuts
  - [ ] 2.1 Write tests for sidebar keyboard navigation
  - [ ] 2.2 Implement arrow key navigation between feeds and categories
  - [ ] 2.3 Add Enter key selection and Space key expansion
  - [ ] 2.4 Create visual focus indicators for selected feeds
  - [ ] 2.5 Handle Escape key to return focus to main content
  - [ ] 2.6 Verify feed navigation works with collapsed/expanded categories

- [ ] 3. Article List Navigation Shortcuts
  - [ ] 3.1 Write tests for article list keyboard navigation
  - [ ] 3.2 Implement j/k navigation through article list
  - [ ] 3.3 Add article selection and opening with Enter/o keys
  - [ ] 3.4 Implement mark as read (m) and star (s) shortcuts for selected articles
  - [ ] 3.5 Add bulk actions (mark all read) and next/previous unread navigation
  - [ ] 3.6 Verify navigation works with infinite scroll and filtered views

- [ ] 4. Article Modal Keyboard Controls
  - [ ] 4.1 Write tests for article modal keyboard navigation
  - [ ] 4.2 Implement modal navigation (Escape to close, arrow keys for next/prev)
  - [ ] 4.3 Add article action shortcuts within modal (mark read, star)
  - [ ] 4.4 Implement Space/Shift+Space scrolling within article content
  - [ ] 4.5 Create focus trapping to keep keyboard navigation within modal
  - [ ] 4.6 Verify modal shortcuts work and restore focus when closed

- [ ] 5. Search and Filter Keyboard Integration
  - [ ] 5.1 Write tests for search and filter keyboard shortcuts
  - [ ] 5.2 Implement search focus shortcut (/) with proper input selection
  - [ ] 5.3 Add filter dropdown toggle (f) and navigation shortcuts
  - [ ] 5.4 Handle Escape key for clearing search and closing filter dropdown
  - [ ] 5.5 Implement Enter key for applying filters and searches
  - [ ] 5.6 Verify keyboard shortcuts work with existing search and filter functionality