import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Box, Typography, Paper } from '@mui/material'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

// 한국 원화 포맷팅
const formatCurrency = (value) => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(0)}K`
  }
  return value.toLocaleString('ko-KR')
}

// 범례 아이템 컴포넌트
function LegendItem({ color, name, total }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: '160px' }}>
      <Box
        sx={{
          width: 16,
          height: 16,
          borderRadius: '50%',
          backgroundColor: color,
          flexShrink: 0
        }}
      />
      <Box>
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            opacity: 0.7,
            fontSize: '0.875rem',
            whiteSpace: 'nowrap'
          }}
        >
          {name}
        </Typography>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            fontSize: '1.25rem',
            whiteSpace: 'nowrap'
          }}
        >
          {Math.round(total).toLocaleString('ko-KR')}원
        </Typography>
      </Box>
    </Box>
  )
}

// 커스텀 툴팁
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const formattedDate = format(new Date(data.date), 'MM월 dd일', { locale: ko })

    return (
      <Paper
        elevation={3}
        sx={{
          p: 2,
          backgroundColor: 'white',
          border: '1px solid',
          borderColor: 'grey.200'
        }}
      >
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          {formattedDate}
        </Typography>
        {payload.map((entry, index) => (
          <Typography
            key={index}
            variant="body2"
            sx={{
              color: entry.color,
              display: 'flex',
              justifyContent: 'space-between',
              gap: 2,
              mb: 0.5
            }}
          >
            <span>{entry.name}:</span>
            <span style={{ fontWeight: 600 }}>
              {Math.round(entry.value).toLocaleString('ko-KR')}원
            </span>
          </Typography>
        ))}
      </Paper>
    )
  }
  return null
}

export default function SalesChart({ data }) {
  // 차트 데이터 변환 (date를 문자열로 변환)
  const chartData = data.map(item => ({
    ...item,
    date: typeof item.date === 'string' ? item.date : item.date.toISOString().split('T')[0],
    매출: item.total_sales,
    광고비: item.ad_cost,
    순이익: item.total_profit
  }))

  // 평균 계산
  const dataCount = chartData.length || 1
  const totals = {
    매출: Math.round(chartData.reduce((sum, item) => sum + item.매출, 0) / dataCount),
    광고비: Math.round(chartData.reduce((sum, item) => sum + item.광고비, 0) / dataCount),
    순이익: Math.round(chartData.reduce((sum, item) => sum + item.순이익, 0) / dataCount)
  }

  // Y축 최대값 계산 (가장 큰 값 기준)
  const maxValue = Math.max(
    ...chartData.map(item => Math.max(item.매출, item.광고비, item.순이익))
  )
  const yAxisMax = Math.ceil(maxValue * 1.1 / 1000000) * 1000000

  return (
    <Paper
      sx={{
        p: 3,
        backgroundColor: '#fcfcfc',
        borderRadius: 2,
        position: 'relative',
        minHeight: '500px'
      }}
    >
      {/* 차트 제목 */}
      <Typography
        variant="h5"
        sx={{
          fontWeight: 600,
          mb: 3,
          color: 'text.primary'
        }}
      >
        기간별 매출 추이
      </Typography>

      {/* 차트 영역 */}
      <Box sx={{ width: '100%', height: 350, mb: 3 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="5 5"
              stroke="#e0e0e0"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: '#999',
                fontSize: 12
              }}
              tickFormatter={(value) => {
                const date = new Date(value)
                return format(date, 'MM/dd', { locale: ko })
              }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{
                fill: '#999',
                fontSize: 12
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
          </LineChart>
        </ResponsiveContainer>
      </Box>

      {/* 범례 및 총합 */}
      <Box
        sx={{
          display: 'flex',
          gap: 5,
          flexWrap: 'wrap',
          justifyContent: 'flex-start',
          pt: 2,
          borderTop: '1px solid',
          borderColor: 'grey.200'
        }}
      >
        <LegendItem color="#2268D1" name="평균 매출" total={totals.매출} />
        <LegendItem color="#FF9800" name="평균 광고비" total={totals.광고비} />
        <LegendItem color="#14A166" name="평균 순이익" total={totals.순이익} />
      </Box>
    </Paper>
  )
}
