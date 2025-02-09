<script lang="ts">
    import { onMount } from 'svelte';
    import { experiments, loading, error, experimentActions } from '$lib/stores/experiments';
    import type { Experiment } from '$lib/types/api';
    import type { PageData } from './$types';
    import { goto } from '$app/navigation';

    export let data: PageData;
    $: experimentsList = data.experiments || [];

    onMount(() => {
        experimentActions.loadExperiments();
    });

    async function handleStopExperiment(experimentId: string) {
        const reason = prompt('Please provide a reason for stopping the experiment:');
        if (reason !== null) {
            await experimentActions.stopExperiment(experimentId, reason);
        }
    }

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
</script>

<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">Experiments</h1>
        <button
            on:click={() => goto('/experiments/new')}
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
            Create Experiment
        </button>
    </div>

    {#if $error}
        <div class="p-4 mb-6 text-red-700 bg-red-100 rounded-md">
            {$error}
        </div>
    {/if}

    {#if $loading && !experimentsList.length}
        <div class="text-center py-12">
            <span class="inline-block animate-spin text-4xl">⌛</span>
            <p class="mt-4 text-gray-600">Loading experiments...</p>
        </div>
    {:else if !experimentsList.length}
        <div class="text-center py-12 bg-white rounded-lg shadow">
            <p class="text-gray-600 mb-4">No experiments yet</p>
            <button
                on:click={() => goto('/experiments/new')}
                class="px-4 py-2 text-blue-600 hover:text-blue-800 border border-blue-600 rounded-md"
            >
                Create your first experiment
            </button>
        </div>
    {:else}
        <div class="grid gap-6">
            {#each experimentsList as experiment (experiment.id)}
                <div class="p-6 bg-white rounded-lg shadow">
                    <div class="flex justify-between items-start">
                        <div>
                            <a 
                                href="/experiments/{experiment.id}" 
                                class="text-xl font-semibold hover:text-blue-600"
                            >
                                {experiment.name}
                            </a>
                            <p class="text-gray-600 mt-1">{experiment.description}</p>
                            {#if experiment.hypothesis}
                                <p class="mt-2 text-sm text-gray-500">
                                    <strong>Hypothesis:</strong> {experiment.hypothesis}
                                </p>
                            {/if}
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="px-3 py-1 text-sm rounded-full {getStatusClasses(experiment.status)}">
                                {experiment.status}
                            </span>
                            {#if experiment.status === 'running'}
                                <button
                                    on:click={() => handleStopExperiment(experiment.id)}
                                    class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                                >
                                    Stop
                                </button>
                            {/if}
                        </div>
                    </div>

                    <div class="mt-4 grid grid-cols-2 gap-4">
                        <div>
                            <h4 class="font-medium mb-2">Metrics</h4>
                            <ul class="space-y-1">
                                {#each experiment.metrics || [] as metric}
                                    <li class="text-sm text-gray-600">{metric}</li>
                                {/each}
                            </ul>
                        </div>
                        <div>
                            <h4 class="font-medium mb-2">Variants</h4>
                            <div class="space-y-2">
                                {#each experiment.variants || [] as variant}
                                    <div class="flex justify-between text-sm">
                                        <span>{variant.name}</span>
                                        <span class="text-gray-600">{variant.traffic_percentage}%</span>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    </div>

                    {#if experiment.schedule?.start_time || experiment.schedule?.end_time}
                        <div class="mt-4 pt-4 border-t">
                            <h4 class="font-medium mb-2">Schedule</h4>
                            <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
                                {#if experiment.schedule.start_time}
                                    <div>
                                        <span class="font-medium">Start:</span>
                                        {new Date(experiment.schedule.start_time).toLocaleString()}
                                    </div>
                                {/if}
                                {#if experiment.schedule.end_time}
                                    <div>
                                        <span class="font-medium">End:</span>
                                        {new Date(experiment.schedule.end_time).toLocaleString()}
                                    </div>
                                {/if}
                            </div>
                        </div>
                    {/if}

                    {#if experiment.stopped_reason}
                        <div class="mt-4 pt-4 border-t">
                            <h4 class="font-medium mb-2">Stop Reason</h4>
                            <p class="text-sm text-gray-600">{experiment.stopped_reason}</p>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div> 