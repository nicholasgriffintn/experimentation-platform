<script lang="ts">
    import type { MetricDefinition } from '../../types/api';

    export let metric: MetricDefinition;
</script>

<div class="border-b pb-4 last:border-b-0">
    <h3 class="font-medium">
        <a class="text-blue-600 hover:text-blue-800" href="/metrics/{encodeURIComponent(metric.name)}">
            {metric.name}
        </a>
    </h3>
    <p class="text-sm text-gray-600">{metric.description}</p>
    <div class="mt-1 flex space-x-2">
        <span class="text-xs px-2 py-1 bg-gray-100 rounded-full">
            {metric.unit}
        </span>
        <span class="text-xs px-2 py-1 bg-gray-100 rounded-full">
            {metric.aggregation_method}
        </span>
    </div>
</div> 