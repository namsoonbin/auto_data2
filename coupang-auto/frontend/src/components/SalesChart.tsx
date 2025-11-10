import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card } from './ui/card';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

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
function LegendItem({ color, name, total }: LegendItemProps) {
  const isQuantity = name.includes('판매량');
  return (
    <div className="flex items-center gap-1.5 min-w-[160px]">
      <div
        className="w-4 h-4 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      <div>
        <p className="text-sm text-muted-foreground opacity-70 whitespace-nowrap">
          {name}
        </p>
        <p className="text-xl font-semibold whitespace-nowrap">
          {Math.round(total).toLocaleString('ko-KR')}{isQuantity ? '개' : '원'}
        </p>
      </div>
    </div>
  );
}

// 커스텀 툴팁
const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const formattedDate = format(new Date(data.date), 'MM월 dd일', { locale: ko });

    return (
      <Card className="p-4 bg-white border shadow-lg">
        <p className="text-sm font-semibold mb-2">{formattedDate}</p>
        {payload.map((entry, index) => {
          const isQuantity = entry.name === '판매량';
          return (
            <div
              key={index}
              className="flex justify-between gap-4 text-sm mb-1"
              style={{ color: entry.color }}
            >
              <span>{entry.name}:</span>
              <span className="font-semibold">
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
    <Card className="p-6 bg-[#fcfcfc] rounded-lg relative min-h-[500px]">
      {/* 차트 제목 */}
      <h2 className="text-xl font-semibold mb-6 text-black">기간별 매출 추이</h2>

      {/* 차트 영역 */}
      <div className="w-full h-[350px] mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="5 5" stroke="#e0e0e0" vertical={false} />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: '#999',
                fontSize: 12,
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
                fill: '#999',
                fontSize: 12,
              }}
              tickFormatter={formatCurrency}
              domain={[0, yAxisMax]}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* 매출 라인 */}
            <Line
              type="monotone"
              dataKey="매출"
              stroke="#2268D1"
              strokeWidth={3}
              dot={{ fill: '#2268D1', r: 4 }}
              activeDot={{ r: 6 }}
              name="매출"
            />

            {/* 광고비 라인 */}
            <Line
              type="monotone"
              dataKey="광고비"
              stroke="#FF9800"
              strokeWidth={3}
              dot={{ fill: '#FF9800', r: 4 }}
              activeDot={{ r: 6 }}
              name="광고비"
            />

            {/* 순이익 라인 */}
            <Line
              type="monotone"
              dataKey="순이익"
              stroke="#14A166"
              strokeWidth={3}
              dot={{ fill: '#14A166', r: 4 }}
              activeDot={{ r: 6 }}
              name="순이익"
            />

            {/* 판매량 라인 */}
            <Line
              type="monotone"
              dataKey="판매량"
              stroke="#9C27B0"
              strokeWidth={3}
              dot={{ fill: '#9C27B0', r: 4 }}
              activeDot={{ r: 6 }}
              name="판매량"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 범례 및 총합 */}
      <div className="flex gap-5 flex-wrap justify-start pt-4 border-t border-gray-200">
        <LegendItem color="#2268D1" name="평균 매출" total={totals.매출} />
        <LegendItem color="#FF9800" name="평균 광고비" total={totals.광고비} />
        <LegendItem color="#14A166" name="평균 순이익" total={totals.순이익} />
        <LegendItem color="#9C27B0" name="평균 판매량" total={totals.판매량} />
      </div>
    </Card>
  );
}
