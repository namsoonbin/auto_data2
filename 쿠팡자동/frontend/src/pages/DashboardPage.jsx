import React, { useState, useEffect, forwardRef } from 'react'
import {
  Box,
  Typography,
  Grid,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  Switch,
  FormControlLabel,
  FormGroup,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  AccountBalance as MoneyIcon,
  Percent as PercentIcon,
  ShoppingCart as OrderIcon,
  Campaign as AdIcon,
  CalendarToday as CalendarIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon
} from '@mui/icons-material'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  ComposedChart,
  Area
} from 'recharts'
import axios from 'axios'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import SalesChart from '../components/SalesChart'

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

function DashboardPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [roasData, setRoasData] = useState(null)
  const [dateRange, setDateRange] = useState([null, null])
  const [startDate, endDate] = dateRange
  const [groupBy, setGroupBy] = useState('option')  // 'option' or 'product'

  // Product chart modal states
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [productChartOpen, setProductChartOpen] = useState(false)
  const [productChartData, setProductChartData] = useState(null)
  const [loadingProductChart, setLoadingProductChart] = useState(false)

  useEffect(() => {
    fetchSummary()

    // Set default dates (last 30 days)
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 30)
    setDateRange([start, end])
  }, [])

  const handleGroupByChange = async (newGroupBy) => {
    console.log(`[Toggle] Changing from ${groupBy} to ${newGroupBy}`)

    setGroupBy(newGroupBy)

    // Only refetch if we already have data loaded
    if (!metrics || !startDate || !endDate) {
      console.log('[Toggle] No data to refetch yet')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd')
      const endDateStr = format(endDate, 'yyyy-MM-dd')

      console.log(`[Toggle] Fetching with group_by=${newGroupBy}, dates=${startDateStr} to ${endDateStr}`)

      const metricsResponse = await axios.get(`${API_BASE_URL}/metrics`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
          group_by: newGroupBy
        }
      })

      console.log(`[Toggle] Response received:`, metricsResponse.data)
      setMetrics(metricsResponse.data)

      const roasResponse = await axios.get(`${API_BASE_URL}/metrics/roas`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr
        }
      })
      setRoasData(roasResponse.data)

      console.log(`[Toggle] Successfully updated to groupBy: ${newGroupBy}`)
    } catch (err) {
      console.error('[Toggle] Error:', err)
      const errorDetail = err.response?.data?.detail
      const errorMessage = Array.isArray(errorDetail)
        ? errorDetail.map(e => typeof e === 'string' ? e : JSON.stringify(e)).join(', ')
        : typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail)
        : errorDetail || err.message
      setError('Failed to fetch metrics: ' + errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/metrics/summary`)
      setSummary(response.data)
    } catch (err) {
      console.error('Failed to fetch summary:', err)
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

  const fetchMetrics = async () => {
    if (!startDate || !endDate) {
      setError('기간을 선택해주세요')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd')
      const endDateStr = format(endDate, 'yyyy-MM-dd')

      // Fetch metrics
      const metricsResponse = await axios.get(`${API_BASE_URL}/metrics`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
          group_by: groupBy
        }
      })
      setMetrics(metricsResponse.data)

      // Fetch ROAS data
      const roasResponse = await axios.get(`${API_BASE_URL}/metrics/roas`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr
        }
      })
      setRoasData(roasResponse.data)
    } catch (err) {
      const errorDetail = err.response?.data?.detail
      const errorMessage = Array.isArray(errorDetail)
        ? errorDetail.map(e => typeof e === 'string' ? e : JSON.stringify(e)).join(', ')
        : typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail)
        : errorDetail || err.message
      setError('Failed to fetch metrics: ' + errorMessage)
    } finally {
      setLoading(false)
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

  const handleProductClick = async (product) => {
    if (!startDate || !endDate) {
      return
    }

    setSelectedProduct(product)
    setProductChartOpen(true)
    setLoadingProductChart(true)

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd')
      const endDateStr = format(endDate, 'yyyy-MM-dd')

      const response = await axios.get(`${API_BASE_URL}/metrics/product-trend`, {
        params: {
          product_name: product.product_name,
          option_id: groupBy === 'option' ? product.option_id : null,
          start_date: startDateStr,
          end_date: endDateStr
        }
      })

      setProductChartData(response.data.daily_trend)
    } catch (err) {
      console.error('Failed to fetch product trend:', err)
      setProductChartData([])
    } finally {
      setLoadingProductChart(false)
    }
  }

  const handleCloseProductChart = () => {
    setProductChartOpen(false)
    setSelectedProduct(null)
    setProductChartData(null)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUpIcon fontSize="large" />
        판매 성과 대시보드
      </Typography>

      {/* Sales Trend Chart */}
      {metrics && metrics.daily_trend && metrics.daily_trend.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <SalesChart data={metrics.daily_trend} />
        </Box>
      )}

      {/* Date Range Selector */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          기간 선택
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
              placeholderText="기간을 선택하세요"
              isClearable={true}
              monthsShown={2}
              popperPlacement="bottom-start"
              shouldCloseOnSelect={false}
              locale={ko}
              renderCustomHeader={renderCustomHeader}
              maxDate={new Date()}
            />
          </Grid>
          <Grid item xs={12} md={4} lg={6}>
            <Button
              variant="contained"
              onClick={fetchMetrics}
              fullWidth
              disabled={loading || !startDate || !endDate}
              size="large"
            >
              {loading ? <CircularProgress size={24} /> : '분석 조회'}
            </Button>
          </Grid>
        </Grid>
        {startDate && endDate && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            선택된 기간: {format(startDate, 'yyyy년 MM월 dd일')} ~ {format(endDate, 'yyyy년 MM월 dd일')}
          </Typography>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Charts and Tables */}
      {metrics && (
        <>
          {/* Period Summary */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {/* 1. 기간 매출 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {formatCurrency(metrics.total_sales)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  기간 매출
                </Typography>
              </Paper>
            </Grid>

            {/* 2. 기간 광고비 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {formatCurrency(metrics.total_ad_cost)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  기간 광고비
                </Typography>
              </Paper>
            </Grid>

            {/* 3. 기간 순이익 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {formatCurrency(metrics.total_profit)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  기간 순이익
                </Typography>
              </Paper>
            </Grid>

            {/* 4. 마진율 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {(((metrics.total_sales - (metrics.total_sales - metrics.total_profit - metrics.total_ad_cost * 1.1)) / metrics.total_sales) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  마진율
                </Typography>
              </Paper>
            </Grid>

            {/* 5. 광고비율 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {((metrics.total_ad_cost / metrics.total_sales) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  광고비율
                </Typography>
              </Paper>
            </Grid>

            {/* 6. 이윤율 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {((metrics.total_profit / metrics.total_sales) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  이윤율
                </Typography>
              </Paper>
            </Grid>

            {/* 7. 총 판매량 */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4">
                  {formatNumber(metrics.total_quantity)}개
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  총 판매량
                </Typography>
              </Paper>
            </Grid>

            {/* 8. 전체 ROAS */}
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {roasData?.overall_roas.toFixed(1) || '0.0'}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  전체 ROAS
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Product Performance Table */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                상품별 성과 상세
              </Typography>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={groupBy === 'product'}
                      onChange={(e) => {
                        const newGroupBy = e.target.checked ? 'product' : 'option'
                        console.log(`Toggle switch: ${groupBy} → ${newGroupBy}`)
                        handleGroupByChange(newGroupBy)
                      }}
                      color="primary"
                    />
                  }
                  label={groupBy === 'product' ? '상품별 보기' : '옵션별 보기'}
                />
              </FormGroup>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'grey.100' }}>
                    <TableCell width="35%"><strong>상품명</strong></TableCell>
                    <TableCell align="right" width="12%"><strong>매출</strong></TableCell>
                    <TableCell align="right" width="11%"><strong>순이익</strong></TableCell>
                    <TableCell align="right" width="11%"><strong>광고비</strong></TableCell>
                    <TableCell align="right" width="8%"><strong>판매량</strong></TableCell>
                    <TableCell align="right" width="8%"><strong>마진율</strong></TableCell>
                    <TableCell align="right" width="7%"><strong>광고비율</strong></TableCell>
                    <TableCell align="right" width="8%"><strong>이윤율</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {metrics.by_product.map((product, index) => (
                    <TableRow
                      key={product.option_id === 0 ? `product-${product.product_name}` : `option-${product.option_id}`}
                      onClick={() => handleProductClick(product)}
                      sx={{
                        '&:hover': { bgcolor: 'grey.100', cursor: 'pointer' },
                        bgcolor: index % 2 === 0 ? 'background.paper' : 'grey.50',
                        transition: 'background-color 0.2s'
                      }}
                    >
                      <TableCell>
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                            {product.product_name}
                            {index < 3 && (
                              <Chip
                                label={`#${index + 1}`}
                                size="small"
                                color="primary"
                                sx={{ ml: 1 }}
                              />
                            )}
                          </Box>
                          {product.option_name && (
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                              {product.option_name}
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <strong>{formatCurrency(product.total_sales)}</strong>
                      </TableCell>
                      <TableCell align="right" sx={{ color: product.total_profit > 0 ? 'success.main' : 'error.main' }}>
                        {formatCurrency(product.total_profit)}
                      </TableCell>
                      <TableCell align="right">
                        {formatCurrency(product.total_ad_cost)}
                      </TableCell>
                      <TableCell align="right">{formatNumber(product.total_quantity)}</TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${product.cost_rate.toFixed(1)}%`}
                          size="small"
                          color={product.cost_rate < 50 ? 'success' : product.cost_rate < 70 ? 'warning' : 'error'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${product.ad_cost_rate.toFixed(1)}%`}
                          size="small"
                          color={product.ad_cost_rate < 10 ? 'success' : product.ad_cost_rate < 20 ? 'warning' : 'error'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${product.margin_rate.toFixed(1)}%`}
                          size="small"
                          color={product.margin_rate > 30 ? 'success' : product.margin_rate > 15 ? 'warning' : 'error'}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {metrics.by_product.length === 0 && (
              <Box sx={{ py: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  이 기간에는 상품 데이터가 없습니다
                </Typography>
              </Box>
            )}
          </Paper>
        </>
      )}

      {!metrics && !loading && (
        <Paper sx={{ p: 6, textAlign: 'center', bgcolor: 'grey.50' }}>
          <TrendingUpIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            데이터가 로드되지 않았습니다
          </Typography>
          <Typography color="text.secondary">
            기간을 선택하고 "분석 조회" 버튼을 클릭하여 상세 지표를 확인하세요
          </Typography>
        </Paper>
      )}

      {/* Product Chart Modal */}
      <Dialog
        open={productChartOpen}
        onClose={handleCloseProductChart}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          {selectedProduct?.product_name}
          {selectedProduct?.option_name && (
            <Typography variant="body2" color="text.secondary">
              {selectedProduct.option_name}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {loadingProductChart ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
              <CircularProgress />
            </Box>
          ) : productChartData && productChartData.length > 0 ? (
            <Box sx={{ mt: 2 }}>
              <SalesChart data={productChartData} />
            </Box>
          ) : (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                이 상품에 대한 데이터가 없습니다
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseProductChart} variant="contained">
            닫기
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default DashboardPage
