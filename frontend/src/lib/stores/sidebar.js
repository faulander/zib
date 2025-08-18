import { writable } from 'svelte/store';

// Mobile detection and sidebar state
export const isMobile = writable(false);
export const isSidebarOpen = writable(false);

// Toggle sidebar
export function toggleSidebar() {
  isSidebarOpen.update(state => !state);
}

// Close sidebar
export function closeSidebar() {
  isSidebarOpen.set(false);
}

// Check if mobile
export function checkMobile() {
  const mobile = window.innerWidth < 768; // md breakpoint
  isMobile.set(mobile);
  if (!mobile) {
    closeSidebar(); // Reset sidebar state on desktop
  }
  return mobile;
}