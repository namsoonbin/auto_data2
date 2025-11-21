import React, { useState, useEffect, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Trash2,
  RefreshCw,
  Filter,
  X,
  Calendar,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Loader2,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

// Interfaces
interface SalesRecord {
  id: number;
  option_id: string;
  product_name: string;
  option_name?: string;
  date: string;
  sales_amount: number;
  sales_quantity: number;
  ad_cost: number;
  net_profit: number;
  actual_margin_rate?: number;
  roas?: number;
  created_at: string;
  updated_at: string;
}

// Custom input component for DatePicker - Theme-aware factory
interface CustomDateInputProps {
  value?: string;
  onClick?: () => void;
  theme?: 'light' | 'dark';
}

const createCustomDateInput = (theme: 'light' | 'dark') =>
  forwardRef<HTMLInputElement, CustomDateInputProps>(
    ({ value, onClick }, ref) => (
      <div className="relative">
        <Input
          value={value}
          onClick={onClick}
          ref={ref}
          readOnly
          placeholder="기간을 선택하세요"
          className={`cursor-pointer min-w-[280px] pr-10 ${
            theme === 'dark'
              ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
              : ''
          }`}
        />
        <Calendar className={`absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 pointer-events-none ${
          theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
        }`} />
      </div>
    )
  );

function DataManagementPage() {
  const { theme } = useTheme();

  // Custom header component for DatePicker
  const renderCustomHeader = ({
    monthDate,
    decreaseMonth,
    increaseMonth,
    prevMonthButtonDisabled,
    nextMonthButtonDisabled,
  }: any) => (
    <div className={`flex items-center justify-between px-3 py-2 ${
      theme === 'dark' ? 'bg-gray-800' : 'bg-white'
    }`}>
      <button
        onClick={decreaseMonth}
        disabled={prevMonthButtonDisabled}
        className={`p-1 rounded disabled:opacity-50 ${
          theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
        }`}
        type="button"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>
      <span className="font-semibold text-lg">
        {format(monthDate, 'yyyy년 M월', { locale: ko })}
      </span>
      <button
        onClick={increaseMonth}
        disabled={nextMonthButtonDisabled}
        className={`p-1 rounded disabled:opacity-50 ${
          theme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
        }`}
        type="button"
      >
        <ChevronRight className="h-5 w-5" />
      </button>
    </div>
  );

  const [records, setRecords] = useState<SalesRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [deleteAllDialog, setDeleteAllDialog] = useState(false);
  const [deleteBatchDialog, setDeleteBatchDialog] = useState(false);

  // Date filter states
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [startDate, endDate] = dateRange;
  const [filterActive, setFilterActive] = useState(false);

  // Pagination state
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);

  const fetchRecords = async (applyDateFilter = false) => {
    setLoading(true);
    setError(null);

    try {
      let url = `${API_BASE_URL}/data/records`;
      const params = new URLSearchParams();

      if (applyDateFilter && startDate) {
        params.append('start_date', format(startDate, 'yyyy-MM-dd'));
      }
      if (applyDateFilter && endDate) {
        params.append('end_date', format(endDate, 'yyyy-MM-dd'));
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get<{ records: SalesRecord[] }>(url);
      setRecords(response.data.records || []);
      setFilterActive(applyDateFilter && (startDate !== null || endDate !== null));
      setPage(0); // Reset to first page when data changes
    } catch (err: any) {
      setError(err.response?.data?.message || '데이터 조회 실패');
      console.error('Failed to fetch records:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords(false);
  }, []);

  const handleDeleteRecord = async (recordId: number) => {
    if (!window.confirm('이 레코드를 삭제하시겠습니까?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/data/records/${recordId}`);
      fetchRecords(filterActive);
      setSelectedRows([]);
    } catch (err: any) {
      alert('삭제 실패: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedRows.length === 0) return;

    try {
      await axios.post(`${API_BASE_URL}/data/records/batch-delete`, {
        ids: selectedRows,
      });
      setDeleteBatchDialog(false);
      fetchRecords(filterActive);
      setSelectedRows([]);
    } catch (err: any) {
      alert('일괄 삭제 실패: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleDeleteAll = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/data/records`);
      setDeleteAllDialog(false);
      fetchRecords(false);
      setSelectedRows([]);
    } catch (err: any) {
      alert('전체 삭제 실패: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleDateRangeChange = (update: [Date | null, Date | null]) => {
    const [start, end] = update;

    // If same date is clicked twice (or range selected with same date)
    if (start && end && start.toDateString() === end.toDateString()) {
      setDateRange([start, end]);
    } else {
      setDateRange(update);
    }
  };

  const handleApplyFilter = () => {
    fetchRecords(true);
  };

  const handleClearFilter = () => {
    setDateRange([null, null]);
    setFilterActive(false);
    fetchRecords(false);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num || 0);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR');
  };

  // Handle row selection
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const currentPageIds = paginatedRecords.map((row) => row.id);
      setSelectedRows(currentPageIds);
    } else {
      setSelectedRows([]);
    }
  };

  const handleSelectRow = (id: number) => {
    setSelectedRows((prev) => {
      if (prev.includes(id)) {
        return prev.filter((rowId) => rowId !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const isAllSelected = () => {
    const currentPageIds = paginatedRecords.map((row) => row.id);
    return currentPageIds.length > 0 && currentPageIds.every((id) => selectedRows.includes(id));
  };

  const isSomeSelected = () => {
    const currentPageIds = paginatedRecords.map((row) => row.id);
    return currentPageIds.some((id) => selectedRows.includes(id)) && !isAllSelected();
  };

  // Pagination
  const paginatedRecords = records.slice(page * pageSize, page * pageSize + pageSize);
  const totalPages = Math.ceil(records.length / pageSize);

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPage(0);
  };

  const CustomDateInput = createCustomDateInput(theme);

  return (
    <div className={`min-h-screen p-4 relative ${
      theme === 'dark'
        ? 'bg-[#0f1115]'
        : 'bg-gray-50'
    }`}>
      {/* Grain texture overlay for dark mode */}
      {theme === 'dark' && (
        <div
          className="fixed inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
      )}

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className={`flex items-center gap-2 text-3xl font-bold ${
            theme === 'dark' ? 'text-white' : 'text-black'
          }`}>
            <Trash2 className={`h-8 w-8 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
            데이터 관리
          </h1>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchRecords(filterActive)}
              disabled={loading}
              className={theme === 'dark'
                ? 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10'
                : ''
              }
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setDeleteAllDialog(true)}
              disabled={records.length === 0}
              className={theme === 'dark' ? 'bg-red-600/80 hover:bg-red-700/80' : ''}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              전체 삭제
            </Button>
          </div>
        </div>

        <p className={`mb-6 ${
          theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
        }`}>
          통합된 판매 데이터를 조회하고 삭제할 수 있습니다
        </p>

        {error && (
          <Alert variant="destructive" className={`mb-6 ${
            theme === 'dark' ? 'bg-red-950/20 border-red-500/30 text-red-400' : ''
          }`}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Date Range Filter */}
        <Card className={`mb-6 shadow-lg ${
          theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
        }`}>
          <CardHeader>
            <CardTitle className={`flex items-center gap-2 ${
              theme === 'dark' ? 'text-white' : ''
            }`}>
              <Filter className={`h-5 w-5 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
              날짜 범위 필터
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 flex-wrap">
              <div className="w-full sm:w-auto">
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
                  shouldCloseOnSelect={false}
                  locale={ko}
                  renderCustomHeader={renderCustomHeader}
                  maxDate={new Date()}
                />
              </div>
              <Button
                onClick={handleApplyFilter}
                disabled={!startDate && !endDate}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] disabled:opacity-50 disabled:hover:shadow-none'
                  : ''
                }
              >
                <Filter className="h-4 w-4 mr-2" />
                필터 적용
              </Button>
              <Button
                variant="outline"
                onClick={handleClearFilter}
                disabled={!filterActive}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400 disabled:opacity-50'
                  : ''
                }
              >
                <X className="h-4 w-4 mr-2" />
                필터 초기화
              </Button>
            </div>
            {filterActive && (
              <Alert className={`mt-4 ${
                theme === 'dark'
                  ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-400'
                  : 'bg-blue-50 border-blue-300'
              }`}>
                <AlertDescription className={theme === 'dark' ? 'text-cyan-300' : 'text-blue-800'}>
                  {startDate && endDate
                    ? `${format(startDate, 'yyyy-MM-dd')} ~ ${format(endDate, 'yyyy-MM-dd')} 기간의 데이터를 표시 중입니다`
                    : startDate
                    ? `${format(startDate, 'yyyy-MM-dd')} 이후 데이터를 표시 중입니다`
                    : `${format(endDate!, 'yyyy-MM-dd')} 이전 데이터를 표시 중입니다`}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Action Bar */}
        {selectedRows.length > 0 && (
          <Card className={`mb-4 shadow-lg ${
            theme === 'dark'
              ? 'bg-[#1a1d23] border-gray-800'
              : 'bg-blue-50 border-blue-300'
          }`}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Badge className={theme === 'dark' ? 'bg-cyan-500/30 text-cyan-400 border-cyan-500/50' : 'bg-blue-600'}>
                  {selectedRows.length}개 선택됨
                </Badge>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setDeleteBatchDialog(true)}
                  className={theme === 'dark' ? 'bg-red-600/80 hover:bg-red-700/80' : ''}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  선택 삭제
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Statistics */}
        <div className="flex gap-2 mb-4">
          <Badge variant="outline" className={theme === 'dark' ? 'border-gray-600 text-gray-300' : ''}>
            전체 레코드: {formatNumber(records.length)}
          </Badge>
          {filterActive && (
            <Badge variant="secondary" className={theme === 'dark' ? 'bg-cyan-500/30 text-cyan-400' : ''}>
              필터 활성화
            </Badge>
          )}
        </div>

        {/* Data Table */}
        <Card className={`shadow-lg ${
          theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
        }`}>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex justify-center items-center min-h-[400px]">
                <Loader2 className={`h-8 w-8 animate-spin ${
                  theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                }`} />
              </div>
            ) : records.length === 0 ? (
              <div className="flex flex-col justify-center items-center min-h-[400px] p-6">
                <Trash2 className={`h-16 w-16 mb-4 ${
                  theme === 'dark' ? 'text-gray-600' : 'text-muted-foreground'
                }`} />
                <h3 className={`text-lg font-semibold mb-2 ${
                  theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
                }`}>데이터가 없습니다</h3>
                <p className={`text-sm text-center ${
                  theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                }`}>
                  {filterActive
                    ? '선택한 기간에 데이터가 없습니다. 필터를 초기화하거나 다른 기간을 선택해보세요'
                    : '파일을 업로드하면 여기에 데이터가 표시됩니다'}
                </p>
              </div>
            ) : (
              <>
                <div className={`rounded-md border ${
                  theme === 'dark' ? 'border-gray-800' : ''
                }`}>
                  <Table>
                    <TableHeader>
                      <TableRow className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50'}>
                        <TableHead className={`w-12 ${theme === 'dark' ? 'text-gray-300' : ''}`}>
                          <Checkbox
                            checked={isAllSelected()}
                            onCheckedChange={handleSelectAll}
                            aria-label="전체 선택"
                          />
                        </TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>옵션ID</TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>상품명/옵션</TableHead>
                        <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>날짜</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>매출액</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>판매량</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>광고비</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>순이익</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>이윤율(%)</TableHead>
                        <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>ROAS</TableHead>
                        <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>작업</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedRecords.map((record) => (
                        <TableRow
                          key={record.id}
                          className={theme === 'dark'
                            ? 'hover:bg-gray-900/30 border-gray-800 cursor-pointer'
                            : 'hover:bg-gray-50 cursor-pointer'
                          }
                          onClick={() => handleSelectRow(record.id)}
                        >
                          <TableCell onClick={(e) => e.stopPropagation()}>
                            <Checkbox
                              checked={selectedRows.includes(record.id)}
                              onCheckedChange={() => handleSelectRow(record.id)}
                              aria-label={`행 ${record.id} 선택`}
                            />
                          </TableCell>
                          <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                            {record.option_id}
                          </TableCell>
                          <TableCell className="max-w-[300px]">
                            <div>
                              <div className={`font-medium truncate ${
                                theme === 'dark' ? 'text-white' : ''
                              }`}>{record.product_name}</div>
                              {record.option_name && (
                                <p className={`text-xs truncate ${
                                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                                }`}>{record.option_name}</p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                            {formatDate(record.date)}
                          </TableCell>
                          <TableCell className={`text-right ${theme === 'dark' ? 'text-cyan-400' : ''}`}>
                            {formatNumber(record.sales_amount)}원
                          </TableCell>
                          <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                            {formatNumber(record.sales_quantity)}개
                          </TableCell>
                          <TableCell className={`text-right ${theme === 'dark' ? 'text-cyan-400' : ''}`}>
                            {formatNumber(record.ad_cost)}원
                          </TableCell>
                          <TableCell
                            className={`text-right font-semibold ${
                              record.net_profit >= 0
                                ? (theme === 'dark' ? 'text-green-400' : 'text-green-600')
                                : (theme === 'dark' ? 'text-red-400' : 'text-red-600')
                            }`}
                          >
                            {formatNumber(record.net_profit)}원
                          </TableCell>
                          <TableCell
                            className={`text-right ${
                              (record.actual_margin_rate || 0) >= 0
                                ? (theme === 'dark' ? 'text-green-400' : 'text-green-600')
                                : (theme === 'dark' ? 'text-red-400' : 'text-red-600')
                            }`}
                          >
                            {record.actual_margin_rate?.toFixed(1) || '0.0'}%
                          </TableCell>
                          <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                            {record.roas?.toFixed(2) || '0.00'}
                          </TableCell>
                          <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                            <Button
                              size="sm"
                              variant="ghost"
                              className={theme === 'dark'
                                ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                                : 'text-red-600 hover:text-red-700 hover:bg-red-50'
                              }
                              onClick={() => handleDeleteRecord(record.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Custom Pagination */}
                <div className={`flex items-center justify-between px-4 py-4 border-t ${
                  theme === 'dark' ? 'border-gray-800' : ''
                }`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm ${
                      theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
                    }`}>페이지당 행:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                      className={`border rounded px-2 py-1 text-sm ${
                        theme === 'dark'
                          ? 'bg-gray-900/50 border-gray-700 text-white focus:border-cyan-500/50 focus:outline-none'
                          : ''
                      }`}
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-sm ${
                      theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
                    }`}>
                      {page * pageSize + 1}-{Math.min((page + 1) * pageSize, records.length)} / 총{' '}
                      {records.length}
                    </span>
                    <div className="flex gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(0)}
                        disabled={page === 0}
                        className={theme === 'dark'
                          ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400 disabled:opacity-50'
                          : ''
                        }
                      >
                        <ChevronsLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page - 1)}
                        disabled={page === 0}
                        className={theme === 'dark'
                          ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400 disabled:opacity-50'
                          : ''
                        }
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page + 1)}
                        disabled={page >= totalPages - 1}
                        className={theme === 'dark'
                          ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400 disabled:opacity-50'
                          : ''
                        }
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(totalPages - 1)}
                        disabled={page >= totalPages - 1}
                        className={theme === 'dark'
                          ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400 disabled:opacity-50'
                          : ''
                        }
                      >
                        <ChevronsRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Delete All Confirmation Dialog */}
        <Dialog open={deleteAllDialog} onOpenChange={setDeleteAllDialog}>
          <DialogContent className={theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                전체 데이터 삭제
              </DialogTitle>
              <DialogDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
                정말로 모든 데이터를 삭제하시겠습니까?
                <br />
                <strong className={theme === 'dark' ? 'text-red-400' : ''}>
                  이 작업은 되돌릴 수 없습니다.
                </strong>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteAllDialog(false)}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                  : ''
                }
              >
                취소
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteAll}
                className={theme === 'dark' ? 'bg-red-600/80 hover:bg-red-700/80' : ''}
              >
                삭제
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Selected Confirmation Dialog */}
        <Dialog open={deleteBatchDialog} onOpenChange={setDeleteBatchDialog}>
          <DialogContent className={theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                선택 삭제
              </DialogTitle>
              <DialogDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
                선택한 {selectedRows.length}개의 레코드를 삭제하시겠습니까?
                <br />
                <strong className={theme === 'dark' ? 'text-red-400' : ''}>
                  이 작업은 되돌릴 수 없습니다.
                </strong>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setDeleteBatchDialog(false)}
                className={theme === 'dark'
                  ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400'
                  : ''
                }
              >
                취소
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteSelected}
                className={theme === 'dark' ? 'bg-red-600/80 hover:bg-red-700/80' : ''}
              >
                삭제
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default DataManagementPage;
