import React, { useState, useEffect, forwardRef } from 'react'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Tabs,
  Tab,
  Badge,
  Grid
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CloudDownload as DownloadIcon,
  CloudUpload as UploadIcon,
  CalendarToday as CalendarIcon,
  Calculate as CalculateIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

// Custom input component for DatePicker
const CustomDateInput = forwardRef(({ value, onClick }, ref) => (
  <TextField
    fullWidth
    label="기간 선택"
    value={value}
    onClick={onClick}
    ref={ref}
    InputProps={{
      readOnly: true,
      endAdornment: <CalendarIcon sx={{ color: 'action.active', mr: 1 }} />
    }}
    sx={{ cursor: 'pointer', minWidth: '280px' }}
  />
))

// Custom header component for DatePicker
const renderCustomHeader = ({
  monthDate,
  decreaseMonth,
  increaseMonth,
  prevMonthButtonDisabled,
  nextMonthButtonDisabled
}) => (
  <Box sx={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    backgroundColor: '#ffffff'
  }}>
    <IconButton
      onClick={decreaseMonth}
      disabled={prevMonthButtonDisabled}
      size="small"
      sx={{ color: '#000000' }}
    >
      <ChevronLeftIcon />
    </IconButton>
    <Typography sx={{ fontWeight: 600, color: '#000000', fontSize: '1.1rem' }}>
      {format(monthDate, 'yyyy년 M월', { locale: ko })}
    </Typography>
    <IconButton
      onClick={increaseMonth}
      disabled={nextMonthButtonDisabled}
      size="small"
      sx={{ color: '#000000' }}
    >
      <ChevronRightIcon />
    </IconButton>
  </Box>
)

function MarginManagementPage() {
  const [margins, setMargins] = useState([])
  const [unmatchedProducts, setUnmatchedProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [tabValue, setTabValue] = useState(0)

  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState('create') // 'create' or 'edit'
  const [currentMargin, setCurrentMargin] = useState(null)

  // Excel upload states
  const [excelFile, setExcelFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)

  // Form states
  const [formData, setFormData] = useState({
    option_id: '',
    product_name: '',
    option_name: '',
    cost_price: 0,
    selling_price: 0,
    margin_rate: 0,
    fee_rate: 0,
    fee_amount: 0,
    vat: 0,
    notes: ''
  })

  // Recalculation states
  const [dateRange, setDateRange] = useState([null, null])
  const [startDate, endDate] = dateRange
  const [recalculating, setRecalculating] = useState(false)
  const [recalcResult, setRecalcResult] = useState(null)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchMargins()
    fetchUnmatchedProducts()
  }, [])

  const fetchMargins = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_BASE_URL}/margins`)
      setMargins(response.data.margins)
    } catch (err) {
      setError('마진 데이터 조회 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const fetchUnmatchedProducts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/margins/unmatched/products?limit=100`)
      setUnmatchedProducts(response.data.unmatched_products)
    } catch (err) {
      console.error('Failed to fetch unmatched products:', err)
    }
  }

  const handleOpenDialog = (mode, margin = null) => {
    setDialogMode(mode)
    if (mode === 'edit' && margin) {
      setCurrentMargin(margin)
      setFormData({
        option_id: margin.option_id,
        product_name: margin.product_name,
        option_name: margin.option_name || '',
        cost_price: margin.cost_price,
        selling_price: margin.selling_price,
        margin_rate: margin.margin_rate,
        fee_rate: margin.fee_rate,
        fee_amount: margin.fee_amount,
        vat: margin.vat,
        notes: margin.notes || ''
      })
    } else if (mode === 'create' && margin) {
      // Creating from unmatched product
      setFormData({
        option_id: margin.option_id,
        product_name: margin.product_name,
        option_name: margin.option_name || '',
        cost_price: 0,
        selling_price: 0,
        margin_rate: 0,
        fee_rate: 0,
        fee_amount: 0,
        vat: 0,
        notes: ''
      })
    } else {
      // Empty form for new margin
      setFormData({
        option_id: '',
        product_name: '',
        option_name: '',
        cost_price: 0,
        selling_price: 0,
        margin_rate: 0,
        fee_rate: 0,
        fee_amount: 0,
        vat: 0,
        notes: ''
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setCurrentMargin(null)
    setError(null)
  }

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async () => {
    setError(null)
    setSuccess(null)

    // Validate required fields
    if (!formData.cost_price || formData.cost_price <= 0) {
      setError('도매가는 필수이며 0보다 커야 합니다')
      return
    }
    if (formData.fee_amount === null || formData.fee_amount === undefined || formData.fee_amount < 0) {
      setError('총 수수료는 필수이며 0 이상이어야 합니다')
      return
    }
    if (formData.vat === null || formData.vat === undefined || formData.vat < 0) {
      setError('부가세는 필수이며 0 이상이어야 합니다')
      return
    }

    try {
      if (dialogMode === 'create') {
        await axios.post(`${API_BASE_URL}/margins`, formData)
        setSuccess('마진 데이터가 성공적으로 추가되었습니다')
      } else {
        await axios.put(`${API_BASE_URL}/margins/${currentMargin.option_id}`, formData)
        setSuccess('마진 데이터가 성공적으로 수정되었습니다')
      }

      handleCloseDialog()
      fetchMargins()
      fetchUnmatchedProducts()
    } catch (err) {
      setError(
        dialogMode === 'create'
          ? '마진 추가 실패: ' + (err.response?.data?.detail || err.message)
          : '마진 수정 실패: ' + (err.response?.data?.detail || err.message)
      )
    }
  }

  const handleDelete = async (optionId) => {
    if (!window.confirm('정말 이 마진 데이터를 삭제하시겠습니까?')) {
      return
    }

    setError(null)
    setSuccess(null)

    try {
      await axios.delete(`${API_BASE_URL}/margins/${optionId}`)
      setSuccess('마진 데이터가 성공적으로 삭제되었습니다')
      fetchMargins()
      fetchUnmatchedProducts()
    } catch (err) {
      setError('마진 삭제 실패: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/margins/template/download`, {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `margin_template_${new Date().toISOString().split('T')[0]}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setSuccess('Excel 템플릿이 다운로드되었습니다')
    } catch (err) {
      setError('템플릿 다운로드 실패: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleExcelFileChange = (event) => {
    const file = event.target.files[0]
    setExcelFile(file)
    setUploadResult(null)
  }

  const handleExcelUpload = async () => {
    if (!excelFile) {
      setError('Excel 파일을 선택해주세요')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', excelFile)

      const response = await axios.post(
        `${API_BASE_URL}/margins/upload/excel?skip_existing=true&update_existing=false`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      setUploadResult(response.data)

      if (response.data.status === 'success') {
        setSuccess(response.data.message)
        setExcelFile(null)
        // Reset file input
        document.getElementById('excel-file-input').value = ''
        fetchMargins()
        fetchUnmatchedProducts()
      } else if (response.data.status === 'partial_success') {
        setError(response.data.message)
      } else {
        setError(response.data.message)
      }
    } catch (err) {
      setError('Excel 업로드 실패: ' + (err.response?.data?.detail || err.message))
      setUploadResult(null)
    } finally {
      setUploading(false)
    }
  }

  const handleDateRangeChange = (update) => {
    const [start, end] = update

    // If same date is clicked twice (or range selected with same date)
    if (start && end && start.toDateString() === end.toDateString()) {
      setDateRange([start, end])
    } else {
      setDateRange(update)
    }
  }

  const handleRecalculate = async () => {
    setRecalculating(true)
    setRecalcResult(null)
    setError(null)
    setSuccess(null)

    try {
      const params = {}
      if (startDate) {
        params.start_date = format(startDate, 'yyyy-MM-dd')
      }
      if (endDate) {
        params.end_date = format(endDate, 'yyyy-MM-dd')
      }

      const response = await axios.post(`${API_BASE_URL}/margins/recalculate`, null, {
        params: params
      })

      setRecalcResult(response.data)
      if (response.data.status === 'success') {
        setSuccess(response.data.message)
      }
    } catch (err) {
      setError('재계산 실패: ' + (err.response?.data?.detail || err.message))
      setRecalcResult(null)
    } finally {
      setRecalculating(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatNumber = (value) => {
    return new Intl.NumberFormat('ko-KR').format(value)
  }

  // Filter margins based on search query
  const filteredMargins = margins.filter(margin => {
    if (!searchQuery) return true

    const query = searchQuery.toLowerCase()
    return (
      margin.option_id.toString().includes(query) ||
      margin.product_name.toLowerCase().includes(query) ||
      (margin.option_name && margin.option_name.toLowerCase().includes(query))
    )
  })

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          마진 관리
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadTemplate}
          >
            템플릿 다운로드
          </Button>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={() => {
              fetchMargins()
              fetchUnmatchedProducts()
            }}
          >
            새로고침
          </Button>
          <Button
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog('create')}
          >
            마진 추가
          </Button>
        </Box>
      </Box>

      {/* Excel Upload Section */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.50', border: '1px solid', borderColor: 'info.main' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'info.main', minWidth: '120px' }}>
            Excel 일괄 업로드
          </Typography>
          <Typography variant="caption" color="error.main" sx={{ fontWeight: 'bold' }}>
            ⚠️ 필수 항목: 도매가, 총 수수료, 부가세 (순이익 계산에 필수)
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <input
            id="excel-file-input"
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={handleExcelFileChange}
          />
          <Button
            variant="outlined"
            size="small"
            component="label"
            htmlFor="excel-file-input"
            startIcon={excelFile ? null : <UploadIcon />}
          >
            {excelFile ? excelFile.name : '파일 선택'}
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleExcelUpload}
            disabled={!excelFile || uploading}
          >
            {uploading ? '업로드 중...' : '업로드'}
          </Button>
          {uploadResult && (
            <Box sx={{ ml: 2 }}>
              <Chip
                label={`생성: ${uploadResult.created} | 건너뜀: ${uploadResult.skipped} | 오류: ${uploadResult.total_errors || 0}`}
                size="small"
                color={uploadResult.status === 'success' ? 'success' : uploadResult.status === 'partial_success' ? 'warning' : 'error'}
              />
            </Box>
          )}
        </Box>
        {uploadResult && uploadResult.errors && uploadResult.errors.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="error">
              오류 목록:
            </Typography>
            {uploadResult.errors.map((err, idx) => (
              <Typography key={idx} variant="caption" display="block" color="error" sx={{ ml: 1 }}>
                • {err}
              </Typography>
            ))}
          </Box>
        )}
      </Paper>

      {/* Margin Recalculation Section */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.main' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <CalculateIcon color="success" />
          <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'success.main' }}>
            마진 데이터 재계산
          </Typography>
        </Box>

        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
          날짜 범위를 선택하여 통합 레코드의 마진 데이터를 현재 마진 정보로 재계산합니다.
          날짜를 선택하지 않으면 전체 데이터가 재계산됩니다.
        </Typography>

        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8} lg={6}>
            <DatePicker
              selectsRange={true}
              startDate={startDate}
              endDate={endDate}
              onChange={handleDateRangeChange}
              customInput={<CustomDateInput />}
              dateFormat="yyyy-MM-dd"
              placeholderText="기간을 선택하세요 (선택사항)"
              isClearable={true}
              monthsShown={2}
              popperPlacement="bottom-start"
              shouldCloseOnSelect={false}
              locale={ko}
              renderCustomHeader={renderCustomHeader}
              maxDate={new Date()}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              color="success"
              onClick={handleRecalculate}
              disabled={recalculating}
              startIcon={recalculating ? <CircularProgress size={20} /> : <CalculateIcon />}
              fullWidth
            >
              {recalculating ? '재계산 중...' : '재계산 실행'}
            </Button>
          </Grid>
        </Grid>

        {recalcResult && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success" sx={{ mb: 1 }}>
              <Typography variant="subtitle2" fontWeight="bold">
                {recalcResult.message}
              </Typography>
            </Alert>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`총 레코드: ${recalcResult.total_records}`}
                size="small"
                color="info"
              />
              <Chip
                label={`업데이트: ${recalcResult.updated_count}`}
                size="small"
                color="success"
              />
              <Chip
                label={`매칭 상품: ${recalcResult.matched_products}`}
                size="small"
                color="primary"
              />
              <Chip
                label={`기간: ${recalcResult.date_range?.start || '전체'} ~ ${recalcResult.date_range?.end || '전체'}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="마진 데이터 목록" />
          <Tab
            label={
              <Badge badgeContent={unmatchedProducts.length} color="error">
                미매칭 상품
              </Badge>
            }
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      {tabValue === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              등록된 마진 데이터 ({filteredMargins.length}개)
              {searchQuery && ` / 전체 ${margins.length}개`}
            </Typography>
          </Box>

          <TextField
            fullWidth
            size="small"
            placeholder="옵션ID, 상품명, 옵션명으로 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <Box component="span" sx={{ mr: 1, color: 'text.secondary' }}>
                  🔍
                </Box>
              )
            }}
          />

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredMargins.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                {searchQuery ? '검색 결과가 없습니다' : '등록된 마진 데이터가 없습니다'}
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.100' }}>
                    <TableCell><strong>옵션ID</strong></TableCell>
                    <TableCell><strong>상품명</strong></TableCell>
                    <TableCell><strong>옵션명</strong></TableCell>
                    <TableCell align="right"><strong>도매가</strong></TableCell>
                    <TableCell align="right"><strong>판매가</strong></TableCell>
                    <TableCell align="right"><strong>마진율</strong></TableCell>
                    <TableCell align="right"><strong>수수료율</strong></TableCell>
                    <TableCell align="center"><strong>작업</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredMargins.map((margin) => (
                    <TableRow
                      key={margin.option_id}
                      sx={{ '&:hover': { bgcolor: 'grey.50' } }}
                    >
                      <TableCell>{margin.option_id}</TableCell>
                      <TableCell>{margin.product_name}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {margin.option_name || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{formatCurrency(margin.cost_price)}</TableCell>
                      <TableCell align="right">{formatCurrency(margin.selling_price)}</TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${margin.margin_rate.toFixed(1)}%`}
                          size="small"
                          color={margin.margin_rate > 30 ? 'success' : margin.margin_rate > 15 ? 'warning' : 'error'}
                        />
                      </TableCell>
                      <TableCell align="right">{margin.fee_rate.toFixed(1)}%</TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleOpenDialog('edit', margin)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(margin.option_id)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
            <WarningIcon color="error" />
            <Typography variant="h6">
              마진 데이터가 없는 상품 ({unmatchedProducts.length}개)
            </Typography>
          </Box>

          <Alert severity="warning" sx={{ mb: 3 }}>
            아래 상품들은 매출 데이터는 있지만 마진 정보가 등록되지 않아 정확한 수익 계산이 불가능합니다.
            매출액이 높은 순서로 표시됩니다.
          </Alert>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : unmatchedProducts.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="success.main" variant="h6">
                모든 상품에 마진 데이터가 등록되어 있습니다!
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'error.50' }}>
                    <TableCell><strong>옵션ID</strong></TableCell>
                    <TableCell><strong>상품명</strong></TableCell>
                    <TableCell><strong>옵션명</strong></TableCell>
                    <TableCell align="right"><strong>매출액</strong></TableCell>
                    <TableCell align="right"><strong>판매량</strong></TableCell>
                    <TableCell align="center"><strong>작업</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {unmatchedProducts.map((product) => (
                    <TableRow
                      key={product.option_id}
                      sx={{ '&:hover': { bgcolor: 'grey.50' } }}
                    >
                      <TableCell>{product.option_id}</TableCell>
                      <TableCell>{product.product_name}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {product.option_name || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <strong>{formatCurrency(product.sales_amount)}</strong>
                      </TableCell>
                      <TableCell align="right">{formatNumber(product.sales_quantity)}</TableCell>
                      <TableCell align="center">
                        <Button
                          size="small"
                          variant="contained"
                          color="error"
                          startIcon={<AddIcon />}
                          onClick={() => handleOpenDialog('create', product)}
                        >
                          마진 추가
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? '마진 데이터 추가' : '마진 데이터 수정'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="옵션 ID"
              value={formData.option_id}
              onChange={(e) => handleFormChange('option_id', e.target.value)}
              fullWidth
              disabled={dialogMode === 'edit'}
              required
            />
            <TextField
              label="상품명"
              value={formData.product_name}
              onChange={(e) => handleFormChange('product_name', e.target.value)}
              fullWidth
              required
            />
            <TextField
              label="옵션명"
              value={formData.option_name}
              onChange={(e) => handleFormChange('option_name', e.target.value)}
              fullWidth
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="도매가 (원)"
                type="number"
                value={formData.cost_price}
                onChange={(e) => handleFormChange('cost_price', parseFloat(e.target.value) || 0)}
                fullWidth
                required
                helperText="필수: 순이익 계산에 사용됩니다"
                error={formData.cost_price <= 0}
              />
              <TextField
                label="판매가 (원)"
                type="number"
                value={formData.selling_price}
                onChange={(e) => handleFormChange('selling_price', parseFloat(e.target.value) || 0)}
                fullWidth
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="마진율 (%)"
                type="number"
                value={formData.margin_rate}
                onChange={(e) => handleFormChange('margin_rate', parseFloat(e.target.value) || 0)}
                fullWidth
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="총 수수료율 (%)"
                type="number"
                value={formData.fee_rate}
                onChange={(e) => handleFormChange('fee_rate', parseFloat(e.target.value) || 0)}
                fullWidth
              />
              <TextField
                label="총 수수료 (원)"
                type="number"
                value={formData.fee_amount}
                onChange={(e) => handleFormChange('fee_amount', parseFloat(e.target.value) || 0)}
                fullWidth
                required
                helperText="필수: 순이익 계산에 사용됩니다"
              />
            </Box>
            <TextField
              label="부가세 (원)"
              type="number"
              value={formData.vat}
              onChange={(e) => handleFormChange('vat', parseFloat(e.target.value) || 0)}
              fullWidth
              required
              helperText="필수: 순이익 계산에 사용됩니다"
            />
            <TextField
              label="메모"
              value={formData.notes}
              onChange={(e) => handleFormChange('notes', e.target.value)}
              fullWidth
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>취소</Button>
          <Button onClick={handleSubmit} variant="contained">
            {dialogMode === 'create' ? '추가' : '수정'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default MarginManagementPage
