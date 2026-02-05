import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'

export function ThemeToggle() {
  const { isDark, toggle } = useTheme()

  return (
    <div
      className="inline-flex items-center gap-2"
      data-state={isDark ? 'unchecked' : 'checked'}
    >
      {/* Moon — dark mode indicator */}
      <button
        type="button"
        aria-label="Dark mode"
        onClick={() => !isDark && toggle()}
        className="cursor-pointer transition-colors"
      >
        <Moon
          className={`w-4 h-4 ${
            isDark ? 'text-indigo-400' : 'text-gray-300 dark:text-white/20'
          }`}
        />
      </button>

      {/* Switch */}
      <button
        type="button"
        role="switch"
        aria-checked={!isDark}
        aria-label="Toggle between dark and light mode"
        onClick={toggle}
        className={`relative h-[22px] w-[40px] rounded-full transition-colors duration-300 ${
          isDark ? 'bg-white/[0.1]' : 'bg-indigo-500'
        }`}
      >
        <span
          className={`absolute top-[3px] h-4 w-4 rounded-full bg-white shadow-sm transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            isDark ? 'left-[3px]' : 'left-[21px]'
          }`}
        />
      </button>

      {/* Sun — light mode indicator */}
      <button
        type="button"
        aria-label="Light mode"
        onClick={() => isDark && toggle()}
        className="cursor-pointer transition-colors"
      >
        <Sun
          className={`w-4 h-4 ${
            !isDark ? 'text-amber-500' : 'text-white/20'
          }`}
        />
      </button>
    </div>
  )
}
