<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { 
    Chart, 
    BarController, 
    BarElement, 
    CategoryScale, 
    LinearScale,
    Title,
    Tooltip,
    Legend,
    type ChartData, 
    type ChartOptions 
  } from 'chart.js';
  
  // Register the required components
  Chart.register(
    BarController, 
    BarElement, 
    CategoryScale, 
    LinearScale,
    Title,
    Tooltip,
    Legend
  );
  
  export let data: ChartData;
  export let options: ChartOptions = {};
  export let height = '300px';
  
  let canvas: HTMLCanvasElement;
  let chart: Chart;
  
  onMount(() => {
    chart = new Chart(canvas, {
      type: 'bar',
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            mode: 'index',
            intersect: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true
          }
        },
        ...options
      }
    });
  });
  
  onDestroy(() => {
    if (chart) chart.destroy();
  });
  
  $: if (chart && data) {
    chart.data = data;
    chart.update();
  }
</script>

<div style="height: {height};">
  <canvas bind:this={canvas}></canvas>
</div> 