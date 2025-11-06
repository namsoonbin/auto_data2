import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Lock, Shield, Trash2 } from 'lucide-react';
import PasswordChangeDialog from './PasswordChangeDialog';

function SecurityTab({ onSuccess, onError }) {
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);

  return (
    <>
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>보안 설정</CardTitle>
          <CardDescription>계정 보안을 관리하고 설정하세요</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 비밀번호 변경 */}
          <div className="flex items-center justify-between py-3 border-b border-gray-100">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 rounded-full p-3">
                <Lock className="size-5 text-blue-600" />
              </div>
              <div>
                <p className="text-black font-medium">비밀번호 변경</p>
                <p className="text-gray-500 text-sm">계정 비밀번호를 업데이트하세요</p>
              </div>
            </div>
            <Button
              onClick={() => setPasswordDialogOpen(true)}
              variant="outline"
              className="text-blue-600 hover:bg-blue-50 border-blue-200"
            >
              변경
            </Button>
          </div>

          {/* 2단계 인증 */}
          <div className="flex items-center justify-between py-3 border-b border-gray-100">
            <div className="flex items-center gap-4">
              <div className="bg-purple-100 rounded-full p-3">
                <Shield className="size-5 text-purple-600" />
              </div>
              <div>
                <p className="text-black font-medium">2단계 인증</p>
                <p className="text-gray-500 text-sm">계정 보안을 강화하세요</p>
              </div>
            </div>
            <Button
              variant="outline"
              className="text-purple-600 hover:bg-purple-50 border-purple-200"
              disabled
            >
              설정 (준비 중)
            </Button>
          </div>

          {/* 계정 삭제 */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-4">
              <div className="bg-red-100 rounded-full p-3">
                <Trash2 className="size-5 text-red-600" />
              </div>
              <div>
                <p className="text-black font-medium">계정 삭제</p>
                <p className="text-gray-500 text-sm">계정을 영구적으로 삭제합니다</p>
              </div>
            </div>
            <Button
              variant="outline"
              className="text-red-600 hover:bg-red-50 border-red-200"
              disabled
            >
              삭제 (준비 중)
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
    </>
  );
}

export default SecurityTab;
