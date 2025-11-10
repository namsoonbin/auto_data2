import React, { useState, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import {
  Upload,
  CheckCircle,
  AlertCircle,
  BarChart3,
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import axios from 'axios';

interface UploadResult {
  status: 'success' | 'error';
  message: string;
  total_records?: number;
  matched_with_ads?: number;
  matched_with_margin?: number;
  fully_integrated?: number;
  warnings?: string[];
}

// Custom input component for DatePicker
interface CustomDateInputProps {
  value?: string;
  onClick?: () => void;
}

const CustomDateInput = forwardRef<HTMLInputElement, CustomDateInputProps>(
  ({ value, onClick }, ref) => (
    <div className="relative">
      <Input
        ref={ref}
        value={value}
        onClick={onClick}
        placeholder="데이터 날짜 선택 (필수)"
        readOnly
        className="cursor-pointer pr-10 bg-gray-50 border-gray-300"
      />
      <CalendarIcon className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
    </div>
  )
);

// Custom header component for DatePicker
interface CustomHeaderProps {
  monthDate: Date;
  decreaseMonth: () => void;
  increaseMonth: () => void;
  prevMonthButtonDisabled: boolean;
  nextMonthButtonDisabled: boolean;
}

const renderCustomHeader = ({
  monthDate,
  decreaseMonth,
  increaseMonth,
  prevMonthButtonDisabled,
  nextMonthButtonDisabled
}: CustomHeaderProps) => (
  <div className="flex justify-between items-center px-3 py-2 bg-white">
    <button
      onClick={decreaseMonth}
      disabled={prevMonthButtonDisabled}
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <ChevronLeft className="w-5 h-5" />
    </button>
    <span className="font-semibold text-gray-900 text-lg">
      {format(monthDate, 'yyyy년 M월', { locale: ko })}
    </span>
    <button
      onClick={increaseMonth}
      disabled={nextMonthButtonDisabled}
      className="p-1 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <ChevronRight className="w-5 h-5" />
    </button>
  </div>
);

function HomePage() {
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [adsFile, setAdsFile] = useState<File | null>(null);
  const [dataDate, setDataDate] = useState<Date | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (setter: React.Dispatch<React.SetStateAction<File | null>>) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      setter(file || null);
    };

  const handleUpload = async () => {
    if (!salesFile || !adsFile) {
      setUploadResult({
        status: 'error',
        message: '판매 데이터와 광고 데이터 파일을 선택해주세요',
        warnings: ['통합을 위해 두 파일이 모두 필요합니다']
      });
      return;
    }

    if (!dataDate) {
      setUploadResult({
        status: 'error',
        message: '데이터 날짜를 선택해주세요',
        warnings: ['데이터의 정확한 날짜를 지정해야 합니다']
      });
      return;
    }

    setUploading(true);
    setUploadResult(null);
    setUploadProgress(0);

    // Simulate progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const formData = new FormData();
      formData.append('sales_file', salesFile);
      formData.append('ads_file', adsFile);
      formData.append('data_date', format(dataDate, 'yyyy-MM-dd'));

      const response = await axios.post<UploadResult>(
        'http://localhost:8000/api/upload/integrated',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadResult(response.data);

      // Clear files on success
      if (response.data.status === 'success') {
        setSalesFile(null);
        setAdsFile(null);
        setDataDate(null);
        // Reset file inputs
        const salesInput = document.getElementById('sales-file-input') as HTMLInputElement;
        const adsInput = document.getElementById('ads-file-input') as HTMLInputElement;
        if (salesInput) salesInput.value = '';
        if (adsInput) adsInput.value = '';
      }
    } catch (error: any) {
      clearInterval(progressInterval);
      setUploadProgress(0);
      setUploadResult({
        status: 'error',
        message: error.response?.data?.message || error.message || '업로드 실패',
        total_records: 0,
        matched_with_ads: 0,
        matched_with_margin: 0,
        fully_integrated: 0,
        warnings: [error.response?.data?.detail || '알 수 없는 오류']
      });
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const allFilesSelected = salesFile && adsFile && dataDate;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
            <BarChart3 className="w-8 h-8 text-blue-600" />
            쿠팡 판매 데이터 통합
          </h1>
          <p className="text-gray-600">
            판매, 광고 데이터를 업로드하세요. 마진 데이터는 마진 관리 페이지에서 미리 등록된 데이터를 자동으로 불러옵니다.
          </p>
        </div>

        {/* Upload Card */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <CardTitle>파일 업로드</CardTitle>
            <CardDescription>판매 데이터와 광고 데이터를 선택하여 업로드하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Sales File */}
              <div
                className={`border-2 rounded-lg p-6 text-center transition-colors ${
                  salesFile
                    ? 'bg-green-50 border-green-500'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-semibold text-gray-900 mb-1">Sales Data (판매 데이터)</h3>
                <p className="text-sm text-gray-500 mb-4">
                  옵션 ID, 옵션명, 상품명, 매출, 판매량
                </p>
                <Button
                  variant={salesFile ? 'outline' : 'default'}
                  className={`w-full ${salesFile ? 'border-green-500 text-green-700 hover:bg-green-50' : ''}`}
                  asChild
                >
                  <label className="cursor-pointer">
                    {salesFile ? (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        {salesFile.name}
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        파일 선택
                      </>
                    )}
                    <input
                      id="sales-file-input"
                      type="file"
                      accept=".xlsx,.xls"
                      className="hidden"
                      onChange={handleFileChange(setSalesFile)}
                    />
                  </label>
                </Button>
              </div>

              {/* Ads File */}
              <div
                className={`border-2 rounded-lg p-6 text-center transition-colors ${
                  adsFile
                    ? 'bg-green-50 border-green-500'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-semibold text-gray-900 mb-1">Advertising Data (광고 데이터)</h3>
                <p className="text-sm text-gray-500 mb-4">
                  광고 집행 옵션 ID, 광고비, 노출수, 클릭수
                </p>
                <Button
                  variant={adsFile ? 'outline' : 'default'}
                  className={`w-full ${adsFile ? 'border-green-500 text-green-700 hover:bg-green-50' : ''}`}
                  asChild
                >
                  <label className="cursor-pointer">
                    {adsFile ? (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        {adsFile.name}
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4 mr-2" />
                        파일 선택
                      </>
                    )}
                    <input
                      id="ads-file-input"
                      type="file"
                      accept=".xlsx,.xls"
                      className="hidden"
                      onChange={handleFileChange(setAdsFile)}
                    />
                  </label>
                </Button>
              </div>
            </div>

            {/* Date Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-900 mb-2">
                데이터 날짜 <span className="text-red-500">*</span>
              </label>
              <DatePicker
                selected={dataDate}
                onChange={(date) => setDataDate(date)}
                customInput={<CustomDateInput />}
                dateFormat="yyyy-MM-dd"
                placeholderText="날짜를 선택하세요"
                isClearable={false}
                locale={ko}
                renderCustomHeader={renderCustomHeader}
                maxDate={new Date()}
              />
              <p className="text-xs text-gray-500 mt-1">판매 및 광고 데이터의 정확한 날짜를 선택하세요</p>
            </div>

            {/* Upload Button */}
            <Button
              size="lg"
              className="w-full bg-blue-600 hover:bg-blue-700"
              onClick={handleUpload}
              disabled={!allFilesSelected || uploading}
            >
              <Upload className="w-5 h-5 mr-2" />
              {uploading ? '업로드 중...' : '파일 업로드 및 통합'}
            </Button>

            {/* Progress */}
            {uploading && (
              <div className="mt-4">
                <Progress value={uploadProgress} className="h-2" />
                <p className="text-sm text-gray-500 mt-2 text-center">
                  파일 처리 및 통합 중... {uploadProgress}%
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upload Results */}
        {uploadResult && (
          <Card className="shadow-lg">
            <CardContent className="pt-6">
              <Alert variant={uploadResult.status === 'success' ? 'default' : 'destructive'} className="mb-6">
                {uploadResult.status === 'success' ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <AlertTitle className="font-bold">{uploadResult.message}</AlertTitle>
              </Alert>

              {uploadResult.status === 'success' && uploadResult.total_records && (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">통합 통계</h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-center text-white">
                      <p className="text-4xl font-bold mb-1">{uploadResult.total_records}</p>
                      <p className="text-sm text-blue-100">총 레코드</p>
                    </div>

                    <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg p-6 text-center text-white">
                      <p className="text-4xl font-bold mb-1">{uploadResult.matched_with_ads}</p>
                      <p className="text-sm text-cyan-100">광고 매칭</p>
                    </div>

                    <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg p-6 text-center text-white">
                      <p className="text-4xl font-bold mb-1">{uploadResult.matched_with_margin}</p>
                      <p className="text-sm text-amber-100">마진 매칭</p>
                    </div>

                    <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-center text-white">
                      <p className="text-4xl font-bold mb-1">{uploadResult.fully_integrated}</p>
                      <p className="text-sm text-green-100">완전 통합</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-600 mb-2">매칭률:</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="default" className="bg-cyan-500">
                        광고: {((uploadResult.matched_with_ads / uploadResult.total_records) * 100).toFixed(1)}%
                      </Badge>
                      <Badge variant="secondary" className="bg-amber-500 text-white">
                        마진: {((uploadResult.matched_with_margin / uploadResult.total_records) * 100).toFixed(1)}%
                      </Badge>
                      <Badge variant="default" className="bg-green-500">
                        완료: {((uploadResult.fully_integrated / uploadResult.total_records) * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                </>
              )}

              {uploadResult.warnings && uploadResult.warnings.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-semibold text-amber-600 mb-2">경고:</h4>
                  <div className="space-y-2">
                    {uploadResult.warnings.map((warning, index) => (
                      <Alert key={index} variant="default" className="border-amber-200 bg-amber-50">
                        <AlertCircle className="h-4 w-4 text-amber-600" />
                        <AlertDescription className="text-amber-800">{warning}</AlertDescription>
                      </Alert>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Instructions */}
        <Card className="mt-6 bg-gray-50 shadow-lg">
          <CardHeader>
            <CardTitle>사용 방법</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-3 text-sm text-gray-700">
              <li>
                <strong>마진 데이터 먼저 등록:</strong> 마진 관리 페이지에서 상품별 마진 데이터를 미리 등록하세요
              </li>
              <li>
                <strong>판매 데이터 다운로드:</strong>
                <ul className="list-disc list-inside ml-6 mt-2 space-y-1">
                  <li>쿠팡윙 비즈니스 인사이트 접속</li>
                  <li>판매분석 메뉴 선택</li>
                  <li>하루치 날짜 선택 (예: 2025-01-15 ~ 2025-01-15)</li>
                  <li>엑셀 다운로드 버튼 클릭</li>
                  <li>"상품별" 엑셀 다운로드 선택</li>
                </ul>
              </li>
              <li>
                <strong>광고 데이터 다운로드:</strong>
                <ul className="list-disc list-inside ml-6 mt-2 space-y-1">
                  <li>쿠팡윙 광고센터 접속</li>
                  <li>광고보고서 → 내 보고서 템플릿 선택</li>
                  <li>특정기간에서 하루치 데이터 선택 (예: 2025-01-15 ~ 2025-01-15)</li>
                  <li>합계 옵션 선택</li>
                  <li>지표 설정에서 다음 필수 지표 추가:</li>
                  <ul className="list-circle list-inside ml-6 text-xs space-y-1">
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
                <code className="bg-gray-200 px-2 py-1 rounded text-xs">
                  매출 - (도매가 + 수수료 + 부가세) × 판매량 - 광고비 × 1.1
                </code>
              </li>
              <li>ROAS (광고 수익률) = 전환 매출액 ÷ 광고비</li>
              <li>결과는 대시보드에서 확인하세요</li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default HomePage;
