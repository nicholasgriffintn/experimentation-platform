<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let title: string;
    export let description: string | undefined = undefined;
    export let tags: {
        label: string;
        value: string | number;
        className?: string;
    }[] = [];
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
                        <span class="inline-block px-2 py-1 text-sm rounded {tag.className || 'bg-gray-100'}">
                            {tag.label}: {tag.value}
                        </span>
                    {/each}
                </div>
            {/if}
        </div>
        {#if showActions}
            <div class="flex-shrink-0 ml-4 space-x-2">
                <button
                    on:click={() => dispatch('edit')}
                    class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded"
                >
                    Edit
                </button>
                <button
                    on:click={() => dispatch('delete')}
                    class="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
                >
                    Delete
                </button>
            </div>
        {/if}
    </div>
    <div class="mt-4 flex-1">
        <slot />
    </div>
</div> 