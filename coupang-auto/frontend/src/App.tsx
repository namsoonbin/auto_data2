import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Button } from './components/ui/button';
import {
  Upload,
  LayoutDashboard,
  History,
  Trash2,
  Download,
  Calculator,
  LogOut,
  Settings,
  Users,
} from 'lucide-react';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import DataManagementPage from './pages/DataManagementPage';
import ExportPage from './pages/ExportPage';
import MarginManagementPage from './pages/MarginManagementPage';
import LoginPage from './pages/LoginPage';
import ProfileSettingsPage from './pages/ProfileSettingsPage';
import TeamManagementPage from './pages/TeamManagementPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';

const drawerWidth = 240;

interface MenuItem {
  text: string;
  icon: React.ReactNode;
  path: string;
}

const menuItems: MenuItem[] = [
  { text: '파일 업로드', icon: <Upload className="h-5 w-5" />, path: '/' },
  { text: '대시보드', icon: <LayoutDashboard className="h-5 w-5" />, path: '/dashboard' },
  { text: '마진 관리', icon: <Calculator className="h-5 w-5" />, path: '/margins' },
  { text: '업로드 히스토리', icon: <History className="h-5 w-5" />, path: '/history' },
  { text: '데이터 관리', icon: <Trash2 className="h-5 w-5" />, path: '/management' },
  { text: '엑셀 다운로드', icon: <Download className="h-5 w-5" />, path: '/export' },
  { text: '팀 관리', icon: <Users className="h-5 w-5" />, path: '/team' },
  { text: '프로필 및 설정', icon: <Settings className="h-5 w-5" />, path: '/settings' },
];

function AppContent() {
  const location = useLocation();
  const { user, tenant, logout, isAuthenticated } = useAuth();

  const handleLogout = () => {
    logout();
  };

  // 로그인 페이지에서는 사이드바를 표시하지 않음
  const showSidebar = isAuthenticated && location.pathname !== '/login';

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* AppBar */}
      {showSidebar && (
        <header className="fixed top-0 left-0 right-0 h-16 bg-blue-600 text-white shadow-lg z-50">
          <div className="flex items-center justify-between h-full px-6">
            <h1 className="text-xl font-semibold">쿠팡 판매 데이터 자동화</h1>
            <div className="flex items-center gap-4">
              {tenant && (
                <span className="text-sm font-medium">{tenant.name}</span>
              )}
              {user && (
                <span className="text-sm">
                  {user.full_name} ({user.role})
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-white hover:bg-blue-700"
              >
                <LogOut className="h-4 w-4 mr-2" />
                로그아웃
              </Button>
            </div>
          </div>
        </header>
      )}

      {/* Sidebar */}
      {showSidebar && (
        <aside
          className="fixed left-0 top-16 bottom-0 bg-white border-r border-gray-200 overflow-y-auto"
          style={{ width: drawerWidth }}
        >
          <nav className="p-2">
            <ul className="space-y-1">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <li key={item.text}>
                    <Link
                      to={item.path}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-blue-50 text-blue-600 font-medium'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span className={isActive ? 'text-blue-600' : 'text-gray-500'}>
                        {item.icon}
                      </span>
                      <span className="text-sm">{item.text}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </aside>
      )}

      {/* Main Content */}
      <main
        className={`flex-1 ${showSidebar ? 'pt-16' : ''}`}
        style={{ marginLeft: showSidebar ? drawerWidth : 0 }}
      >
        <div className={showSidebar ? '' : 'min-h-screen'}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/margins"
              element={
                <ProtectedRoute>
                  <MarginManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <HistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/management"
              element={
                <ProtectedRoute>
                  <DataManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/export"
              element={
                <ProtectedRoute>
                  <ExportPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team"
              element={
                <ProtectedRoute>
                  <TeamManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <ProfileSettingsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
