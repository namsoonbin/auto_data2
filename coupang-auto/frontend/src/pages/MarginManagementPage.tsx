import React, { useState, useEffect, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
  Plus,
  Edit,
  Trash2,
  RefreshCw,
  AlertCircle,
  Download,
  Upload,
  Calendar,
  Calculator,
  ChevronLeft,
  ChevronRight,
  Search,
  Loader2,
} from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import axios from 'axios';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

// Interfaces
interface Margin {
  option_id: string;
  product_name: string;
  option_name?: string;
  cost_price: number;
  selling_price: number;
  margin_rate: number;
  fee_rate: number;
  fee_amount: number;
  vat: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface UnmatchedProduct {
  option_id: string;
  product_name: string;
  option_name?: string;
  sales_amount: number;
  sales_quantity: number;
}

interface UploadResult {
  status: 'success' | 'partial_success' | 'error';
  message: string;
  created: number;
  skipped: number;
  total_errors?: number;
  errors?: string[];
}

interface RecalcResult {
  status: string;
  message: string;
  total_records: number;
  updated_count: number;
  matched_products: number;
  date_range?: {
    start: string;
    end: string;
  };
}

interface MarginFormData {
  option_id: string;
  product_name: string;
  option_name: string;
  cost_price: number;
  selling_price: number;
  margin_rate: number;
  fee_rate: number;
  fee_amount: number;
  vat: number;
  notes: string;
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
        placeholder="기간을 선택하세요 (선택사항)"
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

function MarginManagementPage() {
  const [margins, setMargins] = useState<Margin[]>([]);
  const [unmatchedProducts, setUnmatchedProducts] = useState<UnmatchedProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('margins');

  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [currentMargin, setCurrentMargin] = useState<Margin | null>(null);

  // Excel upload states
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  // Form states
  const [formData, setFormData] = useState<MarginFormData>({
    option_id: '',
    product_name: '',
    option_name: '',
    cost_price: 0,
    selling_price: 0,
    margin_rate: 0,
    fee_rate: 0,
    fee_amount: 0,
    vat: 0,
    notes: '',
  });

  // Recalculation states
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [startDate, endDate] = dateRange;
  const [recalculating, setRecalculating] = useState(false);
  const [recalcResult, setRecalcResult] = useState<RecalcResult | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchMargins();
    fetchUnmatchedProducts();
  }, []);

  const fetchMargins = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<{ margins: Margin[] }>(`${API_BASE_URL}/margins`);
      setMargins(response.data.margins);
    } catch (err: any) {
      setError('마진 데이터 조회 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const fetchUnmatchedProducts = async () => {
    try {
      const response = await axios.get<{ unmatched_products: UnmatchedProduct[] }>(
        `${API_BASE_URL}/margins/unmatched/products?limit=100`
      );
      setUnmatchedProducts(response.data.unmatched_products);
    } catch (err) {
      console.error('Failed to fetch unmatched products:', err);
    }
  };

  const handleOpenDialog = (mode: 'create' | 'edit', item: Margin | UnmatchedProduct | null = null) => {
    setDialogMode(mode);
    if (mode === 'edit' && item && 'created_at' in item) {
      setCurrentMargin(item as Margin);
      setFormData({
        option_id: item.option_id,
        product_name: item.product_name,
        option_name: item.option_name || '',
        cost_price: item.cost_price,
        selling_price: item.selling_price,
        margin_rate: item.margin_rate,
        fee_rate: item.fee_rate,
        fee_amount: item.fee_amount,
        vat: item.vat,
        notes: item.notes || '',
      });
    } else if (mode === 'create' && item) {
      // Creating from unmatched product
      setFormData({
        option_id: item.option_id,
        product_name: item.product_name,
        option_name: item.option_name || '',
        cost_price: 0,
        selling_price: 0,
        margin_rate: 0,
        fee_rate: 0,
        fee_amount: 0,
        vat: 0,
        notes: '',
      });
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
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setCurrentMargin(null);
    setError(null);
  };

  const handleFormChange = (field: keyof MarginFormData, value: string | number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async () => {
    setError(null);
    setSuccess(null);

    // Validate required fields
    if (!formData.cost_price || formData.cost_price <= 0) {
      setError('도매가는 필수이며 0보다 커야 합니다');
      return;
    }
    if (formData.fee_amount === null || formData.fee_amount === undefined || formData.fee_amount < 0) {
      setError('총 수수료는 필수이며 0 이상이어야 합니다');
      return;
    }
    if (formData.vat === null || formData.vat === undefined || formData.vat < 0) {
      setError('부가세는 필수이며 0 이상이어야 합니다');
      return;
    }

    try {
      if (dialogMode === 'create') {
        await axios.post(`${API_BASE_URL}/margins`, formData);
        setSuccess('마진 데이터가 성공적으로 추가되었습니다');
      } else {
        await axios.put(`${API_BASE_URL}/margins/${currentMargin?.option_id}`, formData);
        setSuccess('마진 데이터가 성공적으로 수정되었습니다');
      }

      handleCloseDialog();
      fetchMargins();
      fetchUnmatchedProducts();
    } catch (err: any) {
      setError(
        dialogMode === 'create'
          ? '마진 추가 실패: ' + (err.response?.data?.detail || err.message)
          : '마진 수정 실패: ' + (err.response?.data?.detail || err.message)
      );
    }
  };

  const handleDelete = async (optionId: string) => {
    if (!window.confirm('정말 이 마진 데이터를 삭제하시겠습니까?')) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      await axios.delete(`${API_BASE_URL}/margins/${optionId}`);
      setSuccess('마진 데이터가 성공적으로 삭제되었습니다');
      fetchMargins();
      fetchUnmatchedProducts();
    } catch (err: any) {
      setError('마진 삭제 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/margins/template/download`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `margin_template_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess('Excel 템플릿이 다운로드되었습니다');
    } catch (err: any) {
      setError('템플릿 다운로드 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleExcelFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setExcelFile(file);
      setUploadResult(null);
    }
  };

  const handleExcelUpload = async () => {
    if (!excelFile) {
      setError('Excel 파일을 선택해주세요');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);
    setUploadResult(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append('file', excelFile);

      const response = await axios.post<UploadResult>(
        `${API_BASE_URL}/margins/upload/excel?skip_existing=true&update_existing=false`,
        formDataObj,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setUploadResult(response.data);

      if (response.data.status === 'success') {
        setSuccess(response.data.message);
        setExcelFile(null);
        // Reset file input
        const input = document.getElementById('excel-file-input') as HTMLInputElement;
        if (input) input.value = '';
        fetchMargins();
        fetchUnmatchedProducts();
      } else if (response.data.status === 'partial_success') {
        setError(response.data.message);
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError('Excel 업로드 실패: ' + (err.response?.data?.detail || err.message));
      setUploadResult(null);
    } finally {
      setUploading(false);
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

  const handleRecalculate = async () => {
    setRecalculating(true);
    setRecalcResult(null);
    setError(null);
    setSuccess(null);

    try {
      const params: any = {};
      if (startDate) {
        params.start_date = format(startDate, 'yyyy-MM-dd');
      }
      if (endDate) {
        params.end_date = format(endDate, 'yyyy-MM-dd');
      }

      const response = await axios.post<RecalcResult>(`${API_BASE_URL}/margins/recalculate`, null, {
        params: params,
      });

      setRecalcResult(response.data);
      if (response.data.status === 'success') {
        setSuccess(response.data.message);
      }
    } catch (err: any) {
      setError('재계산 실패: ' + (err.response?.data?.detail || err.message));
      setRecalcResult(null);
    } finally {
      setRecalculating(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('ko-KR').format(value);
  };

  // Filter margins based on search query
  const filteredMargins = margins.filter((margin) => {
    if (!searchQuery) return true;

    const query = searchQuery.toLowerCase();
    return (
      margin.option_id.toString().includes(query) ||
      margin.product_name.toLowerCase().includes(query) ||
      (margin.option_name && margin.option_name.toLowerCase().includes(query))
    );
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-black">마진 관리</h1>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleDownloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              템플릿 다운로드
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                fetchMargins();
                fetchUnmatchedProducts();
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              새로고침
            </Button>
            <Button size="sm" onClick={() => handleOpenDialog('create')}>
              <Plus className="h-4 w-4 mr-2" />
              마진 추가
            </Button>
          </div>
        </div>

        {/* Excel Upload Section */}
        <Card className="mb-6 border-blue-300 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="font-semibold text-blue-700 min-w-[120px]">Excel 일괄 업로드</h3>
              <p className="text-xs text-red-600 font-semibold">
                ⚠️ 필수 항목: 도매가, 총 수수료, 부가세 (순이익 계산에 필수)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                id="excel-file-input"
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={handleExcelFileChange}
              />
              <Button variant="outline" size="sm" asChild>
                <label htmlFor="excel-file-input" className="cursor-pointer">
                  {excelFile ? (
                    excelFile.name
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      파일 선택
                    </>
                  )}
                </label>
              </Button>
              <Button size="sm" onClick={handleExcelUpload} disabled={!excelFile || uploading}>
                {uploading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    업로드 중...
                  </>
                ) : (
                  '업로드'
                )}
              </Button>
              {uploadResult && (
                <Badge
                  variant={
                    uploadResult.status === 'success'
                      ? 'default'
                      : uploadResult.status === 'partial_success'
                      ? 'secondary'
                      : 'destructive'
                  }
                >
                  생성: {uploadResult.created} | 건너뜀: {uploadResult.skipped} | 오류:{' '}
                  {uploadResult.total_errors || 0}
                </Badge>
              )}
            </div>
            {uploadResult && uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className="mt-3 space-y-1">
                <p className="text-xs text-red-600">오류 목록:</p>
                {uploadResult.errors.map((err, idx) => (
                  <p key={idx} className="text-xs text-red-600 ml-2">
                    • {err}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Margin Recalculation Section */}
        <Card className="mb-6 border-green-300 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className="h-5 w-5 text-green-600" />
              <h3 className="font-semibold text-green-700">마진 데이터 재계산</h3>
            </div>

            <p className="text-xs text-muted-foreground mb-4">
              날짜 범위를 선택하여 통합 레코드의 마진 데이터를 현재 마진 정보로 재계산합니다. 날짜를
              선택하지 않으면 전체 데이터가 재계산됩니다.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="md:col-span-2">
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
                  shouldCloseOnSelect={false}
                  locale={ko}
                  renderCustomHeader={renderCustomHeader}
                  maxDate={new Date()}
                />
              </div>
              <Button
                className="bg-green-600 hover:bg-green-700"
                onClick={handleRecalculate}
                disabled={recalculating}
              >
                {recalculating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    재계산 중...
                  </>
                ) : (
                  <>
                    <Calculator className="h-4 w-4 mr-2" />
                    재계산 실행
                  </>
                )}
              </Button>
            </div>

            {recalcResult && (
              <div className="mt-4 space-y-2">
                <Alert className="bg-green-100 border-green-300">
                  <AlertTitle className="text-green-800 font-bold">{recalcResult.message}</AlertTitle>
                </Alert>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="secondary">총 레코드: {recalcResult.total_records}</Badge>
                  <Badge className="bg-green-600">업데이트: {recalcResult.updated_count}</Badge>
                  <Badge>매칭 상품: {recalcResult.matched_products}</Badge>
                  <Badge variant="outline">
                    기간: {recalcResult.date_range?.start || '전체'} ~{' '}
                    {recalcResult.date_range?.end || '전체'}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Alert Messages */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-6 bg-green-50 border-green-200 text-green-800">
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="margins">마진 데이터 목록</TabsTrigger>
            <TabsTrigger value="unmatched" className="relative">
              미매칭 상품
              {unmatchedProducts.length > 0 && (
                <Badge variant="destructive" className="ml-2 px-1.5 py-0 text-xs">
                  {unmatchedProducts.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Margins Tab */}
          <TabsContent value="margins">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>
                    등록된 마진 데이터 ({filteredMargins.length}개)
                    {searchQuery && ` / 전체 ${margins.length}개`}
                  </CardTitle>
                </div>
                <div className="relative mt-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="옵션ID, 상품명, 옵션명으로 검색..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : filteredMargins.length === 0 ? (
                  <div className="py-8 text-center text-muted-foreground">
                    {searchQuery ? '검색 결과가 없습니다' : '등록된 마진 데이터가 없습니다'}
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead className="font-bold">옵션ID</TableHead>
                          <TableHead className="font-bold">상품명/옵션</TableHead>
                          <TableHead className="text-right font-bold">도매가</TableHead>
                          <TableHead className="text-right font-bold">판매가</TableHead>
                          <TableHead className="text-right font-bold">마진율</TableHead>
                          <TableHead className="text-right font-bold">수수료율</TableHead>
                          <TableHead className="text-center font-bold">작업</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredMargins.map((margin) => (
                          <TableRow key={margin.option_id} className="hover:bg-gray-50">
                            <TableCell>{margin.option_id}</TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium">{margin.product_name}</div>
                                {margin.option_name && (
                                  <p className="text-xs text-gray-500">{margin.option_name}</p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="text-right">{formatCurrency(margin.cost_price)}</TableCell>
                            <TableCell className="text-right">
                              {formatCurrency(margin.selling_price)}
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge
                                variant={
                                  margin.margin_rate > 30
                                    ? 'default'
                                    : margin.margin_rate > 15
                                    ? 'secondary'
                                    : 'destructive'
                                }
                                className={
                                  margin.margin_rate > 30
                                    ? 'bg-green-600'
                                    : margin.margin_rate > 15
                                    ? 'bg-amber-500'
                                    : ''
                                }
                              >
                                {margin.margin_rate.toFixed(1)}%
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{margin.fee_rate.toFixed(1)}%</TableCell>
                            <TableCell className="text-center">
                              <div className="flex justify-center gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleOpenDialog('edit', margin)}
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  onClick={() => handleDelete(margin.option_id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Unmatched Products Tab */}
          <TabsContent value="unmatched">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <CardTitle>마진 데이터가 없는 상품 ({unmatchedProducts.length}개)</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <Alert className="mb-4 bg-amber-50 border-amber-300">
                  <AlertDescription className="text-amber-800">
                    아래 상품들은 매출 데이터는 있지만 마진 정보가 등록되지 않아 정확한 수익 계산이
                    불가능합니다. 매출액이 높은 순서로 표시됩니다.
                  </AlertDescription>
                </Alert>

                {loading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : unmatchedProducts.length === 0 ? (
                  <div className="py-8 text-center">
                    <p className="text-lg font-semibold text-green-600">
                      모든 상품에 마진 데이터가 등록되어 있습니다!
                    </p>
                  </div>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-red-50">
                          <TableHead className="font-bold">옵션ID</TableHead>
                          <TableHead className="font-bold">상품명/옵션</TableHead>
                          <TableHead className="text-right font-bold">매출액</TableHead>
                          <TableHead className="text-right font-bold">판매량</TableHead>
                          <TableHead className="text-center font-bold">작업</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {unmatchedProducts.map((product) => (
                          <TableRow key={product.option_id} className="hover:bg-gray-50">
                            <TableCell>{product.option_id}</TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium">{product.product_name}</div>
                                {product.option_name && (
                                  <p className="text-xs text-gray-500">{product.option_name}</p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className="text-right font-semibold">
                              {formatCurrency(product.sales_amount)}
                            </TableCell>
                            <TableCell className="text-right">{formatNumber(product.sales_quantity)}</TableCell>
                            <TableCell className="text-center">
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleOpenDialog('create', product)}
                              >
                                <Plus className="h-4 w-4 mr-1" />
                                마진 추가
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {dialogMode === 'create' ? '마진 데이터 추가' : '마진 데이터 수정'}
              </DialogTitle>
              <DialogDescription>
                {dialogMode === 'create'
                  ? '새로운 마진 정보를 입력하세요. 도매가, 총 수수료, 부가세는 필수입니다.'
                  : '마진 정보를 수정하세요.'}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="option_id">옵션 ID *</Label>
                <Input
                  id="option_id"
                  value={formData.option_id}
                  onChange={(e) => handleFormChange('option_id', e.target.value)}
                  disabled={dialogMode === 'edit'}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="product_name">상품명 *</Label>
                <Input
                  id="product_name"
                  value={formData.product_name}
                  onChange={(e) => handleFormChange('product_name', e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="option_name">옵션명</Label>
                <Input
                  id="option_name"
                  value={formData.option_name}
                  onChange={(e) => handleFormChange('option_name', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="cost_price" className="text-red-600">
                    도매가 (원) *
                  </Label>
                  <Input
                    id="cost_price"
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => handleFormChange('cost_price', parseFloat(e.target.value) || 0)}
                    className={formData.cost_price <= 0 ? 'border-red-500' : ''}
                  />
                  <p className="text-xs text-muted-foreground">필수: 순이익 계산에 사용됩니다</p>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="selling_price">판매가 (원)</Label>
                  <Input
                    id="selling_price"
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) => handleFormChange('selling_price', parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="margin_rate">마진율 (%)</Label>
                <Input
                  id="margin_rate"
                  type="number"
                  value={formData.margin_rate}
                  onChange={(e) => handleFormChange('margin_rate', parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="fee_rate">총 수수료율 (%)</Label>
                  <Input
                    id="fee_rate"
                    type="number"
                    value={formData.fee_rate}
                    onChange={(e) => handleFormChange('fee_rate', parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="fee_amount" className="text-red-600">
                    총 수수료 (원) *
                  </Label>
                  <Input
                    id="fee_amount"
                    type="number"
                    value={formData.fee_amount}
                    onChange={(e) => handleFormChange('fee_amount', parseFloat(e.target.value) || 0)}
                  />
                  <p className="text-xs text-muted-foreground">필수: 순이익 계산에 사용됩니다</p>
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="vat" className="text-red-600">
                  부가세 (원) *
                </Label>
                <Input
                  id="vat"
                  type="number"
                  value={formData.vat}
                  onChange={(e) => handleFormChange('vat', parseFloat(e.target.value) || 0)}
                />
                <p className="text-xs text-muted-foreground">필수: 순이익 계산에 사용됩니다</p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="notes">메모</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleFormChange('notes', e.target.value)}
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleCloseDialog}>
                취소
              </Button>
              <Button onClick={handleSubmit}>{dialogMode === 'create' ? '추가' : '수정'}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default MarginManagementPage;
