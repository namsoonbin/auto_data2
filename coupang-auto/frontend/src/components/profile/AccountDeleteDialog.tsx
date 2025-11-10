import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Checkbox } from '../ui/checkbox';
import { AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface AccountDeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userRole?: string;
}

function AccountDeleteDialog({ open, onOpenChange, userRole }: AccountDeleteDialogProps) {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [localError, setLocalError] = useState('');
  const [loading, setLoading] = useState(false);

  const isOwner = userRole === 'owner';

  // 다이얼로그가 닫힐 때 상태 초기화
  useEffect(() => {
    if (!open) {
      setPassword('');
      setConfirmed(false);
      setLocalError('');
      setShowPassword(false);
    }
  }, [open]);

  const handleAccountDelete = async () => {
    setLocalError('');

    // 유효성 검사
    if (!password) {
      setLocalError('비밀번호를 입력해주세요');
      return;
    }

    if (!confirmed) {
      setLocalError('계정 삭제에 동의해주세요');
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.delete(
        `${API_BASE_URL}/api/auth/account`,
        {
          data: { password },
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // 로컬스토리지 클리어
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');

      // 로그인 페이지로 리다이렉트
      navigate('/login', {
        state: {
          message: response.data.message || '계정이 성공적으로 삭제되었습니다'
        }
      });
    } catch (err: any) {
      console.error('계정 삭제 실패:', err);
      const errorMessage = err.response?.data?.detail || '계정 삭제에 실패했습니다';
      setLocalError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="size-5" />
            계정 삭제
          </DialogTitle>
          <DialogDescription className="text-gray-600">
            이 작업은 되돌릴 수 없습니다. 신중하게 진행해주세요.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 경고 메시지 */}
          <Alert className="bg-red-50 border-red-200">
            <AlertTriangle className="size-4 text-red-600" />
            <AlertDescription className="text-red-800 text-sm ml-2">
              {isOwner ? (
                <>
                  <strong>Owner 계정 삭제 시:</strong>
                  <ul className="mt-2 ml-4 list-disc space-y-1">
                    <li>테넌트의 모든 데이터가 삭제됩니다</li>
                    <li>모든 팀원의 계정이 삭제됩니다</li>
                    <li>판매 데이터, 마진 정보 등이 모두 삭제됩니다</li>
                  </ul>
                </>
              ) : (
                <>
                  <strong>계정 삭제 시:</strong>
                  <ul className="mt-2 ml-4 list-disc space-y-1">
                    <li>본인의 계정만 삭제됩니다</li>
                    <li>팀 멤버십이 해제됩니다</li>
                    <li>이 작업은 되돌릴 수 없습니다</li>
                  </ul>
                </>
              )}
            </AlertDescription>
          </Alert>

          {/* 에러 메시지 */}
          {localError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {localError}
            </div>
          )}

          {/* 비밀번호 입력 */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-gray-700">
              비밀번호 확인
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
                disabled={loading}
                placeholder="현재 비밀번호를 입력하세요"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                disabled={loading}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* 확인 체크박스 */}
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <Checkbox
              id="confirm"
              checked={confirmed}
              onCheckedChange={(checked) => setConfirmed(checked as boolean)}
              disabled={loading}
              className="mt-0.5"
            />
            <label
              htmlFor="confirm"
              className="text-sm text-gray-700 cursor-pointer leading-relaxed"
            >
              위의 내용을 이해했으며, 계정 삭제에 동의합니다.
              {isOwner && (
                <span className="block mt-1 text-red-600 font-medium">
                  모든 데이터가 영구적으로 삭제됨을 확인합니다.
                </span>
              )}
            </label>
          </div>
        </div>

        <DialogFooter>
          <Button
            onClick={() => onOpenChange(false)}
            variant="outline"
            disabled={loading}
          >
            취소
          </Button>
          <Button
            onClick={handleAccountDelete}
            className="bg-red-600 hover:bg-red-700 text-white"
            disabled={loading || !password || !confirmed}
          >
            {loading ? '삭제 중...' : '계정 삭제'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default AccountDeleteDialog;
