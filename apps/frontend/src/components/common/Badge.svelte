<script lang="ts">
    export let label: string;
    export let value: string | number;
    export let size: 'sm' | 'md' = 'sm';
    export let variant: 'default' | 'info' | 'success' | 'warning' | 'error' = 'default';

    function getVariantClasses(variant: string): string {
        switch (variant) {
            case 'info':
                return 'bg-blue-100 text-blue-800';
            case 'success':
                return 'bg-green-100 text-green-800';
            case 'warning':
                return 'bg-yellow-100 text-yellow-800';
            case 'error':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    const sizeClasses = {
        sm: 'px-2 py-1',
        md: 'px-3 py-2'
    };
</script>

<span class="text-sm rounded-full {sizeClasses[size]} {getVariantClasses(variant)}">
    {label}: {value}
</span> 