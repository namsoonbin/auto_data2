import React, { useState, useEffect, forwardRef } from 'react'
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Chip,
  Alert,
  CircularProgress,
  Stack,
  TablePagination,
  Checkbox
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import {
  Delete as DeleteIcon,
  DeleteSweep as DeleteAllIcon,
  Refresh as RefreshIcon,
  FilterAlt as FilterIcon,
  Clear as ClearIcon,
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

function DataManagementPage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedRows, setSelectedRows] = useState([])
  const [deleteAllDialog, setDeleteAllDialog] = useState(false)
  const [deleteBatchDialog, setDeleteBatchDialog] = useState(false)

  // Date filter states
  const [dateRange, setDateRange] = useState([null, null])
  const [startDate, endDate] = dateRange
  const [filterActive, setFilterActive] = useState(false)

  // Pagination state
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)

  const fetchRecords = async (applyDateFilter = false) => {
    setLoading(true)
    setError(null)

    try {
      let url = 'http://localhost:8000/api/data/records'
      const params = new URLSearchParams()

      if (applyDateFilter && startDate) {
        params.append('start_date', format(startDate, 'yyyy-MM-dd'))
      }
      if (applyDateFilter && endDate) {
        params.append('end_date', format(endDate, 'yyyy-MM-dd'))
      }

      if (params.toString()) {
        url += `?${params.toString()}`
      }

      const response = await axios.get(url)
      setRecords(response.data.records || [])
      setFilterActive(applyDateFilter && (startDate || endDate))
    } catch (err) {
      setError(err.response?.data?.message || '데이터 조회 실패')
      console.error('Failed to fetch records:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRecords(false)
  }, [])

  const handleDeleteRecord = async (recordId) => {
    if (!window.confirm('이 레코드를 삭제하시겠습니까?')) {
      return
    }

    try {
      await axios.delete(`http://localhost:8000/api/data/records/${recordId}`)
      fetchRecords(filterActive)
      setSelectedRows([])
    } catch (err) {
      alert('삭제 실패: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteSelected = async () => {
    if (selectedRows.length === 0) return

    try {
      await axios.post('http://localhost:8000/api/data/records/batch-delete', {
        ids: selectedRows
      })
      setDeleteBatchDialog(false)
      fetchRecords(filterActive)
      setSelectedRows([])
    } catch (err) {
      alert('일괄 삭제 실패: ' + (err.response?.data?.message || err.message))
    }
  }

  const handleDeleteAll = async () => {
    try {
      await axios.delete('http://localhost:8000/api/data/records')
      setDeleteAllDialog(false)
      fetchRecords(false)
      setSelectedRows([])
    } catch (err) {
      alert('전체 삭제 실패: ' + (err.response?.data?.message || err.message))
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

  const handleApplyFilter = () => {
    fetchRecords(true)
  }

  const handleClearFilter = () => {
    setDateRange([null, null])
    setFilterActive(false)
    fetchRecords(false)
  }

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ko-KR').format(num || 0)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR')
  }

  // Handle row selection
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      const currentPageIds = records.slice(page * pageSize, page * pageSize + pageSize).map(row => row.id)
      setSelectedRows(currentPageIds)
    } else {
      setSelectedRows([])
    }
  }

  const handleSelectRow = (id) => {
    setSelectedRows(prev => {
      if (prev.includes(id)) {
        return prev.filter(rowId => rowId !== id)
      } else {
        return [...prev, id]
      }
    })
  }

  const isAllSelected = () => {
    const currentPageIds = records.slice(page * pageSize, page * pageSize + pageSize).map(row => row.id)
    return currentPageIds.length > 0 && currentPageIds.every(id => selectedRows.includes(id))
  }

  const isSomeSelected = () => {
    const currentPageIds = records.slice(page * pageSize, page * pageSize + pageSize).map(row => row.id)
    return currentPageIds.some(id => selectedRows.includes(id)) && !isAllSelected()
  }

  // DataGrid columns
  const columns = [
    {
      field: 'select',
      headerName: '',
      width: 60,
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      renderHeader: () => (
        <Checkbox
          checked={isAllSelected()}
          indeterminate={isSomeSelected()}
          onChange={handleSelectAll}
          onClick={(e) => e.stopPropagation()}
        />
      ),
      renderCell: (params) => (
        <Checkbox
          checked={selectedRows.includes(params.row.id)}
          onChange={(e) => {
            e.stopPropagation()
            handleSelectRow(params.row.id)
          }}
          onClick={(e) => e.stopPropagation()}
        />
      )
    },
    {
      field: 'option_id',
      headerName: '옵션ID',
      width: 120,
      type: 'string',
      valueFormatter: (value) => String(value)
    },
    {
      field: 'product_name',
      headerName: '상품명',
      width: 250,
      flex: 1
    },
    {
      field: 'option_name',
      headerName: '옵션명',
      width: 200
    },
    {
      field: 'date',
      headerName: '날짜',
      width: 120,
      valueFormatter: (value) => formatDate(value)
    },
    {
      field: 'sales_amount',
      headerName: '매출액',
      width: 130,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatNumber(value) + '원'
    },
    {
      field: 'sales_quantity',
      headerName: '판매량',
      width: 100,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatNumber(value) + '개'
    },
    {
      field: 'ad_cost',
      headerName: '광고비',
      width: 120,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatNumber(value) + '원'
    },
    {
      field: 'net_profit',
      headerName: '순이익',
      width: 130,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography
          variant="body2"
          color={params.value >= 0 ? 'success.main' : 'error.main'}
          fontWeight="bold"
        >
          {formatNumber(params.value)}원
        </Typography>
      )
    },
    {
      field: 'actual_margin_rate',
      headerName: '이윤율(%)',
      width: 110,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Typography
          variant="body2"
          color={params.value >= 0 ? 'success.main' : 'error.main'}
        >
          {params.value?.toFixed(1)}%
        </Typography>
      )
    },
    {
      field: 'roas',
      headerName: 'ROAS',
      width: 100,
      type: 'number',
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => value?.toFixed(2) || '0.00'
    },
    {
      field: 'actions',
      headerName: '작업',
      width: 80,
      align: 'center',
      headerAlign: 'center',
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Tooltip title="삭제">
          <IconButton
            size="small"
            color="error"
            onClick={(e) => {
              e.stopPropagation()
              handleDeleteRecord(params.id)
            }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )
    }
  ]

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DeleteIcon fontSize="large" />
          데이터 관리
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="새로고침">
            <IconButton onClick={() => fetchRecords(filterActive)} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteAllIcon />}
            onClick={() => setDeleteAllDialog(true)}
            disabled={records.length === 0}
          >
            전체 삭제
          </Button>
        </Box>
      </Box>

      <Typography variant="body1" color="text.secondary" paragraph>
        통합된 판매 데이터를 조회하고 삭제할 수 있습니다
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Date Range Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterIcon />
          날짜 범위 필터
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box sx={{ width: 400 }}>
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
          <Button
            variant="contained"
            onClick={handleApplyFilter}
            disabled={!startDate && !endDate}
            startIcon={<FilterIcon />}
          >
            필터 적용
          </Button>
          <Button
            variant="outlined"
            onClick={handleClearFilter}
            disabled={!filterActive}
            startIcon={<ClearIcon />}
          >
            필터 초기화
          </Button>
        </Stack>
        {filterActive && (
          <Alert severity="info" sx={{ mt: 2 }}>
            {startDate && endDate
              ? `${format(startDate, 'yyyy-MM-dd')} ~ ${format(endDate, 'yyyy-MM-dd')} 기간의 데이터를 표시 중입니다`
              : startDate
              ? `${format(startDate, 'yyyy-MM-dd')} 이후 데이터를 표시 중입니다`
              : `${format(endDate, 'yyyy-MM-dd')} 이전 데이터를 표시 중입니다`}
          </Alert>
        )}
      </Paper>

      {/* Action Bar */}
      {selectedRows.length > 0 && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'action.selected' }}>
          <Stack direction="row" spacing={2} alignItems="center">
            <Chip
              label={`${selectedRows.length}개 선택됨`}
              color="primary"
              size="small"
            />
            <Button
              variant="contained"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteBatchDialog(true)}
              size="small"
            >
              선택 삭제
            </Button>
          </Stack>
        </Paper>
      )}

      {/* Statistics */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Chip
          label={`전체 레코드: ${formatNumber(records.length)}`}
          color="primary"
          variant="outlined"
        />
        {filterActive && (
          <Chip
            label="필터 활성화"
            color="info"
            size="small"
          />
        )}
      </Box>

      <Paper sx={{ width: '100%' }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400, p: 3 }}>
            <CircularProgress />
          </Box>
        ) : records.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: 400, p: 6 }}>
            <DeleteIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              데이터가 없습니다
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {filterActive
                ? '선택한 기간에 데이터가 없습니다. 필터를 초기화하거나 다른 기간을 선택해보세요'
                : '파일을 업로드하면 여기에 데이터가 표시됩니다'}
            </Typography>
          </Box>
        ) : (
          <>
            <DataGrid
              rows={records.slice(page * pageSize, page * pageSize + pageSize)}
              columns={columns}
              getRowId={(row) => row.id}
              hideFooter
              autoHeight
              onRowClick={(params) => handleSelectRow(params.row.id)}
              sx={{
                border: 'none',
                '& .MuiDataGrid-cell:focus': {
                  outline: 'none'
                },
                '& .MuiDataGrid-row:hover': {
                  backgroundColor: 'action.hover',
                  cursor: 'pointer'
                },
                '& .MuiDataGrid-row': {
                  cursor: 'pointer'
                }
              }}
            />
            <TablePagination
              component="div"
              count={records.length}
              page={page}
              onPageChange={(event, newPage) => setPage(newPage)}
              rowsPerPage={pageSize}
              onRowsPerPageChange={(event) => {
                setPageSize(parseInt(event.target.value, 10))
                setPage(0)
              }}
              rowsPerPageOptions={[10, 25, 50, 100]}
              labelRowsPerPage="페이지당 행:"
              labelDisplayedRows={({ from, to, count }) => `${from}-${to} / 총 ${count}`}
            />
          </>
        )}
      </Paper>

      {/* Delete All Confirmation Dialog */}
      <Dialog
        open={deleteAllDialog}
        onClose={() => setDeleteAllDialog(false)}
      >
        <DialogTitle>전체 데이터 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText>
            정말로 모든 데이터를 삭제하시겠습니까?
            <br />
            <strong>이 작업은 되돌릴 수 없습니다.</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAllDialog(false)}>
            취소
          </Button>
          <Button onClick={handleDeleteAll} color="error" variant="contained">
            삭제
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Selected Confirmation Dialog */}
      <Dialog
        open={deleteBatchDialog}
        onClose={() => setDeleteBatchDialog(false)}
      >
        <DialogTitle>선택 삭제</DialogTitle>
        <DialogContent>
          <DialogContentText>
            선택한 {selectedRows.length}개의 레코드를 삭제하시겠습니까?
            <br />
            <strong>이 작업은 되돌릴 수 없습니다.</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteBatchDialog(false)}>
            취소
          </Button>
          <Button onClick={handleDeleteSelected} color="error" variant="contained">
            삭제
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  )
}

export default DataManagementPage
