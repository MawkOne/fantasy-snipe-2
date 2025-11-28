"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { generateThemeVariables, setThemeMode, getSystemTheme, type ThemeMode } from '@/lib/theme'

interface ThemeContextType {
  mode: ThemeMode
  actualMode: 'light' | 'dark'
  accentColor: string
  setMode: (mode: ThemeMode) => void
  setAccentColor: (color: string) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function MaterialThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>('light')
  const [actualMode, setActualMode] = useState<'light' | 'dark'>('light')
  const [accentColor, setAccentColorState] = useState('#1976d2')
  const [mounted, setMounted] = useState(false)

  // Load saved preferences on mount
  useEffect(() => {
    setMounted(true)
    const savedMode = (localStorage.getItem('theme-mode') as ThemeMode) || 'light'
    const savedColor = localStorage.getItem('accent-color') || '#1976d2'
    
    setModeState(savedMode)
    setAccentColorState(savedColor)
    
    const actual = savedMode === 'system' ? getSystemTheme() : savedMode
    setActualMode(actual)
    setThemeMode(savedMode)
  }, [])

  // Apply theme when mode or color changes
  useEffect(() => {
    if (!mounted) return

    const themeVars = generateThemeVariables(accentColor)
    const root = document.documentElement
    
    // Remove old variables
    Object.keys(themeVars.light).forEach(key => {
      root.style.removeProperty(key)
    })
    
    // Apply new variables
    const varsToApply = actualMode === 'dark' ? themeVars.dark : themeVars.light
    Object.entries(varsToApply).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })
  }, [accentColor, actualMode, mounted])

  // Listen for system theme changes
  useEffect(() => {
    if (!mounted || mode !== 'system') return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      const newMode = e.matches ? 'dark' : 'light'
      setActualMode(newMode)
      setThemeMode('system')
    }

    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [mode, mounted])

  const handleSetMode = (newMode: ThemeMode) => {
    console.log("handleSetMode called with:", newMode)
    setModeState(newMode)
    localStorage.setItem('theme-mode', newMode)
    
    const actual = newMode === 'system' ? getSystemTheme() : newMode
    console.log("Actual mode will be:", actual)
    setActualMode(actual)
    const result = setThemeMode(newMode)
    console.log("setThemeMode returned:", result)
    console.log("HTML classes:", document.documentElement.classList.toString())
  }

  const handleSetAccentColor = (color: string) => {
    setAccentColorState(color)
    localStorage.setItem('accent-color', color)
  }

  return (
    <ThemeContext.Provider
      value={{
        mode,
        actualMode,
        accentColor,
        setMode: handleSetMode,
        setAccentColor: handleSetAccentColor,
      }}
    >
      {mounted ? children : <div style={{ visibility: 'hidden' }}>{children}</div>}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within MaterialThemeProvider')
  }
  return context
}

