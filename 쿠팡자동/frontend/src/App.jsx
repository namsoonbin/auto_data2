import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  CssBaseline,
  Button
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  AccountBalance as MarginIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Group as GroupIcon
} from '@mui/icons-material'
import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import HistoryPage from './pages/HistoryPage'
import DataManagementPage from './pages/DataManagementPage'
import ExportPage from './pages/ExportPage'
import MarginManagementPage from './pages/MarginManagementPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import TenantSettingsPage from './pages/TenantSettingsPage'
import TeamManagementPage from './pages/TeamManagementPage'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './contexts/AuthContext'

const drawerWidth = 240

const menuItems = [
  { text: '파일 업로드', icon: <UploadIcon />, path: '/' },
  { text: '대시보드', icon: <DashboardIcon />, path: '/dashboard' },
  { text: '마진 관리', icon: <MarginIcon />, path: '/margins' },
  { text: '업로드 히스토리', icon: <HistoryIcon />, path: '/history' },
  { text: '데이터 관리', icon: <DeleteIcon />, path: '/management' },
  { text: '엑셀 다운로드', icon: <DownloadIcon />, path: '/export' },
  { text: '팀 관리', icon: <GroupIcon />, path: '/team' },
  { text: '프로필 관리', icon: <PersonIcon />, path: '/profile' },
  { text: '테넌트 설정', icon: <SettingsIcon />, path: '/settings' }
]

function AppContent() {
  const location = useLocation()
  const { user, tenant, logout, isAuthenticated } = useAuth()

  const handleLogout = () => {
    logout()
  }

  // 로그인 페이지에서는 사이드바를 표시하지 않음
  const showSidebar = isAuthenticated && location.pathname !== '/login'

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />

      {/* AppBar */}
      {showSidebar && (
        <AppBar
          position="fixed"
          sx={{
            zIndex: (theme) => theme.zIndex.drawer + 1
          }}
        >
          <Toolbar>
            <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
              쿠팡 판매 데이터 자동화
            </Typography>
            {tenant && (
              <Typography variant="subtitle1" sx={{ mr: 2 }}>
                {tenant.name}
              </Typography>
            )}
            {user && (
              <Typography variant="body2" sx={{ mr: 2 }}>
                {user.full_name} ({user.role})
              </Typography>
            )}
            <Button color="inherit" startIcon={<LogoutIcon />} onClick={handleLogout}>
              로그아웃
            </Button>
          </Toolbar>
        </AppBar>
      )}

      {/* Drawer */}
      {showSidebar && (
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box'
            }
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              {menuItems.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton
                    component={Link}
                    to={item.path}
                    selected={location.pathname === item.path}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.text} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: '#f5f5f5',
          p: showSidebar ? 3 : 0,
          minHeight: '100vh'
        }}
      >
        {showSidebar && <Toolbar />}
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/margins" element={<ProtectedRoute><MarginManagementPage /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
          <Route path="/management" element={<ProtectedRoute><DataManagementPage /></ProtectedRoute>} />
          <Route path="/export" element={<ProtectedRoute><ExportPage /></ProtectedRoute>} />
          <Route path="/team" element={<ProtectedRoute><TeamManagementPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><TenantSettingsPage /></ProtectedRoute>} />
        </Routes>
      </Box>
    </Box>
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
