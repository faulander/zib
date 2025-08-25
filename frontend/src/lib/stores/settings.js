/**
 * Settings store for the Zib RSS Reader
 */

import { writable } from 'svelte/store';

// Default settings
const defaultSettings = {
  autoRefreshFeeds: false,
  showUnreadCountInTitle: false,
  markReadScrollBatchSize: 5, // Number of articles to batch before marking as read
  markReadScrollDelay: 1000, // Delay in ms after article leaves viewport before adding to batch
  mark_read_scroll_batch_size: 5, // Backend field name
  mark_read_scroll_delay: 1000, // Backend field name
  font_scale: 1.0 // Font scale for accessibility
};

// Load settings from localStorage
function loadSettings() {
  if (typeof window === 'undefined') return defaultSettings;
  
  try {
    const saved = localStorage.getItem('zib-settings');
    if (saved) {
      return { ...defaultSettings, ...JSON.parse(saved) };
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
  
  return defaultSettings;
}

// Save settings to localStorage
function saveSettings(settings) {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem('zib-settings', JSON.stringify(settings));
  } catch (err) {
    console.error('Failed to save settings:', err);
  }
}

// Create the settings store
function createSettingsStore() {
  const { subscribe, set, update } = writable(loadSettings());
  
  return {
    subscribe,
    set: (value) => {
      saveSettings(value);
      set(value);
    },
    update: (updater) => {
      update((current) => {
        const newSettings = updater(current);
        saveSettings(newSettings);
        return newSettings;
      });
    },
    setSetting: (key, value) => {
      update((current) => {
        const newSettings = { ...current, [key]: value };
        saveSettings(newSettings);
        return newSettings;
      });
    },
    reset: () => {
      saveSettings(defaultSettings);
      set(defaultSettings);
    }
  };
}

export const settings = createSettingsStore();