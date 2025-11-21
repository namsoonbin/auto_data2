import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // localStorage에서 테마 초기값 로드, 없으면 시스템 설정을 따름
  const [theme, setThemeState] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) return savedTheme;

    // 시스템 설정 확인 (prefers-color-scheme)
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  });

  // 테마 변경 시 localStorage에 저장
  useEffect(() => {
    localStorage.setItem('theme', theme);

    // HTML root에 data-theme 속성 설정 (CSS 변수 사용 시 유용)
    document.documentElement.setAttribute('data-theme', theme);

    // body 배경색도 즉시 변경
    if (theme === 'dark') {
      document.body.style.backgroundColor = '#0f1115';
    } else {
      document.body.style.backgroundColor = '#f8fafc';
    }
  }, [theme]);

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
