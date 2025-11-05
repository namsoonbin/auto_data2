import svgPaths from "./svg-6jc3zu9i9z";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Chart data based on the design
const chartData = [
  { month: 'Jan', Chrome: 6000, Safari: 12000, Edge: 28000 },
  { month: 'Feb', Chrome: 14000, Safari: 12500, Edge: 30000 },
  { month: 'Mar', Chrome: 5000, Safari: 13000, Edge: 28500 },
  { month: 'Apr', Chrome: 28000, Safari: 25000, Edge: 35000 },
  { month: 'May', Chrome: 3500, Safari: 17000, Edge: 31000 },
  { month: 'Jun', Chrome: 17000, Safari: 19000, Edge: 29000 },
];

// Calculate totals
const totals = {
  Chrome: chartData.reduce((sum, item) => sum + item.Chrome, 0),
  Safari: chartData.reduce((sum, item) => sum + item.Safari, 0),
  Edge: chartData.reduce((sum, item) => sum + item.Edge, 0),
};

function LegendItem({ color, name }: { color: string; name: string }) {
  return (
    <div className="content-stretch flex gap-[12px] items-center relative shrink-0 w-[160px]">
      <div className="relative shrink-0 size-[16px]">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 16 16">
          <circle cx="8" cy="8" fill={color} r="8" />
        </svg>
      </div>
      <p className="font-['Albert_Sans:Medium',sans-serif] font-medium leading-[normal] opacity-[0.45] relative shrink-0 text-[#212123] text-[24px] text-nowrap whitespace-pre">{name}</p>
    </div>
  );
}

function MoreHoriz() {
  return (
    <div className="absolute right-[36px] size-[36px] top-[30px] cursor-pointer" data-name="more_horiz">
      <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 36 36">
        <g id="more_horiz">
          <mask height="36" id="mask0_1_74" maskUnits="userSpaceOnUse" style={{ maskType: "alpha" }} width="36" x="0" y="0">
            <rect fill="var(--fill-0, #D9D9D9)" height="36" id="Bounding box" width="36" />
          </mask>
          <g mask="url(#mask0_1_74)">
            <path d={svgPaths.p7679300} fill="var(--fill-0, #212123)" id="more_horiz_2" />
          </g>
        </g>
      </svg>
    </div>
  );
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-['Albert_Sans:Medium',sans-serif] mb-2">{payload[0].payload.month}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="font-['Albert_Sans:Regular',sans-serif]">
            {entry.name}: {entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Chart1() {
  return (
    <div className="bg-[#fcfcfc] overflow-clip relative rounded-[8px] size-full" data-name="Chart1">
      <p className="absolute font-['Albert_Sans:SemiBold',sans-serif] font-semibold leading-[normal] left-[32px] text-[#212123] text-[28px] text-nowrap top-[31px] whitespace-pre z-10">Browsers</p>
      
      {/* Legend */}
      <div className="absolute bottom-[94px] content-stretch flex gap-[40px] items-start left-[32px] z-10">
        <LegendItem color="#2268D1" name="Chrome" />
        <LegendItem color="#14A166" name="Safari" />
        <LegendItem color="#D122A0" name="Edge" />
      </div>
      
      <MoreHoriz />
      
      {/* Chart Container */}
      <div className="absolute bottom-[174px] left-[32px] right-[36px] h-[374px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid 
              strokeDasharray="5 5" 
              stroke="#979797" 
              vertical={false}
            />
            <XAxis 
              dataKey="month" 
              axisLine={false}
              tickLine={false}
              tick={{ 
                fill: '#979797', 
                fontFamily: 'Albert Sans, sans-serif',
                fontSize: 24
              }}
              dy={10}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ 
                fill: '#979797', 
                fontFamily: 'Albert Sans, sans-serif',
                fontSize: 24
              }}
              tickFormatter={(value) => `${value / 1000}k`}
              ticks={[0, 10000, 20000, 30000, 40000]}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="Chrome" 
              stroke="#2268D1" 
              strokeWidth={3}
              dot={{ fill: '#2268D1', r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="Safari" 
              stroke="#14A166" 
              strokeWidth={3}
              dot={{ fill: '#14A166', r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line 
              type="monotone" 
              dataKey="Edge" 
              stroke="#D122A0" 
              strokeWidth={3}
              dot={{ fill: '#D122A0', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Total Values */}
      <p className="absolute bottom-[75px] font-['Albert_Sans:Regular',sans-serif] font-normal leading-[normal] left-[34px] text-[#212123] text-[36px] text-nowrap translate-y-[100%] whitespace-pre">{totals.Chrome.toLocaleString()}</p>
      <p className="absolute bottom-[75px] font-['Albert_Sans:Regular',sans-serif] font-normal leading-[normal] left-[232px] text-[#212123] text-[36px] text-nowrap translate-y-[100%] whitespace-pre">{totals.Safari.toLocaleString()}</p>
      <p className="absolute bottom-[75px] font-['Albert_Sans:Regular',sans-serif] font-normal leading-[normal] left-[432px] text-[#212123] text-[36px] text-nowrap translate-y-[100%] whitespace-pre">{totals.Edge.toLocaleString()}</p>
    </div>
  );
}