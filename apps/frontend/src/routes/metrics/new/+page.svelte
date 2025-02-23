<script lang="ts">
    import { goto } from '$app/navigation';
    import { loading, error, metricActions } from '$lib/stores/metrics';
    import MetricForm from '../../../components/metrics/MetricForm.svelte';
    import FormLayout from '../../../components/common/FormLayout.svelte';
    import type { MetricDefinition } from '../../../types/api';

    async function handleSubmit(event: CustomEvent<MetricDefinition>) {
        try {
            await metricActions.createMetric(event.detail);
            goto('/metrics');
        } catch (e) {
            // Error is handled by store
        }
    }
</script>

<FormLayout title="Create New Metric" error={$error}>
    <MetricForm
        on:submit={handleSubmit}
        on:cancel={() => goto('/metrics')}
        loading={$loading}
    />
</FormLayout> 