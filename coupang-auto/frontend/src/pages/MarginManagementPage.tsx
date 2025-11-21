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
import { useTheme } from '../contexts/ThemeContext';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

// Interfaces
interface Margin {
  option_id: number;
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
  option_id: number;
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
  option_id: number | string;
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
          placeholder="기간을 선택하세요 (선택사항)"
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

function MarginManagementPage() {
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
    option_id: 0,
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
        option_id: 0,
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
      // Convert option_id to number before sending
      const payload = {
        ...formData,
        option_id: typeof formData.option_id === 'string'
          ? parseInt(formData.option_id, 10)
          : formData.option_id
      };

      if (dialogMode === 'create') {
        await axios.post(`${API_BASE_URL}/margins`, payload);
        setSuccess('마진 데이터가 성공적으로 추가되었습니다');
      } else {
        await axios.put(`${API_BASE_URL}/margins/${currentMargin?.option_id}`, payload);
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
        <div className="flex justify-between items-center mb-6">
          <h1 className={`text-3xl font-bold ${
            theme === 'dark' ? 'text-white' : 'text-black'
          }`}>마진 관리</h1>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadTemplate}
              className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400' : ''}
            >
              <Download className={`h-4 w-4 mr-2 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
              템플릿 다운로드
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                fetchMargins();
                fetchUnmatchedProducts();
              }}
              className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400' : ''}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
              새로고침
            </Button>
            <Button
              size="sm"
              onClick={() => handleOpenDialog('create')}
              className={theme === 'dark'
                ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                : ''
              }
            >
              <Plus className="h-4 w-4 mr-2" />
              마진 추가
            </Button>
          </div>
        </div>

        {/* Excel Upload Section */}
        <Card className={`mb-6 shadow-lg ${
          theme === 'dark'
            ? 'bg-[#1a1d23] border-gray-800'
            : 'border-blue-300 bg-blue-50'
        }`}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-3">
              <Upload className={`h-5 w-5 ${theme === 'dark' ? 'text-cyan-400' : 'text-blue-700'}`} />
              <h3 className={`font-semibold min-w-[120px] ${
                theme === 'dark' ? 'text-gray-200' : 'text-blue-700'
              }`}>Excel 일괄 업로드</h3>
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
              <Button
                variant="outline"
                size="sm"
                asChild
                className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800 text-gray-300 hover:text-cyan-400' : ''}
              >
                <label htmlFor="excel-file-input" className="cursor-pointer">
                  {excelFile ? (
                    excelFile.name
                  ) : (
                    <>
                      <Upload className={`h-4 w-4 mr-2 ${theme === 'dark' ? 'text-cyan-400' : ''}`} />
                      파일 선택
                    </>
                  )}
                </label>
              </Button>
              <Button
                size="sm"
                onClick={handleExcelUpload}
                disabled={!excelFile || uploading}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] disabled:opacity-50 disabled:hover:shadow-none'
                  : ''
                }
              >
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
        <Card className={`mb-6 shadow-lg ${
          theme === 'dark'
            ? 'bg-[#1a1d23] border-gray-800'
            : 'border-green-300 bg-green-50'
        }`}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className={`h-5 w-5 ${
                theme === 'dark' ? 'text-cyan-400' : 'text-green-600'
              }`} />
              <h3 className={`font-semibold ${
                theme === 'dark' ? 'text-gray-200' : 'text-green-700'
              }`}>마진 데이터 재계산</h3>
            </div>

            <p className={`text-xs mb-4 ${
              theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
            }`}>
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
                onClick={handleRecalculate}
                disabled={recalculating}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] disabled:opacity-50 disabled:hover:shadow-none'
                  : 'bg-green-600 hover:bg-green-700'
                }
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
                <Alert className={theme === 'dark' ? 'bg-cyan-950/20 border-cyan-500/30' : 'bg-green-100 border-green-300'}>
                  <AlertTitle className={`font-bold ${
                    theme === 'dark' ? 'text-cyan-400' : 'text-green-800'
                  }`}>{recalcResult.message}</AlertTitle>
                </Alert>
                <div className="flex gap-2 flex-wrap">
                  <Badge variant="secondary" className={theme === 'dark' ? 'bg-gray-700 text-gray-200' : ''}>
                    총 레코드: {recalcResult.total_records}
                  </Badge>
                  <Badge className={theme === 'dark' ? 'bg-cyan-500/30 text-cyan-400 border-cyan-500/50' : 'bg-green-600'}>
                    업데이트: {recalcResult.updated_count}
                  </Badge>
                  <Badge variant="secondary" className={theme === 'dark' ? 'bg-gray-700 text-gray-200' : ''}>
                    매칭 상품: {recalcResult.matched_products}
                  </Badge>
                  <Badge variant="outline" className={theme === 'dark' ? 'border-gray-600 text-gray-300' : ''}>
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
          <Alert variant="destructive" className={`mb-6 ${
            theme === 'dark' ? 'bg-red-950/20 border-red-500/30 text-red-400' : ''
          }`}>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className={`mb-6 ${
            theme === 'dark'
              ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-400'
              : 'bg-green-50 border-green-200 text-green-800'
          }`}>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className={`grid w-full grid-cols-2 mb-6 ${
            theme === 'dark' ? 'bg-gray-900/50 border border-gray-800' : ''
          }`}>
            <TabsTrigger
              value="margins"
              className={theme === 'dark'
                ? 'data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400 text-gray-400 hover:text-gray-300'
                : ''
              }
            >
              마진 데이터 목록
            </TabsTrigger>
            <TabsTrigger
              value="unmatched"
              className={`relative ${
                theme === 'dark'
                  ? 'data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400 text-gray-400 hover:text-gray-300'
                  : ''
              }`}
            >
              미매칭 상품
              {unmatchedProducts.length > 0 && (
                <Badge variant="destructive" className={`ml-2 px-1.5 py-0 text-xs ${
                  theme === 'dark' ? 'bg-red-600/80' : ''
                }`}>
                  {unmatchedProducts.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Margins Tab */}
          <TabsContent value="margins">
            <Card className={`shadow-lg ${
              theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
            }`}>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className={theme === 'dark' ? 'text-white' : ''}>
                    등록된 마진 데이터 ({filteredMargins.length}개)
                    {searchQuery && ` / 전체 ${margins.length}개`}
                  </CardTitle>
                </div>
                <div className="relative mt-4">
                  <Search className={`absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 ${
                    theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                  }`} />
                  <Input
                    placeholder="옵션ID, 상품명, 옵션명으로 검색..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className={`pl-9 ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                        : ''
                    }`}
                  />
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className={`h-8 w-8 animate-spin ${
                      theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                    }`} />
                  </div>
                ) : filteredMargins.length === 0 ? (
                  <div className={`py-8 text-center ${
                    theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'
                  }`}>
                    {searchQuery ? '검색 결과가 없습니다' : '등록된 마진 데이터가 없습니다'}
                  </div>
                ) : (
                  <div className={`rounded-md border ${
                    theme === 'dark' ? 'border-gray-700' : ''
                  }`}>
                    <Table>
                      <TableHeader>
                        <TableRow className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700' : 'bg-gray-50'}>
                          <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>옵션ID</TableHead>
                          <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>상품명/옵션</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>도매가</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>판매가</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>마진율</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>수수료율</TableHead>
                          <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>작업</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredMargins.map((margin) => (
                          <TableRow key={margin.id} className={theme === 'dark' ? 'hover:bg-gray-900/30 border-gray-800' : 'hover:bg-gray-50'}>
                            <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                              {margin.option_id}
                            </TableCell>
                            <TableCell>
                              <div>
                                <div className={`font-medium ${theme === 'dark' ? 'text-white' : ''}`}>
                                  {margin.product_name}
                                </div>
                                {margin.option_name && (
                                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                                    {margin.option_name}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                              {formatCurrency(margin.cost_price)}
                            </TableCell>
                            <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
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
                                    ? theme === 'dark'
                                      ? 'bg-green-600/80 text-white'
                                      : 'bg-green-600'
                                    : margin.margin_rate > 15
                                    ? theme === 'dark'
                                      ? 'bg-amber-500/80 text-white'
                                      : 'bg-amber-500'
                                    : theme === 'dark'
                                    ? 'bg-red-600/80 text-white'
                                    : ''
                                }
                              >
                                {margin.margin_rate.toFixed(1)}%
                              </Badge>
                            </TableCell>
                            <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                              {margin.fee_rate.toFixed(1)}%
                            </TableCell>
                            <TableCell className="text-center">
                              <div className="flex justify-center gap-1">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleOpenDialog('edit', margin)}
                                  className={theme === 'dark'
                                    ? 'text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10'
                                    : ''
                                  }
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className={theme === 'dark'
                                    ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                                    : 'text-red-600 hover:text-red-700 hover:bg-red-50'
                                  }
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
            <Card className={`shadow-lg ${
              theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
            }`}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <AlertCircle className={`h-5 w-5 ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`} />
                  <CardTitle className={theme === 'dark' ? 'text-white' : ''}>
                    마진 데이터가 없는 상품 ({unmatchedProducts.length}개)
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <Alert className={`mb-4 ${
                  theme === 'dark'
                    ? 'bg-amber-950/20 border-amber-500/30'
                    : 'bg-amber-50 border-amber-300'
                }`}>
                  <AlertDescription className={theme === 'dark' ? 'text-amber-300' : 'text-amber-800'}>
                    아래 상품들은 매출 데이터는 있지만 마진 정보가 등록되지 않아 정확한 수익 계산이
                    불가능합니다. 매출액이 높은 순서로 표시됩니다.
                  </AlertDescription>
                </Alert>

                {loading ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className={`h-8 w-8 animate-spin ${
                      theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
                    }`} />
                  </div>
                ) : unmatchedProducts.length === 0 ? (
                  <div className="py-8 text-center">
                    <p className={`text-lg font-semibold ${
                      theme === 'dark' ? 'text-green-400' : 'text-green-600'
                    }`}>
                      모든 상품에 마진 데이터가 등록되어 있습니다!
                    </p>
                  </div>
                ) : (
                  <div className={`rounded-md border ${
                    theme === 'dark' ? 'border-gray-700' : ''
                  }`}>
                    <Table>
                      <TableHeader>
                        <TableRow className={theme === 'dark' ? 'bg-gray-900/50 border-gray-700' : 'bg-red-50'}>
                          <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>옵션ID</TableHead>
                          <TableHead className={`font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>상품명/옵션</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>매출액</TableHead>
                          <TableHead className={`text-right font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>판매량</TableHead>
                          <TableHead className={`text-center font-bold ${theme === 'dark' ? 'text-gray-300' : ''}`}>작업</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {unmatchedProducts.map((product, index) => (
                          <TableRow key={`unmatched-${product.option_id}-${index}`} className={theme === 'dark' ? 'hover:bg-gray-900/30 border-gray-800' : 'hover:bg-gray-50'}>
                            <TableCell className={theme === 'dark' ? 'text-gray-200' : ''}>
                              {product.option_id}
                            </TableCell>
                            <TableCell>
                              <div>
                                <div className={`font-medium ${theme === 'dark' ? 'text-white' : ''}`}>
                                  {product.product_name}
                                </div>
                                {product.option_name && (
                                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                                    {product.option_name}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell className={`text-right font-semibold ${
                              theme === 'dark' ? 'text-cyan-400' : ''
                            }`}>
                              {formatCurrency(product.sales_amount)}
                            </TableCell>
                            <TableCell className={`text-right ${theme === 'dark' ? 'text-gray-200' : ''}`}>
                              {formatNumber(product.sales_quantity)}
                            </TableCell>
                            <TableCell className="text-center">
                              <Button
                                size="sm"
                                onClick={() => handleOpenDialog('create', product)}
                                className={theme === 'dark'
                                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                                  : 'bg-red-600 hover:bg-red-700 text-white'
                                }
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
          <DialogContent className={`max-w-2xl ${
            theme === 'dark' ? 'bg-[#1a1d23] border-gray-800' : ''
          }`}>
            <DialogHeader>
              <DialogTitle className={theme === 'dark' ? 'text-white' : ''}>
                {dialogMode === 'create' ? '마진 데이터 추가' : '마진 데이터 수정'}
              </DialogTitle>
              <DialogDescription className={theme === 'dark' ? 'text-gray-400' : ''}>
                {dialogMode === 'create'
                  ? '새로운 마진 정보를 입력하세요. 도매가, 총 수수료, 부가세는 필수입니다.'
                  : '마진 정보를 수정하세요.'}
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="option_id" className={theme === 'dark' ? 'text-gray-300' : ''}>옵션 ID *</Label>
                <Input
                  id="option_id"
                  type="number"
                  value={formData.option_id}
                  onChange={(e) => handleFormChange('option_id', e.target.value ? parseInt(e.target.value, 10) : '')}
                  disabled={dialogMode === 'edit'}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50 disabled:opacity-50'
                    : ''
                  }
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="product_name" className={theme === 'dark' ? 'text-gray-300' : ''}>상품명 *</Label>
                <Input
                  id="product_name"
                  value={formData.product_name}
                  onChange={(e) => handleFormChange('product_name', e.target.value)}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="option_name" className={theme === 'dark' ? 'text-gray-300' : ''}>옵션명</Label>
                <Input
                  id="option_name"
                  value={formData.option_name}
                  onChange={(e) => handleFormChange('option_name', e.target.value)}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="cost_price" className={`text-red-600 ${theme === 'dark' ? 'font-semibold' : ''}`}>
                    도매가 (원) *
                  </Label>
                  <Input
                    id="cost_price"
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => handleFormChange('cost_price', parseFloat(e.target.value) || 0)}
                    className={`${formData.cost_price <= 0 ? 'border-red-500' : ''} ${
                      theme === 'dark'
                        ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                        : ''
                    }`}
                  />
                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'}`}>
                    필수: 순이익 계산에 사용됩니다
                  </p>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="selling_price" className={theme === 'dark' ? 'text-gray-300' : ''}>판매가 (원)</Label>
                  <Input
                    id="selling_price"
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) => handleFormChange('selling_price', parseFloat(e.target.value) || 0)}
                    className={theme === 'dark'
                      ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                      : ''
                    }
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="margin_rate" className={theme === 'dark' ? 'text-gray-300' : ''}>마진율 (%)</Label>
                <Input
                  id="margin_rate"
                  type="number"
                  value={formData.margin_rate}
                  onChange={(e) => handleFormChange('margin_rate', parseFloat(e.target.value) || 0)}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="fee_rate" className={theme === 'dark' ? 'text-gray-300' : ''}>총 수수료율 (%)</Label>
                  <Input
                    id="fee_rate"
                    type="number"
                    value={formData.fee_rate}
                    onChange={(e) => handleFormChange('fee_rate', parseFloat(e.target.value) || 0)}
                    className={theme === 'dark'
                      ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                      : ''
                    }
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="fee_amount" className={`text-red-600 ${theme === 'dark' ? 'font-semibold' : ''}`}>
                    총 수수료 (원) *
                  </Label>
                  <Input
                    id="fee_amount"
                    type="number"
                    value={formData.fee_amount}
                    onChange={(e) => handleFormChange('fee_amount', parseFloat(e.target.value) || 0)}
                    className={theme === 'dark'
                      ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                      : ''
                    }
                  />
                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'}`}>
                    필수: 순이익 계산에 사용됩니다
                  </p>
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="vat" className={`text-red-600 ${theme === 'dark' ? 'font-semibold' : ''}`}>
                  부가세 (원) *
                </Label>
                <Input
                  id="vat"
                  type="number"
                  value={formData.vat}
                  onChange={(e) => handleFormChange('vat', parseFloat(e.target.value) || 0)}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
                <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-muted-foreground'}`}>
                  필수: 순이익 계산에 사용됩니다
                </p>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="notes" className={theme === 'dark' ? 'text-gray-300' : ''}>메모</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleFormChange('notes', e.target.value)}
                  rows={3}
                  className={theme === 'dark'
                    ? 'bg-gray-900/50 border-gray-700 text-white placeholder:text-gray-500 focus:border-cyan-500/50'
                    : ''
                  }
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={handleCloseDialog}
                className={theme === 'dark' ? 'border-gray-700 hover:border-cyan-500/50 hover:bg-gray-800' : ''}
              >
                취소
              </Button>
              <Button
                onClick={handleSubmit}
                className={theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  : ''
                }
              >
                {dialogMode === 'create' ? '추가' : '수정'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default MarginManagementPage;
