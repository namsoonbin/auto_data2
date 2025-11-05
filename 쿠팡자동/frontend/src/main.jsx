// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';

import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
// App은 한 번만 임포트 (확실히 하려면 확장자까지 명시)
import App from './App.jsx';
import { AuthProvider } from './contexts/AuthContext.jsx';

import './index.css';

const theme = createTheme({
  typography: {
    fontFamily:
      "'Spoqa Han Sans Neo', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Apple SD Gothic Neo', 'Malgun Gothic', '맑은 고딕', sans-serif",
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
);
