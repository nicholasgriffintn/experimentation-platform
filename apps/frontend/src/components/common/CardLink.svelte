<script lang="ts">
	export let href: string;
</script>

<a
	{href}
	class="block p-4 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
>
	<div class="flex items-center justify-between">
		<div class="flex items-center space-x-2">
			<slot />
		</div>
		<svg class="h-5 w-5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
		</svg>
	</div>
</a> 