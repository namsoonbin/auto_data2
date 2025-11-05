import React, { useState } from 'react'
import {
  Paper,
  Typography,
  Button,
  Box,
  LinearProgress,
  Alert
} from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import axios from 'axios'

function UploadForm({ title, type, onUploadComplete, description }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setError('파일을 선택해주세요.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    // 엔드포인트 매핑
    const endpoints = {
      sales: '/api/upload/sales',
      ads: '/api/upload/ads',
      products: '/api/upload/products'
    }

    setLoading(true)
    setError(null)

    try {
      const res = await axios.post(endpoints[type], formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // 업로드 완료 콜백
      if (onUploadComplete) {
        onUploadComplete(res.data)
      }

      // 파일 초기화
      setFile(null)
      // 파일 input 초기화
      const fileInput = document.getElementById(`file-input-${type}`)
      if (fileInput) fileInput.value = ''

    } catch (err) {
      console.error('Upload error', err)
      setError(err.response?.data?.message || '업로드 중 오류가 발생했습니다.')

      if (onUploadComplete) {
        onUploadComplete({
          status: 'error',
          message: err.response?.data?.message || '업로드 실패',
          records: 0,
          errors: [err.message]
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>

      <Typography variant="body2" color="text.secondary" gutterBottom>
        {description}
      </Typography>

      <Box sx={{ mt: 2, mb: 2 }}>
        <input
          id={`file-input-${type}`}
          type="file"
          accept=".xlsx, .xls, .csv"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        <label htmlFor={`file-input-${type}`}>
          <Button
            variant="outlined"
            component="span"
            fullWidth
            startIcon={<CloudUploadIcon />}
          >
            파일 선택
          </Button>
        </label>
      </Box>

      {file && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          선택된 파일: {file.name}
        </Typography>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Button
        variant="contained"
        fullWidth
        onClick={handleUpload}
        disabled={!file || loading}
        sx={{ mt: 2 }}
      >
        {loading ? '업로드 중...' : '업로드'}
      </Button>

      {loading && <LinearProgress sx={{ mt: 2 }} />}
    </Paper>
  )
}

export default UploadForm
