<script lang="ts">
	import { goto } from '$app/navigation';
	import { metricActions } from '$lib/stores/metrics';
	import { loading, error, experimentActions } from '$lib/stores/experiments';
	import ExperimentForm from '../../../components/experiments/ExperimentForm.svelte';
	import FormLayout from '../../../components/common/FormLayout.svelte';
	import type { ExperimentCreate } from '../../../types/api';
	import { onMount } from 'svelte';

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

<FormLayout title="Create New Experiment" error={$error}>
	<ExperimentForm
		on:submit={handleSubmit}
		on:cancel={() => goto('/experiments')}
		loading={$loading}
	/>
</FormLayout> 