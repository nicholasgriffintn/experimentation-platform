<script lang="ts">
	import { onMount } from 'svelte';
	import { experiments, activeExperiments, completedExperiments } from '$lib/stores/experiments';
	import { metrics } from '$lib/stores/metrics';
	import { experimentActions } from '$lib/stores/experiments';
	import { metricActions } from '$lib/stores/metrics';

	onMount(() => {
		experimentActions.loadExperiments();
		metricActions.loadMetrics();
	});
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Dashboard</h1>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
		<div class="bg-white p-6 rounded-lg shadow">
			<h3 class="text-lg font-medium text-gray-900">Total Experiments</h3>
			<p class="mt-2 text-3xl font-semibold">{$experiments.length}</p>
		</div>
		<div class="bg-white p-6 rounded-lg shadow">
			<h3 class="text-lg font-medium text-gray-900">Active Experiments</h3>
			<p class="mt-2 text-3xl font-semibold text-green-600">{$activeExperiments.length}</p>
		</div>
		<div class="bg-white p-6 rounded-lg shadow">
			<h3 class="text-lg font-medium text-gray-900">Completed Experiments</h3>
			<p class="mt-2 text-3xl font-semibold text-green-600">{$completedExperiments.length}</p>
		</div>
		<div class="bg-white p-6 rounded-lg shadow">
			<h3 class="text-lg font-medium text-gray-900">Available Metrics</h3>
			<p class="mt-2 text-3xl font-semibold text-blue-600">{$metrics.length}</p>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<div class="bg-white p-6 rounded-lg shadow">
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-xl font-semibold">Recent Experiments</h2>
				<a 
					href="/experiments" 
					class="text-sm text-blue-600 hover:text-blue-800"
				>
					View all →
				</a>
			</div>
			{#if $experiments.length === 0}
				<p class="text-gray-500">No experiments yet</p>
			{:else}
				<div class="space-y-4">
					{#each $experiments.slice(0, 5) as experiment}
						<div class="border-b pb-4 last:border-b-0">
							<div class="flex justify-between items-start">
								<div>
									<h3 class="font-medium">{experiment.name}</h3>
									<p class="text-sm text-gray-600">{experiment.description}</p>
								</div>
								<span class="px-2 py-1 text-sm rounded-full
									{experiment.status === 'running' ? 'bg-green-100 text-green-800' :
									experiment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
									experiment.status === 'stopped' ? 'bg-red-100 text-red-800' :
									'bg-gray-100 text-gray-800'}">
									{experiment.status}
								</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<div class="bg-white p-6 rounded-lg shadow">
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-xl font-semibold">Available Metrics</h2>
				<a 
					href="/metrics" 
					class="text-sm text-blue-600 hover:text-blue-800"
				>
					Manage metrics →
				</a>
			</div>
			{#if $metrics.length === 0}
				<p class="text-gray-500">No metrics defined yet</p>
			{:else}
				<div class="space-y-4">
					{#each $metrics.slice(0, 5) as metric}
						<div class="border-b pb-4 last:border-b-0">
							<h3 class="font-medium">{metric.name}</h3>
							<p class="text-sm text-gray-600">{metric.description}</p>
							<div class="mt-1 flex space-x-2">
								<span class="text-xs px-2 py-1 bg-gray-100 rounded-full">
									{metric.unit}
								</span>
								<span class="text-xs px-2 py-1 bg-gray-100 rounded-full">
									{metric.aggregation_method}
								</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
