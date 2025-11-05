import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import { Edit as EditIcon, Lock as LockIcon, Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    full_name: '',
    phone: ''
  })
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false)
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/api/auth/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setProfile(response.data)
      setFormData({
        full_name: response.data.full_name || '',
        phone: response.data.phone || ''
      })
      setLoading(false)
    } catch (err) {
      console.error('프로필 조회 실패:', err)
      setError('프로필을 불러오는데 실패했습니다')
      setLoading(false)
    }
  }

  const handleEdit = () => {
    setEditing(true)
    setError('')
    setSuccess('')
  }

  const handleCancel = () => {
    setEditing(false)
    setFormData({
      full_name: profile.full_name || '',
      phone: profile.phone || ''
    })
    setError('')
  }

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.put(
        `${API_BASE_URL}/api/auth/profile`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setProfile(response.data)
      setEditing(false)
      setSuccess('프로필이 성공적으로 수정되었습니다')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('프로필 수정 실패:', err)
      setError(err.response?.data?.detail || '프로필 수정에 실패했습니다')
    }
  }

  const handlePasswordChange = async () => {
    setPasswordError('')
    setPasswordSuccess('')

    // 유효성 검사
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('새 비밀번호가 일치하지 않습니다')
      return
    }

    if (passwordData.new_password.length < 8) {
      setPasswordError('새 비밀번호는 최소 8자 이상이어야 합니다')
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      await axios.put(
        `${API_BASE_URL}/api/auth/password`,
        {
          old_password: passwordData.old_password,
          new_password: passwordData.new_password
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setPasswordSuccess('비밀번호가 성공적으로 변경되었습니다')
      setTimeout(() => {
        setPasswordDialogOpen(false)
        setPasswordData({ old_password: '', new_password: '', confirm_password: '' })
        setPasswordSuccess('')
      }, 2000)
    } catch (err) {
      console.error('비밀번호 변경 실패:', err)
      setPasswordError(err.response?.data?.detail || '비밀번호 변경에 실패했습니다')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR')
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        프로필 관리
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">기본 정보</Typography>
          <Box>
            {!editing ? (
              <>
                <Button
                  variant="outlined"
                  startIcon={<LockIcon />}
                  onClick={() => setPasswordDialogOpen(true)}
                  sx={{ mr: 1 }}
                >
                  비밀번호 변경
                </Button>
                <Button
                  variant="contained"
                  startIcon={<EditIcon />}
                  onClick={handleEdit}
                >
                  수정
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={handleCancel}
                  sx={{ mr: 1 }}
                >
                  취소
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                >
                  저장
                </Button>
              </>
            )}
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              label="이메일"
              value={profile?.email || ''}
              fullWidth
              disabled
              helperText="이메일은 변경할 수 없습니다"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="역할"
              value={profile?.role === 'owner' ? '소유자' : profile?.role === 'admin' ? '관리자' : '멤버'}
              fullWidth
              disabled
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="이름"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              fullWidth
              disabled={!editing}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="전화번호"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              fullWidth
              disabled={!editing}
              placeholder="010-1234-5678"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="가입일"
              value={formatDate(profile?.created_at)}
              fullWidth
              disabled
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="마지막 로그인"
              value={formatDate(profile?.last_login)}
              fullWidth
              disabled
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="계정 상태"
              value={profile?.is_active ? '활성' : '비활성'}
              fullWidth
              disabled
            />
          </Grid>
        </Grid>
      </Paper>

      {/* 비밀번호 변경 다이얼로그 */}
      <Dialog
        open={passwordDialogOpen}
        onClose={() => !passwordSuccess && setPasswordDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>비밀번호 변경</DialogTitle>
        <DialogContent>
          {passwordError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {passwordError}
            </Alert>
          )}

          {passwordSuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {passwordSuccess}
            </Alert>
          )}

          <TextField
            label="현재 비밀번호"
            type="password"
            fullWidth
            value={passwordData.old_password}
            onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
            sx={{ mt: 2, mb: 2 }}
            disabled={!!passwordSuccess}
          />

          <TextField
            label="새 비밀번호"
            type="password"
            fullWidth
            value={passwordData.new_password}
            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
            helperText="최소 8자 이상"
            sx={{ mb: 2 }}
            disabled={!!passwordSuccess}
          />

          <TextField
            label="새 비밀번호 확인"
            type="password"
            fullWidth
            value={passwordData.confirm_password}
            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
            disabled={!!passwordSuccess}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setPasswordDialogOpen(false)
              setPasswordData({ old_password: '', new_password: '', confirm_password: '' })
              setPasswordError('')
              setPasswordSuccess('')
            }}
            disabled={!!passwordSuccess}
          >
            취소
          </Button>
          <Button
            onClick={handlePasswordChange}
            variant="contained"
            disabled={!!passwordSuccess}
          >
            변경
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ProfilePage
