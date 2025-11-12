import React, { useState, useEffect, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  TrendingUp,
  DollarSign,
  Percent,
  ShoppingCart,
  Megaphone,
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  BarChart3,
} from 'lucide-react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import SalesChart from '../components/SalesChart';

const API_BASE_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;

interface MetricsSummary {
  total_sales: number;
  total_ad_cost: number;
  total_profit: number;
  total_quantity: number;
}

interface ProductMetric {
  option_id: number;
  product_name: string;
  option_name?: string;
  total_sales: number;
  total_profit: number;
  total_ad_cost: number;
  total_quantity: number;
  cost_rate: number;
  ad_cost_rate: number;
  margin_rate: number;
}

interface MetricsResponse {
  total_sales: number;
  total_ad_cost: number;
  total_profit: number;
  total_quantity: number;
  by_product: ProductMetric[];
  daily_trend?: any[];
}

interface RoasData {
  overall_roas: number;
}

interface DailyTrend {
  date: string;
  total_sales: number;
  ad_cost: number;
  total_profit: number;
  total_quantity: number;
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
        placeholder="기간 선택"
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
  nextMonthButtonDisabled,
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

function DashboardPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [roasData, setRoasData] = useState<RoasData | null>(null);
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [startDate, endDate] = dateRange;
  const [groupBy, setGroupBy] = useState<'option' | 'product'>('option');

  // Product chart modal states
  const [selectedProduct, setSelectedProduct] = useState<ProductMetric | null>(null);
  const [productChartOpen, setProductChartOpen] = useState(false);
  const [productChartData, setProductChartData] = useState<DailyTrend[] | null>(null);
  const [loadingProductChart, setLoadingProductChart] = useState(false);

  useEffect(() => {
    fetchSummary();

    // Set default dates (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setDateRange([start, end]);
  }, []);

  const handleGroupByChange = async (checked: boolean) => {
    const newGroupBy = checked ? 'product' : 'option';
    console.log(`[Toggle] Changing from ${groupBy} to ${newGroupBy}`);

    setGroupBy(newGroupBy);

    // Only refetch if we already have data loaded
    if (!metrics || !startDate || !endDate) {
      console.log('[Toggle] No data to refetch yet');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      console.log(`[Toggle] Fetching with group_by=${newGroupBy}, dates=${startDateStr} to ${endDateStr}`);

      const metricsResponse = await axios.get<MetricsResponse>(`${API_BASE_URL}/metrics`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
          group_by: newGroupBy,
        },
      });

      console.log(`[Toggle] Response received:`, metricsResponse.data);
      setMetrics(metricsResponse.data);

      const roasResponse = await axios.get<RoasData>(`${API_BASE_URL}/metrics/roas`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
        },
      });
      setRoasData(roasResponse.data);

      console.log(`[Toggle] Successfully updated to groupBy: ${newGroupBy}`);
    } catch (err: any) {
      console.error('[Toggle] Error:', err);
      const errorDetail = err.response?.data?.detail;
      const errorMessage = Array.isArray(errorDetail)
        ? errorDetail.map((e: any) => (typeof e === 'string' ? e : JSON.stringify(e))).join(', ')
        : typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail)
        : errorDetail || err.message;
      setError('Failed to fetch metrics: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get<MetricsSummary>(`${API_BASE_URL}/metrics/summary`);
      setSummary(response.data);
    } catch (err) {
      console.error('Failed to fetch summary:', err);
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

  const fetchMetrics = async () => {
    if (!startDate || !endDate) {
      setError('기간을 선택해주세요');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      // Fetch metrics
      const metricsResponse = await axios.get<MetricsResponse>(`${API_BASE_URL}/metrics`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
          group_by: groupBy,
        },
      });
      setMetrics(metricsResponse.data);

      // Fetch ROAS data
      const roasResponse = await axios.get<RoasData>(`${API_BASE_URL}/metrics/roas`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
        },
      });
      setRoasData(roasResponse.data);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      const errorMessage = Array.isArray(errorDetail)
        ? errorDetail.map((e: any) => (typeof e === 'string' ? e : JSON.stringify(e))).join(', ')
        : typeof errorDetail === 'object'
        ? JSON.stringify(errorDetail)
        : errorDetail || err.message;
      setError('Failed to fetch metrics: ' + errorMessage);
    } finally {
      setLoading(false);
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

  const handleProductClick = async (product: ProductMetric) => {
    if (!startDate || !endDate) {
      return;
    }

    setSelectedProduct(product);
    setProductChartOpen(true);
    setLoadingProductChart(true);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      const response = await axios.get<{ daily_trend: DailyTrend[] }>(
        `${API_BASE_URL}/metrics/product-trend`,
        {
          params: {
            product_name: product.product_name,
            option_id: groupBy === 'option' ? product.option_id : null,
            start_date: startDateStr,
            end_date: endDateStr,
          },
        }
      );

      setProductChartData(response.data.daily_trend);
    } catch (err) {
      console.error('Failed to fetch product trend:', err);
      setProductChartData([]);
    } finally {
      setLoadingProductChart(false);
    }
  };

  const handleCloseProductChart = () => {
    setProductChartOpen(false);
    setSelectedProduct(null);
    setProductChartData(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            판매 성과 대시보드
          </h1>
        </div>

        {/* Sales Trend Chart */}
        {metrics && metrics.daily_trend && metrics.daily_trend.length > 0 && (
          <div className="mb-6">
            <SalesChart data={metrics.daily_trend} />
          </div>
        )}

        {/* Date Range Selector */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <CardTitle>기간 선택</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="md:col-span-2">
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
              </div>
              <div>
                <Button
                  onClick={fetchMetrics}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  disabled={loading || !startDate || !endDate}
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      로딩 중...
                    </>
                  ) : (
                    '분석 조회'
                  )}
                </Button>
              </div>
            </div>
            {startDate && endDate && (
              <p className="text-sm text-gray-500 mt-2">
                선택된 기간: {format(startDate, 'yyyy년 MM월 dd일')} ~ {format(endDate, 'yyyy년 MM월 dd일')}
              </p>
            )}
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Charts and Tables */}
        {metrics && (
          <>
            {/* Period Summary - 8개 지표 카드 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* 1. 기간 매출 */}
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-center text-white shadow-lg">
                <DollarSign className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">{formatCurrency(metrics.total_sales)}</p>
                <p className="text-sm text-blue-100">기간 매출</p>
              </div>

              {/* 2. 기간 광고비 */}
              <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg p-6 text-center text-white shadow-lg">
                <Megaphone className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">{formatCurrency(metrics.total_ad_cost)}</p>
                <p className="text-sm text-amber-100">기간 광고비</p>
              </div>

              {/* 3. 기간 순이익 */}
              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-center text-white shadow-lg">
                <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">{formatCurrency(metrics.total_profit)}</p>
                <p className="text-sm text-green-100">기간 순이익</p>
              </div>

              {/* 4. 마진율 */}
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-center text-white shadow-lg">
                <Percent className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">
                  {((((metrics.total_sales - (metrics.total_sales - metrics.total_profit - metrics.total_ad_cost * 1.1)) / metrics.total_sales)) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-purple-100">마진율</p>
              </div>

              {/* 5. 광고비율 */}
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg p-6 text-center text-white shadow-lg">
                <Percent className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">
                  {((metrics.total_ad_cost / metrics.total_sales) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-orange-100">광고비율</p>
              </div>

              {/* 6. 이윤율 */}
              <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg p-6 text-center text-white shadow-lg">
                <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">
                  {((metrics.total_profit / metrics.total_sales) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-teal-100">이윤율</p>
              </div>

              {/* 7. 총 판매량 */}
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg p-6 text-center text-white shadow-lg">
                <ShoppingCart className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">{formatNumber(metrics.total_quantity)}개</p>
                <p className="text-sm text-indigo-100">총 판매량</p>
              </div>

              {/* 8. 전체 ROAS */}
              <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg p-6 text-center text-white shadow-lg">
                <TrendingUp className="w-8 h-8 mx-auto mb-2 opacity-90" />
                <p className="text-3xl font-bold mb-1">{roasData?.overall_roas.toFixed(1) || '0.0'}%</p>
                <p className="text-sm text-cyan-100">전체 ROAS</p>
              </div>
            </div>

            {/* Product Performance Table */}
            <Card className="shadow-lg">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>상품별 성과 상세</CardTitle>
                  <div className="flex items-center gap-2">
                    <Label htmlFor="groupby-switch" className="text-sm font-medium">
                      {groupBy === 'product' ? '상품별 보기' : '옵션별 보기'}
                    </Label>
                    <Switch
                      id="groupby-switch"
                      checked={groupBy === 'product'}
                      onCheckedChange={handleGroupByChange}
                      className="data-[state=unchecked]:bg-gray-300"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-100">
                        <TableHead className="w-[25%]">상품명</TableHead>
                        <TableHead className="text-right w-[13%]">매출</TableHead>
                        <TableHead className="text-right w-[12%]">순이익</TableHead>
                        <TableHead className="text-right w-[12%]">광고비</TableHead>
                        <TableHead className="text-right w-[10%]">판매량</TableHead>
                        <TableHead className="text-right w-[9%]">마진율</TableHead>
                        <TableHead className="text-right w-[9%]">광고비율</TableHead>
                        <TableHead className="text-right w-[10%]">이윤율</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {metrics.by_product.map((product, index) => (
                        <TableRow
                          key={product.option_id === 0 ? `product-${product.product_name}` : `option-${product.option_id}`}
                          onClick={() => handleProductClick(product)}
                          className="cursor-pointer hover:bg-gray-100 transition-colors"
                        >
                          <TableCell>
                            <div className="max-w-full">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium">
                                  {product.product_name}
                                </span>
                                {index < 3 && (
                                  <Badge variant="default" className="bg-blue-500 shrink-0">
                                    #{index + 1}
                                  </Badge>
                                )}
                              </div>
                              {product.option_name && (
                                <p
                                  className="text-xs text-gray-500 truncate max-w-[250px]"
                                  title={product.option_name}
                                >
                                  {product.option_name}
                                </p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right font-semibold">
                            {formatCurrency(product.total_sales)}
                          </TableCell>
                          <TableCell
                            className={`text-right font-semibold ${
                              product.total_profit > 0 ? 'text-green-600' : 'text-red-600'
                            }`}
                          >
                            {formatCurrency(product.total_profit)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(product.total_ad_cost)}
                          </TableCell>
                          <TableCell className="text-right">{formatNumber(product.total_quantity)}</TableCell>
                          <TableCell className="text-right">
                            <Badge
                              variant={
                                product.cost_rate < 50
                                  ? 'default'
                                  : product.cost_rate < 70
                                  ? 'secondary'
                                  : 'destructive'
                              }
                              className={
                                product.cost_rate < 50
                                  ? 'bg-green-500'
                                  : product.cost_rate < 70
                                  ? 'bg-amber-500'
                                  : ''
                              }
                            >
                              {product.cost_rate.toFixed(1)}%
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge
                              variant={
                                product.ad_cost_rate < 10
                                  ? 'default'
                                  : product.ad_cost_rate < 20
                                  ? 'secondary'
                                  : 'destructive'
                              }
                              className={
                                product.ad_cost_rate < 10
                                  ? 'bg-green-500'
                                  : product.ad_cost_rate < 20
                                  ? 'bg-amber-500'
                                  : ''
                              }
                            >
                              {product.ad_cost_rate.toFixed(1)}%
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge
                              variant={
                                product.margin_rate > 30
                                  ? 'default'
                                  : product.margin_rate > 15
                                  ? 'secondary'
                                  : 'destructive'
                              }
                              className={
                                product.margin_rate > 30
                                  ? 'bg-green-500'
                                  : product.margin_rate > 15
                                  ? 'bg-amber-500'
                                  : ''
                              }
                            >
                              {product.margin_rate.toFixed(1)}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {metrics.by_product.length === 0 && (
                  <div className="py-8 text-center">
                    <p className="text-gray-500">이 기간에는 상품 데이터가 없습니다</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}

        {!metrics && !loading && (
          <Card className="shadow-lg bg-gray-50">
            <CardContent className="py-12 text-center">
              <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">데이터가 로드되지 않았습니다</h3>
              <p className="text-gray-500">
                기간을 선택하고 "분석 조회" 버튼을 클릭하여 상세 지표를 확인하세요
              </p>
            </CardContent>
          </Card>
        )}

        {/* Product Chart Modal */}
        <Dialog open={productChartOpen} onOpenChange={setProductChartOpen}>
          <DialogContent className="max-w-6xl sm:max-w-6xl">
            <DialogHeader>
              <DialogTitle>
                {selectedProduct?.product_name}
                {selectedProduct?.option_name && (
                  <p className="text-sm text-gray-500 font-normal mt-1">
                    {selectedProduct.option_name}
                  </p>
                )}
              </DialogTitle>
            </DialogHeader>
            <div className="mt-4">
              {loadingProductChart ? (
                <div className="flex justify-center items-center min-h-[400px]">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              ) : productChartData && productChartData.length > 0 ? (
                <SalesChart data={productChartData} />
              ) : (
                <div className="py-12 text-center">
                  <p className="text-gray-500">이 상품에 대한 데이터가 없습니다</p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button onClick={handleCloseProductChart} className="bg-blue-600 hover:bg-blue-700">
                닫기
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default DashboardPage;
