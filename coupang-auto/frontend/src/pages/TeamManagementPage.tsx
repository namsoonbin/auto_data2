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
import { useTheme } from '../contexts/ThemeContext';

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
  const { theme } = useTheme();
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
    if (theme === 'dark') {
      const darkRoleColors: Record<string, string> = {
        owner: 'bg-red-500/30 text-red-400 border-red-500/50',
        admin: 'bg-amber-500/30 text-amber-400 border-amber-500/50',
        member: 'bg-blue-500/30 text-blue-400 border-blue-500/50',
      };
      return darkRoleColors[role] || 'bg-blue-500/30 text-blue-400 border-blue-500/50';
    } else {
      const roleColors: Record<string, string> = {
        owner: 'bg-red-600',
        admin: 'bg-amber-500',
        member: 'bg-blue-600',
      };
      return roleColors[role] || 'bg-blue-600';
    }
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
      <div className={`min-h-screen p-4 ${
        theme === 'dark'
          ? 'bg-[#0f1115]'
          : 'bg-gray-50'
      }`}>
        <div className="flex justify-center items-center min-h-[400px]">
          <Loader2 className={`h-8 w-8 animate-spin ${
            theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
          }`} />
        </div>
      </div>
    );
  }

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

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className={`flex items-center gap-2 text-3xl font-bold ${
            theme === 'dark' ? 'text-white' : 'text-black'
          }`}>
            <Users className={`h-8 w-8 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
            팀 관리
          </h1>
          {canInvite && (
            <Button
              onClick={() => setInviteDialogOpen(true)}
              className={theme === 'dark'
                ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                : ''
              }
            >
              <UserPlus className="h-4 w-4 mr-2" />
              팀원 초대
            </Button>
          )}
        </div>

        {success && (
          <Alert className={`mb-4 ${
            theme === 'dark'
              ? 'bg-green-950/20 border-green-500/30'
              : 'bg-green-50 border-green-300'
          }`}>
            <CheckCircle2 className={`h-4 w-4 ${
              theme === 'dark' ? 'text-green-400' : 'text-green-600'
            }`} />
            <AlertDescription className={theme === 'dark' ? 'text-green-400' : 'text-green-800'}>{success}</AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive" className={`mb-4 ${
            theme === 'dark' ? 'bg-red-950/20 border-red-500/30 text-red-400' : ''
          }`}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Card className={`shadow-lg ${
          theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
        }`}>
          <CardContent className="p-0">
            <div className={`rounded-md border ${
              theme === 'dark' ? 'border-gray-800' : ''
            }`}>
              <Table>
                <TableHeader>
                  <TableRow className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50'}>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>이메일</TableHead>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>이름</TableHead>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>역할</TableHead>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>상태</TableHead>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>가입일</TableHead>
                    <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>마지막 로그인</TableHead>
                    <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {members.map((member) => (
                    <TableRow key={member.id} className={theme === 'dark'
                      ? 'hover:bg-gray-900/30 border-gray-800'
                      : 'hover:bg-gray-50'
                    }>
                      <TableCell className={theme === 'dark' ? 'text-white' : ''}>
                        {member.email}
                      </TableCell>
                      <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                        {member.full_name || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={getRoleBadgeClass(member.role)}>
                          {getRoleLabel(member.role)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={member.is_active ? 'default' : 'secondary'}
                          className={member.is_active
                            ? (theme === 'dark' ? 'bg-green-500/30 text-green-400 border-green-500/50' : 'bg-green-600')
                            : (theme === 'dark' ? 'bg-gray-500/30 text-gray-400 border-gray-500/50' : '')
                          }
                        >
                          {member.is_active ? '활성' : '비활성'}
                        </Badge>
                      </TableCell>
                      <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                        {formatDate(member.created_at)}
                      </TableCell>
                      <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                        {formatDate(member.last_login)}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex justify-center gap-1">
                          {canEditRole && member.role !== 'owner' && member.id !== user?.id && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className={theme === 'dark'
                                ? 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10'
                                : ''
                              }
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
                              className={theme === 'dark'
                                ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                                : 'text-red-600 hover:text-red-700 hover:bg-red-50'
                              }
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
          <DialogContent className={`max-w-md ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                팀원 초대
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="invite-email" className={theme === 'dark' ? 'text-gray-300' : ''}>
                  이메일 *
                </Label>
                <Input
                  id="invite-email"
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  placeholder="email@example.com"
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-name" className={theme === 'dark' ? 'text-gray-300' : ''}>
                  이름 *
                </Label>
                <Input
                  id="invite-name"
                  value={inviteData.full_name}
                  onChange={(e) => setInviteData({ ...inviteData, full_name: e.target.value })}
                  placeholder="홍길동"
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-password" className={theme === 'dark' ? 'text-gray-300' : ''}>
                  초기 비밀번호 *
                </Label>
                <Input
                  id="invite-password"
                  type="password"
                  value={inviteData.password}
                  onChange={(e) => setInviteData({ ...inviteData, password: e.target.value })}
                  placeholder="최소 8자 이상"
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
                <p className={`text-xs ${
                  theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                }`}>최소 8자 이상</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="invite-role" className={theme === 'dark' ? 'text-gray-300' : ''}>
                  역할 *
                </Label>
                <Select
                  value={inviteData.role}
                  onValueChange={(value) => setInviteData({ ...inviteData, role: value as 'admin' | 'member' })}
                >
                  <SelectTrigger id="invite-role" className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white focus:border-cyan-500/50'
                    : ''
                  }>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''}>
                    <SelectItem value="member" className={theme === 'dark' ? 'text-white hover:bg-gray-800' : ''}>
                      멤버
                    </SelectItem>
                    <SelectItem value="admin" className={theme === 'dark' ? 'text-white hover:bg-gray-800' : ''}>
                      관리자
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setInviteDialogOpen(false)}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                  : ''
                }
              >
                취소
              </Button>
              <Button
                onClick={handleInvite}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  : ''
                }
              >
                초대
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 역할 변경 다이얼로그 */}
        <Dialog open={roleDialogOpen} onOpenChange={setRoleDialogOpen}>
          <DialogContent className={`max-w-sm ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                역할 변경
              </DialogTitle>
              <DialogDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
                {selectedMember?.email}의 역할을 변경합니다
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="change-role" className={theme === 'dark' ? 'text-gray-300' : ''}>
                  역할
                </Label>
                <Select
                  value={newRole}
                  onValueChange={(value) => setNewRole(value as 'owner' | 'admin' | 'member')}
                >
                  <SelectTrigger id="change-role" className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white focus:border-cyan-500/50'
                    : ''
                  }>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className={theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''}>
                    <SelectItem value="owner" className={theme === 'dark' ? 'text-white hover:bg-gray-800' : ''}>
                      소유자
                    </SelectItem>
                    <SelectItem value="admin" className={theme === 'dark' ? 'text-white hover:bg-gray-800' : ''}>
                      관리자
                    </SelectItem>
                    <SelectItem value="member" className={theme === 'dark' ? 'text-white hover:bg-gray-800' : ''}>
                      멤버
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setRoleDialogOpen(false)}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                  : ''
                }
              >
                취소
              </Button>
              <Button
                onClick={handleRoleChange}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  : ''
                }
              >
                변경
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 팀원 제거 확인 다이얼로그 */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent className={`max-w-sm ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                팀원 제거
              </DialogTitle>
              <DialogDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
                {selectedMember?.email}을(를) 팀에서 제거하시겠습니까?
              </DialogDescription>
            </DialogHeader>

            <p className={`text-sm py-4 ${
              theme === 'dark' ? 'text-red-400' : 'text-red-600'
            }`}>이 작업은 되돌릴 수 없습니다.</p>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteDialogOpen(false)}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                  : ''
                }
              >
                취소
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                className={theme === 'dark' ? 'bg-red-600/80 hover:bg-red-700/80' : ''}
              >
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
