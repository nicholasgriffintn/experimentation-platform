<script lang="ts">
    import type { PageData } from './$types';
    import ExperimentsList from '$lib/components/experiments/ExperimentsList.svelte';

    export let data: PageData;
</script>

<div class="container mx-auto px-4 py-8">
    <ExperimentsList initialExperiments={data.experiments} />
</div> 