import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card } from './ui/card';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useTheme } from '../contexts/ThemeContext';

// Interfaces
interface DailyData {
  date: string | Date;
  total_sales: number;
  ad_cost: number;
  total_profit: number;
  total_quantity: number;
}

interface ChartDataPoint {
  date: string;
  매출: number;
  광고비: number;
  순이익: number;
  판매량: number;
}

interface SalesChartProps {
  data: DailyData[];
}

interface LegendItemProps {
  color: string;
  name: string;
  total: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    name: string;
    color: string;
    payload: ChartDataPoint;
  }>;
}

// 한국 원화 포맷팅
const formatCurrency = (value: number) => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(0)}K`;
  }
  return value.toLocaleString('ko-KR');
};

// 범례 아이템 컴포넌트
function LegendItem({ color, name, total, theme }: LegendItemProps & { theme: 'dark' | 'light' }) {
  const isQuantity = name.includes('판매량');
  return (
    <div className="flex items-center gap-2 min-w-[160px] group">
      <div
        className={`w-3 h-3 rounded-sm flex-shrink-0 transition-all ${
          theme === 'dark'
            ? 'shadow-[0_0_8px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_12px_rgba(6,182,212,0.6)]'
            : 'shadow-sm group-hover:shadow-md'
        }`}
        style={{ backgroundColor: color }}
      />
      <div>
        <p className={`text-xs tracking-wide whitespace-nowrap uppercase ${
          theme === 'dark' ? 'text-gray-500' : 'text-gray-600'
        }`}>
          {name}
        </p>
        <p className={`text-lg font-bold whitespace-nowrap ${
          theme === 'dark' ? 'text-white' : 'text-gray-900'
        }`}>
          {Math.round(total).toLocaleString('ko-KR')}{isQuantity ? '개' : '원'}
        </p>
      </div>
    </div>
  );
}

// 커스텀 툴팁
const CustomTooltip: React.FC<CustomTooltipProps & { theme: 'dark' | 'light' }> = ({ active, payload, theme }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const formattedDate = format(new Date(data.date), 'MM월 dd일', { locale: ko });

    return (
      <Card className={`p-4 shadow-lg ${
        theme === 'dark'
          ? 'bg-[#1a1d23] border-gray-700 shadow-[0_0_30px_rgba(6,182,212,0.3)]'
          : 'bg-white border-gray-300 shadow-xl'
      }`}>
        <p className={`text-sm font-bold mb-3 tracking-wide pb-2 ${
          theme === 'dark'
            ? 'text-cyan-400 border-b border-gray-800'
            : 'text-blue-600 border-b border-gray-200'
        }`}>
          {formattedDate}
        </p>
        {payload.map((entry, index) => {
          const isQuantity = entry.name === '판매량';
          return (
            <div
              key={index}
              className="flex justify-between gap-6 text-sm mb-2"
            >
              <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} style={{ color: entry.color }}>
                {entry.name}:
              </span>
              <span className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {Math.round(entry.value).toLocaleString('ko-KR')}{isQuantity ? '개' : '원'}
              </span>
            </div>
          );
        })}
      </Card>
    );
  }
  return null;
};

export default function SalesChart({ data }: SalesChartProps) {
  const { theme } = useTheme();

  // 차트 데이터 변환 (date를 문자열로 변환)
  const chartData: ChartDataPoint[] = data.map((item) => ({
    date: typeof item.date === 'string' ? item.date : item.date.toISOString().split('T')[0],
    매출: item.total_sales,
    광고비: item.ad_cost,
    순이익: item.total_profit,
    판매량: item.total_quantity,
  }));

  // 평균 계산
  const dataCount = chartData.length || 1;
  const totals = {
    매출: Math.round(chartData.reduce((sum, item) => sum + item.매출, 0) / dataCount),
    광고비: Math.round(chartData.reduce((sum, item) => sum + item.광고비, 0) / dataCount),
    순이익: Math.round(chartData.reduce((sum, item) => sum + item.순이익, 0) / dataCount),
    판매량: Math.round(chartData.reduce((sum, item) => sum + item.판매량, 0) / dataCount),
  };

  // Y축 최대값 계산 (가장 큰 값 기준, 판매량 제외)
  const maxValue = Math.max(
    ...chartData.map((item) => Math.max(item.매출, item.광고비, item.순이익))
  );
  const yAxisMax = Math.ceil((maxValue * 1.1) / 1000000) * 1000000;

  return (
    <Card className={`p-6 rounded-lg relative min-h-[500px] ${
      theme === 'dark'
        ? 'bg-[#1a1d23] border-gray-800 shadow-[0_0_20px_rgba(6,182,212,0.1)]'
        : 'bg-white border-gray-200 shadow-lg'
    }`}>
      {/* 차트 제목 */}
      <h2 className={`text-xl font-bold mb-6 tracking-wide flex items-center gap-2 ${
        theme === 'dark' ? 'text-cyan-400' : 'text-blue-600'
      }`}>
        <div className={`w-1 h-6 rounded-full ${
          theme === 'dark'
            ? 'bg-gradient-to-b from-cyan-400 to-cyan-600'
            : 'bg-gradient-to-b from-blue-500 to-blue-700'
        }`} />
        기간별 매출 추이
      </h2>

      {/* 차트 영역 */}
      <div className="w-full h-[350px] mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <defs>
              <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={theme === 'dark' ? '#06b6d4' : '#3b82f6'} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={theme === 'dark' ? '#06b6d4' : '#3b82f6'} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={theme === 'dark' ? '#374151' : '#e5e7eb'}
              vertical={false}
              opacity={theme === 'dark' ? 0.3 : 0.5}
            />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: theme === 'dark' ? '#6b7280' : '#6b7280',
                fontSize: 11,
                fontFamily: 'inherit',
              }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return format(date, 'MM/dd', { locale: ko });
              }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{
                fill: theme === 'dark' ? '#6b7280' : '#6b7280',
                fontSize: 11,
                fontFamily: 'inherit',
              }}
              tickFormatter={formatCurrency}
              domain={[0, yAxisMax]}
            />
            <Tooltip
              content={<CustomTooltip theme={theme} />}
              cursor={{
                stroke: theme === 'dark' ? '#06b6d4' : '#3b82f6',
                strokeWidth: 1,
                strokeDasharray: '5 5'
              }}
            />

            {/* 매출 라인 */}
            <Line
              type="monotone"
              dataKey="매출"
              stroke={theme === 'dark' ? '#06b6d4' : '#3b82f6'}
              strokeWidth={2.5}
              dot={{
                fill: theme === 'dark' ? '#06b6d4' : '#3b82f6',
                r: 3,
                strokeWidth: 2,
                stroke: theme === 'dark' ? '#0f1115' : '#ffffff'
              }}
              activeDot={{
                r: 5,
                fill: theme === 'dark' ? '#06b6d4' : '#3b82f6',
                stroke: '#fff',
                strokeWidth: 2
              }}
              name="매출"
            />

            {/* 광고비 라인 */}
            <Line
              type="monotone"
              dataKey="광고비"
              stroke={theme === 'dark' ? '#f59e0b' : '#f97316'}
              strokeWidth={2.5}
              dot={{
                fill: theme === 'dark' ? '#f59e0b' : '#f97316',
                r: 3,
                strokeWidth: 2,
                stroke: theme === 'dark' ? '#0f1115' : '#ffffff'
              }}
              activeDot={{
                r: 5,
                fill: theme === 'dark' ? '#f59e0b' : '#f97316',
                stroke: '#fff',
                strokeWidth: 2
              }}
              name="광고비"
            />

            {/* 순이익 라인 */}
            <Line
              type="monotone"
              dataKey="순이익"
              stroke={theme === 'dark' ? '#10b981' : '#22c55e'}
              strokeWidth={2.5}
              dot={{
                fill: theme === 'dark' ? '#10b981' : '#22c55e',
                r: 3,
                strokeWidth: 2,
                stroke: theme === 'dark' ? '#0f1115' : '#ffffff'
              }}
              activeDot={{
                r: 5,
                fill: theme === 'dark' ? '#10b981' : '#22c55e',
                stroke: '#fff',
                strokeWidth: 2
              }}
              name="순이익"
            />

            {/* 판매량 라인 */}
            <Line
              type="monotone"
              dataKey="판매량"
              stroke={theme === 'dark' ? '#a78bfa' : '#8b5cf6'}
              strokeWidth={2.5}
              dot={{
                fill: theme === 'dark' ? '#a78bfa' : '#8b5cf6',
                r: 3,
                strokeWidth: 2,
                stroke: theme === 'dark' ? '#0f1115' : '#ffffff'
              }}
              activeDot={{
                r: 5,
                fill: theme === 'dark' ? '#a78bfa' : '#8b5cf6',
                stroke: '#fff',
                strokeWidth: 2
              }}
              name="판매량"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 범례 및 총합 */}
      <div className={`flex gap-6 flex-wrap justify-start pt-4 border-t ${
        theme === 'dark' ? 'border-gray-800' : 'border-gray-200'
      }`}>
        <LegendItem
          color={theme === 'dark' ? '#06b6d4' : '#3b82f6'}
          name="평균 매출"
          total={totals.매출}
          theme={theme}
        />
        <LegendItem
          color={theme === 'dark' ? '#f59e0b' : '#f97316'}
          name="평균 광고비"
          total={totals.광고비}
          theme={theme}
        />
        <LegendItem
          color={theme === 'dark' ? '#10b981' : '#22c55e'}
          name="평균 순이익"
          total={totals.순이익}
          theme={theme}
        />
        <LegendItem
          color={theme === 'dark' ? '#a78bfa' : '#8b5cf6'}
          name="평균 판매량"
          total={totals.판매량}
          theme={theme}
        />
      </div>
    </Card>
  );
}
