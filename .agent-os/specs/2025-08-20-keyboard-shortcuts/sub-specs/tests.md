# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-20-keyboard-shortcuts/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Test Coverage

### Unit Tests

**KeyboardService**
- Test shortcut registration and removal
- Test event filtering (ignore inputs, textareas, contenteditable)
- Test modifier key combinations (ctrl+key, alt+key)
- Test shortcut conflict detection and resolution
- Test context-aware shortcut activation/deactivation

**FocusManager**
- Test article focus tracking and updates
- Test focus navigation bounds (first/last article)
- Test focus persistence across article list updates
- Test visual focus indicator application and removal

### Integration Tests

**Navigation Shortcuts**
- Test j/k navigation moves focus correctly through article list
- Test enter/space opens focused article in modal
- Test navigation wraps around at list boundaries
- Test navigation works with filtered article lists
- Test navigation updates URL/state appropriately

**Action Shortcuts**
- Test m key toggles read status of focused article
- Test s key toggles star status of focused article
- Test r key refreshes current category/feed
- Test actions update backend and refresh UI appropriately

**View Control Shortcuts**
- Test v key cycles through view modes (list/card)
- Test f key cycles through filters (all/unread/starred)
- Test esc key closes active modals (article reader, help overlay)
- Test ? key opens help overlay with current context shortcuts

**Category Navigation**
- Test arrow keys navigate sidebar categories
- Test number keys (1-9) quickly select categories
- Test category selection updates article list and focus

### Feature Tests

**Help Overlay Functionality**
- Test help modal opens with ? key and displays all shortcuts
- Test help modal search filters shortcuts correctly
- Test help modal shows context-appropriate shortcuts
- Test help modal closes with esc key or click outside
- Test help modal keyboard navigation (tab through shortcuts)

**Accessibility Compliance**
- Test focus indicators meet WCAG contrast requirements
- Test screen readers can navigate keyboard-focused articles
- Test ARIA attributes update correctly with keyboard navigation
- Test keyboard shortcuts don't interfere with screen reader shortcuts

**Responsive Behavior**
- Test shortcuts work correctly on desktop (1200px+)
- Test shortcuts work correctly on tablet (768px-1199px)
- Test shortcuts are disabled/ignored on mobile (<768px)

### Mocking Requirements

- **KeyboardEvent simulation** - Mock keyboard events for all shortcut combinations
- **Article API responses** - Mock article read/unread and star/unstar API calls
- **Category switching** - Mock category selection and article loading responses
- **Local storage** - Mock user preference storage for view modes and settings