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
  Chip
} from '@mui/material'
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Store as StoreIcon
} from '@mui/icons-material'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'

const API_BASE_URL = 'http://localhost:8000'

function TenantSettingsPage() {
  const { tenant: authTenant, refreshTenant } = useAuth()
  const [tenant, setTenant] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    name: ''
  })
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTenant()
  }, [])

  const fetchTenant = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`${API_BASE_URL}/api/auth/tenant`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setTenant(response.data)
      setFormData({
        name: response.data.name
      })
      setLoading(false)
    } catch (err) {
      console.error('테넌트 조회 실패:', err)
      setError('테넌트 정보를 불러오는데 실패했습니다')
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
      name: tenant.name
    })
    setError('')
  }

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.put(
        `${API_BASE_URL}/api/auth/tenant`,
        formData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )
      setTenant(response.data)
      setEditing(false)
      setSuccess('테넌트 정보가 성공적으로 수정되었습니다')

      // AuthContext의 tenant 정보도 업데이트
      if (refreshTenant) {
        await refreshTenant()
      }

      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('테넌트 수정 실패:', err)
      setError(err.response?.data?.detail || '테넌트 정보 수정에 실패했습니다')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR')
  }

  const getPlanLabel = (plan) => {
    const planLabels = {
      'basic': '베이직',
      'pro': '프로',
      'enterprise': '엔터프라이즈'
    }
    return planLabels[plan] || plan
  }

  const getPlanColor = (plan) => {
    const planColors = {
      'basic': 'default',
      'pro': 'primary',
      'enterprise': 'success'
    }
    return planColors[plan] || 'default'
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
      <Box display="flex" alignItems="center" mb={3}>
        <StoreIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Typography variant="h4">
          테넌트 설정
        </Typography>
      </Box>

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
              <Button
                variant="contained"
                startIcon={<EditIcon />}
                onClick={handleEdit}
              >
                수정
              </Button>
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
              label="쇼핑몰 이름"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              disabled={!editing}
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="슬러그 (URL)"
              value={tenant?.slug || ''}
              fullWidth
              disabled
              helperText="슬러그는 변경할 수 없습니다"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                플랜
              </Typography>
              <Chip
                label={getPlanLabel(tenant?.plan)}
                color={getPlanColor(tenant?.plan)}
                sx={{ mt: 1 }}
              />
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="상태"
              value={tenant?.is_active ? '활성' : '비활성'}
              fullWidth
              disabled
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="생성일"
              value={formatDate(tenant?.created_at)}
              fullWidth
              disabled
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="테넌트 ID"
              value={tenant?.id || ''}
              fullWidth
              disabled
              helperText="시스템 내부 ID"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          데이터 통계
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box textAlign="center" p={2} sx={{ bgcolor: 'primary.light', borderRadius: 2 }}>
              <Typography variant="h4" color="primary.contrastText">
                {authTenant?.name || '-'}
              </Typography>
              <Typography variant="body2" color="primary.contrastText" mt={1}>
                현재 쇼핑몰
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box textAlign="center" p={2} sx={{ bgcolor: 'success.light', borderRadius: 2 }}>
              <Typography variant="h4" color="success.contrastText">
                {getPlanLabel(tenant?.plan)}
              </Typography>
              <Typography variant="body2" color="success.contrastText" mt={1}>
                현재 플랜
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box textAlign="center" p={2} sx={{ bgcolor: 'info.light', borderRadius: 2 }}>
              <Typography variant="h4" color="info.contrastText">
                {tenant?.is_active ? '활성' : '비활성'}
              </Typography>
              <Typography variant="body2" color="info.contrastText" mt={1}>
                계정 상태
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  )
}

export default TenantSettingsPage
