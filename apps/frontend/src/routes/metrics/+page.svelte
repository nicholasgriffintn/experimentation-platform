<script lang="ts">
	import MetricsList from '../../components/metrics/MetricsList.svelte';
	import type { PageData } from './$types';

	export let data: PageData;
</script>

<div class="container mx-auto px-4 py-8">
	<MetricsList initialMetrics={data.metrics} />
</div> 