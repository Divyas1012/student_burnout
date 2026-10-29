/**
 * charts.js
 * Chart.js configurations styled to match Stitch project design system.
 * Palette: Forest Sage (#355f4d), Lavender Slate (#5b5a87), Warm Earth (#734f2d), Rose (#ba1a1a).
 */

let trendChartInstance = null;
let radarChartInstance = null;
let cohortChartInstance = null;
let benchmarkChartInstance = null;

export function renderTrendChart(canvasId, historyData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  // Generate 7 day labels starting 6 days ago up to Today
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const now = new Date();
  const labels = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    labels.push(i === 0 ? "Today" : dayNames[d.getDay()]);
  }

  // Default smooth 7-day baseline curves
  let cognitiveReserve = [82, 78, 72, 65, 58, 68, 75];
  let courseworkLoad = [45, 55, 68, 85, 78, 50, 40];
  let cognitiveFatigue = [18, 22, 28, 35, 42, 32, 25];

  if (historyData && historyData.length > 0) {
    const count = historyData.length;
    const latest = historyData[count - 1];
    const latestRisk = latest.risk_score !== null ? latest.risk_score : 25;
    const latestWorkload = (latest.academic_workload || 5) * 10;

    const step = count > 1 ? 6 / (count - 1) : 0;
    let realReserve = new Array(7).fill(null);
    let realLoad = new Array(7).fill(null);
    let realFatigue = new Array(7).fill(null);

    historyData.forEach((h, idx) => {
      const pos = count === 1 ? 6 : Math.min(6, Math.round(idx * step));
      const rScore = h.risk_score !== null ? h.risk_score : 25;
      const wLoad = (h.academic_workload || 5) * 10;

      realReserve[pos] = Math.max(10, Math.min(95, 100 - rScore));
      realLoad[pos] = Math.max(10, Math.min(95, wLoad));
      realFatigue[pos] = Math.max(5, Math.min(95, rScore));
    });

    const interpolate = (arr, defaultVal) => {
      let lastVal = defaultVal;
      for (let i = 0; i < 7; i++) {
        if (arr[i] !== null) {
          lastVal = arr[i];
        } else {
          arr[i] = lastVal;
        }
      }
      return arr;
    };

    cognitiveReserve = interpolate(realReserve, 100 - latestRisk);
    courseworkLoad = interpolate(realLoad, latestWorkload);
    cognitiveFatigue = interpolate(realFatigue, latestRisk);
  }

  const reserveGradient = ctx.createLinearGradient(0, 0, 0, 300);
  reserveGradient.addColorStop(0, "rgba(53, 95, 77, 0.28)");
  reserveGradient.addColorStop(1, "rgba(53, 95, 77, 0.02)");

  const fatigueGradient = ctx.createLinearGradient(0, 0, 0, 300);
  fatigueGradient.addColorStop(0, "rgba(186, 26, 26, 0.22)");
  fatigueGradient.addColorStop(1, "rgba(186, 26, 26, 0.01)");

  trendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Cognitive Reserve (%)",
          data: cognitiveReserve,
          borderColor: "#355f4d",
          backgroundColor: reserveGradient,
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#355f4d",
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2
        },
        {
          label: "Coursework Load",
          data: courseworkLoad,
          borderColor: "#5b5a87",
          backgroundColor: "transparent",
          borderWidth: 2.5,
          borderDash: [5, 5],
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: "#5b5a87",
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2
        },
        {
          label: "Cognitive Fatigue (%)",
          data: cognitiveFatigue,
          borderColor: "#ba1a1a",
          backgroundColor: fatigueGradient,
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: "#ba1a1a",
          pointBorderColor: "#ffffff",
          pointBorderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 10, bottom: 5, left: 10, right: 10 }
      },
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          position: "top",
          align: "end",
          labels: {
            boxWidth: 10,
            boxHeight: 10,
            usePointStyle: true,
            font: { family: "Plus Jakarta Sans", size: 11, weight: "600" },
            color: "#414944",
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: "#151d1a",
          titleFont: { family: "Manrope", size: 12, weight: "bold" },
          bodyFont: { family: "Plus Jakarta Sans", size: 11 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${Math.round(context.raw)}%`;
            }
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          grid: { color: "rgba(225, 234, 228, 0.7)", drawBorder: false },
          ticks: {
            callback: (val) => `${val}%`,
            font: { family: "Plus Jakarta Sans", size: 10 },
            color: "#717974",
            stepSize: 20
          }
        },
        x: {
          grid: { display: false, drawBorder: false },
          ticks: {
            font: { family: "Plus Jakarta Sans", size: 11, weight: "600" },
            color: "#414944"
          }
        }
      }
    }
  });
}

export function renderRadarChart(canvasId, surveyData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (radarChartInstance) {
    radarChartInstance.destroy();
  }

  const data = surveyData || {};
  const sleepHours = typeof data.sleep_hours_per_night === "number" ? data.sleep_hours_per_night : 7.5;
  const exerciseDays = typeof data.exercise_days === "number" ? data.exercise_days : 3;
  const socialSupport = typeof data.social_support === "number" ? data.social_support : 7;
  const moodEnergy = typeof data.mood_energy === "number" ? data.mood_energy : 7;
  const screenHours = typeof data.screen_time_hours === "number" ? data.screen_time_hours : 5.0;
  const workload = typeof data.academic_workload === "number" ? data.academic_workload : 5;

  const sleepNorm = Math.min(10, Math.max(1, (sleepHours / 8.5) * 10));
  const exerciseNorm = Math.min(10, Math.max(1, (exerciseDays / 5) * 10));
  const socialNorm = Math.min(10, Math.max(1, socialSupport));
  const moodNorm = Math.min(10, Math.max(1, moodEnergy));
  const screenBalanceNorm = Math.min(10, Math.max(1, 10 - (screenHours / 12) * 10));
  const workloadBalanceNorm = Math.min(10, Math.max(1, 10 - workload));

  radarChartInstance = new Chart(ctx, {
    type: "radar",
    data: {
      labels: [
        "Sleep Health",
        "Physical Vitality",
        "Social Buffering",
        "Emotional Valence",
        "Digital Balance",
        "Workload Margin"
      ],
      datasets: [{
        label: "Equilibrium Indices",
        data: [
          Math.round(sleepNorm),
          Math.round(exerciseNorm),
          Math.round(socialNorm),
          Math.round(moodNorm),
          Math.round(screenBalanceNorm),
          Math.round(workloadBalanceNorm)
        ],
        backgroundColor: "rgba(53, 95, 77, 0.25)",
        borderColor: "#355f4d",
        pointBackgroundColor: "#355f4d",
        pointBorderColor: "#ffffff",
        pointHoverBackgroundColor: "#ffffff",
        pointHoverBorderColor: "#355f4d",
        pointRadius: 4,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 10, bottom: 10, left: 10, right: 10 }
      },
      scales: {
        r: {
          angleLines: { color: "rgba(192, 200, 194, 0.6)" },
          grid: { color: "rgba(220, 229, 222, 0.8)" },
          suggestedMin: 0,
          suggestedMax: 10,
          ticks: { display: false, stepSize: 2 },
          pointLabels: {
            font: { family: "Plus Jakarta Sans", size: 11, weight: "600" },
            color: "#355f4d"
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#151d1a",
          titleFont: { family: "Manrope", size: 12 },
          bodyFont: { family: "Plus Jakarta Sans", size: 11 },
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}/10`;
            }
          }
        }
      }
    }
  });
}

export function renderCohortChart(canvasId, summary) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (cohortChartInstance) {
    cohortChartInstance.destroy();
  }

  const low = summary.low_risk_count || 0;
  const mod = summary.moderate_risk_count || 0;
  const high = summary.high_risk_count || 0;

  cohortChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Balanced (Low Risk)", "Watchlist (Moderate)", "Triage (High Risk)"],
      datasets: [{
        data: [low, mod, high],
        backgroundColor: ["#355f4d", "#ffdcbf", "#ffdad6"],
        borderWidth: 3,
        borderColor: "#f2fcf5",
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 12,
            usePointStyle: true,
            font: { family: "Plus Jakarta Sans", size: 11 },
            color: "#414944"
          }
        }
      }
    }
  });
}

export function renderBenchmarkChart(canvasId, benchmarkData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (benchmarkChartInstance) {
    benchmarkChartInstance.destroy();
  }

  if (!benchmarkData || !benchmarkData.models_benchmark) return;

  const models = Object.keys(benchmarkData.models_benchmark);
  const accuracies = models.map(m => (benchmarkData.models_benchmark[m].accuracy * 100).toFixed(1));
  const f1Scores = models.map(m => (benchmarkData.models_benchmark[m].f1_weighted * 100).toFixed(1));

  benchmarkChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: models,
      datasets: [
        {
          label: "Accuracy (%)",
          data: accuracies,
          backgroundColor: "#355f4d",
          borderRadius: 8,
        },
        {
          label: "Weighted F1 (%)",
          data: f1Scores,
          backgroundColor: "#5b5a87",
          borderRadius: 8,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 70,
          max: 100,
          ticks: {
            callback: (val) => `${val}%`,
            font: { family: "Plus Jakarta Sans", size: 10 }
          },
          grid: { color: "#e1eae4" }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: "Plus Jakarta Sans", size: 10 } }
        }
      },
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "Plus Jakarta Sans", size: 11 } }
        }
      }
    }
  });
}
