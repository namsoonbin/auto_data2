import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { User, Store, Shield } from 'lucide-react';
import ProfileTab from '../components/profile/ProfileTab';
import TenantTab from '../components/profile/TenantTab';
import SecurityTab from '../components/profile/SecurityTab';

function ProfileSettingsPage() {
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleSuccess = (message) => {
    setSuccess(message);
    setError('');
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleError = (message) => {
    setError(message);
    setSuccess('');
    setTimeout(() => setError(''), 5000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-black mb-2">프로필 및 설정</h1>
          <p className="text-gray-600">개인 정보와 쇼핑몰 설정을 관리하세요</p>
        </div>

        {/* 알림 메시지 */}
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-600 text-sm flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            {success}
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {/* 탭 컨테이너 */}
        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="size-4" />
              개인 정보
            </TabsTrigger>
            <TabsTrigger value="tenant" className="flex items-center gap-2">
              <Store className="size-4" />
              쇼핑몰 설정
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2">
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
