import React, { useState, useEffect, forwardRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Percent,
  ShoppingCart,
  Megaphone,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  BarChart3,
  X,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import axios from 'axios';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Skeleton } from '../components/ui/skeleton';
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

// Animated counter
const AnimatedNumber = ({ value, suffix = '', prefix = '' }: { value: number; suffix?: string; prefix?: string }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number;
    let animationFrame: number;
    let isMounted = true;

    const animate = (currentTime: number) => {
      if (!isMounted) return;
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / 800, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.floor(value * easeOut));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => {
      isMounted = false;
      cancelAnimationFrame(animationFrame);
    };
  }, [value]);

  return (
    <span className="tracking-tight">
      {prefix}{displayValue.toLocaleString()}{suffix}
    </span>
  );
};

interface MetricCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  suffix?: string;
  prefix?: string;
  delay: number;
  accentColor: string;
}

const MetricCard = ({ title, value, icon, suffix = '', prefix = '', delay, accentColor }: MetricCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="relative group"
    >
      {/* Grain texture overlay */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none"
           style={{
             backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
           }}
      />

      {/* Glow effect on hover */}
      <div className={`absolute -inset-px bg-gradient-to-br ${accentColor} opacity-0 group-hover:opacity-20
                       blur-xl transition-opacity duration-500 rounded-lg`} />

      <div className="relative bg-[#1a1d23] border border-gray-800 rounded-lg p-5
                      group-hover:border-cyan-500/30 transition-all duration-300">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-lg bg-gray-800/50 border border-gray-700">
            {icon}
          </div>
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
            {title}
          </h3>
        </div>

        {/* Value */}
        <div className="text-3xl font-bold text-white mb-2">
          <AnimatedNumber value={value} suffix={suffix} prefix={prefix} />
        </div>

        {/* Bottom decoration */}
        <div className="absolute bottom-2 right-2 w-4 h-4 grid grid-cols-2 gap-[2px] opacity-10">
          <div className="bg-cyan-400 rounded-sm"></div>
          <div className="bg-cyan-400 rounded-sm"></div>
          <div className="bg-cyan-400 rounded-sm"></div>
          <div className="bg-cyan-400 rounded-sm"></div>
        </div>
      </div>
    </motion.div>
  );
};

// Custom DatePicker Input
interface CustomDateInputProps {
  value?: string;
  onClick?: () => void;
}

const CustomDateInput = forwardRef<HTMLInputElement, CustomDateInputProps>(
  ({ value, onClick }, ref) => (
    <div className="relative w-72">
      <Input
        ref={ref}
        value={value}
        onClick={onClick}
        placeholder="기간 선택"
        readOnly
        className="bg-gray-800 border-gray-700 text-white text-sm cursor-pointer
                   hover:border-cyan-500/50 transition-colors pr-10 w-full"
      />
      <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
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
  <div className="flex justify-between items-center px-3 py-2 bg-[#0f1115] border-b border-gray-800">
    <button
      onClick={decreaseMonth}
      disabled={prevMonthButtonDisabled}
      className="p-1 hover:bg-cyan-500/10 rounded disabled:opacity-30 disabled:cursor-not-allowed
                 transition-colors text-cyan-400 hover:text-cyan-300"
    >
      <ChevronLeft className="w-5 h-5" />
    </button>
    <span className="font-semibold text-cyan-400 text-sm tracking-wider">
      {format(monthDate, 'yyyy년 M월', { locale: ko })}
    </span>
    <button
      onClick={increaseMonth}
      disabled={nextMonthButtonDisabled}
      className="p-1 hover:bg-cyan-500/10 rounded disabled:opacity-30 disabled:cursor-not-allowed
                 transition-colors text-cyan-400 hover:text-cyan-300"
    >
      <ChevronRight className="w-5 h-5" />
    </button>
  </div>
);

// Toggle Switch Component
const ToggleSwitch = ({ checked, onChange, label }: { checked: boolean; onChange: (checked: boolean) => void; label: string }) => {
  return (
    <label className="flex items-center gap-3 cursor-pointer group">
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only peer"
        />
        <div className="w-11 h-6 bg-gray-800 rounded-full border border-gray-700 peer-checked:bg-cyan-600
                        peer-checked:border-cyan-500 transition-all duration-300 peer-focus:ring-2
                        peer-focus:ring-cyan-500/20"></div>
        <div className="absolute left-1 top-1 w-4 h-4 bg-gray-600 rounded-full transition-all duration-300
                        peer-checked:translate-x-5 peer-checked:bg-white"></div>
      </div>
      <span className="text-sm text-gray-400 group-hover:text-gray-200 transition-colors">
        {label}
      </span>
    </label>
  );
};

// Skeleton Loading Components
const MetricCardSkeleton = () => (
  <div className="relative group">
    <div className="relative bg-[#1a1d23] border border-gray-800 rounded-lg p-5">
      <div className="flex items-center gap-3 mb-4">
        <Skeleton className="w-10 h-10 rounded-lg" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="h-10 w-32 mb-2" />
      <div className="h-px bg-gray-800" />
    </div>
  </div>
);

const ChartSkeleton = () => (
  <div className="p-6 bg-[#1a1d23] border border-gray-800 rounded-lg">
    <div className="flex items-center gap-2 mb-6">
      <Skeleton className="w-1 h-6 rounded-full" />
      <Skeleton className="h-6 w-40" />
    </div>
    <Skeleton className="w-full h-[350px] mb-6" />
    <div className="flex gap-6 flex-wrap pt-4 border-t border-gray-800">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <Skeleton className="w-3 h-3 rounded-sm" />
          <div>
            <Skeleton className="h-3 w-20 mb-2" />
            <Skeleton className="h-5 w-24" />
          </div>
        </div>
      ))}
    </div>
  </div>
);

const TableSkeleton = () => (
  <div className="p-6 bg-[#1a1d23] border border-gray-800 rounded-lg">
    <Skeleton className="h-6 w-32 mb-4" />
    <div className="space-y-3">
      <div className="flex gap-4 pb-3 border-b border-gray-800">
        {[...Array(8)].map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex gap-4 py-3">
          {[...Array(8)].map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  </div>
);

// Sortable Table Header Component
interface SortableHeaderProps {
  column: keyof ProductMetric;
  label: string;
  sortBy: keyof ProductMetric | null;
  sortDirection: 'asc' | 'desc';
  onSort: (column: keyof ProductMetric) => void;
  align?: 'left' | 'right';
}

const SortableHeader = ({ column, label, sortBy, sortDirection, onSort, align = 'left' }: SortableHeaderProps) => {
  const isActive = sortBy === column;

  return (
    <th
      className={`px-6 py-4 text-${align} text-xs text-gray-400 uppercase tracking-wider
                  cursor-pointer hover:text-cyan-400 transition-colors select-none group`}
      onClick={() => onSort(column)}
    >
      <div className={`flex items-center gap-2 ${align === 'right' ? 'justify-end' : ''}`}>
        <span>{label}</span>
        <div className="w-4 h-4 flex items-center justify-center">
          {isActive ? (
            sortDirection === 'desc' ? (
              <ArrowDown className="w-3.5 h-3.5 text-cyan-400" />
            ) : (
              <ArrowUp className="w-3.5 h-3.5 text-cyan-400" />
            )
          ) : (
            <ArrowUpDown className="w-3.5 h-3.5 opacity-0 group-hover:opacity-50 transition-opacity" />
          )}
        </div>
      </div>
    </th>
  );
};

export default function DashboardPageRedesign() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [roasData, setRoasData] = useState<RoasData | null>(null);
  const [dateRange, setDateRange] = useState<[Date | null, Date | null]>([null, null]);
  const [startDate, endDate] = dateRange;
  const [groupBy, setGroupBy] = useState<'option' | 'product'>('option');
  const [includeFakePurchase, setIncludeFakePurchase] = useState(false);

  // Product chart modal
  const [selectedProduct, setSelectedProduct] = useState<ProductMetric | null>(null);
  const [productChartOpen, setProductChartOpen] = useState(false);
  const [productChartData, setProductChartData] = useState<DailyTrend[] | null>(null);
  const [loadingProductChart, setLoadingProductChart] = useState(false);

  // Table sorting
  const [sortBy, setSortBy] = useState<keyof ProductMetric | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    // Set default dates (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setDateRange([start, end]);
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      fetchMetrics();
    }
  }, [startDate, endDate, includeFakePurchase]);

  const handleGroupByChange = async (checked: boolean) => {
    const newGroupBy = checked ? 'product' : 'option';
    setGroupBy(newGroupBy);

    // Only refetch if we already have data loaded
    if (!metrics || !startDate || !endDate) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      const [metricsResponse, roasResponse] = await Promise.all([
        axios.get<MetricsResponse>(`${API_BASE_URL}/metrics`, {
          params: {
            start_date: startDateStr,
            end_date: endDateStr,
            group_by: newGroupBy,
            include_fake_purchase_adjustment: includeFakePurchase,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
          },
        }),
        axios.get<RoasData>(`${API_BASE_URL}/metrics/roas`, {
          params: {
            start_date: startDateStr,
            end_date: endDateStr,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
          },
        }),
      ]);

      setMetrics(metricsResponse.data);
      setRoasData(roasResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    if (!startDate || !endDate) return;

    setLoading(true);
    setError(null);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      const [metricsResponse, roasResponse] = await Promise.all([
        axios.get<MetricsResponse>(`${API_BASE_URL}/metrics`, {
          params: {
            start_date: startDateStr,
            end_date: endDateStr,
            group_by: groupBy,
            include_fake_purchase_adjustment: includeFakePurchase,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
          },
        }),
        axios.get<RoasData>(`${API_BASE_URL}/metrics/roas`, {
          params: {
            start_date: startDateStr,
            end_date: endDateStr,
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
          },
        }),
      ]);

      setMetrics(metricsResponse.data);
      setRoasData(roasResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = async (product: ProductMetric) => {
    if (!startDate || !endDate) return;

    setSelectedProduct(product);
    setProductChartOpen(true);
    setLoadingProductChart(true);

    try {
      const startDateStr = format(startDate, 'yyyy-MM-dd');
      const endDateStr = format(endDate, 'yyyy-MM-dd');

      const response = await axios.get(`${API_BASE_URL}/metrics/product-trend`, {
        params: {
          product_name: product.product_name,
          option_id: groupBy === 'option' ? product.option_id : null,
          start_date: startDateStr,
          end_date: endDateStr,
          include_fake_purchase_adjustment: includeFakePurchase,
        },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      setProductChartData(response.data.daily_trend || []);
    } catch (err: any) {
      console.error('Failed to fetch product trend:', err);
      setProductChartData([]);
    } finally {
      setLoadingProductChart(false);
    }
  };

  // Handle table sorting
  const handleSort = (column: keyof ProductMetric) => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('desc');
    }
  };

  // Get sorted products
  const getSortedProducts = () => {
    if (!metrics?.by_product) return [];

    const products = [...metrics.by_product];

    if (!sortBy) return products;

    return products.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return 0;
    });
  };

  if (loading && !metrics) {
    return (
      <div className="min-h-screen bg-[#0f1115] text-white">
        {/* Grain overlay */}
        <div className="fixed inset-0 opacity-[0.015] pointer-events-none"
             style={{
               backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
             }}
        />

        <div className="relative p-6 space-y-6">
          {/* Header Skeleton */}
          <div className="flex items-center justify-between mb-8">
            <Skeleton className="h-10 w-48" />
            <div className="flex gap-3">
              <Skeleton className="h-10 w-72" />
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-40" />
            </div>
          </div>

          {/* Metric Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <MetricCardSkeleton key={i} />
            ))}
          </div>

          {/* Chart Skeleton */}
          <ChartSkeleton />

          {/* Table Skeleton */}
          <TableSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1115] text-white">
      {/* Grain overlay */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none"
           style={{
             backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
           }}
      />

      {/* Compact Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative border-b border-gray-800/50 backdrop-blur-sm z-50"
      >
        <div className="w-full px-4 py-3">
          <div className="flex items-center justify-between flex-wrap gap-4 relative z-50">
            <div className="flex items-baseline gap-3">
              <h1 className="text-2xl md:text-3xl font-black tracking-tight"
                  style={{ fontFamily: 'Archivo Black, sans-serif' }}>
                DASHBOARD
              </h1>
              <span className="text-xs text-gray-500 uppercase tracking-widest">
                실시간 성과 분석
              </span>
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {/* Date Range Picker */}
              <div className="relative">
                <DatePicker
                  selectsRange
                  startDate={startDate}
                  endDate={endDate}
                  onChange={(update) => setDateRange(update)}
                  customInput={<CustomDateInput />}
                  dateFormat="yyyy-MM-dd"
                  placeholderText="기간을 선택하세요"
                  isClearable={false}
                  monthsShown={2}
                  shouldCloseOnSelect={false}
                  locale={ko}
                  renderCustomHeader={renderCustomHeader}
                  maxDate={new Date()}
                  withPortal
                  portalId="datepicker-portal"
                />
              </div>

              {/* Toggles */}
              <ToggleSwitch
                checked={groupBy === 'product'}
                onChange={handleGroupByChange}
                label={groupBy === 'product' ? '상품별' : '옵션별'}
              />

              <ToggleSwitch
                checked={includeFakePurchase}
                onChange={setIncludeFakePurchase}
                label="가구매 조정"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="w-full px-4 py-4">
        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 font-mono text-sm">
            {error}
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="총 매출"
            value={metrics?.total_sales || 0}
            icon={<DollarSign className="w-5 h-5 text-white" />}
            suffix="₩"
            delay={0.1}
            accentColor="from-cyan-500 to-blue-600"
          />

          <MetricCard
            title="순이익"
            value={metrics?.total_profit || 0}
            icon={<TrendingUp className="w-5 h-5 text-white" />}
            suffix="₩"
            delay={0.2}
            accentColor="from-emerald-500 to-teal-600"
          />

          <MetricCard
            title="광고비"
            value={metrics?.total_ad_cost || 0}
            icon={<Megaphone className="w-5 h-5 text-white" />}
            suffix="₩"
            delay={0.3}
            accentColor="from-amber-500 to-orange-600"
          />

          <MetricCard
            title="ROAS"
            value={roasData?.overall_roas || 0}
            icon={<Percent className="w-5 h-5 text-white" />}
            suffix="x"
            delay={0.4}
            accentColor="from-purple-500 to-pink-600"
          />

          <MetricCard
            title="마진율"
            value={metrics ? (((metrics.total_sales - (metrics.total_sales - metrics.total_profit - metrics.total_ad_cost * 1.1)) / metrics.total_sales) * 100) : 0}
            icon={<Percent className="w-5 h-5 text-white" />}
            suffix="%"
            delay={0.5}
            accentColor="from-violet-500 to-purple-600"
          />

          <MetricCard
            title="광고비율"
            value={metrics ? ((metrics.total_ad_cost / metrics.total_sales) * 100) : 0}
            icon={<Percent className="w-5 h-5 text-white" />}
            suffix="%"
            delay={0.6}
            accentColor="from-orange-500 to-red-600"
          />

          <MetricCard
            title="이윤율"
            value={metrics ? ((metrics.total_profit / metrics.total_sales) * 100) : 0}
            icon={<Percent className="w-5 h-5 text-white" />}
            suffix="%"
            delay={0.7}
            accentColor="from-teal-500 to-cyan-600"
          />

          <MetricCard
            title="총 판매량"
            value={metrics?.total_quantity || 0}
            icon={<ShoppingCart className="w-5 h-5 text-white" />}
            suffix="개"
            delay={0.8}
            accentColor="from-indigo-500 to-blue-600"
          />
        </div>

        {/* Sales Chart */}
        {metrics?.daily_trend && (
          <div className="relative bg-[#1a1d23] border border-gray-800 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              판매 추이
            </h3>
            <SalesChart data={metrics.daily_trend} />
          </div>
        )}

        {/* Product Table */}
        {metrics?.by_product && metrics.by_product.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="relative bg-[#1a1d23] border border-gray-800 rounded-lg overflow-hidden"
          >
            <div className="p-6">
              <h3 className="text-lg font-bold mb-4">상품별 성과</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-t border-b border-gray-800 bg-gray-900/50">
                    <SortableHeader
                      column="product_name"
                      label="상품명"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="left"
                    />
                    <SortableHeader
                      column="total_sales"
                      label="매출"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="total_profit"
                      label="순이익"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="total_ad_cost"
                      label="광고비"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="total_quantity"
                      label="수량"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="cost_rate"
                      label="마진율"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="ad_cost_rate"
                      label="광고비율"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                    <SortableHeader
                      column="margin_rate"
                      label="이윤율"
                      sortBy={sortBy}
                      sortDirection={sortDirection}
                      onSort={handleSort}
                      align="right"
                    />
                  </tr>
                </thead>
                <tbody>
                  {getSortedProducts().map((product, index) => (
                    <motion.tr
                      key={product.option_id === 0 ? `product-${index}-${product.product_name}` : `option-${product.option_id}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      onClick={() => handleProductClick(product)}
                      className="border-b border-gray-800/50 hover:bg-cyan-500/5 cursor-pointer
                                 transition-colors group"
                    >
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-white group-hover:text-cyan-400 transition-colors">
                            {product.product_name}
                          </div>
                          {product.option_name && (
                            <div className="text-sm text-gray-500">
                              {product.option_name}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        {product.total_sales.toLocaleString()}₩
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        <span className={product.total_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                          {product.total_profit.toLocaleString()}₩
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-amber-400">
                        {product.total_ad_cost.toLocaleString()}₩
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        {product.total_quantity.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        {product.cost_rate.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        {product.ad_cost_rate.toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        {product.margin_rate.toFixed(1)}%
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </div>

      {/* Product Trend Dialog */}
      <Dialog open={productChartOpen} onOpenChange={setProductChartOpen}>
        <DialogContent className="max-w-6xl sm:max-w-6xl w-full bg-[#1a1d23] border-gray-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              {selectedProduct?.product_name}
              {selectedProduct?.option_name && (
                <span className="text-sm text-gray-500">
                  - {selectedProduct.option_name}
                </span>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="mt-4">
            {loadingProductChart ? (
              <ChartSkeleton />
            ) : productChartData && productChartData.length > 0 ? (
              <SalesChart data={productChartData} />
            ) : (
              <div className="text-center text-gray-500 py-12">
                데이터가 없습니다
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Custom DatePicker Styles */}
      <style>{`
        /* Portal container - appears at document body level */
        .react-datepicker__portal {
          background-color: rgba(0, 0, 0, 0.8) !important;
          backdrop-filter: blur(4px);
          z-index: 99999 !important;
        }

        .react-datepicker__portal .react-datepicker {
          background-color: #1a1d23 !important;
          border: 1px solid #374151 !important;
          font-family: 'Spoqa Han Sans Neo', 'sans-serif', "Noto Sans KR" !important;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.9), 0 0 30px rgba(6, 182, 212, 0.2) !important;
          border-radius: 8px;
        }

        /* Regular datepicker (fallback) */
        .react-datepicker {
          background-color: #1a1d23 !important;
          border: 1px solid #374151 !important;
          font-family: 'Spoqa Han Sans Neo', 'sans-serif', "Noto Sans KR" !important;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4) !important;
        }

        .react-datepicker__header {
          background-color: #0f1115 !important;
          border-bottom: 1px solid #374151 !important;
          border-radius: 8px 8px 0 0;
        }

        .react-datepicker__current-month,
        .react-datepicker__day-name {
          color: #06b6d4 !important;
          font-weight: 600;
        }

        .react-datepicker__day {
          color: #d1d5db !important;
          transition: all 0.2s ease;
        }

        .react-datepicker__day:hover {
          background-color: #06b6d4 !important;
          color: white !important;
          transform: scale(1.05);
        }

        .react-datepicker__day--selected,
        .react-datepicker__day--in-range,
        .react-datepicker__day--range-start,
        .react-datepicker__day--range-end {
          background-color: #06b6d4 !important;
          color: white !important;
          font-weight: bold;
        }

        .react-datepicker__day--keyboard-selected {
          background-color: #0e7490 !important;
        }

        .react-datepicker__navigation {
          top: 13px;
        }

        .react-datepicker__navigation-icon::before {
          border-color: #06b6d4 !important;
        }
      `}</style>
    </div>
  );
}
