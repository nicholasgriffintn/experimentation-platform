<script lang="ts">
    import type { MetricDefinition } from '../../types/api';
    import TextLink from '../common/TextLink.svelte';
    import Badge from '../common/Badge.svelte';

    export let metric: MetricDefinition;
</script>

<div class="border-b pb-4 last:border-b-0">
    <div class="flex justify-between items-start">
        <div>
            <h3 class="font-medium">
                <TextLink href="/metrics/{encodeURIComponent(metric.name)}">
                    {metric.name}
                </TextLink>
            </h3>
            <p class="text-sm text-gray-600">{metric.description}</p>
        </div>
        <div class="flex space-x-2">
            <Badge
                label="Unit"
                value={metric.unit}
                variant="default"
                size="sm"
            />
            <Badge
                label="Aggregation"
                value={metric.aggregation_method}
                variant="default"
                size="sm"
            />
        </div>
    </div>
</div> 