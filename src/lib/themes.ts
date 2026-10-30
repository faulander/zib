// Color themes. Each theme has a light and a dark variant (see layout.css);
// the light/dark toggle picks the variant, this setting picks the palette.
export const THEMES = [
  { id: 'default', label: 'Slate' },
  { id: 'github', label: 'GitHub' },
  { id: 'nord', label: 'Nord' },
  { id: 'solarized', label: 'Solarized' },
  { id: 'gruvbox', label: 'Gruvbox' },
  { id: 'catppuccin', label: 'Catppuccin' },
  { id: 'dracula', label: 'Dracula' },
  { id: 'tokyo-night', label: 'Tokyo Night' },
  { id: 'rose-pine', label: 'Rosé Pine' },
  { id: 'one', label: 'One Dark' },
  { id: 'sepia', label: 'Sepia' }
] as const;

export type ThemeId = (typeof THEMES)[number]['id'];

export function isThemeId(value: unknown): value is ThemeId {
  return THEMES.some((t) => t.id === value);
}

export function applyTheme(theme: ThemeId) {
  document.documentElement.dataset.theme = theme;
}
