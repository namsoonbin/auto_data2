import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  UserPlus,
  Edit,
  Trash2,
  Users,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Interfaces
interface TeamMember {
  id: number;
  email: string;
  full_name: string | null;
  role: 'owner' | 'admin' | 'member';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface InviteData {
  email: string;
  full_name: string;
  password: string;
  role: 'admin' | 'member';
}

function TeamManagementPage() {
  const { user } = useAuth();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const [inviteData, setInviteData] = useState<InviteData>({
    email: '',
    full_name: '',
    password: '',
    role: 'member',
  });

  const [newRole, setNewRole] = useState<'owner' | 'admin' | 'member'>('member');

  useEffect(() => {
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get<{ members: TeamMember[] }>(`${API_BASE_URL}/api/team/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMembers(response.data.members);
      setLoading(false);
    } catch (err) {
      console.error('팀원 조회 실패:', err);
      setError('팀원 목록을 불러오는데 실패했습니다');
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(`${API_BASE_URL}/api/team/members`, inviteData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess('팀원이 성공적으로 초대되었습니다');
      setInviteDialogOpen(false);
      setInviteData({ email: '', full_name: '', password: '', role: 'member' });
      fetchMembers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('팀원 초대 실패:', err);
      setError(err.response?.data?.detail || '팀원 초대에 실패했습니다');
    }
  };

  const handleRoleChange = async () => {
    if (!selectedMember) return;

    try {
      const token = localStorage.getItem('access_token');
      await axios.put(
        `${API_BASE_URL}/api/team/members/${selectedMember.id}/role`,
        { role: newRole },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setSuccess('역할이 성공적으로 변경되었습니다');
      setRoleDialogOpen(false);
      setSelectedMember(null);
      fetchMembers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('역할 변경 실패:', err);
      setError(err.response?.data?.detail || '역할 변경에 실패했습니다');
    }
  };

  const handleDelete = async () => {
    if (!selectedMember) return;

    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(`${API_BASE_URL}/api/team/members/${selectedMember.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess('팀원이 성공적으로 제거되었습니다');
      setDeleteDialogOpen(false);
      setSelectedMember(null);
      fetchMembers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('팀원 제거 실패:', err);
      setError(err.response?.data?.detail || '팀원 제거에 실패했습니다');
    }
  };

  const getRoleLabel = (role: string) => {
    const roleLabels: Record<string, string> = {
      owner: '소유자',
      admin: '관리자',
      member: '멤버',
    };
    return roleLabels[role] || role;
  };

  const getRoleBadgeClass = (role: string) => {
    const roleColors: Record<string, string> = {
      owner: 'bg-red-600',
      admin: 'bg-amber-500',
      member: 'bg-blue-600',
    };
    return roleColors[role] || 'bg-blue-600';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR');
  };

  const canInvite = user?.role === 'owner' || user?.role === 'admin';
  const canEditRole = user?.role === 'owner';
  const canDelete = user?.role === 'owner' || user?.role === 'admin';

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-black flex items-center gap-2">
            <Users className="h-8 w-8" />
            팀 관리
          </h1>
          {canInvite && (
            <Button onClick={() => setInviteDialogOpen(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              팀원 초대
            </Button>
          )}
        </div>

        {success && (
          <Alert className="mb-4 bg-green-50 border-green-300">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Card>
          <CardContent className="p-0">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50">
                    <TableHead className="font-bold">이메일</TableHead>
                    <TableHead className="font-bold">이름</TableHead>
                    <TableHead className="font-bold">역할</TableHead>
                    <TableHead className="font-bold">상태</TableHead>
                    <TableHead className="font-bold">가입일</TableHead>
                    <TableHead className="font-bold">마지막 로그인</TableHead>
                    <TableHead className="text-center font-bold">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member) => (
                    <TableRow key={member.id} className="hover:bg-gray-50">
                      <TableCell>{member.email}</TableCell>
                      <TableCell>{member.full_name || '-'}</TableCell>
                      <TableCell>
                        <Badge className={getRoleBadgeClass(member.role)}>
                          {getRoleLabel(member.role)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={member.is_active ? 'default' : 'secondary'}
                          className={member.is_active ? 'bg-green-600' : ''}
                        >
                          {member.is_active ? '활성' : '비활성'}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(member.created_at)}</TableCell>
                      <TableCell>{formatDate(member.last_login)}</TableCell>
                      <TableCell className="text-center">
                        <div className="flex justify-center gap-1">
                          {canEditRole && member.role !== 'owner' && member.id !== user?.id && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setSelectedMember(member);
                                setNewRole(member.role);
                                setRoleDialogOpen(true);
                              }}
                              title="역할 변경"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                          {canDelete && member.role !== 'owner' && member.id !== user?.id && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => {
                                setSelectedMember(member);
                                setDeleteDialogOpen(true);
                              }}
                              title="팀원 제거"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* 팀원 초대 다이얼로그 */}
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>팀원 초대</DialogTitle>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="invite-email">이메일 *</Label>
                <Input
                  id="invite-email"
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  placeholder="email@example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-name">이름 *</Label>
                <Input
                  id="invite-name"
                  value={inviteData.full_name}
                  onChange={(e) => setInviteData({ ...inviteData, full_name: e.target.value })}
                  placeholder="홍길동"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-password">초기 비밀번호 *</Label>
                <Input
                  id="invite-password"
                  type="password"
                  value={inviteData.password}
                  onChange={(e) => setInviteData({ ...inviteData, password: e.target.value })}
                  placeholder="최소 8자 이상"
                />
                <p className="text-xs text-muted-foreground">최소 8자 이상</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-role">역할 *</Label>
                <Select
                  value={inviteData.role}
                  onValueChange={(value) => setInviteData({ ...inviteData, role: value as 'admin' | 'member' })}
                >
                  <SelectTrigger id="invite-role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="member">멤버</SelectItem>
                    <SelectItem value="admin">관리자</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setInviteDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleInvite}>초대</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 역할 변경 다이얼로그 */}
        <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>역할 변경</DialogTitle>
              <DialogDescription>
                {selectedMember?.email}의 역할을 변경합니다
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="change-role">역할</Label>
                <Select
                  value={newRole}
                  onValueChange={(value) => setNewRole(value as 'owner' | 'admin' | 'member')}
                >
                  <SelectTrigger id="change-role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owner">소유자</SelectItem>
                    <SelectItem value="admin">관리자</SelectItem>
                    <SelectItem value="member">멤버</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setRoleDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleRoleChange}>변경</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 팀원 제거 확인 다이얼로그 */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>팀원 제거</DialogTitle>
              <DialogDescription>
                {selectedMember?.email}을(를) 팀에서 제거하시겠습니까?
              </DialogDescription>
            </DialogHeader>

            <p className="text-sm text-red-600 py-4">이 작업은 되돌릴 수 없습니다.</p>

            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                취소
              </Button>
              <Button variant="destructive" onClick={handleDelete}>
                제거
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default TeamManagementPage;
