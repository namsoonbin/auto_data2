import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Mail, User, Calendar, Shield, Activity } from 'lucide-react';
import axios from 'axios';
import { User as UserType } from '../../types';
import { useTheme } from '../../contexts/ThemeContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProfileTabProps {
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

interface ProfileFormData {
  full_name: string;
  phone: string;
}

function ProfileTab({ onSuccess, onError }: ProfileTabProps) {
  const { theme } = useTheme();
  const [profile, setProfile] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState<ProfileFormData>({
    full_name: '',
    phone: ''
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get<UserType>(`${API_BASE_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfile(response.data);
      setFormData({
        full_name: response.data.full_name || '',
        phone: response.data.phone || ''
      });
      setLoading(false);
    } catch (err) {
      console.error('프로필 조회 실패:', err);
      if (onError) onError('프로필을 불러오는데 실패했습니다');
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    if (profile) {
      setFormData({
        full_name: profile.full_name || '',
        phone: profile.phone || ''
      });
    }
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.put<UserType>(
        `${API_BASE_URL}/api/auth/profile`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setProfile(response.data);
      setEditing(false);
      if (onSuccess) onSuccess('프로필이 성공적으로 수정되었습니다');
    } catch (err: any) {
      console.error('프로필 수정 실패:', err);
      if (onError) onError(err.response?.data?.detail || '프로필 수정에 실패했습니다');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  const getRoleLabel = (role: string) => {
    const roleLabels: Record<string, string> = {
      'owner': '소유자',
      'admin': '관리자',
      'member': '멤버'
    };
    return roleLabels[role] || role;
  };

  if (loading) {
    return (
      <Card className={`shadow-lg ${
        theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
      }`}>
        <CardContent className="pt-6">
          <div className="flex justify-center items-center h-32">
            <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${
              theme === 'dark' ? 'border-cyan-400' : 'border-blue-600'
            }`}></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`shadow-lg ${
      theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
    }`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className={theme === 'dark' ? 'text-white' : ''}>
              기본 정보
            </CardTitle>
            <CardDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
              프로필에 표시될 기본 정보를 관리하세요
            </CardDescription>
          </div>
          <div className="flex gap-2">
            {!editing ? (
              <Button
                onClick={() => setEditing(true)}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  : 'bg-blue-600 hover:bg-blue-700'
                }
              >
                수정
              </Button>
            ) : (
              <>
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                    : ''
                  }
                >
                  취소
                </Button>
                <Button
                  onClick={handleSave}
                  className={theme === 'dark'
                    ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                    : 'bg-blue-600 hover:bg-blue-700'
                  }
                >
                  저장
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 편집 가능한 필드 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 이름 */}
          <div className="space-y-2">
            <Label htmlFor="full_name" className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              이름 <span className={theme === 'dark' ? 'text-red-400' : 'text-red-500'}>*</span>
            </Label>
            <Input
              id="full_name"
              type="text"
              placeholder="이름을 입력하세요"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className={theme === 'dark'
                ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                : 'bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500'
              }
              disabled={!editing}
            />
          </div>

          {/* 전화번호 */}
          <div className="space-y-2">
            <Label htmlFor="phone" className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>
              전화번호
            </Label>
            <Input
              id="phone"
              type="text"
              placeholder="010-1234-5678"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className={theme === 'dark'
                ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                : 'bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500'
              }
              disabled={!editing}
            />
          </div>
        </div>

        <Separator className={`my-6 ${theme === 'dark' ? 'bg-gray-800' : ''}`} />

        {/* 읽기 전용 정보 */}
        <div className="space-y-4">
          <h3 className={`mb-1 ${theme === 'dark' ? 'text-white' : 'text-black'}`}>계정 정보</h3>
          <p className={`text-sm mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>계정과 관련된 읽기 전용 정보입니다</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 이메일 */}
            <div className={`rounded-lg p-4 flex items-center gap-4 ${
              theme === 'dark'
                ? 'bg-blue-500/10 border border-blue-500/30'
                : 'bg-blue-50 border border-blue-100'
            }`}>
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-blue-500/20' : 'bg-blue-100'
              }`}>
                <Mail className={`size-5 ${
                  theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                }`} />
              </div>
              <div>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>이메일</p>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>{profile?.email || '-'}</p>
              </div>
            </div>

            {/* 역할 */}
            <div className={`rounded-lg p-4 flex items-center gap-4 ${
              theme === 'dark'
                ? 'bg-purple-500/10 border border-purple-500/30'
                : 'bg-purple-50 border border-purple-100'
            }`}>
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-purple-500/20' : 'bg-purple-100'
              }`}>
                <Shield className={`size-5 ${
                  theme === 'dark' ? 'text-purple-400' : 'text-purple-600'
                }`} />
              </div>
              <div>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>역할</p>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>{getRoleLabel(profile?.role || '')}</p>
              </div>
            </div>

            {/* 가입일 */}
            <div className={`rounded-lg p-4 flex items-center gap-4 ${
              theme === 'dark'
                ? 'bg-green-500/10 border border-green-500/30'
                : 'bg-green-50 border border-green-100'
            }`}>
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-green-500/20' : 'bg-green-100'
              }`}>
                <Calendar className={`size-5 ${
                  theme === 'dark' ? 'text-green-400' : 'text-green-600'
                }`} />
              </div>
              <div>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>가입일</p>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>{formatDate(profile?.created_at)}</p>
              </div>
            </div>

            {/* 마지막 로그인 */}
            <div className={`rounded-lg p-4 flex items-center gap-4 ${
              theme === 'dark'
                ? 'bg-orange-500/10 border border-orange-500/30'
                : 'bg-orange-50 border border-orange-100'
            }`}>
              <div className={`rounded-full p-3 ${
                theme === 'dark' ? 'bg-orange-500/20' : 'bg-orange-100'
              }`}>
                <Activity className={`size-5 ${
                  theme === 'dark' ? 'text-orange-400' : 'text-orange-600'
                }`} />
              </div>
              <div>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>마지막 로그인</p>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>{formatDate(profile?.last_login)}</p>
              </div>
            </div>
          </div>

          {/* 계정 상태 */}
          <div className={`border rounded-lg p-4 flex items-center justify-between ${
            profile?.is_active
              ? (theme === 'dark' ? 'bg-green-500/10 border-green-500/30' : 'bg-green-50 border-green-100')
              : (theme === 'dark' ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-100')
          }`}>
            <div className="flex items-center gap-4">
              <div className={`rounded-full p-3 ${
                profile?.is_active
                  ? (theme === 'dark' ? 'bg-green-500/20' : 'bg-green-100')
                  : (theme === 'dark' ? 'bg-red-500/20' : 'bg-red-100')
              }`}>
                <User className={`size-5 ${
                  profile?.is_active
                    ? (theme === 'dark' ? 'text-green-400' : 'text-green-600')
                    : (theme === 'dark' ? 'text-red-400' : 'text-red-600')
                }`} />
              </div>
              <div>
                <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>계정 상태</p>
                <p className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-black'}`}>{profile?.is_active ? '활성' : '비활성'}</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ProfileTab;
