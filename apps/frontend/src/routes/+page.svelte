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

	onMount(() => {
		experimentActions.loadExperiments();
		metricActions.loadMetrics();
	});
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Dashboard</h1>

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
			valueColor="text-blue-600"
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
