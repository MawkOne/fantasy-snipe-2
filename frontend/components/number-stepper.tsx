"use client"

import { Minus, Plus } from "lucide-react"

export function NumberStepper({
  value,
  setValue,
  min = 0,
  max = 10,
}: {
  value: number
  setValue: (n: number) => void
  min?: number
  max?: number
}) {
  return (
    <div className="inline-flex items-center rounded-md border bg-white">
      <button
        type="button"
        aria-label="decrement"
        className="p-2 hover:bg-gray-50"
        onClick={() => setValue(Math.max(min, value - 1))}
      >
        <Minus className="w-4 h-4" />
      </button>
      <div className="w-10 text-center text-sm">{value}</div>
      <button
        type="button"
        aria-label="increment"
        className="p-2 hover:bg-gray-50"
        onClick={() => setValue(Math.min(max, value + 1))}
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  )
}
