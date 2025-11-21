import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Lock, Shield, Trash2 } from 'lucide-react';
import PasswordChangeDialog from './PasswordChangeDialog';
import AccountDeleteDialog from './AccountDeleteDialog';
import axios from 'axios';
import { User as UserType } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface SecurityTabProps {
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

function SecurityTab({ onSuccess, onError }: SecurityTabProps) {
  const { theme } = useTheme();
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userRole, setUserRole] = useState<string>('');

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get<UserType>(`${API_BASE_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserRole(response.data.role);
    } catch (err) {
      console.error('사용자 정보 조회 실패:', err);
    }
  };

  return (
    <>
      <Card className={`shadow-lg ${
        theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
      }`}>
        <CardHeader>
          <CardTitle className={theme === 'dark' ? 'text-white' : ''}>
            보안 설정
          </CardTitle>
          <CardDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
            계정 보안을 관리하고 설정하세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 비밀번호 변경 */}
          <div className={`flex items-center justify-between py-3 border-b ${
            theme === 'dark' ? 'border-gray-800' : 'border-gray-100'
          }`}>
            <div className="flex items-center gap-4">
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-blue-500/20' : 'bg-blue-100'
              }`}>
                <Lock className={`size-5 ${
                  theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                }`} />
              </div>
              <div>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>비밀번호 변경</p>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>계정 비밀번호를 업데이트하세요</p>
              </div>
            </div>
            <Button
              onClick={() => setPasswordDialogOpen(true)}
              variant="outline"
              className={theme === 'dark'
                ? 'bg-gray-900/50 border-gray-700 text-cyan-400 hover:bg-cyan-500/10 hover:border-cyan-500/50'
                : 'text-blue-600 hover:bg-blue-50 border-blue-200'
              }
            >
              변경
            </Button>
          </div>

          {/* 2단계 인증 */}
          <div className={`flex items-center justify-between py-3 border-b ${
            theme === 'dark' ? 'border-gray-800' : 'border-gray-100'
          }`}>
            <div className="flex items-center gap-4">
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-purple-500/20' : 'bg-purple-100'
              }`}>
                <Shield className={`size-5 ${
                  theme === 'dark' ? 'text-purple-400' : 'text-purple-600'
                }`} />
              </div>
              <div>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>2단계 인증</p>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>계정 보안을 강화하세요</p>
              </div>
            </div>
            <Button
              variant="outline"
              className={theme === 'dark'
                ? 'bg-gray-900/50 border-gray-700 text-gray-500 disabled:opacity-50'
                : 'text-purple-600 hover:bg-purple-50 border-purple-200'
              }
              disabled
            >
              설정 (준비 중)
            </Button>
          </div>

          {/* 계정 삭제 */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-4">
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-red-500/20' : 'bg-red-100'
              }`}>
                <Trash2 className={`size-5 ${
                  theme === 'dark' ? 'text-red-400' : 'text-red-600'
                }`} />
              </div>
              <div>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>계정 삭제</p>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>계정을 영구적으로 삭제합니다</p>
              </div>
            </div>
            <Button
              onClick={() => setDeleteDialogOpen(true)}
              variant="outline"
              className={theme === 'dark'
                ? 'bg-gray-900/50 border-gray-700 text-red-400 hover:bg-red-500/10 hover:border-red-500/50'
                : 'text-red-600 hover:bg-red-50 border-red-200'
              }
            >
              삭제
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 비밀번호 변경 다이얼로그 */}
      <PasswordChangeDialog
        open={passwordDialogOpen}
        onOpenChange={setPasswordDialogOpen}
        onSuccess={onSuccess}
        onError={onError}
      />

      {/* 계정 삭제 다이얼로그 */}
      <AccountDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        userRole={userRole}
      />
    </>
  );
}

export default SecurityTab;
