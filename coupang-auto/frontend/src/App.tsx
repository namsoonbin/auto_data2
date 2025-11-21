import React, { useState } from 'react';
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
  Menu,
  X,
  ShoppingCart,
  Sparkles,
  Sun,
  Moon,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import DataManagementPage from './pages/DataManagementPage';
import ExportPage from './pages/ExportPage';
import MarginManagementPage from './pages/MarginManagementPage';
import FakePurchaseManagementPage from './pages/FakePurchaseManagementPage';
import LoginPage from './pages/LoginPage';
import ProfileSettingsPage from './pages/ProfileSettingsPage';
import TeamManagementPage from './pages/TeamManagementPage';
import ProtectedRoute from './components/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';
import { useTheme } from './contexts/ThemeContext';

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
  { text: '가구매 관리', icon: <ShoppingCart className="h-5 w-5" />, path: '/fake-purchases' },
  { text: '업로드 히스토리', icon: <History className="h-5 w-5" />, path: '/history' },
  { text: '데이터 관리', icon: <Trash2 className="h-5 w-5" />, path: '/management' },
  { text: '엑셀 다운로드', icon: <Download className="h-5 w-5" />, path: '/export' },
  { text: '팀 관리', icon: <Users className="h-5 w-5" />, path: '/team' },
  { text: '프로필 및 설정', icon: <Settings className="h-5 w-5" />, path: '/settings' },
];

function AppContent() {
  const location = useLocation();
  const { user, tenant, logout, isAuthenticated } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // 로그인 페이지에서는 사이드바를 표시하지 않음
  const showSidebar = isAuthenticated && location.pathname !== '/login';

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#0f1115]' : 'bg-gray-50'}`}>
      {/* Header */}
      {showSidebar && (
        <header className={`fixed top-0 left-0 right-0 h-16 border-b shadow-lg z-50 relative overflow-hidden ${
          theme === 'dark'
            ? 'bg-[#0f1115] border-cyan-500/10 shadow-2xl'
            : 'bg-white border-gray-200 shadow-md'
        }`}>
          {/* Grain texture overlay - dark mode only */}
          {theme === 'dark' && (
            <div
              className="absolute inset-0 opacity-[0.02] pointer-events-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
              }}
            />
          )}

          {/* Scan line animation - dark mode only */}
          {theme === 'dark' && (
            <div className="absolute inset-0 pointer-events-none opacity-5">
              <div
                className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400 to-transparent h-[2px]"
                style={{
                  animation: 'scan 8s linear infinite',
                }}
              />
            </div>
          )}

          <div className="flex items-center justify-between h-full px-4 md:px-6 relative z-10">
            {/* Sidebar Toggle Button */}
            {showSidebar && (
              <button
                onClick={toggleSidebar}
                className={`p-2 rounded-lg transition-all ${
                  theme === 'dark'
                    ? 'hover:bg-cyan-500/10 text-cyan-400 hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                    : 'hover:bg-blue-50 text-blue-600'
                }`}
                title={sidebarOpen ? '사이드바 숨기기' : '사이드바 보이기'}
              >
                {sidebarOpen ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeft className="h-5 w-5" />}
              </button>
            )}

            <h1 className={`text-sm md:text-base font-bold tracking-wider md:tracking-[0.2em] uppercase flex-1 md:flex-none text-center md:text-left ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              <span className={`font-mono ${theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}`}>
                COUPANG
              </span>
              <span className="text-gray-500 hidden md:inline mx-1">///</span>
              <span className="hidden md:inline font-light">DATA TERMINAL</span>
            </h1>

            <div className="flex items-center gap-2 md:gap-4">
              {tenant && (
                <div className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md border ${
                  theme === 'dark'
                    ? 'bg-cyan-500/5 border-cyan-500/10'
                    : 'bg-blue-50 border-blue-200'
                }`}>
                  <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${
                    theme === 'dark' ? 'bg-cyan-400' : 'bg-blue-600'
                  }`} />
                  <span className={`text-xs font-mono tracking-wide ${
                    theme === 'dark' ? 'text-cyan-400/90' : 'text-blue-600'
                  }`}>
                    {tenant.name}
                  </span>
                </div>
              )}
              {user && (
                <span className={`hidden md:inline text-xs font-mono tracking-wide ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  <span className="text-gray-500">[</span>
                  {user.full_name}
                  <span className="text-gray-500">]</span>
                  <span className={`ml-2 ${theme === 'dark' ? 'text-cyan-400/60' : 'text-blue-600'}`}>
                    {user.role}
                  </span>
                </span>
              )}

              {/* Theme Toggle Button */}
              <button
                onClick={toggleTheme}
                className={`group relative p-2 rounded-md border transition-all overflow-hidden ${
                  theme === 'dark'
                    ? 'bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 hover:from-cyan-500/20 hover:to-cyan-500/10 text-cyan-400 border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : 'bg-blue-50 hover:bg-blue-100 text-blue-600 border-blue-200 hover:border-blue-300'
                }`}
                title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              >
                {theme === 'dark' && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                )}
                {theme === 'dark' ? (
                  <Sun className="h-4 w-4 relative z-10" />
                ) : (
                  <Moon className="h-4 w-4 relative z-10" />
                )}
              </button>

              <button
                onClick={handleLogout}
                className={`group relative px-3 py-1.5 rounded-md border text-xs font-mono tracking-wider flex items-center gap-2 overflow-hidden transition-all ${
                  theme === 'dark'
                    ? 'bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 hover:from-cyan-500/20 hover:to-cyan-500/10 text-cyan-400 border-cyan-500/20 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : 'bg-blue-50 hover:bg-blue-100 text-blue-600 border-blue-200 hover:border-blue-300'
                }`}
              >
                {theme === 'dark' && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                )}
                <LogOut className="h-3.5 w-3.5 relative z-10" />
                <span className="hidden md:inline relative z-10">LOGOUT</span>
              </button>
            </div>
          </div>

          {/* Bottom glow effect - dark mode only */}
          {theme === 'dark' && (
            <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
          )}
        </header>
      )}

      {/* Sidebar */}
      {showSidebar && (
        <aside
          className={`
            fixed left-0 top-16 bottom-0 border-r overflow-y-auto z-40 transition-all duration-300 ease-out
            ${theme === 'dark' ? 'bg-[#0f1115] border-cyan-500/10' : 'bg-white border-gray-200'}
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          `}
          style={{ width: drawerWidth }}
        >
          {/* Grain texture overlay - dark mode only */}
          {theme === 'dark' && (
            <div
              className="absolute inset-0 opacity-[0.02] pointer-events-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
              }}
            />
          )}

          {/* Right edge glow - dark mode only */}
          {theme === 'dark' && (
            <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-transparent via-cyan-500/30 to-transparent" />
          )}

          <nav className="p-3 relative z-10">
            {/* Navigation header */}
            <div className={`mb-4 pb-3 border-b ${
              theme === 'dark' ? 'border-cyan-500/10' : 'border-gray-200'
            }`}>
              <div className={`flex items-center gap-2 text-xs font-mono tracking-widest px-2 ${
                theme === 'dark' ? 'text-cyan-400/60' : 'text-blue-600/70'
              }`}>
                <div className={`w-2 h-2 border rotate-45 ${
                  theme === 'dark' ? 'border-cyan-400/40' : 'border-blue-500/50'
                }`} />
                NAVIGATION
              </div>
            </div>

            <ul className="space-y-1">
              {menuItems.map((item, index) => {
                const isActive = location.pathname === item.path;
                return (
                  <li
                    key={item.text}
                    style={{
                      animationDelay: `${index * 30}ms`,
                    }}
                    className="animate-fadeInUp"
                  >
                    <Link
                      to={item.path}
                      className={`
                        group relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-300 overflow-hidden
                        ${
                          isActive
                            ? theme === 'dark'
                              ? 'bg-gradient-to-r from-cyan-500/15 to-cyan-500/5 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                              : 'bg-blue-50 border border-blue-200 shadow-sm'
                            : theme === 'dark'
                            ? 'border border-transparent hover:border-cyan-500/20 hover:bg-cyan-500/5'
                            : 'border border-transparent hover:border-blue-200 hover:bg-blue-50/50'
                        }
                      `}
                    >
                      {/* Hover glow effect - dark mode only */}
                      {!isActive && theme === 'dark' && (
                        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/10 to-cyan-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                      )}

                      {/* Active indicator */}
                      {isActive && (
                        <div className={`absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full ${
                          theme === 'dark'
                            ? 'bg-gradient-to-b from-cyan-400 to-cyan-600 shadow-[0_0_10px_rgba(6,182,212,0.6)]'
                            : 'bg-gradient-to-b from-blue-500 to-blue-600'
                        }`} />
                      )}

                      <span
                        className={`relative z-10 transition-all duration-300 ${
                          isActive
                            ? theme === 'dark'
                              ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]'
                              : 'text-blue-600'
                            : theme === 'dark'
                            ? 'text-gray-500 group-hover:text-cyan-400'
                            : 'text-gray-600 group-hover:text-blue-600'
                        }`}
                      >
                        {item.icon}
                      </span>
                      <span
                        className={`relative z-10 text-sm font-medium tracking-wide transition-all duration-300 ${
                          isActive
                            ? theme === 'dark'
                              ? 'text-white font-semibold'
                              : 'text-gray-900 font-semibold'
                            : theme === 'dark'
                            ? 'text-gray-400 group-hover:text-gray-200'
                            : 'text-gray-700 group-hover:text-gray-900'
                        }`}
                      >
                        {item.text}
                      </span>

                      {/* Corner accent */}
                      {isActive && (
                        <div className={`absolute top-1 right-1 w-1.5 h-1.5 border-t border-r rounded-tr ${
                          theme === 'dark' ? 'border-cyan-400/40' : 'border-blue-500/50'
                        }`} />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>

            {/* Footer decoration */}
            <div className={`mt-6 pt-4 border-t ${
              theme === 'dark' ? 'border-cyan-500/10' : 'border-gray-200'
            }`}>
              <div className={`flex items-center justify-center gap-1 text-[10px] font-mono tracking-widest ${
                theme === 'dark' ? 'text-gray-600' : 'text-gray-500'
              }`}>
                <div className={`w-1 h-1 rounded-full animate-pulse ${
                  theme === 'dark' ? 'bg-cyan-500/30' : 'bg-blue-500/40'
                }`} />
                SYSTEM ACTIVE
                <div
                  className={`w-1 h-1 rounded-full animate-pulse ${
                    theme === 'dark' ? 'bg-cyan-500/30' : 'bg-blue-500/40'
                  }`}
                  style={{ animationDelay: '1s' }}
                />
              </div>
            </div>
          </nav>
        </aside>
      )}

      {/* Main Content */}
      <main
        className={`transition-all duration-300 ${showSidebar ? 'pt-16' : ''} ${
          showSidebar && sidebarOpen ? 'ml-60' : 'ml-0'
        } ${theme === 'dark' ? 'bg-[#0f1115]' : 'bg-gray-50'}`}
      >
        <div className={showSidebar ? 'min-h-screen' : 'min-h-screen'}>
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
              path="/fake-purchases"
              element={
                <ProtectedRoute>
                  <FakePurchaseManagementPage />
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

      {/* Global styles for animations */}
      <style>{`
        @keyframes scan {
          0% {
            transform: translateY(-100%);
          }
          100% {
            transform: translateY(100vh);
          }
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeInUp {
          animation: fadeInUp 0.4s ease-out forwards;
        }
      `}</style>
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
