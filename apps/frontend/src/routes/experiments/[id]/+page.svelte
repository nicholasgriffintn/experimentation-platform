<script lang="ts">
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import { experimentResults, loading, error, experimentActions } from '$lib/stores/experiments';
	import type { Experiment, ExperimentSchedule } from '$lib/types/api';

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

	async function handlePauseExperiment(id: string) {
		const reason = prompt('Please provide a reason for pausing the experiment:');
		if (reason !== null) {
			await experimentActions.pauseExperiment(id, reason);
		}
	}

	async function handleResumeExperiment(id: string) {
		await experimentActions.resumeExperiment(id);
	}

	async function handleScheduleUpdate(id: string) {
		const defaultSchedule: Partial<ExperimentSchedule> = {
			start_time: undefined,
			end_time: undefined,
			ramp_up_period: undefined,
			auto_stop_conditions: undefined
		};
		const currentSchedule = experiment.schedule || defaultSchedule;
		const startTime = prompt('Enter start time (YYYY-MM-DD HH:mm):', 
			currentSchedule.start_time ? new Date(currentSchedule.start_time).toISOString().slice(0, 16) : ''
		);
		if (startTime === null) return;

		const endTime = prompt('Enter end time (YYYY-MM-DD HH:mm) or leave empty:', 
			currentSchedule.end_time ? new Date(currentSchedule.end_time).toISOString().slice(0, 16) : ''
		);
		if (endTime === null) return;

		const rampUpPeriod = prompt('Enter ramp up period in hours (optional):', 
			currentSchedule.ramp_up_period?.toString() || ''
		);
		if (rampUpPeriod === null) return;

		if (!startTime) {
			error.set('Start time is required');
			return;
		}

		const schedule: ExperimentSchedule = {
			start_time: new Date(startTime).toISOString(),
			end_time: endTime ? new Date(endTime).toISOString() : undefined,
			ramp_up_period: rampUpPeriod ? parseInt(rampUpPeriod) : undefined,
			auto_stop_conditions: undefined
		};

		await experimentActions.updateSchedule(id, schedule);
	}

	function getStatusClasses(status: Experiment['status']): string {
		switch (status) {
			case 'running':
				return 'bg-green-100 text-green-800';
			case 'completed':
				return 'bg-blue-100 text-blue-800';
			case 'stopped':
				return 'bg-red-100 text-red-800';
			case 'paused':
				return 'bg-yellow-100 text-yellow-800';
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
						<div class="flex space-x-2">
							<button
								on:click={() => handlePauseExperiment(experiment.id)}
								class="px-4 py-2 text-yellow-600 border border-yellow-600 rounded-md hover:bg-yellow-50"
							>
								Pause
							</button>
							<button
								on:click={() => handleStopExperiment(experiment.id)}
								class="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700"
							>
								Stop
							</button>
						</div>
					{:else if status === 'paused'}
						<button
							on:click={() => handleResumeExperiment(experiment.id)}
							class="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700"
						>
							Resume
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
					{#if experiment.schedule}
						<div class="bg-white p-6 rounded-lg shadow">
							<div class="flex justify-between items-center mb-4">
								<h2 class="text-xl font-semibold">Schedule</h2>
								<button
									on:click={() => handleScheduleUpdate(experiment.id)}
									class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
								>
									Edit Schedule
								</button>
							</div>
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
								{#if experiment.schedule.ramp_up_period}
									<div>
										<span class="font-medium">Ramp Up Period:</span>
										<div class="mt-1 text-gray-600">
											{experiment.schedule.ramp_up_period} hours
										</div>
									</div>
								{/if}
								{#if experiment.traffic_allocation}
									<div>
										<span class="font-medium">Traffic Allocation:</span>
										<div class="mt-1 text-gray-600">
										{experiment.traffic_allocation.toFixed(1)}% of eligible traffic
										</div>
									</div>
								{/if}
							</div>
						</div>
					{:else}
						<div class="bg-white p-6 rounded-lg shadow">
							<div class="flex justify-between items-center mb-4">
								<h2 class="text-xl font-semibold">Schedule</h2>
								<button
									on:click={() => handleScheduleUpdate(experiment.id)}
									class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
								>
									Add Schedule
								</button>
							</div>
							<p class="text-gray-600">No schedule configured</p>
						</div>
					{/if}

					<div class="bg-white p-6 rounded-lg shadow">
						<h2 class="text-xl font-semibold mb-4">Metrics</h2>
						{#if experiment.metrics?.length}
							<div class="space-y-2">
								<div class="mb-6">
									<h3 class="text-lg font-medium mb-3">Primary Metrics</h3>
									{#each experiment.metrics as metric}
										<div class="p-3 bg-gray-50 rounded-md">
											<span class="font-medium">{metric}</span>
										</div>
									{/each}
								</div>

								{#if experiment.guardrail_metrics?.length}
									<div>
										<h3 class="text-lg font-medium mb-3">Guardrail Metrics</h3>
										<div class="space-y-2">
											{#each experiment.guardrail_metrics as guardrail}
												<div class="p-3 bg-gray-50 rounded-md flex items-center justify-between">
													<span class="font-medium">{guardrail.metric_name}</span>
													<span class="text-gray-600">
														Must be {guardrail.operator} {guardrail.threshold}
													</span>
												</div>
											{/each}
										</div>
									</div>
								{/if}
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