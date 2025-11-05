import React, { useState, forwardRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  TextField,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Stack,
  IconButton
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Analytics as AnalyticsIcon,
  CalendarToday as CalendarIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import axios from 'axios'

// Custom input component for DatePicker
const CustomDateInput = forwardRef(({ value, onClick }, ref) => (
  <TextField
    fullWidth
    label="데이터 날짜 (선택사항)"
    value={value}
    onClick={onClick}
    ref={ref}
    InputProps={{
      readOnly: true,
      endAdornment: <CalendarIcon sx={{ color: 'action.active', mr: 1 }} />
    }}
    sx={{ cursor: 'pointer', minWidth: '280px' }}
    helperText="비워두면 오늘 날짜가 사용됩니다"
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

function HomePage() {
  const [salesFile, setSalesFile] = useState(null)
  const [adsFile, setAdsFile] = useState(null)
  const [dataDate, setDataDate] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)

  const handleFileChange = (setter) => (event) => {
    const file = event.target.files[0]
    setter(file)
  }

  const handleUpload = async () => {
    if (!salesFile || !adsFile) {
      setUploadResult({
        status: 'error',
        message: '판매 데이터와 광고 데이터 파일을 선택해주세요',
        warnings: ['통합을 위해 두 파일이 모두 필요합니다']
      })
      return
    }

    setUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('sales_file', salesFile)
      formData.append('ads_file', adsFile)
      if (dataDate) {
        formData.append('data_date', format(dataDate, 'yyyy-MM-dd'))
      }

      const response = await axios.post('http://localhost:8000/api/upload/integrated', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setUploadResult(response.data)

      // Clear files on success
      if (response.data.status === 'success') {
        setSalesFile(null)
        setAdsFile(null)
        setDataDate('')
        // Reset file inputs
        document.getElementById('sales-file-input').value = ''
        document.getElementById('ads-file-input').value = ''
      }
    } catch (error) {
      setUploadResult({
        status: 'error',
        message: error.response?.data?.message || error.message || '업로드 실패',
        total_records: 0,
        matched_with_ads: 0,
        matched_with_margin: 0,
        fully_integrated: 0,
        warnings: [error.response?.data?.detail || '알 수 없는 오류']
      })
    } finally {
      setUploading(false)
    }
  }

  const allFilesSelected = salesFile && adsFile

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AnalyticsIcon fontSize="large" />
        쿠팡 판매 데이터 통합
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        판매, 광고 데이터를 업로드하세요. 마진 데이터는 마진 관리 페이지에서 미리 등록된 데이터를 자동으로 불러옵니다.
      </Typography>

      {/* Upload Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            파일 업로드
          </Typography>

          <Grid container spacing={3}>
            {/* Sales File */}
            <Grid item xs={12} md={6}>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  textAlign: 'center',
                  bgcolor: salesFile ? 'success.50' : 'background.default',
                  borderColor: salesFile ? 'success.main' : 'divider'
                }}
              >
                <Typography variant="subtitle2" gutterBottom>
                  Sales Data (판매 데이터)
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                  옵션 ID, 옵션명, 상품명, 매출, 판매량
                </Typography>
                <Button
                  variant={salesFile ? 'outlined' : 'contained'}
                  component="label"
                  startIcon={salesFile ? <SuccessIcon /> : <UploadIcon />}
                  color={salesFile ? 'success' : 'primary'}
                  fullWidth
                >
                  {salesFile ? salesFile.name : '파일 선택'}
                  <input
                    id="sales-file-input"
                    type="file"
                    accept=".xlsx,.xls"
                    hidden
                    onChange={handleFileChange(setSalesFile)}
                  />
                </Button>
              </Paper>
            </Grid>

            {/* Ads File */}
            <Grid item xs={12} md={6}>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  textAlign: 'center',
                  bgcolor: adsFile ? 'success.50' : 'background.default',
                  borderColor: adsFile ? 'success.main' : 'divider'
                }}
              >
                <Typography variant="subtitle2" gutterBottom>
                  Advertising Data (광고 데이터)
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                  광고 집행 옵션 ID, 광고비, 노출수, 클릭수
                </Typography>
                <Button
                  variant={adsFile ? 'outlined' : 'contained'}
                  component="label"
                  startIcon={adsFile ? <SuccessIcon /> : <UploadIcon />}
                  color={adsFile ? 'success' : 'primary'}
                  fullWidth
                >
                  {adsFile ? adsFile.name : '파일 선택'}
                  <input
                    id="ads-file-input"
                    type="file"
                    accept=".xlsx,.xls"
                    hidden
                    onChange={handleFileChange(setAdsFile)}
                  />
                </Button>
              </Paper>
            </Grid>

            {/* Date Input */}
            <Grid item xs={12}>
              <DatePicker
                selected={dataDate}
                onChange={(date) => setDataDate(date)}
                customInput={<CustomDateInput />}
                dateFormat="yyyy-MM-dd"
                placeholderText="날짜를 선택하세요"
                isClearable={true}
                locale={ko}
                renderCustomHeader={renderCustomHeader}
                maxDate={new Date()}
              />
            </Grid>

            {/* Upload Button */}
            <Grid item xs={12}>
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleUpload}
                disabled={!allFilesSelected || uploading}
                startIcon={<UploadIcon />}
                sx={{ py: 1.5 }}
              >
                {uploading ? '업로드 중...' : '파일 업로드 및 통합'}
              </Button>
            </Grid>
          </Grid>

          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                파일 처리 및 통합 중...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Upload Results */}
      {uploadResult && (
        <Card>
          <CardContent>
            <Alert
              severity={uploadResult.status === 'success' ? 'success' : 'error'}
              sx={{ mb: 3 }}
              icon={uploadResult.status === 'success' ? <SuccessIcon /> : <ErrorIcon />}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                {uploadResult.message}
              </Typography>
            </Alert>

            {uploadResult.status === 'success' && (
              <>
                <Typography variant="h6" gutterBottom>
                  통합 통계
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="primary.main">
                        {uploadResult.total_records}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        총 레코드
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="info.main">
                        {uploadResult.matched_with_ads}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        광고 매칭
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {uploadResult.matched_with_margin}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        마진 매칭
                      </Typography>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', bgcolor: 'success.50' }}>
                      <Typography variant="h4" color="success.main" fontWeight="bold">
                        {uploadResult.fully_integrated}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        완전 통합
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    매칭률:
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    <Chip
                      label={`광고: ${((uploadResult.matched_with_ads / uploadResult.total_records) * 100).toFixed(1)}%`}
                      size="small"
                      color="info"
                    />
                    <Chip
                      label={`마진: ${((uploadResult.matched_with_margin / uploadResult.total_records) * 100).toFixed(1)}%`}
                      size="small"
                      color="warning"
                    />
                    <Chip
                      label={`완료: ${((uploadResult.fully_integrated / uploadResult.total_records) * 100).toFixed(1)}%`}
                      size="small"
                      color="success"
                    />
                  </Stack>
                </Box>
              </>
            )}

            {uploadResult.warnings && uploadResult.warnings.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" color="warning.main" gutterBottom>
                  경고:
                </Typography>
                {uploadResult.warnings.map((warning, index) => (
                  <Alert key={index} severity="warning" sx={{ mt: 1 }}>
                    {warning}
                  </Alert>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      <Paper sx={{ p: 3, mt: 4, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          사용 방법
        </Typography>
        <Typography variant="body2" component="div">
          <ol>
            <li>
              <strong>마진 데이터 먼저 등록:</strong> 마진 관리 페이지에서 상품별 마진 데이터를 미리 등록하세요
            </li>
            <li>
              <strong>판매 데이터 다운로드:</strong>
              <ul style={{ marginTop: '8px', marginBottom: '8px' }}>
                <li>쿠팡윙 비즈니스 인사이트 접속</li>
                <li>판매분석 메뉴 선택</li>
                <li>하루치 날짜 선택 (예: 2025-01-15 ~ 2025-01-15)</li>
                <li>엑셀 다운로드 버튼 클릭</li>
                <li>"상품별" 엑셀 다운로드 선택</li>
              </ul>
            </li>
            <li>
              <strong>광고 데이터 다운로드:</strong>
              <ul style={{ marginTop: '8px', marginBottom: '8px' }}>
                <li>쿠팡윙 광고센터 접속</li>
                <li>광고보고서 → 내 보고서 템플릿 선택</li>
                <li>특정기간에서 하루치 데이터 선택 (예: 2025-01-15 ~ 2025-01-15)</li>
                <li>합계 옵션 선택</li>
                <li>지표 설정에서 다음 필수 지표 추가:</li>
                <ul style={{ marginTop: '4px', fontSize: '0.9em' }}>
                  <li>광고 집행 옵션 ID</li>
                  <li>광고 집행 상품명</li>
                  <li>광고 전환 매출 발생 옵션 ID</li>
                  <li>노출수</li>
                  <li>클릭수</li>
                  <li>광고비</li>
                  <li>총 전환 매출액 (1일)</li>
                  <li>총 판매수량 (1일)</li>
                </ul>
                <li>엑셀 생성하기 → 엑셀 다운로드</li>
              </ul>
            </li>
            <li><strong>파일 업로드:</strong> 다운로드한 판매 데이터와 광고 데이터 2개 파일을 선택하세요</li>
            <li>파일은 <strong>옵션 ID</strong>를 기준으로 자동 병합됩니다 (판매 + 광고 + 마진 데이터)</li>
            <li>
              순이익 계산식:{' '}
              <code>매출 - (도매가 + 수수료 + 부가세) × 판매량 - 광고비 × 1.1</code>
            </li>
            <li>ROAS (광고 수익률) = 전환 매출액 ÷ 광고비</li>
            <li>결과는 대시보드에서 확인하세요</li>
          </ol>
        </Typography>
      </Paper>
    </Box>
  )
}

export default HomePage
