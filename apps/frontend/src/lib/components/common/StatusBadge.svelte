<script lang="ts">
    import type { Experiment } from '../../types/api';
    
    export let status: Experiment['status'];
    export let size: 'sm' | 'md' = 'md';

    function getStatusClasses(status: Experiment['status']): string {
        switch (status) {
            case 'running':
                return 'bg-green-100 text-green-800 border border-green-800/10';
            case 'completed':
                return 'bg-blue-100 text-blue-800 border border-blue-800/10';
            case 'stopped':
                return 'bg-red-100 text-red-800 border border-red-800/10';
            case 'paused':
                return 'bg-yellow-100 text-yellow-800 border border-yellow-800/10';
            case 'scheduled':
                return 'bg-purple-100 text-purple-800 border border-purple-800/10';
            default:
                return 'bg-gray-100 text-gray-800 border border-gray-800/10';
        }
    }

    const sizeClasses = {
        sm: 'px-2 py-1',
        md: 'px-3 py-2'
    };
</script>

<span class="text-sm rounded-md {sizeClasses[size]} {getStatusClasses(status)}">
    {status}
</span> 