<script lang="ts">
    import type { Experiment } from '../../types/api';
    import TextLink from '../common/TextLink.svelte';
    import StatusBadge from '../common/StatusBadge.svelte';

    export let experiment: Experiment;

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