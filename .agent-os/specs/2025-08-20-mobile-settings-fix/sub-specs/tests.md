# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-20-mobile-settings-fix/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Test Coverage

### Unit Tests

**Responsive Sidebar Behavior**
- Test sidebar hidden by default on mobile (<768px)
- Test sidebar visible by default on desktop (≥768px)
- Test hamburger menu appears only on mobile
- Test sidebar toggle function changes state correctly
- Test auto-close behavior after section selection on mobile

**Layout Adaptations**
- Test grid layouts collapse to single column on mobile
- Test form controls expand to full width on mobile
- Test button sizing increases for touch targets on mobile
- Test modal dialogs adapt to mobile viewport

### Integration Tests

**Mobile Navigation Flow**
- Test hamburger menu opens sidebar overlay on mobile
- Test clicking overlay backdrop closes sidebar
- Test selecting a settings section closes sidebar on mobile
- Test sidebar remains open on desktop when selecting sections
- Test swipe gestures open/close sidebar correctly

**Form Interactions on Mobile**
- Test add feed form is usable with mobile keyboard
- Test filter creation form works with touch input
- Test settings toggles are easily tappable
- Test delete confirmations display properly on mobile

**Cross-Device Consistency**
- Test switching between mobile and desktop preserves selected section
- Test form data persists when toggling sidebar on mobile
- Test settings changes save correctly regardless of device

### Feature Tests

**Complete Mobile User Journey**
- Test user can navigate to settings from main page on mobile
- Test user can access all settings sections via hamburger menu
- Test user can add a new feed entirely on mobile
- Test user can create and edit filters on mobile
- Test user can import OPML file using mobile file picker
- Test user can modify general settings and save on mobile

**Responsive Breakpoint Behavior**
- Test layout at 320px (minimum mobile)
- Test layout at 375px (iPhone SE)
- Test layout at 768px (tablet/desktop boundary)
- Test layout at 1024px (desktop)
- Test dynamic resize from desktop to mobile
- Test dynamic resize from mobile to desktop

**Touch Interaction Quality**
- Test all buttons meet 44x44px minimum touch target
- Test no hover-dependent interactions on mobile
- Test swipe gestures don't interfere with scrolling
- Test form inputs are properly spaced for touch

### Accessibility Tests

**Mobile Screen Reader Support**
- Test hamburger menu has proper ARIA labels
- Test sidebar state is announced to screen readers
- Test focus management when sidebar opens/closes
- Test all settings remain keyboard accessible on mobile

**Visual Accessibility**
- Test contrast ratios remain WCAG compliant on mobile
- Test text remains readable without horizontal scrolling
- Test touch targets are visually distinct
- Test error messages are visible on mobile screens

### Mocking Requirements

- **Window.matchMedia** - Mock media queries for responsive testing
- **Touch events** - Mock touch start/move/end for swipe gestures
- **ResizeObserver** - Mock viewport size changes
- **Local storage** - Mock settings persistence across device changes