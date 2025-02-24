<script lang="ts">
	import { onMount } from 'svelte';
	import { experiments, activeExperiments, completedExperiments } from '$lib/stores/experiments';
	import { metrics } from '$lib/stores/metrics';
	import { experimentActions } from '$lib/stores/experiments';
	import { metricActions } from '$lib/stores/metrics';
	import StatsCard from '../components/common/StatsCard.svelte';
	import SummaryList from '../components/common/SummaryList.svelte';
	import ExperimentSummary from '../components/dashboard/ExperimentSummary.svelte';
	import MetricSummary from '../components/dashboard/MetricSummary.svelte';

	let showWelcomeBanner = false;

	onMount(() => {
		experimentActions.loadExperiments();
		metricActions.loadMetrics();
		
		// TODO: At some point, this should be stored on the backend
		const hasSeenWelcome = localStorage.getItem('hasSeenWelcome');
		if (!hasSeenWelcome) {
			showWelcomeBanner = true;
		}
	});

	function dismissWelcome() {
		showWelcomeBanner = false;
		localStorage.setItem('hasSeenWelcome', 'true');
	}
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Dashboard</h1>

	{#if showWelcomeBanner}
		<div class="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg shadow-lg mb-8 overflow-hidden relative">
			<button 
				on:click={dismissWelcome}
				class="absolute top-2 right-2 text-white hover:text-blue-100 p-2"
				aria-label="Dismiss welcome message"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>
			<div class="p-6 flex flex-col md:flex-row items-center justify-between">
				<div class="text-white mb-4 md:mb-0">
					<h2 class="text-xl font-semibold mb-2">Welcome to Your Experimentation Platform! 🚀</h2>
					<p class="text-blue-100">Get started by trying our interactive demos to explore the platform's capabilities.</p>
				</div>
				<div class="flex space-x-4">
					<a href="/demo/platform" class="inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-md hover:bg-blue-50 transition-colors font-medium">
						Platform Demo
					</a>
					<a href="/demo/simulator" class="inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-md hover:bg-blue-50 transition-colors font-medium">
						Traffic Simulator
					</a>
				</div>
			</div>
		</div>
	{/if}

	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
		<StatsCard
			title="Total Experiments"
			value={$experiments.length}
		/>
		<StatsCard
			title="Active Experiments"
			value={$activeExperiments.length}
			valueColor="text-green-600"
		/>
		<StatsCard
			title="Completed Experiments"
			value={$completedExperiments.length}
			valueColor="text-blue-600"
		/>
		<StatsCard
			title="Available Metrics"
			value={$metrics.length}
		/>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<SummaryList
			title="Recent Experiments"
			viewAllLink="/experiments"
			items={$experiments.slice(0, 5)}
			emptyMessage="No experiments yet"
		>
			<svelte:fragment slot="default" let:items>
				{#each items as experiment}
					<ExperimentSummary {experiment} />
				{/each}
			</svelte:fragment>
		</SummaryList>

		<SummaryList
			title="Available Metrics"
			viewAllLink="/metrics"
			viewAllText="Manage metrics →"
			items={$metrics.slice(0, 5)}
			emptyMessage="No metrics defined yet"
		>
			<svelte:fragment slot="default" let:items>
				{#each items as metric}
					<MetricSummary {metric} />
				{/each}
			</svelte:fragment>
		</SummaryList>
	</div>
</div>
