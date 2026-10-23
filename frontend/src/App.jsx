import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAnalysis() {
      try {
        const response = await fetch(`${API_URL}/api/analysis`);

        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        setAnalysis(data);
      } catch (err) {
        setError(err.message || "Unable to load wind forecast analysis.");
      } finally {
        setLoading(false);
      }
    }

    loadAnalysis();
  }, []);

  if (loading) {
    return <main className="status-screen">Loading wind forecast analysis...</main>;
  }

  if (error) {
    return (
      <main className="status-screen">
        <h2>Unable to load dashboard</h2>
        <p>{error}</p>
        <p>Check that the FastAPI backend is running on port 8000.</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </main>
    );
  }

  const metrics = analysis?.metrics ?? {};
  const records = analysis?.records ?? [];

  const chartData = records.map((record) => ({
    time: new Date(record.startTime).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    }),
    actual: Number(record.actual_generation.toFixed(0)),
    forecast: Number(record.forecast_generation.toFixed(0)),
  }));

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">ENERGY INTELLIGENCE</p>
          <h1>UK Wind Forecast Dashboard</h1>
          <p className="subtitle">
            Actual wind generation versus the latest eligible forecast
          </p>
        </div>
        <div className="period-badge">January 2026 · UTC</div>
      </header>

      <section className="notice">
        <strong>Forecast cutoff assumption:</strong> Latest forecast published
        by 10:00 UTC on the day before delivery. This is a configurable
        analytical assumption, not a confirmed market rule.
      </section>

      {analysis?.message && (
        <p className="analysis-message">{analysis.message}</p>
      )}

      <section className="metrics-grid">
        <MetricCard
          title="Mean Absolute Error"
          value={metrics.mae}
          unit="MW"
          description="Average forecast error magnitude"
        />
        <MetricCard
          title="Forecast Bias"
          value={metrics.bias}
          unit="MW"
          description="Negative means forecasts were higher than actuals"
        />
        <MetricCard
          title="Root Mean Squared Error"
          value={metrics.rmse}
          unit="MW"
          description="Penalises larger errors more heavily"
        />
        <MetricCard
          title="Mean Absolute Percentage Error"
          value={metrics.mape_percent}
          unit="%"
          description="Excludes intervals with zero actual generation"
        />
        <MetricCard
          title="Data Coverage"
          value={metrics.coverage_percent}
          unit="%"
          description={`${metrics.matched_intervals ?? 0} of ${
            metrics.expected_hourly_intervals ?? 744
          } hourly intervals matched`}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Actual vs Forecast Generation</h2>
            <p>Hourly wind generation across January 2026</p>
          </div>
          <span className="unit-label">MW</span>
        </div>

        {chartData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={380}>
              <LineChart
                data={chartData}
                margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  interval={71}
                  minTickGap={25}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="actual"
                  name="Actual generation"
                  stroke="#0f766e"
                  dot={false}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast generation"
                  stroke="#d97706"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p>No matching data is available to display.</p>
        )}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Forecast Comparison</h2>
            <p>First 20 matched delivery intervals</p>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Delivery time (UTC)</th>
                <th>Forecast published (UTC)</th>
                <th>Actual (MW)</th>
                <th>Forecast (MW)</th>
                <th>Error (MW)</th>
              </tr>
            </thead>
            <tbody>
              {records.slice(0, 20).map((record) => (
                <tr key={record.startTime}>
                  <td>{record.startTime.replace("T", " ").replace("Z", "")}</td>
                  <td>{record.publishTime.replace("T", " ").replace("Z", "")}</td>
                  <td>{record.actual_generation.toFixed(1)}</td>
                  <td>{record.forecast_generation.toFixed(1)}</td>
                  <td
                    className={
                      record.error > 0
                        ? "positive-error"
                        : record.error < 0
                          ? "negative-error"
                          : ""
                    }
                  >
                    {record.error.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <footer>
        <p>Source: Elexon BMRS · FUELHH and WINDFOR datasets</p>
        <p>
          Forecast error = actual generation − forecast generation. Results
          describe forecast accuracy, not financial trading performance.
        </p>
      </footer>
    </main>
  );
}

function MetricCard({ title, value, unit, description }) {
  const formattedValue =
    value === null || value === undefined || !Number.isFinite(Number(value))
      ? "N/A"
      : Number(value).toLocaleString("en-GB", {
          maximumFractionDigits: 2,
        });

  return (
    <article className="metric-card">
      <p className="metric-title">{title}</p>
      <p className="metric-value">
        {formattedValue}
        {formattedValue !== "N/A" && (
          <span className="metric-unit"> {unit}</span>
        )}
      </p>
      <p className="metric-description">{description}</p>
    </article>
  );
}

export default App;