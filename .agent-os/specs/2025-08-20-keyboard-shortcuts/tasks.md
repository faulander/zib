# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-20-keyboard-shortcuts/spec.md

> Created: 2025-08-20
> Status: Ready for Implementation

## Tasks

- [ ] 1. Create Keyboard Service Infrastructure
  - [ ] 1.1 Write tests for KeyboardService class with event filtering and shortcut registration
  - [ ] 1.2 Implement KeyboardService with global event listener and shortcut mapping
  - [ ] 1.3 Add input field detection to prevent conflicts with form typing
  - [ ] 1.4 Implement context-aware shortcut activation/deactivation system
  - [ ] 1.5 Verify all KeyboardService tests pass

- [ ] 2. Implement Article Focus Management
  - [ ] 2.1 Write tests for focus tracking, visual indicators, and navigation bounds
  - [ ] 2.2 Create FocusManager to track currently selected article
  - [ ] 2.3 Add visual focus indicators with proper contrast and accessibility
  - [ ] 2.4 Implement focus persistence across article list updates and filtering
  - [ ] 2.5 Verify all focus management tests pass

- [ ] 3. Add Navigation Shortcuts (j/k/enter/space)
  - [ ] 3.1 Write tests for article navigation, modal opening, and list boundaries
  - [ ] 3.2 Implement j/k keys for next/previous article navigation
  - [ ] 3.3 Implement enter/space keys to open focused article in modal
  - [ ] 3.4 Add navigation wrapping at beginning/end of article lists
  - [ ] 3.5 Verify all navigation shortcut tests pass

- [ ] 4. Implement Action Shortcuts (m/s/r)
  - [ ] 4.1 Write tests for mark read/unread, star/unstar, and refresh actions
  - [ ] 4.2 Connect m key to toggle read status of focused article
  - [ ] 4.3 Connect s key to toggle star status of focused article
  - [ ] 4.4 Connect r key to refresh current category/feed
  - [ ] 4.5 Verify all action shortcut tests pass and UI updates correctly

- [ ] 5. Add View Control Shortcuts (v/f/esc)
  - [ ] 5.1 Write tests for view mode cycling, filter cycling, and modal closing
  - [ ] 5.2 Implement v key to cycle through view modes (list/card)
  - [ ] 5.3 Implement f key to cycle through filters (all/unread/starred)
  - [ ] 5.4 Implement esc key to close active modals consistently
  - [ ] 5.5 Verify all view control tests pass

- [ ] 6. Create Keyboard Shortcuts Help Overlay
  - [ ] 6.1 Write tests for help modal opening, search functionality, and context awareness
  - [ ] 6.2 Create HelpOverlay component with searchable shortcut list
  - [ ] 6.3 Implement ? key to open help modal with context-appropriate shortcuts
  - [ ] 6.4 Add search functionality to filter shortcuts by description or key
  - [ ] 6.5 Verify all help overlay tests pass

- [ ] 7. Add Category Navigation Shortcuts (arrows/numbers)
  - [ ] 7.1 Write tests for sidebar navigation and quick category selection
  - [ ] 7.2 Implement arrow keys for navigating sidebar categories
  - [ ] 7.3 Implement number keys (1-9) for quick category selection
  - [ ] 7.4 Ensure category selection updates articles and maintains focus
  - [ ] 7.5 Verify all category navigation tests pass

- [ ] 8. Integration and Accessibility Testing
  - [ ] 8.1 Write comprehensive integration tests covering all shortcut combinations
  - [ ] 8.2 Test accessibility compliance with screen readers and WCAG guidelines
  - [ ] 8.3 Test responsive behavior across desktop and tablet screen sizes
  - [ ] 8.4 Verify no conflicts with existing functionality or browser shortcuts
  - [ ] 8.5 Verify all integration and accessibility tests pass