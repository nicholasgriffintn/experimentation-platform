<script lang="ts">
    import { goto } from '$app/navigation';
    import { loading, error, metricActions } from '$lib/stores/metrics';
    import MetricForm from '$lib/components/metrics/MetricForm.svelte';
    import FormLayout from '$lib/components/common/FormLayout.svelte';
    import type { MetricDefinition } from '$lib/types/api';

    async function handleSubmit(event: CustomEvent<MetricDefinition>) {
        try {
            await metricActions.createMetric(event.detail);
            goto('/metrics');
        } catch (e) {
            // Error is handled by store
        }
    }
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-8">Create New Metric</h1>
	<FormLayout error={$error}>
		<MetricForm
			on:submit={handleSubmit}
			on:cancel={() => goto('/metrics')}
			loading={$loading}
        />
    </FormLayout> 
</div>