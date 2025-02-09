<script lang="ts">
    import { onMount } from 'svelte';
    import { metrics, loading, error, metricActions } from '$lib/stores/metrics';
    import MetricForm from './MetricForm.svelte';
    import type { MetricDefinition } from '$lib/types/api';

    export let initialMetrics: MetricDefinition[] | undefined = undefined;

    let showCreateForm = false;
    let editingMetric: MetricDefinition | null = null;

    onMount(() => {
        if (initialMetrics) {
            metrics.set(initialMetrics);
        } else {
            metricActions.loadMetrics();
        }
    });

    async function handleCreate(event: CustomEvent<MetricDefinition>) {
        try {
            await metricActions.createMetric(event.detail);
            showCreateForm = false;
        } catch (e) {
        }
    }

    async function handleUpdate(event: CustomEvent<MetricDefinition>) {
        if (!editingMetric) return;
        try {
            await metricActions.updateMetric(editingMetric.name, event.detail);
            editingMetric = null;
        } catch (e) {
        }
    }

    async function handleDelete(metric: MetricDefinition) {
        if (!confirm(`Are you sure you want to delete the metric "${metric.name}"?`)) {
            return;
        }
        try {
            await metricActions.deleteMetric(metric.name);
        } catch (e) {
        }
    }
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h2 class="text-3xl font-bold">Metrics</h2> 
        <button
            on:click={() => showCreateForm = true}
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
            Create Metric
        </button>
    </div>

    {#if $error}
        <div class="p-4 text-red-700 bg-red-100 rounded-md">
            {$error}
        </div>
    {/if}

    {#if showCreateForm}
        <div class="p-6 bg-white rounded-lg shadow">
            <h3 class="text-lg font-semibold mb-4">Create New Metric</h3>
            <MetricForm
                on:submit={handleCreate}
                on:cancel={() => showCreateForm = false}
                loading={$loading}
            />
        </div>
    {/if}

    {#if editingMetric}
        <div class="p-6 bg-white rounded-lg shadow">
            <h3 class="text-lg font-semibold mb-4">Edit Metric: {editingMetric.name}</h3>
            <MetricForm
                metric={editingMetric}
                on:submit={handleUpdate}
                on:cancel={() => editingMetric = null}
                loading={$loading}
                submitLabel="Update Metric"
            />
        </div>
    {/if}

    {#if $loading && !$metrics.length}
        <div class="text-center py-8">
            <span class="inline-block animate-spin text-2xl">⌛</span>
            <p class="mt-2 text-gray-600">Loading metrics...</p>
        </div>
    {:else}
        <div class="grid gap-4">
            {#each $metrics as metric (metric.name)}
                <div class="p-4 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="text-lg font-semibold">{metric.name}</h3>
                            <p class="text-gray-600 mt-1">{metric.description}</p>
                            <div class="mt-2 space-x-2">
                                <span class="inline-block px-2 py-1 text-sm bg-gray-100 rounded">
                                    Unit: {metric.unit}
                                </span>
                                <span class="inline-block px-2 py-1 text-sm bg-gray-100 rounded">
                                    Aggregation: {metric.aggregation_method}
                                </span>
                                {#if metric.min_sample_size}
                                    <span class="inline-block px-2 py-1 text-sm bg-gray-100 rounded">
                                        Min Sample: {metric.min_sample_size.toLocaleString()}
                                    </span>
                                {/if}
                                {#if metric.min_effect_size}
                                    <span class="inline-block px-2 py-1 text-sm bg-gray-100 rounded">
                                        Min Effect: {(metric.min_effect_size * 100).toFixed(1)}%
                                    </span>
                                {/if}
                            </div>
                        </div>
                        <div class="space-x-2">
                            <button
                                on:click={() => editingMetric = metric}
                                class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
                            >
                                Edit
                            </button>
                            <button
                                on:click={() => handleDelete(metric)}
                                class="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                    <div class="mt-4">
                        <pre class="p-3 bg-gray-50 rounded text-sm font-mono overflow-x-auto">
                            {metric.query_template}
                        </pre>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div> 