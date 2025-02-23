<script lang="ts">
	export let href: string;
	export let size: 'sm' | 'base' = 'base';
</script>

<a
	{href}
	class="text-blue-600 hover:text-blue-800 {size === 'sm' ? 'text-sm' : 'text-base'}"
>
	<slot />
</a> 