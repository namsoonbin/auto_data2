import React, { useState, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import {
  Download,
  Calendar,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
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
interface IncludeFields {
  basic: boolean;
  sales: boolean;
  ads: boolean;
  margin: boolean;
  calculated: boolean;
}

interface ExportResult {
  status: 'success' | 'error';
  message: string;
  filename?: string;
}

// Custom input component for DatePicker - with theme support
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

function ExportPage() {
  const { theme } = useTheme();
  const CustomDateInput = createCustomDateInput(theme);

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
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [startDate, endDate] = dateRange;
  const [exportFormat, setExportFormat] = useState<'xlsx' | 'csv'>('xlsx');
  const [groupBy, setGroupBy] = useState<'option' | 'product'>('option');
  const [dateGrouping, setDateGrouping] = useState<'daily' | 'total'>('daily');
  const [includeFields, setIncludeFields] = useState<IncludeFields>({
    basic: true,
    sales: true,
    ads: true,
    margin: true,
    calculated: true,
  });
  const [includeFakePurchaseAdjustment, setIncludeFakePurchaseAdjustment] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);

  const handleDateRangeChange = (update: [Date | null, Date | null]) => {
    const [start, end] = update;

    // If same date is clicked twice (or range selected with same date)
    if (start && end && start.toDateString() === end.toDateString()) {
      setDateRange([start, end]);
    } else {
      setDateRange(update);
    }
  };

  const handleFieldChange = (field: keyof IncludeFields, checked: boolean) => {
    setIncludeFields({
      ...includeFields,
      [field]: checked,
    });
  };

  const handleExport = async () => {
    setExporting(true);
    setExportResult(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/data/export`, {
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
          include_calculated: includeFields.calculated,
          include_fake_purchase_adjustment: includeFakePurchaseAdjustment,
        },
        responseType: 'blob', // Important for file download
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      const dateStr = new Date().toISOString().split('T')[0];
      const filename = `coupang_data_${dateStr}.${exportFormat}`;
      link.setAttribute('download', filename);

      document.body.appendChild(link);
      link.click();
      link.remove();

      setExportResult({
        status: 'success',
        message: '엑셀 파일이 다운로드되었습니다',
        filename: filename,
      });
    } catch (error: any) {
      setExportResult({
        status: 'error',
        message: error.response?.data?.message || '내보내기 실패',
      });
    } finally {
      setExporting(false);
    }
  };

  const isAnyFieldSelected = Object.values(includeFields).some((v) => v === true);

  return (
    <div className={`min-h-screen p-4 relative ${
      theme === 'dark'
        ? 'bg-[#0f1115]'
        : 'bg-gray-50'
    }`}>
      {/* Dark theme grain texture */}
      {theme === 'dark' && (
        <div
          className="fixed inset-0 opacity-[0.015] pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />
      )}

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <h1 className={`flex items-center gap-2 mb-2 text-3xl font-bold ${
          theme === 'dark' ? 'text-white' : 'text-black'
        }`}>
          <Download className={`h-8 w-8 ${
            theme === 'dark' ? 'text-cyan-400' : ''
          }`} />
          엑셀 다운로드
        </h1>
        <p className={`mb-6 ${
          theme === 'dark' ? 'text-gray-400 text-sm' : 'text-muted-foreground'
        }`}>통합된 판매 데이터를 엑셀 파일로 내보내기</p>

        {/* Export Options Card */}
        <Card className={`mb-6 shadow-lg ${
          theme === 'dark'
            ? 'bg-[#1a1d23] border-gray-800'
            : ''
        }`}>
          <CardHeader>
            <CardTitle className={theme === 'dark' ? 'text-white' : ''}>내보내기 옵션</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Date Range */}
            <div>
              <Label className={`flex items-center gap-1 mb-2 ${
                theme === 'dark' ? 'text-gray-300' : ''
              }`}>
                <Calendar className="h-4 w-4" />
                기간 선택 (선택사항)
              </Label>
              <DatePicker
                selectsRange={true}
                startDate={startDate}
                endDate={endDate}
                onChange={handleDateRangeChange}
                customInput={React.createElement(CustomDateInput)}
                dateFormat="yyyy-MM-dd"
                placeholderText="기간을 선택하세요"
                isClearable={true}
                monthsShown={2}
                shouldCloseOnSelect={false}
                locale={ko}
                renderCustomHeader={renderCustomHeader}
                maxDate={new Date()}
              />
              <p className={`text-xs mt-1 ${
                theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
              }`}>
                비워두면 전체 기간 데이터를 내보냅니다
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Grouping Option */}
              <div>
                <Label className={`mb-3 block ${theme === 'dark' ? 'text-gray-300' : ''}`}>데이터 그룹화</Label>
                <RadioGroup value={groupBy} onValueChange={(value) => setGroupBy(value as 'option' | 'product')}>
                  <div className="flex items-center space-x-2 mb-2">
                    <RadioGroupItem value="option" id="group-option" />
                    <Label htmlFor="group-option" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      옵션별 보기 - 각 옵션을 개별 행으로 표시
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="product" id="group-product" />
                    <Label htmlFor="group-product" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      상품별 보기 - 같은 상품의 옵션을 합산하여 표시
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Date Grouping Option */}
              <div>
                <Label className={`mb-3 block ${theme === 'dark' ? 'text-gray-300' : ''}`}>기간 표시 방식</Label>
                <RadioGroup value={dateGrouping} onValueChange={(value) => setDateGrouping(value as 'daily' | 'total')}>
                  <div className="flex items-center space-x-2 mb-2">
                    <RadioGroupItem value="daily" id="date-daily" />
                    <Label htmlFor="date-daily" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      일별 보기 - 각 날짜별로 데이터 표시
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="total" id="date-total" />
                    <Label htmlFor="date-total" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      합계 보기 - 선택한 기간의 합계만 표시
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Export Format */}
              <div>
                <Label className={`mb-3 block ${theme === 'dark' ? 'text-gray-300' : ''}`}>파일 형식</Label>
                <RadioGroup value={exportFormat} onValueChange={(value) => setExportFormat(value as 'xlsx' | 'csv')}>
                  <div className="flex items-center space-x-2 mb-2">
                    <RadioGroupItem value="xlsx" id="format-xlsx" />
                    <Label htmlFor="format-xlsx" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      Excel (.xlsx) - 권장
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="csv" id="format-csv" />
                    <Label htmlFor="format-csv" className={`font-normal cursor-pointer ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      CSV (.csv)
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Include Fields */}
              <div>
                <Label className={`mb-3 block ${theme === 'dark' ? 'text-gray-300' : ''}`}>포함할 데이터 필드</Label>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="field-basic"
                      checked={includeFields.basic}
                      onCheckedChange={(checked) => handleFieldChange('basic', checked as boolean)}
                    />
                    <Label htmlFor="field-basic" className={`font-normal cursor-pointer text-sm ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      기본 정보 (옵션ID, 상품명, 날짜)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="field-sales"
                      checked={includeFields.sales}
                      onCheckedChange={(checked) => handleFieldChange('sales', checked as boolean)}
                    />
                    <Label htmlFor="field-sales" className={`font-normal cursor-pointer text-sm ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      판매 데이터 (매출, 판매량)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="field-ads"
                      checked={includeFields.ads}
                      onCheckedChange={(checked) => handleFieldChange('ads', checked as boolean)}
                    />
                    <Label htmlFor="field-ads" className={`font-normal cursor-pointer text-sm ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      광고 데이터 (광고비, 노출, 클릭)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="field-margin"
                      checked={includeFields.margin}
                      onCheckedChange={(checked) => handleFieldChange('margin', checked as boolean)}
                    />
                    <Label htmlFor="field-margin" className={`font-normal cursor-pointer text-sm ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      마진 데이터 (도매가, 수수료, 부가세)
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="field-calculated"
                      checked={includeFields.calculated}
                      onCheckedChange={(checked) => handleFieldChange('calculated', checked as boolean)}
                    />
                    <Label htmlFor="field-calculated" className={`font-normal cursor-pointer text-sm ${
                      theme === 'dark' ? 'text-gray-300' : ''
                    }`}>
                      계산 필드 (순이익, 마진율, ROAS)
                    </Label>
                  </div>
                </div>
              </div>
            </div>

            {/* Fake Purchase Adjustment Option */}
            <div className={`pt-2 ${
              theme === 'dark' ? 'border-t border-gray-700' : 'border-t'
            }`}>
              <Label className={`mb-3 block ${theme === 'dark' ? 'text-gray-300' : ''}`}>가구매 조정</Label>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="fake-purchase-adjustment"
                  checked={includeFakePurchaseAdjustment}
                  onCheckedChange={(checked) => setIncludeFakePurchaseAdjustment(checked as boolean)}
                />
                <Label htmlFor="fake-purchase-adjustment" className={`font-normal cursor-pointer text-sm ${
                  theme === 'dark' ? 'text-gray-300' : ''
                }`}>
                  가구매를 반영하여 매출/광고비 조정 (체크하면 가구매를 제외한 실제 데이터로 계산)
                </Label>
              </div>
              <p className={`text-xs mt-2 ml-6 ${
                theme === 'dark' ? 'text-gray-500' : 'text-muted-foreground'
              }`}>
                가구매로 등록된 항목의 매출과 판매량을 차감하고, 가구매 비용을 광고비에 추가합니다
              </p>
            </div>

            {/* Export Button */}
            <Button
              className={`w-full py-6 text-lg ${
                theme === 'dark'
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/10 hover:from-cyan-500/30 hover:to-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)]'
                  : ''
              }`}
              onClick={handleExport}
              disabled={!isAnyFieldSelected || exporting}
            >
              {exporting ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  내보내는 중...
                </>
              ) : (
                <>
                  <Download className="h-5 w-5 mr-2" />
                  엑셀 파일 다운로드
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Export Result */}
        {exportResult && (
          <Alert
            variant={exportResult.status === 'success' ? 'default' : 'destructive'}
            className={
              exportResult.status === 'success'
                ? theme === 'dark'
                  ? 'bg-green-950/20 border-green-500/30 mb-6'
                  : 'bg-green-50 border-green-300 mb-6'
                : 'mb-6'
            }
          >
            {exportResult.status === 'success' && (
              <CheckCircle2 className={`h-4 w-4 ${
                theme === 'dark' ? 'text-green-400' : 'text-green-600'
              }`} />
            )}
            <AlertTitle className={
              exportResult.status === 'success'
                ? theme === 'dark'
                  ? 'text-green-400'
                  : 'text-green-800'
                : ''
            }>
              {exportResult.message}
            </AlertTitle>
            {exportResult.filename && (
              <AlertDescription className={
                exportResult.status === 'success'
                  ? theme === 'dark'
                    ? 'text-green-400'
                    : 'text-green-700'
                  : ''
              }>
                파일명: <code className={`px-1 rounded ${
                  theme === 'dark'
                    ? 'bg-gray-800 text-cyan-400 border border-gray-700'
                    : 'bg-white'
                }`}>{exportResult.filename}</code>
              </AlertDescription>
            )}
          </Alert>
        )}

        {/* Instructions */}
        <Card className={`shadow-lg ${
          theme === 'dark'
            ? 'bg-[#1a1d23] border-gray-800'
            : 'bg-gray-50'
        }`}>
          <CardHeader>
            <CardTitle className={theme === 'dark' ? 'text-white' : ''}>사용 안내</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className={`space-y-2 text-sm ${
              theme === 'dark' ? 'text-gray-300' : ''
            }`}>
              <li className="flex gap-2">
                <span className={theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}>•</span>
                <span>원하는 기간과 데이터 필드를 선택하여 엑셀 파일로 다운로드할 수 있습니다</span>
              </li>
              <li className="flex gap-2">
                <span className={theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}>•</span>
                <span>기간을 선택하지 않으면 전체 데이터가 내보내집니다</span>
              </li>
              <li className="flex gap-2">
                <span className={theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}>•</span>
                <span>
                  <strong className={theme === 'dark' ? 'text-white' : ''}>Excel (.xlsx)</strong> 형식은 서식과 다중 시트를 지원합니다 (권장)
                </span>
              </li>
              <li className="flex gap-2">
                <span className={theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}>•</span>
                <span>
                  <strong className={theme === 'dark' ? 'text-white' : ''}>CSV (.csv)</strong> 형식은 텍스트 기반으로 더 가볍지만 서식이 없습니다
                </span>
              </li>
              <li className="flex gap-2">
                <span className={theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'}>•</span>
                <span>최소 하나 이상의 데이터 필드를 선택해야 합니다</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Statistics */}
        <div className="mt-6 flex gap-2">
          <Badge variant="outline" className={
            theme === 'dark'
              ? 'bg-gray-900/50 border-gray-700 text-gray-300'
              : 'bg-white'
          }>
            대용량 데이터도 빠르게 처리
          </Badge>
          <Badge variant="outline" className={
            theme === 'dark'
              ? 'bg-gray-900/50 border-gray-700 text-gray-300'
              : 'bg-white'
          }>
            한글 파일명 자동 생성
          </Badge>
        </div>
      </div>
    </div>
  );
}

export default ExportPage;
