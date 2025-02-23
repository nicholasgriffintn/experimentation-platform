<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import Button from './Button.svelte';

    export let title: string;
    export let description: string | undefined = undefined;
    export let tags: Array<{
        label: string;
        value: string | number;
        className?: string;
        component?: any;
        props?: Record<string, any>;
    }> = [];
    export let showActions = true;
    export let href: string | undefined = undefined;

    const dispatch = createEventDispatcher<{
        edit: void;
        delete: void;
    }>();
</script>

<div class="p-6 bg-white rounded-lg shadow h-full flex flex-col">
    <div class="flex justify-between items-start">
        <div class="flex-1 min-w-0">
            {#if href}
                <a {href} class="block">
                    <h3 class="text-lg font-semibold truncate text-blue-600 hover:text-blue-800">{title}</h3>
                    {#if description}
                        <p class="text-gray-600 mt-1 line-clamp-2">{description}</p>
                    {/if}
                </a>
            {:else}
                <h3 class="text-lg font-semibold truncate">{title}</h3>
                {#if description}
                    <p class="text-gray-600 mt-1 line-clamp-2">{description}</p>
                {/if}
            {/if}
            {#if tags.length > 0}
                <div class="mt-2 flex flex-wrap gap-2">
                    {#each tags as tag}
                        {#if tag.component}
                            <svelte:component this={tag.component} {...tag.props} />
                        {:else}
                            <span class="inline-block px-2 py-1 text-sm rounded {tag.className || 'bg-gray-100'}">
                                {tag.label}: {tag.value}
                            </span>
                        {/if}
                    {/each}
                </div>
            {/if}
        </div>
        {#if showActions}
            <div class="flex-shrink-0 ml-4 space-x-2">
                <Button
                    variant="outline"
                    size="sm"
                    on:click={() => dispatch('edit')}
                >
                    Edit
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    class="!text-red-600 !border-red-600 hover:!bg-red-50"
                    on:click={() => dispatch('delete')}
                >
                    Delete
                </Button>
            </div>
        {/if}
    </div>
    <div class="mt-4 flex-1">
        <slot />
    </div>
</div> 