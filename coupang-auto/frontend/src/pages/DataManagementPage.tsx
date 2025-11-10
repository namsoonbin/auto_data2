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

// Custom input component for DatePicker
const CustomDateInput = forwardRef<HTMLInputElement, { value?: string; onClick?: () => void }>(
  ({ value, onClick }, ref) => (
    <div className="relative">
      <Input
        value={value}
        onClick={onClick}
        ref={ref}
        readOnly
        placeholder="기간을 선택하세요"
        className="cursor-pointer min-w-[280px] pr-10"
      />
      <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
    </div>
  )
);

CustomDateInput.displayName = 'CustomDateInput';

// Custom header component for DatePicker
const renderCustomHeader = ({
  monthDate,
  decreaseMonth,
  increaseMonth,
  prevMonthButtonDisabled,
  nextMonthButtonDisabled,
}: any) => (
  <div className="flex items-center justify-between px-3 py-2 bg-white">
    <button
      onClick={decreaseMonth}
      disabled={prevMonthButtonDisabled}
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
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
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
      type="button"
    >
      <ChevronRight className="h-5 w-5" />
    </button>
  </div>
);

function DataManagementPage() {
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-black flex items-center gap-2">
            <Trash2 className="h-8 w-8" />
            데이터 관리
          </h1>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchRecords(filterActive)}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setDeleteAllDialog(true)}
              disabled={records.length === 0}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              전체 삭제
            </Button>
          </div>
        </div>

        <p className="text-muted-foreground mb-6">
          통합된 판매 데이터를 조회하고 삭제할 수 있습니다
        </p>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Date Range Filter */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
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
              <Button onClick={handleApplyFilter} disabled={!startDate && !endDate}>
                <Filter className="h-4 w-4 mr-2" />
                필터 적용
              </Button>
              <Button variant="outline" onClick={handleClearFilter} disabled={!filterActive}>
                <X className="h-4 w-4 mr-2" />
                필터 초기화
              </Button>
            </div>
            {filterActive && (
              <Alert className="mt-4 bg-blue-50 border-blue-300">
                <AlertDescription className="text-blue-800">
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
          <Card className="mb-4 bg-blue-50 border-blue-300">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Badge className="bg-blue-600">{selectedRows.length}개 선택됨</Badge>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setDeleteBatchDialog(true)}
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
          <Badge variant="outline">전체 레코드: {formatNumber(records.length)}</Badge>
          {filterActive && <Badge variant="secondary">필터 활성화</Badge>}
        </div>

        {/* Data Table */}
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex justify-center items-center min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : records.length === 0 ? (
              <div className="flex flex-col justify-center items-center min-h-[400px] p-6">
                <Trash2 className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold text-muted-foreground mb-2">데이터가 없습니다</h3>
                <p className="text-sm text-muted-foreground text-center">
                  {filterActive
                    ? '선택한 기간에 데이터가 없습니다. 필터를 초기화하거나 다른 기간을 선택해보세요'
                    : '파일을 업로드하면 여기에 데이터가 표시됩니다'}
                </p>
              </div>
            ) : (
              <>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="w-12">
                          <Checkbox
                            checked={isAllSelected()}
                            onCheckedChange={handleSelectAll}
                            aria-label="전체 선택"
                          />
                        </TableHead>
                        <TableHead className="font-bold">옵션ID</TableHead>
                        <TableHead className="font-bold">상품명/옵션</TableHead>
                        <TableHead className="font-bold">날짜</TableHead>
                        <TableHead className="text-right font-bold">매출액</TableHead>
                        <TableHead className="text-right font-bold">판매량</TableHead>
                        <TableHead className="text-right font-bold">광고비</TableHead>
                        <TableHead className="text-right font-bold">순이익</TableHead>
                        <TableHead className="text-right font-bold">이윤율(%)</TableHead>
                        <TableHead className="text-right font-bold">ROAS</TableHead>
                        <TableHead className="text-center font-bold">작업</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedRecords.map((record) => (
                        <TableRow
                          key={record.id}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => handleSelectRow(record.id)}
                        >
                          <TableCell onClick={(e) => e.stopPropagation()}>
                            <Checkbox
                              checked={selectedRows.includes(record.id)}
                              onCheckedChange={() => handleSelectRow(record.id)}
                              aria-label={`행 ${record.id} 선택`}
                            />
                          </TableCell>
                          <TableCell>{record.option_id}</TableCell>
                          <TableCell className="max-w-[300px]">
                            <div>
                              <div className="font-medium truncate">{record.product_name}</div>
                              {record.option_name && (
                                <p className="text-xs text-gray-500 truncate">{record.option_name}</p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>{formatDate(record.date)}</TableCell>
                          <TableCell className="text-right">{formatNumber(record.sales_amount)}원</TableCell>
                          <TableCell className="text-right">{formatNumber(record.sales_quantity)}개</TableCell>
                          <TableCell className="text-right">{formatNumber(record.ad_cost)}원</TableCell>
                          <TableCell
                            className={`text-right font-semibold ${
                              record.net_profit >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {formatNumber(record.net_profit)}원
                          </TableCell>
                          <TableCell
                            className={`text-right ${
                              (record.actual_margin_rate || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {record.actual_margin_rate?.toFixed(1) || '0.0'}%
                          </TableCell>
                          <TableCell className="text-right">
                            {record.roas?.toFixed(2) || '0.00'}
                          </TableCell>
                          <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
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
                <div className="flex items-center justify-between px-4 py-4 border-t">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">페이지당 행:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                      className="border rounded px-2 py-1 text-sm"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {page * pageSize + 1}-{Math.min((page + 1) * pageSize, records.length)} / 총{' '}
                      {records.length}
                    </span>
                    <div className="flex gap-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(0)}
                        disabled={page === 0}
                      >
                        <ChevronsLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page - 1)}
                        disabled={page === 0}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(page + 1)}
                        disabled={page >= totalPages - 1}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(totalPages - 1)}
                        disabled={page >= totalPages - 1}
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
          <DialogContent>
            <DialogHeader>
              <DialogTitle>전체 데이터 삭제</DialogTitle>
              <DialogDescription>
                정말로 모든 데이터를 삭제하시겠습니까?
                <br />
                <strong>이 작업은 되돌릴 수 없습니다.</strong>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteAllDialog(false)}>
                취소
              </Button>
              <Button variant="destructive" onClick={handleDeleteAll}>
                삭제
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Selected Confirmation Dialog */}
        <Dialog open={deleteBatchDialog} onOpenChange={setDeleteBatchDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>선택 삭제</DialogTitle>
              <DialogDescription>
                선택한 {selectedRows.length}개의 레코드를 삭제하시겠습니까?
                <br />
                <strong>이 작업은 되돌릴 수 없습니다.</strong>
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteBatchDialog(false)}>
                취소
              </Button>
              <Button variant="destructive" onClick={handleDeleteSelected}>
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
