<script lang="ts">
  import { experiments, activeExperiments, completedExperiments } from '$lib/stores/experiments';
  import { metrics } from '$lib/stores/metrics';
  import LineChart from '$lib/components/common/LineChart.svelte';
  import BarChart from '$lib/components/common/BarChart.svelte';
  import DoughnutChart from '$lib/components/common/DoughnutChart.svelte';
  import { 
    getExperimentsPerMonth, 
    getCompletionRateByMonth, 
    getAverageExperimentDuration,
    getAverageMetricsPerExperiment,
    getTopMetrics,
    getExperimentStatusDistribution
  } from '$lib/utils/chartUtils';
  
  $: experimentsPerMonth = getExperimentsPerMonth($experiments);
  $: completionRateByMonth = getCompletionRateByMonth($experiments);
  $: avgDuration = getAverageExperimentDuration($experiments);
  $: avgMetricsPerExperiment = getAverageMetricsPerExperiment($experiments);
  $: topMetrics = getTopMetrics($experiments, $metrics);
  $: statusDistribution = getExperimentStatusDistribution($experiments);
  
  $: combinedTimelineData = {
    labels: experimentsPerMonth.map(item => {
      const [year, month] = item.date.split('-');
      return `${month}/${year.slice(2)}`;
    }),
    datasets: [
      {
        label: 'Experiments Launched',
        data: experimentsPerMonth.map(item => item.count),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        tension: 0.3,
        yAxisID: 'y'
      },
      {
        label: 'Completion Rate (%)',
        data: completionRateByMonth.map(item => {
          const matchingDate = experimentsPerMonth.find(exp => exp.date === item.date);
          return matchingDate ? item.rate : null;
        }),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.5)',
        tension: 0.3,
        yAxisID: 'y1'
      }
    ]
  };
  
  const combinedChartOptions = {
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Experiments'
        },
        beginAtZero: true
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Completion Rate (%)'
        },
        beginAtZero: true,
        max: 100,
        grid: {
          drawOnChartArea: false
        }
      }
    }
  };
  
  $: topMetricsData = {
    labels: topMetrics.map(item => item.name),
    datasets: [
      {
        label: 'Usage Count',
        data: topMetrics.map(item => item.count),
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(249, 115, 22, 0.7)',
          'rgba(139, 92, 246, 0.7)',
          'rgba(236, 72, 153, 0.7)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(249, 115, 22)',
          'rgb(139, 92, 246)',
          'rgb(236, 72, 153)'
        ],
        borderWidth: 1
      }
    ]
  };
  
  $: statusDistributionData = {
    labels: statusDistribution.map(item => item.status.charAt(0).toUpperCase() + item.status.slice(1)),
    datasets: [
      {
        label: 'Experiments',
        data: statusDistribution.map(item => item.count),
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(249, 115, 22, 0.7)',
          'rgba(139, 92, 246, 0.7)',
          'rgba(236, 72, 153, 0.7)',
          'rgba(75, 85, 99, 0.7)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(249, 115, 22)',
          'rgb(139, 92, 246)',
          'rgb(236, 72, 153)',
          'rgb(75, 85, 99)'
        ],
        borderWidth: 1
      }
    ]
  };
</script>

<div>
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Total</span>
      <span class="text-lg font-semibold">{$experiments.length}</span>
    </div>
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Active</span>
      <span class="text-lg font-semibold text-green-600">{$activeExperiments.length}</span>
    </div>
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Completed</span>
      <span class="text-lg font-semibold text-blue-600">{$completedExperiments.length}</span>
    </div>
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Avg. Duration</span>
      <span class="text-lg font-semibold text-blue-600">{avgDuration} days</span>
    </div>
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Available Metrics</span>
      <span class="text-lg font-semibold">{$metrics.length}</span>
    </div>
    <div class="bg-white p-3 rounded-lg shadow flex flex-col">
      <span class="text-sm text-gray-600">Avg. Metrics/Exp</span>
      <span class="text-lg font-semibold text-green-600">{avgMetricsPerExperiment}</span>
    </div>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="bg-white p-4 rounded-lg shadow lg:col-span-2">
      <h3 class="text-base font-semibold mb-2">Experiment Timeline</h3>
      <LineChart data={combinedTimelineData} options={combinedChartOptions} height="220px" />
    </div>
    
    <div class="bg-white p-4 rounded-lg shadow">
      <h3 class="text-base font-semibold mb-2">Status Distribution</h3>
      <DoughnutChart data={statusDistributionData} height="220px" />
    </div>
  </div>
  
  <div class="bg-white p-4 rounded-lg shadow mt-6">
    <h3 class="text-base font-semibold mb-2">Most Used Metrics</h3>
    <BarChart data={topMetricsData} height="180px" />
  </div>
</div> 