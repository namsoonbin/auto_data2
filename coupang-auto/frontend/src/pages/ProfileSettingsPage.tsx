import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { User, Store, Shield, Settings } from 'lucide-react';
import ProfileTab from '../components/profile/ProfileTab';
import TenantTab from '../components/profile/TenantTab';
import SecurityTab from '../components/profile/SecurityTab';
import { useTheme } from '../contexts/ThemeContext';

function ProfileSettingsPage() {
  const { theme } = useTheme();
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleSuccess = (message: string) => {
    setSuccess(message);
    setError('');
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleError = (message: string) => {
    setError(message);
    setSuccess('');
    setTimeout(() => setError(''), 5000);
  };

  return (
    <div className={`min-h-screen p-4 relative ${
      theme === 'dark'
        ? 'bg-[#0f1115]'
        : 'bg-gray-50'
    }`}>
      {/* Grain texture overlay for dark mode */}
      {theme === 'dark' && (
        <div
          className="fixed inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
      )}

      <div className="max-w-5xl mx-auto relative z-10">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className={`mb-2 text-3xl font-bold flex items-center gap-2 ${
            theme === 'dark' ? 'text-white' : 'text-black'
          }`}>
            <Settings className={`h-8 w-8 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
            프로필 및 설정
          </h1>
          <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>개인 정보와 쇼핑몰 설정을 관리하세요</p>
        </div>

        {/* 알림 메시지 */}
        {success && (
          <div className={`mb-6 p-4 rounded-lg text-sm flex items-center gap-2 ${
            theme === 'dark'
              ? 'bg-green-950/20 border border-green-500/30 text-green-400'
              : 'bg-green-50 border border-green-200 text-green-600'
          }`}>
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            {success}
          </div>
        )}

        {error && (
          <div className={`mb-6 p-4 rounded-lg text-sm flex items-center gap-2 ${
            theme === 'dark'
              ? 'bg-red-950/20 border border-red-500/30 text-red-400'
              : 'bg-red-50 border border-red-200 text-red-600'
          }`}>
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {/* 탭 컨테이너 */}
        <Tabs defaultValue="profile" className="w-full">
          <TabsList className={`grid w-full grid-cols-3 mb-6 ${
            theme === 'dark' ? 'bg-gray-900/50 border border-gray-800' : ''
          }`}>
            <TabsTrigger
              value="profile"
              className={`flex items-center gap-2 ${
                theme === 'dark'
                  ? 'data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400 text-gray-400 hover:text-gray-300'
                  : ''
              }`}
            >
              <User className="size-4" />
              개인 정보
            </TabsTrigger>
            <TabsTrigger
              value="tenant"
              className={`flex items-center gap-2 ${
                theme === 'dark'
                  ? 'data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400 text-gray-400 hover:text-gray-300'
                  : ''
              }`}
            >
              <Store className="size-4" />
              쇼핑몰 설정
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className={`flex items-center gap-2 ${
                theme === 'dark'
                  ? 'data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400 text-gray-400 hover:text-gray-300'
                  : ''
              }`}
            >
              <Shield className="size-4" />
              보안 설정
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <ProfileTab onSuccess={handleSuccess} onError={handleError} />
          </TabsContent>

          <TabsContent value="tenant">
            <TenantTab onSuccess={handleSuccess} onError={handleError} />
          </TabsContent>

          <TabsContent value="security">
            <SecurityTab onSuccess={handleSuccess} onError={handleError} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default ProfileSettingsPage;
