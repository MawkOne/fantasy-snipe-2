import {
  argbFromHex,
  themeFromSourceColor,
  applyTheme,
  Theme,
} from '@material/material-color-utilities'

export type ThemeMode = 'light' | 'dark' | 'system'

// Default accent color (can be changed by user)
const DEFAULT_ACCENT_COLOR = '#1976d2' // Material Blue

export function generateMaterialTheme(hexColor: string = DEFAULT_ACCENT_COLOR) {
  // Convert hex to ARGB
  const argb = argbFromHex(hexColor)
  
  // Generate Material Design 3 theme
  const theme = themeFromSourceColor(argb)
  
  return theme
}

export function applyMaterialTheme(theme: Theme, isDark: boolean) {
  // Apply theme to document
  applyTheme(theme, { target: document.body, dark: isDark })
}

export function setThemeMode(mode: ThemeMode) {
  if (typeof window === 'undefined') return

  const root = document.documentElement
  
  if (mode === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
    return prefersDark ? 'dark' : 'light'
  }
  
  root.classList.toggle('dark', mode === 'dark')
  return mode
}

export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Generate CSS variables for the theme
export function generateThemeVariables(accentColor: string = DEFAULT_ACCENT_COLOR) {
  const theme = generateMaterialTheme(accentColor)
  
  return {
    light: {
      '--md-sys-color-primary': toHex(theme.schemes.light.primary),
      '--md-sys-color-on-primary': toHex(theme.schemes.light.onPrimary),
      '--md-sys-color-primary-container': toHex(theme.schemes.light.primaryContainer),
      '--md-sys-color-on-primary-container': toHex(theme.schemes.light.onPrimaryContainer),
      '--md-sys-color-secondary': toHex(theme.schemes.light.secondary),
      '--md-sys-color-on-secondary': toHex(theme.schemes.light.onSecondary),
      '--md-sys-color-secondary-container': toHex(theme.schemes.light.secondaryContainer),
      '--md-sys-color-on-secondary-container': toHex(theme.schemes.light.onSecondaryContainer),
      '--md-sys-color-tertiary': toHex(theme.schemes.light.tertiary),
      '--md-sys-color-on-tertiary': toHex(theme.schemes.light.onTertiary),
      '--md-sys-color-error': toHex(theme.schemes.light.error),
      '--md-sys-color-on-error': toHex(theme.schemes.light.onError),
      '--md-sys-color-background': toHex(theme.schemes.light.background),
      '--md-sys-color-on-background': toHex(theme.schemes.light.onBackground),
      '--md-sys-color-surface': toHex(theme.schemes.light.surface),
      '--md-sys-color-on-surface': toHex(theme.schemes.light.onSurface),
      '--md-sys-color-surface-variant': toHex(theme.schemes.light.surfaceVariant),
      '--md-sys-color-on-surface-variant': toHex(theme.schemes.light.onSurfaceVariant),
      '--md-sys-color-outline': toHex(theme.schemes.light.outline),
    },
    dark: {
      '--md-sys-color-primary': toHex(theme.schemes.dark.primary),
      '--md-sys-color-on-primary': toHex(theme.schemes.dark.onPrimary),
      '--md-sys-color-primary-container': toHex(theme.schemes.dark.primaryContainer),
      '--md-sys-color-on-primary-container': toHex(theme.schemes.dark.onPrimaryContainer),
      '--md-sys-color-secondary': toHex(theme.schemes.dark.secondary),
      '--md-sys-color-on-secondary': toHex(theme.schemes.dark.onSecondary),
      '--md-sys-color-secondary-container': toHex(theme.schemes.dark.secondaryContainer),
      '--md-sys-color-on-secondary-container': toHex(theme.schemes.dark.onSecondaryContainer),
      '--md-sys-color-tertiary': toHex(theme.schemes.dark.tertiary),
      '--md-sys-color-on-tertiary': toHex(theme.schemes.dark.onTertiary),
      '--md-sys-color-error': toHex(theme.schemes.dark.error),
      '--md-sys-color-on-error': toHex(theme.schemes.dark.onError),
      '--md-sys-color-background': toHex(theme.schemes.dark.background),
      '--md-sys-color-on-background': toHex(theme.schemes.dark.onBackground),
      '--md-sys-color-surface': toHex(theme.schemes.dark.surface),
      '--md-sys-color-on-surface': toHex(theme.schemes.dark.onSurface),
      '--md-sys-color-surface-variant': toHex(theme.schemes.dark.surfaceVariant),
      '--md-sys-color-on-surface-variant': toHex(theme.schemes.dark.onSurfaceVariant),
      '--md-sys-color-outline': toHex(theme.schemes.dark.outline),
    },
  }
}

function toHex(argb: number): string {
  const hex = argb.toString(16).padStart(8, '0')
  return `#${hex.substring(2)}` // Remove alpha channel
}

