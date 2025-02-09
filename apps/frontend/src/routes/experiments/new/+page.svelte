<script lang="ts">
	import { goto } from '$app/navigation';
	import { metricActions } from '$lib/stores/metrics';
	import { loading, error, experimentActions } from '$lib/stores/experiments';
	import ExperimentForm from '$lib/components/experiments/ExperimentForm.svelte';
	import type { ExperimentCreate } from '$lib/types/api';
	import { onMount } from 'svelte';

	onMount(() => {
		metricActions.loadMetrics();
	});

	async function handleSubmit(event: CustomEvent<ExperimentCreate>) {
		try {
			const experiment = await experimentActions.createExperiment(event.detail);
			goto(`/experiments/${experiment.id}`);
		} catch (e) {
			// Error is handled by the store
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<div class="flex justify-between items-center mb-8">
		<h1 class="text-3xl font-bold">Create New Experiment</h1>
	</div>

	{#if $error}
		<div class="p-4 mb-6 text-red-700 bg-red-100 rounded-md">
			{$error}
		</div>
	{/if}

	<div class="bg-white rounded-lg shadow">
		<div class="p-6">
			<ExperimentForm
				on:submit={handleSubmit}
				on:cancel={() => goto('/experiments')}
				loading={$loading}
			/>
		</div>
	</div>
</div> 