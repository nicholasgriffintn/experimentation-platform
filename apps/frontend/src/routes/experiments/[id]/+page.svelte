<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import { experimentResults, loading, error, experimentActions } from '$lib/stores/experiments';
	import type { Experiment } from '$lib/types/api';

	export let data: PageData;
	$: experiment = data.experiment as Experiment;

	onMount(async () => {
		await loadExperimentData();
	});

	async function loadExperimentData() {
		await experimentActions.loadExperimentResults(experiment.id);
	}

	async function handleStopExperiment(id: string) {
		const reason = prompt('Please provide a reason for stopping the experiment:');
		if (reason !== null) {
			await experimentActions.stopExperiment(id, reason);
		}
	}

	function getStatusClasses(status: Experiment['status']): string {
		switch (status) {
			case 'running':
				return 'bg-green-100 text-green-800';
			case 'completed':
				return 'bg-blue-100 text-blue-800';
			case 'stopped':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	{#if $error}
		<div class="p-4 mb-6 text-red-700 bg-red-100 rounded-md">
			{$error}
		</div>
	{/if}

	{#if $loading}
		<div class="text-center py-12">
			<span class="inline-block animate-spin text-4xl">⌛</span>
			<p class="mt-4 text-gray-600">Loading experiment data...</p>
		</div>
	{:else}
		{@const status = experiment.status}
		<div class="space-y-8">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold">{experiment.name}</h1>
					<p class="text-gray-600 mt-2">{experiment.description}</p>
					{#if experiment.hypothesis}
						<p class="mt-4 text-gray-700">
							<strong>Hypothesis:</strong> {experiment.hypothesis}
						</p>
					{/if}
				</div>
				<div class="flex items-center space-x-4">
					<span class="px-3 py-1 text-sm rounded-full {getStatusClasses(status)}">
						{status}
					</span>
					{#if status === 'running'}
						<button
							on:click={() => handleStopExperiment(experiment.id)}
							class="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700"
						>
							Stop Experiment
						</button>
					{/if}
				</div>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-8">
				<div class="bg-white p-6 rounded-lg shadow">
					<h2 class="text-xl font-semibold mb-4">Variants</h2>
					{#if experiment.variants?.length}
						<div class="space-y-4">
							{#each experiment.variants as variant}
								<div class="p-4 border rounded-md">
									<div class="flex justify-between items-center mb-2">
										<h3 class="font-medium">{variant.name}</h3>
										<span class="text-sm text-gray-600">
											{variant.traffic_percentage}% traffic
										</span>
									</div>
									{#if Object.keys(variant.config || {}).length > 0}
										<div class="mt-2">
											<h4 class="text-sm font-medium text-gray-700 mb-2">Configuration</h4>
											<div class="bg-gray-50 p-3 rounded-md">
												<pre class="text-sm">{JSON.stringify(variant.config, null, 2)}</pre>
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-gray-600">No variants configured</p>
					{/if}
				</div>

				<div class="space-y-8">
					{#if experiment.schedule?.start_time || experiment.schedule?.end_time}
						<div class="bg-white p-6 rounded-lg shadow">
							<h2 class="text-xl font-semibold mb-4">Schedule</h2>
							<div class="grid gap-4">
								{#if experiment.schedule.start_time}
									<div>
										<span class="font-medium">Start Time:</span>
										<div class="mt-1 text-gray-600">
											{new Date(experiment.schedule.start_time).toLocaleString()}
										</div>
									</div>
								{/if}
								{#if experiment.schedule.end_time}
									<div>
										<span class="font-medium">End Time:</span>
										<div class="mt-1 text-gray-600">
											{new Date(experiment.schedule.end_time).toLocaleString()}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/if}

					<div class="bg-white p-6 rounded-lg shadow">
						<h2 class="text-xl font-semibold mb-4">Metrics</h2>
						{#if experiment.metrics?.length}
							<div class="space-y-2">
								{#each experiment.metrics as metric}
									<div class="p-3 bg-gray-50 rounded-md">
										<span class="font-medium">{metric}</span>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-gray-600">No target metrics configured</p>
						{/if}
					</div>
				</div>
			</div>

			{#if $experimentResults[experiment.id]?.metrics}
				<div class="bg-white p-6 rounded-lg shadow">
					<h2 class="text-xl font-semibold mb-6">Results</h2>
					<div class="space-y-6">
						{#each Object.entries($experimentResults[experiment.id].metrics) as [metricName, metricResult]}
							<div class="border-b pb-6 last:border-b-0">
								<h3 class="font-medium mb-4">{metricName}</h3>
								<div class="grid gap-4">
									{#each Object.entries(metricResult) as [variantId, result]}
										<div class="p-4 bg-gray-50 rounded-md">
											<h4 class="font-medium mb-2">Variant: {variantId}</h4>
											<div class="grid gap-2">
												<div class="flex items-center justify-between">
													<span>Control Mean:</span>
													<span class="font-medium">{result.control_mean}</span>
												</div>
												<div class="flex items-center justify-between">
													<span>Variant Mean:</span>
													<span class="font-medium">{result.variant_mean}</span>
												</div>
												<div class="flex items-center justify-between">
													<span>Relative Difference:</span>
													<span class="font-medium">{result.relative_difference}%</span>
												</div>
												<div class="flex items-center justify-between">
													<span>P-value:</span>
													<span class="font-medium">{result.p_value}</span>
												</div>
												{#if result.confidence_interval}
													<div class="flex items-center justify-between">
														<span>Confidence Interval:</span>
														<span class="font-medium">
															[{result.confidence_interval[0]}, {result.confidence_interval[1]}]
														</span>
													</div>
												{/if}
												<div class="flex items-center justify-between">
													<span>Sample Size:</span>
													<span class="font-medium">{JSON.stringify(result.sample_size)}</span>
												</div>
												<div class="flex items-center justify-between">
													<span>Power:</span>
													<span class="font-medium">{result.power}</span>
												</div>
												<div class="flex items-center justify-between">
													<span>Significant:</span>
													<span class="font-medium">{result.is_significant ? 'Yes' : 'No'}</span>
												</div>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			{#if experiment.stopped_reason}
				<div class="bg-white p-6 rounded-lg shadow">
					<h2 class="text-xl font-semibold mb-4">Stop Reason</h2>
					<p class="text-gray-600">{experiment.stopped_reason}</p>
				</div>
			{/if}
		</div>
	{/if}
</div> 