<script lang="ts">
    import { onMount } from 'svelte';
    import { metrics as metricsStore, metricActions } from '$lib/stores/metrics';
    import { features as featuresStore, featureActions } from '$lib/stores/features';
    import type { ExperimentType, VariantType, Variant, ExperimentCreate, ExperimentSchedule, GuardrailConfig, GuardrailOperator, AnalysisConfig, FeatureDefinition } from '$lib/types/api';
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
    let analysis_config: AnalysisConfig = {
        method: 'frequentist',
        confidence_level: 0.95,
        correction_method: 'none',
        sequential_testing: false,
        stopping_threshold: 0.01,
        default_metric_config: {
            min_sample_size: 100,
            min_effect_size: 0.01
        },
        metric_configs: {},
        ...experiment.analysis_config
    };

    let selectedFeature: FeatureDefinition | null = null;
    let selectedFeatureName = '';

    function getBayesianValue(value: number | undefined, defaultValue: number): number {
        return value ?? defaultValue;
    }

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
        if (!$featuresStore.length) {
            featureActions.loadFeatures();
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

    function updateVariantConfig(index: number, key: string, event: Event) {
        const input = event.target as HTMLInputElement;
        const variant = variants[index];
        const updatedConfig = { ...variant.config, [key]: input.value };
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
            const variant = variants[variantIndex];
            const updatedConfig = { ...variant.config, [key]: '' };
            variants[variantIndex] = { ...variant, config: updatedConfig };
            variants = [...variants];
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
            guardrail_metrics: guardrail_metrics.length > 0 ? guardrail_metrics : undefined,
            analysis_config
        };
        dispatch('submit', experimentData);
    }

    // Initialize Bayesian fields when method changes
    $: if (analysis_config.method === 'bayesian') {
        analysis_config = {
            ...analysis_config,
            prior_successes: 30,
            prior_trials: 100,
            num_samples: 10000
        };
    }

    $: bayesianRate = analysis_config.method === 'bayesian' ? 
        (getBayesianValue(analysis_config.prior_successes, 30) / 
         getBayesianValue(analysis_config.prior_trials, 100) * 100).toFixed(1) : '0.0';

    $: showBayesianError = analysis_config.method === 'bayesian' && 
        getBayesianValue(analysis_config.prior_successes, 0) > 
        getBayesianValue(analysis_config.prior_trials, 100);

    function handleFeatureSelect(event: Event) {
        const select = event.target as HTMLSelectElement;
        const feature = $featuresStore.find(f => f.name === select.value);
        if (!feature) return;
        
        selectedFeature = feature;
        selectedFeatureName = feature.name;
        parameters = { ...parameters, feature_name: feature.name };
        
        if (feature.possible_values.length >= 2) {
            variants = [
                createVariant('Control', 'feature_flag', { value: feature.possible_values[0] }, 50),
                createVariant('Treatment', 'feature_flag', { value: feature.possible_values[1] }, 50)
            ];
        }
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
                <div class="p-4 border rounded-md space-y-2">
                    <div class="flex items-center justify-between">
                        <h4 class="font-medium">{variant.name}</h4>
                        {#if variants.length > 2}
                            <button
                                type="button"
                                on:click={() => removeVariant(i)}
                                class="text-red-600 hover:text-red-800"
                            >
                                Remove
                            </button>
                        {/if}
                    </div>

                    {#if type === 'feature_flag' && selectedFeature}
                        <div class="space-y-2">
                            <label for={`variant-${i}-value`} class="block text-sm font-medium">Value</label>
                            <select
                                id={`variant-${i}-value`}
                                bind:value={variant.config.value}
                                class="w-full px-3 py-2 border rounded-md"
                            >
                                {#each selectedFeature.possible_values as value}
                                    <option value={value}>{value}</option>
                                {/each}
                            </select>
                        </div>
                    {:else}
                        <div class="space-y-2">
                            {#each Object.entries(variant.config) as [key, value]}
                                <div class="flex items-center space-x-2">
                                    <input
                                        type="text"
                                        value={value}
                                        on:input={(event) => updateVariantConfig(i, key, event)}
                                        class="flex-grow px-3 py-2 border rounded-md"
                                    />
                                    <button
                                        type="button"
                                        on:click={() => removeConfigKey(i, key)}
                                        class="text-red-600 hover:text-red-800"
                                    >
                                        Remove
                                    </button>
                                </div>
                            {/each}
                            <button
                                type="button"
                                on:click={() => addConfigKey(i)}
                                class="text-blue-600 hover:text-blue-800"
                            >
                                Add Config
                            </button>
                        </div>
                    {/if}

                    <div class="space-y-2">
                        <label for={`variant-${i}-traffic`} class="block text-sm font-medium">Traffic %</label>
                        <input
                            id={`variant-${i}-traffic`}
                            type="number"
                            bind:value={variant.traffic_percentage}
                            min="0"
                            max="100"
                            step="0.1"
                            class="w-full px-3 py-2 border rounded-md"
                        />
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

    <div class="space-y-4">
        <h3 class="text-lg font-semibold">Analysis Configuration</h3>
        <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
                <label for="analysis_method" class="block text-sm font-medium">Analysis Method</label>
                <select
                    id="analysis_method"
                    bind:value={analysis_config.method}
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                >
                    <option value="frequentist">Frequentist</option>
                    <option value="bayesian">Bayesian</option>
                </select>
            </div>

            <div class="space-y-2">
                <label for="confidence_level" class="block text-sm font-medium">Confidence Level</label>
                <input
                    type="number"
                    id="confidence_level"
                    bind:value={analysis_config.confidence_level}
                    min="0"
                    max="1"
                    step="0.01"
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                />
            </div>

            <div class="space-y-2">
                <label for="correction_method" class="block text-sm font-medium">Correction Method</label>
                <select
                    id="correction_method"
                    bind:value={analysis_config.correction_method}
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                >
                    <option value="none">None</option>
                    <option value="fdr_bh">Benjamini-Hochberg FDR</option>
                    <option value="holm">Holm-Bonferroni</option>
                </select>
            </div>

            <div class="space-y-2">
                <label class="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        bind:checked={analysis_config.sequential_testing}
                        disabled={loading}
                        class="rounded"
                    />
                    <span class="text-sm font-medium">Enable Sequential Testing</span>
                </label>
                {#if analysis_config.sequential_testing}
                    <input
                        type="number"
                        bind:value={analysis_config.stopping_threshold}
                        min="0"
                        max="1"
                        step="0.001"
                        placeholder="Stopping Threshold"
                        disabled={loading}
                        class="w-full px-3 py-2 border rounded-md mt-2"
                    />
                {/if}
            </div>
        </div>

        <div class="space-y-4">
            <h4 class="font-medium">Default Metric Configuration</h4>
            <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                    <label for="min_sample_size" class="block text-sm font-medium">Minimum Sample Size</label>
                    <input
                        type="number"
                        id="min_sample_size"
                        bind:value={analysis_config.default_metric_config.min_sample_size}
                        min="1"
                        step="1"
                        disabled={loading}
                        class="w-full px-3 py-2 border rounded-md"
                    />
                </div>

                <div class="space-y-2">
                    <label for="min_effect_size" class="block text-sm font-medium">Minimum Effect Size</label>
                    <input
                        type="number"
                        id="min_effect_size"
                        bind:value={analysis_config.default_metric_config.min_effect_size}
                        min="0"
                        step="0.01"
                        disabled={loading}
                        class="w-full px-3 py-2 border rounded-md"
                    />
                </div>
            </div>
        </div>

        {#if analysis_config.method === 'bayesian'}
            <div class="space-y-4">
                <h4 class="font-medium">Bayesian Configuration</h4>
                <p class="text-sm text-gray-600 mb-4">
                    Prior configuration represents your initial beliefs about the metrics before running the experiment.
                    For example, if you believe the baseline conversion rate is around 30%, you might set 30 successes out of 100 trials.
                    Higher numbers indicate stronger prior beliefs.
                </p>
                <div class="grid grid-cols-3 gap-4">
                    <div class="space-y-2">
                        <label for="prior_successes" class="block text-sm font-medium">Prior Successes</label>
                        <input
                            type="number"
                            id="prior_successes"
                            bind:value={analysis_config.prior_successes}
                            min="0"
                            max={getBayesianValue(analysis_config.prior_trials, 100)}
                            step="1"
                            disabled={loading}
                            class="w-full px-3 py-2 border rounded-md"
                        />
                        <p class="text-xs text-gray-500">Number of expected successes in prior data (e.g., conversions)</p>
                    </div>

                    <div class="space-y-2">
                        <label for="prior_trials" class="block text-sm font-medium">Prior Trials</label>
                        <input
                            type="number"
                            id="prior_trials"
                            bind:value={analysis_config.prior_trials}
                            min={getBayesianValue(analysis_config.prior_successes, 0)}
                            step="1"
                            disabled={loading}
                            class="w-full px-3 py-2 border rounded-md"
                        />
                        <p class="text-xs text-gray-500">Total number of prior observations (must be ≥ prior successes)</p>
                    </div>

                    <div class="space-y-2">
                        <label for="num_samples" class="block text-sm font-medium">MCMC Samples</label>
                        <input
                            type="number"
                            id="num_samples"
                            bind:value={analysis_config.num_samples}
                            min="1000"
                            step="1000"
                            disabled={loading}
                            class="w-full px-3 py-2 border rounded-md"
                        />
                        <p class="text-xs text-gray-500">Number of Monte Carlo samples (higher = more precise but slower)</p>
                    </div>
                </div>

                {#if showBayesianError}
                    <p class="text-sm text-red-600 mt-2">
                        Prior successes cannot be greater than prior trials
                    </p>
                {/if}

                <div class="mt-4 p-4 bg-blue-50 rounded-md">
                    <p class="text-sm text-blue-800">
                        With these settings, your prior belief is that the baseline rate is around 
                        {bayesianRate}%
                        with {getBayesianValue(analysis_config.prior_trials, 100)} observations worth of confidence.
                    </p>
                </div>
            </div>
        {/if}
    </div>

    {#if type === 'feature_flag'}
        <div class="space-y-4">
            <h3 class="text-lg font-semibold">Feature Configuration</h3>
            
            <div class="space-y-2">
                <label for="feature" class="block text-sm font-medium">Select Feature</label>
                <select
                    id="feature"
                    value={selectedFeature?.name ?? ''}
                    on:change={handleFeatureSelect}
                    required
                    disabled={loading}
                    class="w-full px-3 py-2 border rounded-md"
                >
                    <option value="">Select a feature...</option>
                    {#each $featuresStore as feature}
                        <option value={feature.name}>{feature.name} - {feature.description}</option>
                    {/each}
                </select>
            </div>

            {#if selectedFeature}
                <div class="space-y-2">
                    <p class="text-sm text-gray-600">
                        Data Type: {selectedFeature.data_type}<br>
                        Possible Values: {selectedFeature.possible_values.join(', ')}
                    </p>
                </div>
            {/if}
        </div>
    {/if}

    <div class="flex justify-end space-x-3">
        <button
            type="button"
            on:click={() => dispatch('cancel')}
            disabled={loading}
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
        >
            Cancel
        </button>
        <button
            type="submit"
            disabled={loading}
            class="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-md"
        >
            {#if loading}
                <span class="inline-block animate-spin mr-2">⌛</span>
            {/if}
            {submitLabel}
        </button>
    </div>
</form> 