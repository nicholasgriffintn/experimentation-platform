<script lang="ts">
    import type { Experiment } from '../../types/api';
    import TextLink from '../common/TextLink.svelte';
    import StatusBadge from '../common/StatusBadge.svelte';

    export let experiment: Experiment;
</script>

<div class="border-b pb-4 last:border-b-0">
    <div class="flex justify-between items-start">
        <div>
            <h3 class="font-medium">
                <TextLink href="/experiments/{experiment.id}">
                    {experiment.name}
                </TextLink>
            </h3>
            <p class="text-sm text-gray-600">{experiment.description}</p>
        </div>
        <StatusBadge status={experiment.status} size="sm" />
    </div>
</div> 