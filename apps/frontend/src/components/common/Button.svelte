<script lang="ts">
	export let href: string | undefined = undefined;
	export let variant: 'primary' | 'secondary' | 'outline' | 'link' | 'danger' = 'primary';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let fullWidth = false;
	export let disabled = false;
	export let type: 'button' | 'submit' | 'reset' = 'button';

	const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500';
	
	const variantStyles = {
		primary: 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300',
		secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400',
		outline: 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-50 disabled:text-gray-400',
		link: 'text-blue-600 hover:text-blue-700 disabled:text-blue-300',
		danger: 'border border-red-600 text-red-600 bg-white hover:bg-red-50 disabled:bg-gray-50 disabled:text-gray-400 disabled:border-gray-300'
	};

	const sizeStyles = {
		sm: 'px-3 py-1.5 text-sm',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-3 text-base'
	};

	$: classes = [
		baseStyles,
		variantStyles[variant],
		sizeStyles[size],
		fullWidth ? 'w-full' : '',
		variant === 'link' ? 'px-0' : ''
	].join(' ');
</script>

{#if href}
	<a {href} class={classes} class:cursor-not-allowed={disabled} {...$$restProps}>
		<slot />
	</a>
{:else}
	<button
		{type}
		{disabled}
		class={classes}
		on:click
		{...$$restProps}
	>
		<slot />
	</button>
{/if} 