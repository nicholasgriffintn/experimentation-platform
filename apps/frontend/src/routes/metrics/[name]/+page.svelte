<script lang="ts">
    import { goto } from '$app/navigation';
    import { loading, error, metricActions } from '$lib/stores/metrics';
    import type { PageData } from './$types';
    import type { MetricDefinition } from '../../../types/api';
    import MetricForm from '../../../components/metrics/MetricForm.svelte';
    import Button from '../../../components/common/Button.svelte';

    export let data: PageData;
    $: metric = data.metric as MetricDefinition;

    let isEditing = false;

    async function handleUpdate(event: CustomEvent<MetricDefinition>) {
        try {
            await metricActions.updateMetric(metric.name, event.detail);
            isEditing = false;
        } catch (e) {
            // Error handled by store
        }
    }

    async function handleDelete() {
        if (!confirm(`Are you sure you want to delete the metric "${metric.name}"?`)) {
            return;
        }
        try {
            await metricActions.deleteMetric(metric.name);
            goto('/metrics');
        } catch (e) {
            // Error handled by store
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
            <p class="mt-4 text-gray-600">Loading metric data...</p>
        </div>
    {:else}
        <div class="space-y-6">
            <div class="flex justify-between items-start">
                <div>
                    <h1 class="text-3xl font-bold">{metric.name}</h1>
                    <p class="text-gray-600 mt-2">{metric.description}</p>
                </div>
                <div class="flex space-x-4">
                    {#if !isEditing}
                        <Button
                            variant="outline"
                            on:click={() => isEditing = true}
                        >
                            Edit Metric
                        </Button>
                        <Button
                            variant="danger"
                            on:click={handleDelete}
                        >
                            Delete Metric
                        </Button>
                    {/if}
                </div>
            </div>

            {#if isEditing}
                <div class="bg-white rounded-lg shadow">
                    <div class="p-6">
                        <h2 class="text-xl font-semibold mb-4">Edit Metric</h2>
                        <MetricForm
                            {metric}
                            on:submit={handleUpdate}
                            on:cancel={() => isEditing = false}
                            loading={$loading}
                            submitLabel="Update Metric"
                        />
                    </div>
                </div>
            {:else}
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h2 class="text-xl font-semibold mb-4">Details</h2>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <h3 class="font-medium text-gray-700">Unit</h3>
                                <p class="mt-1">{metric.unit}</p>
                            </div>
                            <div>
                                <h3 class="font-medium text-gray-700">Data Type</h3>
                                <p class="mt-1">{metric.data_type}</p>
                            </div>
                            <div>
                                <h3 class="font-medium text-gray-700">Aggregation Method</h3>
                                <p class="mt-1">{metric.aggregation_method}</p>
                            </div>
                            {#if metric.min_sample_size}
                                <div>
                                    <h3 class="font-medium text-gray-700">Minimum Sample Size</h3>
                                    <p class="mt-1">{metric.min_sample_size.toLocaleString()}</p>
                                </div>
                            {/if}
                            {#if metric.min_effect_size}
                                <div>
                                    <h3 class="font-medium text-gray-700">Minimum Effect Size</h3>
                                    <p class="mt-1">{(metric.min_effect_size * 100).toFixed(1)}%</p>
                                </div>
                            {/if}
                        </div>
                    </div>

                    <div class="bg-white p-6 rounded-lg shadow">
                        <h2 class="text-xl font-semibold mb-4">Query Template</h2>
                        <pre class="p-4 bg-gray-50 rounded text-sm font-mono overflow-x-auto whitespace-pre-wrap break-all">
                            {metric.query_template}
                        </pre>
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div> 