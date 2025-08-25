/**
 * Font Scale Management
 * Handles dynamic font scaling for accessibility
 */

// Font scale levels
export const FONT_SCALES = {
  VERY_SMALL: { value: 0.85, label: 'Very Small', icon: 'ZoomOut' },
  SMALL: { value: 0.92, label: 'Small', icon: 'Minus' },
  DEFAULT: { value: 1.0, label: 'Default', icon: 'Type' },
  LARGE: { value: 1.15, label: 'Large', icon: 'Plus' },
  VERY_LARGE: { value: 1.3, label: 'Very Large', icon: 'ZoomIn' }
};

// Default scale
export const DEFAULT_FONT_SCALE = FONT_SCALES.DEFAULT.value;

/**
 * Apply font scale to the document
 * @param {number} scale - The font scale multiplier (0.85 to 1.3)
 */
export function applyFontScale(scale) {
  // Clamp scale to valid range
  const clampedScale = Math.max(0.85, Math.min(1.3, scale));
  
  // Apply to root element
  document.documentElement.style.setProperty('--font-scale', clampedScale.toString());
  
  // Store in localStorage for immediate persistence
  localStorage.setItem('fontScale', clampedScale.toString());
  
  return clampedScale;
}

/**
 * Get the current font scale from localStorage or default
 * @returns {number} The current font scale
 */
export function getCurrentFontScale() {
  const stored = localStorage.getItem('fontScale');
  return stored ? parseFloat(stored) : DEFAULT_FONT_SCALE;
}

/**
 * Initialize font scale on page load
 * @param {number} backendScale - Optional font scale from backend settings
 */
export function initializeFontScale(backendScale = null) {
  // Use backend scale if provided, otherwise get from localStorage
  const scale = backendScale !== null ? backendScale : getCurrentFontScale();
  applyFontScale(scale);
  return scale;
}

/**
 * Get the closest font scale level for a given value
 * @param {number} value - The font scale value
 * @returns {string} The font scale level key
 */
export function getFontScaleLevel(value) {
  let closestKey = 'DEFAULT';
  let closestDiff = Math.abs(value - FONT_SCALES.DEFAULT.value);
  
  for (const [key, scale] of Object.entries(FONT_SCALES)) {
    const diff = Math.abs(value - scale.value);
    if (diff < closestDiff) {
      closestDiff = diff;
      closestKey = key;
    }
  }
  
  return closestKey;
}

/**
 * Increase font scale by one level
 * @returns {number} The new font scale
 */
export function increaseFontScale() {
  const current = getCurrentFontScale();
  const levels = Object.values(FONT_SCALES).map(s => s.value).sort((a, b) => a - b);
  const currentIndex = levels.findIndex(v => v >= current);
  
  if (currentIndex < levels.length - 1) {
    return applyFontScale(levels[currentIndex + 1]);
  }
  
  return current;
}

/**
 * Decrease font scale by one level
 * @returns {number} The new font scale
 */
export function decreaseFontScale() {
  const current = getCurrentFontScale();
  const levels = Object.values(FONT_SCALES).map(s => s.value).sort((a, b) => a - b);
  const currentIndex = levels.findIndex(v => v >= current);
  
  if (currentIndex > 0) {
    return applyFontScale(levels[currentIndex - 1]);
  }
  
  return current;
}

/**
 * Reset font scale to default
 * @returns {number} The default font scale
 */
export function resetFontScale() {
  return applyFontScale(DEFAULT_FONT_SCALE);
}