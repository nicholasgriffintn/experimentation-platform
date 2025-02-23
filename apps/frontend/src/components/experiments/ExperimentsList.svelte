<script lang="ts">
    import { onMount } from 'svelte';
    import { experiments, loading, error, experimentActions } from '$lib/stores/experiments';
    import type { Experiment } from '../../types/api';
    import ResourceList from '../common/ResourceList.svelte';
    import ResourceCard from '../common/ResourceCard.svelte';
    import { goto } from '$app/navigation';

    export let initialExperiments: Experiment[] | undefined = undefined;

    onMount(() => {
        if (initialExperiments) {
            experiments.set(initialExperiments);
        } else {
            experimentActions.loadExperiments();
        }
    });

    function getStatusClasses(status: Experiment['status']): string {
        switch (status) {
            case 'running':
                return 'bg-green-100 text-green-800';
            case 'completed':
                return 'bg-blue-100 text-blue-800';
            case 'stopped':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    function getExperimentTags(experiment: Experiment) {
        const tags: Array<{label: string; value: string | number; className?: string}> = [
            { 
                label: 'Status', 
                value: experiment.status,
                className: getStatusClasses(experiment.status)
            }
        ];

        if (experiment.metrics?.length) {
            tags.push({ label: 'Metrics', value: experiment.metrics.length });
        }

        if (experiment.guardrail_metrics?.length) {
            tags.push({ label: 'Guardrails', value: experiment.guardrail_metrics.length });
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

                <div class="mt-4">
                    <h4 class="font-medium mb-2">Metrics</h4>
                    <div class="space-y-2">
                        {#if experiment.metrics?.length}
                            <div>
                                <h5 class="text-sm text-gray-500 mb-1">Primary</h5>
                                <ul class="space-y-1">
                                    {#each experiment.metrics || [] as metric}
                                        <li class="text-sm text-gray-600">{metric}</li>
                                    {/each}
                                </ul>
                            </div>

                            {#if experiment.guardrail_metrics?.length}
                                <div class="mt-2">
                                    <h5 class="text-sm text-gray-500 mb-1">Guardrails</h5>
                                    <ul class="space-y-1">
                                        {#each experiment.guardrail_metrics as guardrail}
                                            <li class="text-sm text-gray-600">
                                                {guardrail.metric_name} {guardrail.operator} {guardrail.threshold}
                                            </li>
                                        {/each}
                                    </ul>
                                </div>
                            {/if}
                        {:else}
                            <p class="text-sm text-gray-500">No metrics configured</p>
                        {/if}
                    </div>
                </div>
            </ResourceCard>
        {/each}
    </svelte:fragment>
</ResourceList> 