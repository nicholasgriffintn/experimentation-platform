<script lang="ts">
    import { onMount } from 'svelte';
    import { metrics as metricsStore, metricActions } from '$lib/stores/metrics';
    import type { ExperimentType, VariantType, Variant, ExperimentCreate, ExperimentSchedule, GuardrailConfig, GuardrailOperator } from '$lib/types/api';
    import { createEventDispatcher } from 'svelte';
    import { formatDateToISO } from '$lib/utils/date';

    export let experiment: Partial<ExperimentCreate> = {};
    export let submitLabel = 'Create Experiment';
    export let loading = false;

    const dispatch = createEventDispatcher<{
        submit: ExperimentCreate;
        cancel: void;
    }>();

    let error: string | null = null;
    let name = experiment.name ?? '';
    let description = experiment.description ?? '';
    let type = (experiment.type ?? 'ab_test') as ExperimentType;
    let hypothesis = experiment.hypothesis ?? '';
    let metrics = experiment.metrics ?? [];
    let guardrail_metrics: GuardrailConfig[] = experiment.guardrail_metrics ?? [];
    let targeting_rules: Record<string, any> = experiment.targeting_rules ?? {};
    let schedule: Partial<ExperimentSchedule> = experiment.schedule ?? {};
    let parameters: Record<string, any> = experiment.parameters ?? {};

    const experimentTypes = ['ab_test', 'multivariate', 'feature_flag'];
    const guardrailOperators: GuardrailOperator[] = ['gt', 'lt', 'gte', 'lte'];

    $: {
        if (type === 'ab_test') {
            variants = [
                createVariant('Control', 'control', {}, 50),
                createVariant('Treatment', 'treatment', {}, 50)
            ];
        } else if (type === 'feature_flag') {
            variants = [
                createVariant('Off', 'feature_flag', { enabled: false }, 50),
                createVariant('On', 'feature_flag', { enabled: true }, 50)
            ];
        } else if (type === 'multivariate') {
            if (variants.length < 2) {
                variants = [
                    createVariant('Control', 'control', {}, 50),
                    createVariant('Treatment A', 'treatment', {}, 50)
                ];
            } else {
                variants = variants.map((v, i) => ({
                    ...v,
                    type: i === 0 ? 'control' as const : 'treatment' as const,
                    name: i === 0 ? 'Control' : `Treatment ${String.fromCharCode(65 + i - 1)}`
                }));
            }
        }
    }

    onMount(() => {
        if (!$metricsStore.length) {
            metricActions.loadMetrics();
        }
    });

    function createVariant(name: string, type: VariantType, config = {}, traffic_percentage: number): Variant {
        return {
            id: crypto.randomUUID(),
            name,
            type,
            config,
            traffic_percentage
        };
    }

    let variants: Variant[] = experiment.variants?.map(v => ({
        ...v,
        id: crypto.randomUUID()
    })) ?? [
        createVariant('Control', 'control', {}, 50),
        createVariant('Treatment', 'treatment', {}, 50)
    ];

    function addVariant() {
        const newVariant = createVariant(
            `Treatment ${variants.length}`,
            type === 'feature_flag' ? 'feature_flag' : 'treatment',
            {},
            0
        );
        variants = [...variants, newVariant];
        rebalanceTraffic();
    }

    function removeVariant(index: number) {
        variants = variants.filter((_, i) => i !== index);
        rebalanceTraffic();
    }

    function rebalanceTraffic() {
        const equalShare = 100 / variants.length;
        variants = variants.map(v => ({ ...v, traffic_percentage: equalShare }));
    }

    function validateVariants(): string | null {
        if (type === 'ab_test') {
            if (variants.length !== 2) return 'A/B tests must have exactly two variants';
            if (variants[0].type !== 'control') return 'First variant must be control';
            if (variants[1].type !== 'treatment') return 'Second variant must be treatment';
        } else if (type === 'multivariate') {
            if (variants.length < 2) return 'Multivariate tests must have at least two variants';
            if (variants[0].type !== 'control') return 'First variant must be control';
            if (!variants.slice(1).every(v => v.type === 'treatment')) {
                return 'All non-control variants must be treatment variants';
            }
        } else if (type === 'feature_flag') {
            if (!variants.every(v => v.type === 'feature_flag')) {
                return 'Feature flags must have all variants of type feature_flag';
            }
        }
        return null;
    }

    function updateVariantConfig(index: number, key: string, value: string) {
        const variant = variants[index];
        const updatedConfig = { ...variant.config, [key]: value };
        variants[index] = { ...variant, config: updatedConfig };
        variants = [...variants];
    }

    function removeConfigKey(variantIndex: number, key: string) {
        const variant = variants[variantIndex];
        const { [key]: _, ...rest } = variant.config;
        variants[variantIndex] = { ...variant, config: rest };
        variants = [...variants];
    }

    function addConfigKey(variantIndex: number) {
        const key = prompt('Enter config key:');
        if (key && !variants[variantIndex].config[key]) {
            updateVariantConfig(variantIndex, key, '');
        }
    }

    function addGuardrailMetric(metric_name: string) {
        guardrail_metrics = [
            ...guardrail_metrics,
            {
                metric_name,
                threshold: 0,
                operator: 'gt'
            }
        ];
    }

    function removeGuardrailMetric(index: number) {
        guardrail_metrics = guardrail_metrics.filter((_, i) => i !== index);
    }

    function handleSubmit() {
        const variantError = validateVariants();
        if (variantError) {
            error = variantError;
            return;
        }
        const finalSchedule = schedule.start_time ? {
            start_time: formatDateToISO(schedule.start_time),
            end_time: schedule.end_time ? formatDateToISO(schedule.end_time) : undefined,
            ramp_up_period: schedule.ramp_up_period,
            auto_stop_conditions: schedule.auto_stop_conditions
        } : undefined;

        const experimentData: ExperimentCreate = {
            name,
            description,
            type,
            hypothesis,
            metrics,
            variants,
            targeting_rules,
            schedule: finalSchedule,
            parameters,
            guardrail_metrics: guardrail_metrics.length > 0 ? guardrail_metrics : undefined
        };
        dispatch('submit', experimentData);
    }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
    <div class="space-y-4">
        <h3 class="text-lg font-semibold">Basic Information</h3>
        
        <div class="space-y-2">
            <label for="name" class="block text-sm font-medium">Name</label>
            <input
                type="text"
                id="name"
                bind:value={name}
                required
                disabled={loading}
                class="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., new_checkout_flow"
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
                placeholder="Describe the experiment..."
            ></textarea>
        </div>

        <div class="space-y-2">
            <label for="type" class="block text-sm font-medium">Experiment Type</label>
            <select
                id="type"
                bind:value={type}
                required
                disabled={loading}
                class="w-full px-3 py-2 border rounded-md"
            >
                {#each experimentTypes as expType}
                    <option value={expType}>{expType}</option>
                {/each}
            </select>
        </div>

        <div class="space-y-2">
            <label for="hypothesis" class="block text-sm font-medium">Hypothesis</label>
            <textarea
                id="hypothesis"
                bind:value={hypothesis}
                disabled={loading}
                class="w-full px-3 py-2 border rounded-md"
                rows="2"
                placeholder="What do you expect to happen?"
            ></textarea>
        </div>
    </div>

    <div class="space-y-4">
        <h3 class="text-lg font-semibold">Metrics</h3>
        <div class="space-y-2">
            {#if $metricsStore.length === 0}
                <p class="text-gray-600">No metrics available. Create some metrics first.</p>
            {:else}
                <div class="grid gap-4">
                    <div class="space-y-2">
                        <h4 class="font-medium">Primary Metrics</h4>
                        <div class="grid gap-2">
                            {#each $metricsStore as metric}
                                <label class="flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        value={metric.name}
                                        bind:group={metrics}
                                        disabled={loading}
                                        class="rounded"
                                    />
                                    <span>{metric.name} - {metric.description}</span>
                                </label>
                            {/each}
                        </div>
                    </div>

                    <div class="space-y-2">
                        <h4 class="font-medium">Guardrail Metrics</h4>
                        <p class="text-sm text-gray-600">Guardrail metrics are used as safety checks. If a guardrail is violated, the experiment will be automatically stopped.</p>
                        
                        <div class="space-y-4">
                            {#each guardrail_metrics as guardrail, i}
                                <div class="flex items-center space-x-4 p-4 border rounded-md">
                                    <div class="flex-1">
                                        <select
                                            bind:value={guardrail.metric_name}
                                            disabled={loading}
                                            class="w-full px-3 py-2 border rounded-md"
                                        >
                                            {#each $metricsStore as metric}
                                                <option value={metric.name}>{metric.name}</option>
                                            {/each}
                                        </select>
                                    </div>
                                    <div class="w-32">
                                        <select
                                            bind:value={guardrail.operator}
                                            disabled={loading}
                                            class="w-full px-3 py-2 border rounded-md"
                                        >
                                            {#each guardrailOperators as op}
                                                <option value={op}>{op}</option>
                                            {/each}
                                        </select>
                                    </div>
                                    <div class="w-32">
                                        <input
                                            type="number"
                                            bind:value={guardrail.threshold}
                                            step="any"
                                            placeholder="Threshold"
                                            disabled={loading}
                                            class="w-full px-3 py-2 border rounded-md"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        on:click={() => removeGuardrailMetric(i)}
                                        disabled={loading}
                                        class="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                                    >
                                        Remove
                                    </button>
                                </div>
                            {/each}

                            <div class="flex flex-wrap gap-2">
                                {#each $metricsStore.filter(m => !guardrail_metrics.some(g => g.metric_name === m.name)) as metric}
                                    <button
                                        type="button"
                                        on:click={() => addGuardrailMetric(metric.name)}
                                        disabled={loading}
                                        class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-full border border-blue-200"
                                    >
                                        + Add {metric.name} as guardrail
                                    </button>
                                {/each}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    </div>

    <div class="space-y-4">
        <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">Variants</h3>
            <button
                type="button"
                on:click={addVariant}
                disabled={loading}
                class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
            >
                Add Variant
            </button>
        </div>

        <div class="space-y-4">
            {#each variants as variant, i}
                <div class="p-4 border rounded-md">
                    <div class="flex justify-between items-start mb-4">
                        <div class="space-y-2 flex-1 mr-4">
                            <input
                                type="text"
                                bind:value={variant.name}
                                placeholder="Variant name"
                                disabled={loading}
                                class="w-full px-3 py-2 border rounded-md"
                            />
                        </div>
                        <div class="space-y-2 w-32">
                            <input
                                type="number"
                                bind:value={variant.traffic_percentage}
                                min="0"
                                max="100"
                                disabled={loading}
                                class="w-full px-3 py-2 border rounded-md"
                            />
                        </div>
                        {#if i > 0}
                            <button
                                type="button"
                                on:click={() => removeVariant(i)}
                                disabled={loading}
                                class="ml-2 px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                            >
                                Remove
                            </button>
                        {/if}
                    </div>

                    <div class="space-y-2">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="font-medium">Configuration</h4>
                            <button
                                type="button"
                                on:click={() => addConfigKey(i)}
                                disabled={loading}
                                class="text-sm text-blue-600 hover:bg-blue-50 px-2 py-1 rounded"
                            >
                                Add Config
                            </button>
                        </div>
                        {#each Object.entries(variant.config) as [key, value]}
                            <div class="flex space-x-2">
                                <input
                                    type="text"
                                    value={key}
                                    readonly
                                    class="flex-1 px-3 py-2 border rounded-md bg-gray-50"
                                />
                                <input
                                    type="text"
                                    value={value}
                                    on:input={(e) => updateVariantConfig(i, key, e.currentTarget.value)}
                                    disabled={loading}
                                    class="flex-1 px-3 py-2 border rounded-md"
                                />
                                <button
                                    type="button"
                                    on:click={() => removeConfigKey(i, key)}
                                    disabled={loading}
                                    class="px-2 py-1 text-red-600 hover:bg-red-50 rounded"
                                >
                                    Remove
                                </button>
                            </div>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>
    </div>

    <div class="space-y-4">
        <h3 class="text-lg font-semibold">Schedule</h3>
        <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
                <label for="start_time" class="block text-sm font-medium">Start Time</label>
                <input
                    type="datetime-local"
                    id="start_time"
                    bind:value={schedule.start_time}
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                />
            </div>
            <div class="space-y-2">
                <label for="end_time" class="block text-sm font-medium">End Time</label>
                <input
                    type="datetime-local"
                    id="end_time"
                    bind:value={schedule.end_time}
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                />
            </div>
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