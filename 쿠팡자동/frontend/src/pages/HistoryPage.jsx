import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  History as HistoryIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import axios from 'axios'

function HistoryPage() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get('http://localhost:8000/api/upload/history')
      setHistory(response.data.uploads || [])
    } catch (err) {
      setError(err.response?.data?.message || '히스토리 조회 실패')
      console.error('Failed to fetch history:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (uploadId) => {
    if (!window.confirm('이 업로드 기록을 삭제하시겠습니까?')) {
      return
    }

    try {
      await axios.delete(`http://localhost:8000/api/upload/history/${uploadId}`)
      fetchHistory() // Refresh list
    } catch (err) {
      alert('삭제 실패: ' + (err.response?.data?.message || err.message))
    }
  }

  const getStatusChip = (status) => {
    if (status === 'success') {
      return (
        <Chip
          icon={<SuccessIcon />}
          label="성공"
          color="success"
          size="small"
        />
      )
    } else {
      return (
        <Chip
          icon={<ErrorIcon />}
          label="실패"
          color="error"
          size="small"
        />
      )
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon fontSize="large" />
          업로드 히스토리
        </Typography>
        <Tooltip title="새로고침">
          <IconButton onClick={fetchHistory} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Typography variant="body1" color="text.secondary" paragraph>
        과거 업로드한 파일 목록과 통합 결과를 확인할 수 있습니다
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : history.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <HistoryIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            업로드 기록이 없습니다
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            파일을 업로드하면 여기에 기록이 표시됩니다
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>업로드 시간</strong></TableCell>
                <TableCell><strong>판매 파일</strong></TableCell>
                <TableCell><strong>광고 파일</strong></TableCell>
                <TableCell><strong>마진 파일</strong></TableCell>
                <TableCell align="center"><strong>총 레코드</strong></TableCell>
                <TableCell align="center"><strong>광고 매칭</strong></TableCell>
                <TableCell align="center"><strong>마진 매칭</strong></TableCell>
                <TableCell align="center"><strong>완전 통합</strong></TableCell>
                <TableCell align="center"><strong>상태</strong></TableCell>
                <TableCell align="center"><strong>작업</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.map((upload) => (
                <TableRow key={upload.id} hover>
                  <TableCell>{formatDate(upload.uploaded_at)}</TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {upload.sales_filename}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {upload.ads_filename}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {upload.margin_filename}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">{upload.total_records || 0}</TableCell>
                  <TableCell align="center">{upload.matched_with_ads || 0}</TableCell>
                  <TableCell align="center">{upload.matched_with_margin || 0}</TableCell>
                  <TableCell align="center">
                    <Typography variant="body2" fontWeight="bold" color="success.main">
                      {upload.fully_integrated || 0}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">{getStatusChip(upload.status)}</TableCell>
                  <TableCell align="center">
                    <Tooltip title="삭제">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(upload.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {history.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            총 {history.length}개의 업로드 기록
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default HistoryPage
