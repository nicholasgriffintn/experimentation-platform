import type { Experiment, MetricDefinition } from '../types/api';

/**
 * Calculates experiments launched per month over time
 */
export function getExperimentsPerMonth(experiments: Experiment[]): { date: string; count: number }[] {
  const monthCounts: Record<string, number> = {};
  
  experiments.forEach(exp => {
    const date = new Date(exp.created_at);
    const monthYear = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    if (!monthCounts[monthYear]) {
      monthCounts[monthYear] = 0;
    }
    monthCounts[monthYear]++;
  });
  
  return Object.entries(monthCounts)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/**
 * Calculates experiment completion rate over time (monthly)
 */
export function getCompletionRateByMonth(experiments: Experiment[]): { date: string; rate: number }[] {
  const monthData: Record<string, { completed: number; total: number }> = {};
  
  experiments.forEach(exp => {
    const date = new Date(exp.created_at);
    const monthYear = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    if (!monthData[monthYear]) {
      monthData[monthYear] = { completed: 0, total: 0 };
    }
    
    monthData[monthYear].total++;
    if (exp.status === 'completed') {
      monthData[monthYear].completed++;
    }
  });
  
  return Object.entries(monthData)
    .map(([date, data]) => ({ 
      date, 
      rate: data.total > 0 ? Math.round((data.completed / data.total) * 100) : 0 
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/**
 * Calculates average experiment duration in days
 */
export function getAverageExperimentDuration(experiments: Experiment[]): number {
  const completedExperiments = experiments.filter(exp => exp.status === 'completed' && exp.started_at && exp.ended_at);
  
  if (completedExperiments.length === 0) {
    return 0;
  }
  
  const totalDurationDays = completedExperiments.reduce((sum, exp) => {
    const startDate = new Date(exp.started_at!);
    const endDate = new Date(exp.ended_at!);
    const durationMs = endDate.getTime() - startDate.getTime();
    const durationDays = durationMs / (1000 * 60 * 60 * 24);
    return sum + durationDays;
  }, 0);
  
  return Math.round((totalDurationDays / completedExperiments.length) * 10) / 10;
}

/**
 * Calculates average metrics per experiment
 */
export function getAverageMetricsPerExperiment(experiments: Experiment[]): number {
  if (experiments.length === 0) {
    return 0;
  }
  
  const totalMetrics = experiments.reduce((sum, exp) => sum + exp.metrics.length, 0);
  return Math.round((totalMetrics / experiments.length) * 10) / 10; // Round to 1 decimal place
}

/**
 * Gets the most commonly used metrics across all experiments
 */
export function getTopMetrics(experiments: Experiment[], metrics: MetricDefinition[], limit = 5): { name: string; count: number }[] {
  const metricCounts: Record<string, number> = {};
  
  experiments.forEach(exp => {
    exp.metrics.forEach(metricName => {
      if (!metricCounts[metricName]) {
        metricCounts[metricName] = 0;
      }
      metricCounts[metricName]++;
    });
  });
  
  return Object.entries(metricCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
}

/**
 * Gets experiment status distribution
 */
export function getExperimentStatusDistribution(experiments: Experiment[]): { status: string; count: number }[] {
  const statusCounts: Record<string, number> = {};
  
  experiments.forEach(exp => {
    if (!statusCounts[exp.status]) {
      statusCounts[exp.status] = 0;
    }
    statusCounts[exp.status]++;
  });
  
  return Object.entries(statusCounts)
    .map(([status, count]) => ({ status, count }));
} 