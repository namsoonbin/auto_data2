// pages/DashboardPage.jsx (일부 발췌)
import { useState, useEffect } from 'react';
import Dashboard from '../components/Dashboard';

function DashboardPage() {
  const [filter, setFilter] = useState({ store: null, product: null, range: 'month' });
  const [metrics, setMetrics] = useState(null);

  const fetchMetrics = async () => {
    const params = new URLSearchParams();
    if (filter.store) params.append("store", filter.store);
    if (filter.product) params.append("product", filter.product);
    // 예: range가 'month'이면 최근 한달, 구체적 날짜 선택 시 start, end 설정 등
    params.append("start_date", "2023-10-01");
    params.append("end_date", "2023-10-31");
    const res = await fetch(`/metrics?${params.toString()}`);
    const data = await res.json();
    setMetrics(data);
  };

  useEffect(() => { fetchMetrics(); }, [filter]);

  return (
    <div>
      {/* 필터 UI (스토어 선택, 상품 선택, 기간 선택 등) */}
      <Dashboard data={metrics} />
    </div>
  );
}
