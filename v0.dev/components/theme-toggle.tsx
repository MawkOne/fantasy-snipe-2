"use client"

import { Moon, Sun, Monitor } from "lucide-react"
import { useTheme } from "./material-theme-provider"

export function ThemeToggle() {
  const { mode, setMode } = useTheme()

  const toggleTheme = () => {
    console.log("Current mode:", mode)
    if (mode === "light") {
      console.log("Switching to dark")
      setMode("dark")
    } else if (mode === "dark") {
      console.log("Switching to system")
      setMode("system")
    } else {
      console.log("Switching to light")
      setMode("light")
    }
  }

  return (
    <button
      onClick={toggleTheme}
      className="w-10 h-10 rounded-full hover:bg-gray-100 dark:hover:bg-[#2f3136] flex items-center justify-center transition-all"
      title={`Current theme: ${mode}`}
    >
      {mode === "light" && <Sun className="w-5 h-5 text-gray-700 dark:text-gray-300" />}
      {mode === "dark" && <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />}
      {mode === "system" && <Monitor className="w-5 h-5 text-gray-700 dark:text-gray-300" />}
    </button>
  )
}

export function ThemeToggleExpanded() {
  const { mode, setMode, accentColor, setAccentColor } = useTheme()

  const accentColors = [
    { name: "Blue", color: "#1976d2" },
    { name: "Purple", color: "#9c27b0" },
    { name: "Green", color: "#388e3c" },
    { name: "Orange", color: "#f57c00" },
    { name: "Red", color: "#d32f2f" },
    { name: "Pink", color: "#c2185b" },
  ]

  return (
    <div className="p-4 space-y-4">
      <div>
        <h3 className="text-sm font-semibold mb-2">Theme Mode</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setMode("light")}
            className={`flex-1 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
              mode === "light"
                ? "bg-blue-500 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            }`}
          >
            <Sun className="w-4 h-4" />
            Light
          </button>
          <button
            onClick={() => setMode("dark")}
            className={`flex-1 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
              mode === "dark"
                ? "bg-blue-500 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            }`}
          >
            <Moon className="w-4 h-4" />
            Dark
          </button>
          <button
            onClick={() => setMode("system")}
            className={`flex-1 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-all ${
              mode === "system"
                ? "bg-blue-500 text-white"
                : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
            }`}
          >
            <Monitor className="w-4 h-4" />
            Auto
          </button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2">Accent Color</h3>
        <div className="grid grid-cols-6 gap-2">
          {accentColors.map((c) => (
            <button
              key={c.color}
              onClick={() => setAccentColor(c.color)}
              className={`w-10 h-10 rounded-full transition-transform hover:scale-110 ${
                accentColor === c.color ? "ring-2 ring-offset-2 ring-blue-500" : ""
              }`}
              style={{ backgroundColor: c.color }}
              title={c.name}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

