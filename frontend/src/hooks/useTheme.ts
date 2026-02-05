import { create } from 'zustand'

interface ThemeStore {
  isDark: boolean
}

const useThemeStore = create<ThemeStore>(() => ({
  isDark: true,
}))

// Initialize from localStorage + sync DOM
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('theme')
  const isDark = stored ? stored === 'dark' : true
  useThemeStore.setState({ isDark })
  document.documentElement.classList.toggle('dark', isDark)
}

export function useTheme() {
  const isDark = useThemeStore((s) => s.isDark)

  const toggle = () => {
    const next = !useThemeStore.getState().isDark
    useThemeStore.setState({ isDark: next })
    localStorage.setItem('theme', next ? 'dark' : 'light')
    document.documentElement.classList.toggle('dark', next)
  }

  return { isDark, toggle }
}
