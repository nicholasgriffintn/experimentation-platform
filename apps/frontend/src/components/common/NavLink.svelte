<script lang="ts">
	export let href: string;
	export let active = false;
</script>

<a
	{href}
	class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium
	{active ? 
		'border-blue-500 text-gray-900' : 
		'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'}"
>
	<slot />
</a> 