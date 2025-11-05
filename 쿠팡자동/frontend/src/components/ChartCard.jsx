// components/ChartCard.jsx (예시 - Chart.js 사용 가정)
import { Bar } from 'react-chartjs-2';

function ChartCard({ title, labels, values }) {
  const data = {
    labels,
    datasets: [{
      label: title,
      data: values,
      backgroundColor: 'rgba(54, 162, 235, 0.5)'
    }]
  };
  const options = { plugins: { legend: { display: false } } };
  return (
    <div className="chart-card">
      <h4>{title}</h4>
      <Bar data={data} options={options} />
    </div>
  );
}
