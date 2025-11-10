import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Badge } from '../ui/badge';
import { Store, Calendar, Hash, Activity, Award } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { Tenant } from '../../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TenantTabProps {
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

interface TenantFormData {
  name: string;
}

function TenantTab({ onSuccess, onError }: TenantTabProps) {
  const { tenant: authTenant, refreshTenant } = useAuth();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState<TenantFormData>({
    name: ''
  });

  useEffect(() => {
    fetchTenant();
  }, []);

  const fetchTenant = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get<Tenant>(`${API_BASE_URL}/api/auth/tenant`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenant(response.data);
      setFormData({
        name: response.data.name
      });
      setLoading(false);
    } catch (err) {
      console.error('테넌트 조회 실패:', err);
      if (onError) onError('테넌트 정보를 불러오는데 실패했습니다');
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    if (tenant) {
      setFormData({
        name: tenant.name
      });
    }
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.put<Tenant>(
        `${API_BASE_URL}/api/auth/tenant`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTenant(response.data);
      setEditing(false);

      // AuthContext의 tenant 정보도 업데이트
      if (refreshTenant) {
        await refreshTenant();
      }

      if (onSuccess) onSuccess('테넌트 정보가 성공적으로 수정되었습니다');
    } catch (err: any) {
      console.error('테넌트 수정 실패:', err);
      if (onError) onError(err.response?.data?.detail || '테넌트 정보 수정에 실패했습니다');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  const getPlanLabel = (plan: string) => {
    const planLabels: Record<string, string> = {
      'basic': '베이직',
      'pro': '프로',
      'enterprise': '엔터프라이즈'
    };
    return planLabels[plan] || plan;
  };

  const getPlanVariant = (plan: string): "default" | "secondary" | "outline" | "destructive" => {
    const planVariants: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
      'basic': 'secondary',
      'pro': 'default',
      'enterprise': 'outline'
    };
    return planVariants[plan] || 'secondary';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="shadow-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>쇼핑몰 정보</CardTitle>
              <CardDescription>쇼핑몰의 기본 정보를 관리하세요</CardDescription>
            </div>
            <div className="flex gap-2">
              {!editing ? (
                <Button
                  onClick={() => setEditing(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  수정
                </Button>
              ) : (
                <>
                  <Button
                    onClick={handleCancel}
                    variant="outline"
                  >
                    취소
                  </Button>
                  <Button
                    onClick={handleSave}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    저장
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 쇼핑몰 이름 */}
            <div className="space-y-2">
              <Label htmlFor="tenant_name" className="text-gray-700">
                쇼핑몰 이름 <span className="text-red-500">*</span>
              </Label>
              <Input
                id="tenant_name"
                type="text"
                placeholder="쇼핑몰 이름을 입력하세요"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="bg-white border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                disabled={!editing}
              />
            </div>

            {/* 슬러그 */}
            <div className="space-y-2">
              <Label htmlFor="slug" className="text-gray-700">
                슬러그 (URL)
              </Label>
              <Input
                id="slug"
                type="text"
                value={tenant?.slug || ''}
                className="bg-gray-100 border-gray-200"
                disabled
              />
              <p className="text-xs text-gray-500">슬러그는 변경할 수 없습니다</p>
            </div>
          </div>

          <Separator className="my-6" />

          {/* 읽기 전용 정보 */}
          <div className="space-y-4">
            <h3 className="text-black mb-1">쇼핑몰 상세 정보</h3>
            <p className="text-gray-600 text-sm mb-4">쇼핑몰과 관련된 읽기 전용 정보입니다</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 플랜 */}
              <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="bg-indigo-100 rounded-full p-3">
                    <Award className="size-5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-gray-500 text-sm">플랜</p>
                    <Badge variant={getPlanVariant(tenant?.plan || '')} className="mt-1">
                      {getPlanLabel(tenant?.plan || '')}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* 상태 */}
              <div className={`${tenant?.status === 'active' ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'} border rounded-lg p-4 flex items-center gap-4`}>
                <div className={`${tenant?.status === 'active' ? 'bg-green-100' : 'bg-red-100'} rounded-full p-3`}>
                  <Activity className={`size-5 ${tenant?.status === 'active' ? 'text-green-600' : 'text-red-600'}`} />
                </div>
                <div>
                  <p className="text-gray-500 text-sm">상태</p>
                  <p className="text-black font-medium">{tenant?.status === 'active' ? '활성' : '비활성'}</p>
                </div>
              </div>

              {/* 생성일 */}
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-center gap-4">
                <div className="bg-blue-100 rounded-full p-3">
                  <Calendar className="size-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-gray-500 text-sm">생성일</p>
                  <p className="text-black font-medium">{formatDate(tenant?.created_at)}</p>
                </div>
              </div>

              {/* 테넌트 ID */}
              <div className="bg-gray-50 border border-gray-100 rounded-lg p-4 flex items-center gap-4">
                <div className="bg-gray-100 rounded-full p-3">
                  <Hash className="size-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-gray-500 text-sm">테넌트 ID</p>
                  <p className="text-black font-medium text-sm">{tenant?.id || '-'}</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 데이터 통계 카드 */}
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>데이터 통계</CardTitle>
          <CardDescription>현재 쇼핑몰의 주요 통계 정보</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-center text-white">
              <Store className="size-8 mx-auto mb-3 opacity-90" />
              <p className="text-2xl font-bold mb-1">{authTenant?.name || tenant?.name || '-'}</p>
              <p className="text-blue-100 text-sm">현재 쇼핑몰</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-center text-white">
              <Award className="size-8 mx-auto mb-3 opacity-90" />
              <p className="text-2xl font-bold mb-1">{getPlanLabel(tenant?.plan || '')}</p>
              <p className="text-purple-100 text-sm">현재 플랜</p>
            </div>

            <div className={`bg-gradient-to-br ${tenant?.status === 'active' ? 'from-green-500 to-green-600' : 'from-red-500 to-red-600'} rounded-lg p-6 text-center text-white`}>
              <Activity className="size-8 mx-auto mb-3 opacity-90" />
              <p className="text-2xl font-bold mb-1">{tenant?.status === 'active' ? '활성' : '비활성'}</p>
              <p className={`${tenant?.status === 'active' ? 'text-green-100' : 'text-red-100'} text-sm`}>계정 상태</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default TenantTab;
