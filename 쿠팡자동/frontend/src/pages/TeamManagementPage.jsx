import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress
} from '@mui/material'
import {
  PersonAdd as PersonAddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Group as GroupIcon
} from '@mui/icons-material'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

const API_BASE_URL = 'http://localhost:8000'

function TeamManagementPage() {
  const { user } = useAuth()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false)
  const [roleDialogOpen, setRoleDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedMember, setSelectedMember] = useState(null)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const [inviteData, setInviteData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'member'
  })

  const [newRole, setNewRole] = useState('')

  useEffect(() => {
    fetchMembers()
  }, [])

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/api/team/members`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setMembers(response.data.members)
      setLoading(false)
    } catch (err) {
      console.error('팀원 조회 실패:', err)
      setError('팀원 목록을 불러오는데 실패했습니다')
      setLoading(false)
    }
  }

  const handleInvite = async () => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.post(
        `${API_BASE_URL}/api/team/members`,
        inviteData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setSuccess('팀원이 성공적으로 초대되었습니다')
      setInviteDialogOpen(false)
      setInviteData({ email: '', full_name: '', password: '', role: 'member' })
      fetchMembers()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('팀원 초대 실패:', err)
      setError(err.response?.data?.detail || '팀원 초대에 실패했습니다')
    }
  }

  const handleRoleChange = async () => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.put(
        `${API_BASE_URL}/api/team/members/${selectedMember.id}/role`,
        { role: newRole },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setSuccess('역할이 성공적으로 변경되었습니다')
      setRoleDialogOpen(false)
      setSelectedMember(null)
      fetchMembers()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('역할 변경 실패:', err)
      setError(err.response?.data?.detail || '역할 변경에 실패했습니다')
    }
  }

  const handleDelete = async () => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.delete(
        `${API_BASE_URL}/api/team/members/${selectedMember.id}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setSuccess('팀원이 성공적으로 제거되었습니다')
      setDeleteDialogOpen(false)
      setSelectedMember(null)
      fetchMembers()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('팀원 제거 실패:', err)
      setError(err.response?.data?.detail || '팀원 제거에 실패했습니다')
    }
  }

  const getRoleLabel = (role) => {
    const roleLabels = {
      'owner': '소유자',
      'admin': '관리자',
      'member': '멤버'
    }
    return roleLabels[role] || role
  }

  const getRoleColor = (role) => {
    const roleColors = {
      'owner': 'error',
      'admin': 'warning',
      'member': 'default'
    }
    return roleColors[role] || 'default'
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR')
  }

  const canInvite = user?.role === 'owner' || user?.role === 'admin'
  const canEditRole = user?.role === 'owner'
  const canDelete = user?.role === 'owner' || user?.role === 'admin'

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <GroupIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Typography variant="h4">
            팀 관리
          </Typography>
        </Box>
        {canInvite && (
          <Button
            variant="contained"
            startIcon={<PersonAddIcon />}
            onClick={() => setInviteDialogOpen(true)}
          >
            팀원 초대
          </Button>
        )}
      </Box>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>이메일</TableCell>
                <TableCell>이름</TableCell>
                <TableCell>역할</TableCell>
                <TableCell>상태</TableCell>
                <TableCell>가입일</TableCell>
                <TableCell>마지막 로그인</TableCell>
                <TableCell align="center">작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {members.map((member) => (
                <TableRow key={member.id}>
                  <TableCell>{member.email}</TableCell>
                  <TableCell>{member.full_name || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={getRoleLabel(member.role)}
                      color={getRoleColor(member.role)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={member.is_active ? '활성' : '비활성'}
                      color={member.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(member.created_at)}</TableCell>
                  <TableCell>{formatDate(member.last_login)}</TableCell>
                  <TableCell align="center">
                    {canEditRole && member.role !== 'owner' && member.id !== user?.id && (
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedMember(member)
                          setNewRole(member.role)
                          setRoleDialogOpen(true)
                        }}
                        title="역할 변경"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}
                    {canDelete && member.role !== 'owner' && member.id !== user?.id && (
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedMember(member)
                          setDeleteDialogOpen(true)
                        }}
                        title="팀원 제거"
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* 팀원 초대 다이얼로그 */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>팀원 초대</DialogTitle>
        <DialogContent>
          <TextField
            label="이메일"
            type="email"
            fullWidth
            value={inviteData.email}
            onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
            required
          />
          <TextField
            label="이름"
            fullWidth
            value={inviteData.full_name}
            onChange={(e) => setInviteData({ ...inviteData, full_name: e.target.value })}
            sx={{ mb: 2 }}
            required
          />
          <TextField
            label="초기 비밀번호"
            type="password"
            fullWidth
            value={inviteData.password}
            onChange={(e) => setInviteData({ ...inviteData, password: e.target.value })}
            helperText="최소 8자 이상"
            sx={{ mb: 2 }}
            required
          />
          <FormControl fullWidth>
            <InputLabel>역할</InputLabel>
            <Select
              value={inviteData.role}
              label="역할"
              onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
            >
              <MenuItem value="member">멤버</MenuItem>
              <MenuItem value="admin">관리자</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>취소</Button>
          <Button onClick={handleInvite} variant="contained">초대</Button>
        </DialogActions>
      </Dialog>

      {/* 역할 변경 다이얼로그 */}
      <Dialog open={roleDialogOpen} onClose={() => setRoleDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>역할 변경</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {selectedMember?.email}의 역할을 변경합니다
          </Typography>
          <FormControl fullWidth>
            <InputLabel>역할</InputLabel>
            <Select
              value={newRole}
              label="역할"
              onChange={(e) => setNewRole(e.target.value)}
            >
              <MenuItem value="owner">소유자</MenuItem>
              <MenuItem value="admin">관리자</MenuItem>
              <MenuItem value="member">멤버</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRoleDialogOpen(false)}>취소</Button>
          <Button onClick={handleRoleChange} variant="contained">변경</Button>
        </DialogActions>
      </Dialog>

      {/* 팀원 제거 확인 다이얼로그 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>팀원 제거</DialogTitle>
        <DialogContent>
          <Typography>
            {selectedMember?.email}을(를) 팀에서 제거하시겠습니까?
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 1 }}>
            이 작업은 되돌릴 수 없습니다.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>취소</Button>
          <Button onClick={handleDelete} variant="contained" color="error">제거</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default TeamManagementPage
