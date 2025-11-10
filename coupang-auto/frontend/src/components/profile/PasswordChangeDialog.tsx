import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { Eye, EyeOff, Lock } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface PasswordChangeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

function PasswordChangeDialog({ open, onOpenChange, onSuccess, onError }: PasswordChangeDialogProps) {
  const [passwordData, setPasswordData] = useState<PasswordData>({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [localError, setLocalError] = useState('');
  const [localSuccess, setLocalSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // 다이얼로그가 닫힐 때 상태 초기화
  useEffect(() => {
    if (!open) {
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      setLocalError('');
      setLocalSuccess('');
      setShowOldPassword(false);
      setShowNewPassword(false);
      setShowConfirmPassword(false);
    }
  }, [open]);

  const handlePasswordChange = async () => {
    setLocalError('');
    setLocalSuccess('');

    // 유효성 검사
    if (passwordData.new_password !== passwordData.confirm_password) {
      setLocalError('새 비밀번호가 일치하지 않습니다');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setLocalError('새 비밀번호는 최소 8자 이상이어야 합니다');
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      await axios.put(
        `${API_BASE_URL}/api/auth/password`,
        {
          old_password: passwordData.old_password,
          new_password: passwordData.new_password
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setLocalSuccess('비밀번호가 성공적으로 변경되었습니다');

      // 2초 후 다이얼로그 닫기
      setTimeout(() => {
        if (onSuccess) onSuccess('비밀번호가 성공적으로 변경되었습니다');
        onOpenChange(false);
      }, 1500);
    } catch (err: any) {
      console.error('비밀번호 변경 실패:', err);
      const errorMessage = err.response?.data?.detail || '비밀번호 변경에 실패했습니다';
      setLocalError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Lock className="size-5" />
            비밀번호 변경
          </DialogTitle>
          <DialogDescription>
            보안을 위해 현재 비밀번호와 새 비밀번호를 입력하세요
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 에러 메시지 */}
          {localError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {localError}
            </div>
          )}

          {/* 성공 메시지 */}
          {localSuccess && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-600 text-sm">
              {localSuccess}
            </div>
          )}

          {/* 현재 비밀번호 */}
          <div className="space-y-2">
            <Label htmlFor="old_password">현재 비밀번호</Label>
            <div className="relative">
              <Input
                id="old_password"
                type={showOldPassword ? 'text' : 'password'}
                value={passwordData.old_password}
                onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                className="pr-10"
                disabled={loading || !!localSuccess}
                placeholder="현재 비밀번호를 입력하세요"
              />
              <button
                type="button"
                onClick={() => setShowOldPassword(!showOldPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={loading || !!localSuccess}
              >
                {showOldPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* 새 비밀번호 */}
          <div className="space-y-2">
            <Label htmlFor="new_password">새 비밀번호</Label>
            <div className="relative">
              <Input
                id="new_password"
                type={showNewPassword ? 'text' : 'password'}
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                className="pr-10"
                disabled={loading || !!localSuccess}
                placeholder="새 비밀번호를 입력하세요 (최소 8자)"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={loading || !!localSuccess}
              >
                {showNewPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500">최소 8자 이상</p>
          </div>

          {/* 새 비밀번호 확인 */}
          <div className="space-y-2">
            <Label htmlFor="confirm_password">새 비밀번호 확인</Label>
            <div className="relative">
              <Input
                id="confirm_password"
                type={showConfirmPassword ? 'text' : 'password'}
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                className="pr-10"
                disabled={loading || !!localSuccess}
                placeholder="새 비밀번호를 다시 입력하세요"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={loading || !!localSuccess}
              >
                {showConfirmPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            onClick={() => onOpenChange(false)}
            variant="outline"
            disabled={loading || !!localSuccess}
          >
            취소
          </Button>
          <Button
            onClick={handlePasswordChange}
            className="bg-blue-600 hover:bg-blue-700"
            disabled={loading || !!localSuccess}
          >
            {loading ? '변경 중...' : '비밀번호 변경'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PasswordChangeDialog;
