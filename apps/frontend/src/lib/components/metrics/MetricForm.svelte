<script lang="ts">
    import type { MetricDefinition } from '$lib/types/api';
    import { createEventDispatcher } from 'svelte';

    export let metric: Partial<MetricDefinition> = {};
    export let submitLabel = 'Save Metric';
    export let loading = false;

    const dispatch = createEventDispatcher<{
        submit: MetricDefinition;
        cancel: void;
    }>();

    let name = metric.name ?? '';
    let description = metric.description ?? '';
    let unit = metric.unit ?? '';
    let data_type = metric.data_type ?? 'count';
    let aggregation_method = metric.aggregation_method ?? 'sum';
    let query_template = metric.query_template ?? '';
    let min_sample_size = metric.min_sample_size ?? null;
    let min_effect_size = metric.min_effect_size ?? null;

    const aggregationMethods = ['sum', 'avg', 'count', 'min', 'max'];
    const dataTypes = ['continuous', 'binary', 'count', 'ratio'];

    function handleSubmit() {
        const metricData: MetricDefinition = {
            name,
            description,
            unit,
            data_type,
            aggregation_method,
            query_template,
            ...(min_sample_size !== null && { min_sample_size: Number(min_sample_size) }),
            ...(min_effect_size !== null && { min_effect_size: Number(min_effect_size) })
        };
        dispatch('submit', metricData);
    }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-4">
    <div class="space-y-2">
        <label for="name" class="block text-sm font-medium">Name</label>
        <input
            type="text"
            id="name"
            bind:value={name}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md"
            placeholder="e.g., conversion_rate"
        />
    </div>

    <div class="space-y-2">
        <label for="description" class="block text-sm font-medium">Description</label>
        <textarea
            id="description"
            bind:value={description}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md"
            rows="3"
            placeholder="Describe what this metric measures..."
        ></textarea>
    </div>

    <div class="space-y-2">
        <label for="unit" class="block text-sm font-medium">Unit</label>
        <input
            type="text"
            id="unit"
            bind:value={unit}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md"
            placeholder="e.g., percentage, count, dollars"
        />
    </div>

    <div class="space-y-2">
        <label for="data_type" class="block text-sm font-medium">
            Data Type
        </label>
        <select
            id="data_type"
            bind:value={data_type}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md"
        >
            {#each dataTypes as type}
                <option value={type}>{type}</option>
            {/each}
        </select>
    </div>

    <div class="space-y-2">
        <label for="aggregation_method" class="block text-sm font-medium">
            Aggregation Method
        </label>
        <select
            id="aggregation_method"
            bind:value={aggregation_method}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md"
        >
            {#each aggregationMethods as method}
                <option value={method}>{method}</option>
            {/each}
        </select>
    </div>

    <div class="space-y-2">
        <label for="query_template" class="block text-sm font-medium">
            Query Template
        </label>
        <textarea
            id="query_template"
            bind:value={query_template}
            required
            disabled={loading}
            class="w-full px-3 py-2 border rounded-md font-mono text-sm"
            rows="5"
            placeholder="SELECT COUNT(*) as value FROM events WHERE experiment_id = 1 AND variant_id = 1"
        ></textarea>
    </div>

    <div class="grid grid-cols-2 gap-4">
        <div class="space-y-2">
            <label for="min_sample_size" class="block text-sm font-medium">
                Minimum Sample Size
            </label>
            <input
                type="number"
                id="min_sample_size"
                bind:value={min_sample_size}
                min="0"
                step="1"
                disabled={loading}
                class="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., 1000"
            />
            <p class="text-xs text-gray-500">Minimum number of samples needed for statistical validity</p>
        </div>

        <div class="space-y-2">
            <label for="min_effect_size" class="block text-sm font-medium">
                Minimum Effect Size
            </label>
            <input
                type="number"
                id="min_effect_size"
                bind:value={min_effect_size}
                min="0"
                step="0.01"
                disabled={loading}
                class="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., 0.05"
            />
            <p class="text-xs text-gray-500">Smallest meaningful difference to detect (e.g., 0.05 for 5%)</p>
        </div>
    </div>

    <div class="flex justify-end space-x-3">
        <button
            type="button"
            on:click={() => dispatch('cancel')}
            disabled={loading}
            class="px-4 py-2 text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
        >
            Cancel
        </button>
        <button
            type="submit"
            disabled={loading}
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
            {#if loading}
                <span class="inline-block animate-spin mr-2">⌛</span>
            {/if}
            {submitLabel}
        </button>
    </div>
</form> 