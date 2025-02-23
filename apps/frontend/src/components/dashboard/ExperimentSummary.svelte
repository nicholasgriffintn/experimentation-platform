<script lang="ts">
    import type { Experiment } from '../../types/api';

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
                <a class="text-blue-600 hover:text-blue-800" href="/experiments/{experiment.id}">
                    {experiment.name}
                </a>
            </h3>
            <p class="text-sm text-gray-600">{experiment.description}</p>
        </div>
        <span class="px-2 py-1 text-sm rounded-full {getStatusClasses(experiment.status)}">
            {experiment.status}
        </span>
    </div>
</div> 