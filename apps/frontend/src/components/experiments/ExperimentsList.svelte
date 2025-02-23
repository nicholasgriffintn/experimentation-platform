<script lang="ts">
    import { onMount } from 'svelte';
    import { experiments, loading, error, experimentActions } from '$lib/stores/experiments';
    import type { Experiment } from '../../types/api';
    import ResourceList from '../common/ResourceList.svelte';
    import ResourceCard from '../common/ResourceCard.svelte';
    import StatusBadge from '../common/StatusBadge.svelte';
    import Badge from '../common/Badge.svelte';
    import { goto } from '$app/navigation';

    export let initialExperiments: Experiment[] | undefined = undefined;

    onMount(() => {
        if (initialExperiments) {
            experiments.set(initialExperiments);
        } else {
            experimentActions.loadExperiments();
        }
    });

    function getExperimentTags(experiment: Experiment) {
        const tags: Array<{label: string; value: string | number; component?: any; props?: Record<string, any>}> = [
            { 
                label: 'Status', 
                value: experiment.status,
                component: StatusBadge,
                props: { status: experiment.status, size: 'sm' }
            }
        ];

        if (experiment.metrics?.length) {
            tags.push({ 
                label: 'Metrics',
                value: experiment.metrics.length,
                component: Badge,
                props: { 
                    label: 'Metrics',
                    value: experiment.metrics.length,
                    variant: 'default',
                    size: 'sm'
                }
            });
        }

        if (experiment.guardrail_metrics?.length) {
            tags.push({ 
                label: 'Guardrails',
                value: experiment.guardrail_metrics.length,
                component: Badge,
                props: { 
                    label: 'Guardrails',
                    value: experiment.guardrail_metrics.length,
                    variant: 'default',
                    size: 'sm'
                }
            });
        }

        if (experiment.variants?.length) {
            tags.push({ 
                label: 'Variants',
                value: experiment.variants.length,
                component: Badge,
                props: { 
                    label: 'Variants',
                    value: experiment.variants.length,
                    variant: 'default',
                    size: 'sm'
                }
            });
        }

        return tags;
    }
</script>

<ResourceList
    title="Experiments"
    items={$experiments}
    loading={$loading}
    error={$error || null}
    createButtonLabel="Create Experiment"
    on:create={() => goto('/experiments/new')}
>
    <svelte:fragment slot="default" let:items>
        {#each items as experiment (experiment.id)}
            <ResourceCard
                title={experiment.name}
                description={experiment.description}
                tags={getExperimentTags(experiment)}
                showActions={false}
                href="/experiments/{experiment.id}"
            >
                {#if experiment.hypothesis}
                    <p class="mt-2 text-sm text-gray-500">
                        <strong>Hypothesis:</strong> {experiment.hypothesis}
                    </p>
                {/if}
            </ResourceCard>
        {/each}
    </svelte:fragment>
</ResourceList> 