<script lang="ts">
	import { onMount } from 'svelte';

	import { goto } from '$app/navigation';
	import { metricActions } from '$lib/stores/metrics';
	import { loading, error, experimentActions } from '$lib/stores/experiments';
	import ExperimentForm from '$lib/components/experiments/ExperimentForm.svelte';
	import FormLayout from '$lib/components/common/FormLayout.svelte';
	import type { ExperimentCreate } from '$lib/types/api';

	onMount(() => {
		metricActions.loadMetrics();
	});

	async function handleSubmit(event: CustomEvent<ExperimentCreate>) {
		try {
			const experiment = await experimentActions.createExperiment(event.detail);
			goto(`/experiments/${experiment.id}`);
		} catch (e) {
			// Error is handled by store
		}
	}
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Create New Experiment</h1>

	<FormLayout error={$error}>
		<ExperimentForm
			on:submit={handleSubmit}
			on:cancel={() => goto('/experiments')}
			loading={$loading}
		/>
	</FormLayout> 
</div>