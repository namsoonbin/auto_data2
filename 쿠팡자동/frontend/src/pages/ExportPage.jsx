import React, { useState, forwardRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  TextField,
  FormControl,
  FormLabel,
  RadioGroup,
  Radio,
  FormControlLabel,
  Checkbox,
  FormGroup,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  IconButton
} from '@mui/material'
import {
  Download as DownloadIcon,
  CalendarToday as CalendarIcon,
  CheckCircle as SuccessIcon,
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

function ExportPage() {
  const [dateRange, setDateRange] = useState([null, null])
  const [startDate, endDate] = dateRange
  const [exportFormat, setExportFormat] = useState('xlsx')
  const [groupBy, setGroupBy] = useState('option')  // 'option' or 'product'
  const [dateGrouping, setDateGrouping] = useState('daily')  // 'daily' or 'total'
  const [includeFields, setIncludeFields] = useState({
    basic: true,
    sales: true,
    ads: true,
    margin: true,
    calculated: true
  })
  const [exporting, setExporting] = useState(false)
  const [exportResult, setExportResult] = useState(null)

  const handleDateRangeChange = (update) => {
    const [start, end] = update

    // If same date is clicked twice (or range selected with same date)
    if (start && end && start.toDateString() === end.toDateString()) {
      setDateRange([start, end])
    } else {
      setDateRange(update)
    }
  }

  const handleFieldChange = (event) => {
    setIncludeFields({
      ...includeFields,
      [event.target.name]: event.target.checked
    })
  }

  const handleExport = async () => {
    setExporting(true)
    setExportResult(null)

    try {
      const response = await axios.get('http://localhost:8000/api/data/export', {
        params: {
          start_date: startDate ? format(startDate, 'yyyy-MM-dd') : undefined,
          end_date: endDate ? format(endDate, 'yyyy-MM-dd') : undefined,
          format: exportFormat,
          group_by: groupBy,
          date_grouping: dateGrouping,
          include_basic: includeFields.basic,
          include_sales: includeFields.sales,
          include_ads: includeFields.ads,
          include_margin: includeFields.margin,
          include_calculated: includeFields.calculated
        },
        responseType: 'blob' // Important for file download
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      // Generate filename
      const dateStr = new Date().toISOString().split('T')[0]
      const filename = `coupang_data_${dateStr}.${exportFormat}`
      link.setAttribute('download', filename)

      document.body.appendChild(link)
      link.click()
      link.remove()

      setExportResult({
        status: 'success',
        message: '엑셀 파일이 다운로드되었습니다',
        filename: filename
      })
    } catch (error) {
      setExportResult({
        status: 'error',
        message: error.response?.data?.message || '내보내기 실패'
      })
    } finally {
      setExporting(false)
    }
  }

  const isAnyFieldSelected = Object.values(includeFields).some(v => v === true)

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <DownloadIcon fontSize="large" />
        엑셀 다운로드
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        통합된 판매 데이터를 엑셀 파일로 내보내기
      </Typography>

      {/* Export Options Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            내보내기 옵션
          </Typography>

          <Grid container spacing={3}>
            {/* Date Range */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CalendarIcon fontSize="small" />
                기간 선택 (선택사항)
              </Typography>
              <Box sx={{ mt: 1 }}>
                <DatePicker
                  selectsRange={true}
                  startDate={startDate}
                  endDate={endDate}
                  onChange={handleDateRangeChange}
                  customInput={<CustomDateInput />}
                  dateFormat="yyyy-MM-dd"
                  placeholderText="기간을 선택하세요"
                  isClearable={true}
                  monthsShown={2}
                  popperPlacement="bottom-start"
                  shouldCloseOnSelect={false}
                  locale={ko}
                  renderCustomHeader={renderCustomHeader}
                  maxDate={new Date()}
                />
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                비워두면 전체 기간 데이터를 내보냅니다
              </Typography>
            </Grid>

            {/* Grouping Option */}
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">데이터 그룹화</FormLabel>
                <RadioGroup
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value)}
                >
                  <FormControlLabel
                    value="option"
                    control={<Radio />}
                    label="옵션별 보기 - 각 옵션을 개별 행으로 표시"
                  />
                  <FormControlLabel
                    value="product"
                    control={<Radio />}
                    label="상품별 보기 - 같은 상품의 옵션을 합산하여 표시"
                  />
                </RadioGroup>
              </FormControl>
            </Grid>

            {/* Date Grouping Option */}
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">기간 표시 방식</FormLabel>
                <RadioGroup
                  value={dateGrouping}
                  onChange={(e) => setDateGrouping(e.target.value)}
                >
                  <FormControlLabel
                    value="daily"
                    control={<Radio />}
                    label="일별 보기 - 각 날짜별로 데이터 표시"
                  />
                  <FormControlLabel
                    value="total"
                    control={<Radio />}
                    label="합계 보기 - 선택한 기간의 합계만 표시"
                  />
                </RadioGroup>
              </FormControl>
            </Grid>

            {/* Export Format */}
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">파일 형식</FormLabel>
                <RadioGroup
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value)}
                >
                  <FormControlLabel
                    value="xlsx"
                    control={<Radio />}
                    label="Excel (.xlsx) - 권장"
                  />
                  <FormControlLabel
                    value="csv"
                    control={<Radio />}
                    label="CSV (.csv)"
                  />
                </RadioGroup>
              </FormControl>
            </Grid>

            {/* Include Fields */}
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">포함할 데이터 필드</FormLabel>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFields.basic}
                        onChange={handleFieldChange}
                        name="basic"
                      />
                    }
                    label="기본 정보 (옵션ID, 상품명, 날짜)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFields.sales}
                        onChange={handleFieldChange}
                        name="sales"
                      />
                    }
                    label="판매 데이터 (매출, 판매량)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFields.ads}
                        onChange={handleFieldChange}
                        name="ads"
                      />
                    }
                    label="광고 데이터 (광고비, 노출, 클릭)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFields.margin}
                        onChange={handleFieldChange}
                        name="margin"
                      />
                    }
                    label="마진 데이터 (도매가, 수수료, 부가세)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={includeFields.calculated}
                        onChange={handleFieldChange}
                        name="calculated"
                      />
                    }
                    label="계산 필드 (순이익, 마진율, ROAS)"
                  />
                </FormGroup>
              </FormControl>
            </Grid>

            {/* Export Button */}
            <Grid item xs={12}>
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleExport}
                disabled={!isAnyFieldSelected || exporting}
                startIcon={exporting ? <CircularProgress size={20} /> : <DownloadIcon />}
                sx={{ py: 1.5 }}
              >
                {exporting ? '내보내는 중...' : '엑셀 파일 다운로드'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Export Result */}
      {exportResult && (
        <Alert
          severity={exportResult.status === 'success' ? 'success' : 'error'}
          icon={exportResult.status === 'success' ? <SuccessIcon /> : undefined}
          sx={{ mb: 3 }}
        >
          <Typography variant="subtitle1" fontWeight="bold">
            {exportResult.message}
          </Typography>
          {exportResult.filename && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              파일명: <code>{exportResult.filename}</code>
            </Typography>
          )}
        </Alert>
      )}

      {/* Instructions */}
      <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          사용 안내
        </Typography>
        <Typography variant="body2" component="div">
          <ul>
            <li>원하는 기간과 데이터 필드를 선택하여 엑셀 파일로 다운로드할 수 있습니다</li>
            <li>기간을 선택하지 않으면 전체 데이터가 내보내집니다</li>
            <li>
              <strong>Excel (.xlsx)</strong> 형식은 서식과 다중 시트를 지원합니다 (권장)
            </li>
            <li>
              <strong>CSV (.csv)</strong> 형식은 텍스트 기반으로 더 가볍지만 서식이 없습니다
            </li>
            <li>최소 하나 이상의 데이터 필드를 선택해야 합니다</li>
          </ul>
        </Typography>
      </Paper>

      {/* Statistics */}
      <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
        <Chip
          label="대용량 데이터도 빠르게 처리"
          size="small"
          color="primary"
          variant="outlined"
        />
        <Chip
          label="한글 파일명 자동 생성"
          size="small"
          color="info"
          variant="outlined"
        />
      </Box>
    </Box>
  )
}

export default ExportPage
