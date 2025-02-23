<script lang="ts">
    import { onMount } from 'svelte';
    import { metrics, loading, error, metricActions } from '$lib/stores/metrics';
    import ResourceList from '../common/ResourceList.svelte';
    import ResourceCard from '../common/ResourceCard.svelte';
    import Badge from '../common/Badge.svelte';
    import type { MetricDefinition } from '../../types/api';
    import { goto } from '$app/navigation';

    export let initialMetrics: MetricDefinition[] | undefined = undefined;

    onMount(() => {
        if (initialMetrics) {
            metrics.set(initialMetrics);
        } else {
            metricActions.loadMetrics();
        }
    });

    function getMetricTags(metric: MetricDefinition) {
        const tags: Array<{label: string; value: string | number; component?: any; props?: Record<string, any>}> = [
            { 
                label: 'Unit',
                value: metric.unit,
                component: Badge,
                props: { 
                    label: 'Unit',
                    value: metric.unit,
                    variant: 'default',
                    size: 'sm'
                }
            },
            { 
                label: 'Aggregation',
                value: metric.aggregation_method,
                component: Badge,
                props: { 
                    label: 'Aggregation',
                    value: metric.aggregation_method,
                    variant: 'default',
                    size: 'sm'
                }
            }
        ];
        
        if (metric.min_sample_size) {
            tags.push({ 
                label: 'Min Sample',
                value: metric.min_sample_size.toLocaleString(),
                component: Badge,
                props: { 
                    label: 'Min Sample',
                    value: metric.min_sample_size.toLocaleString(),
                    variant: 'default',
                    size: 'sm'
                }
            });
        }
        
        if (metric.min_effect_size) {
            tags.push({ 
                label: 'Min Effect',
                value: `${(metric.min_effect_size * 100).toFixed(1)}%`,
                component: Badge,
                props: { 
                    label: 'Min Effect',
                    value: `${(metric.min_effect_size * 100).toFixed(1)}%`,
                    variant: 'default',
                    size: 'sm'
                }
            });
        }
        
        return tags;
    }
</script>

<ResourceList
    title="Metrics"
    items={$metrics}
    loading={$loading}
    error={$error || null}
    createButtonLabel="Create Metric"
    on:create={() => goto('/metrics/new')}
>
    <svelte:fragment slot="default" let:items>
        {#each items as metric (metric.name)}
            <ResourceCard
                title={metric.name}
                description={metric.description}
                tags={getMetricTags(metric)}
                showActions={false}
                href="/metrics/{encodeURIComponent(metric.name)}"
            >
                <div class="mt-4">
                    <pre class="p-3 bg-gray-50 rounded text-sm font-mono overflow-x-auto whitespace-pre-line">{metric.query_template}</pre>
                </div>
            </ResourceCard>
        {/each}
    </svelte:fragment>
</ResourceList> 