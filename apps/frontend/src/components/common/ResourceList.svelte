<script lang="ts">
    import { createEventDispatcher } from 'svelte';

    export let title: string;
    export let items: any[] = [];
    export let loading = false;
    export let error: string | null = null;
    export let createButtonLabel = 'Create';
    export let showCreateForm = false;

    const dispatch = createEventDispatcher<{
        create: void;
        edit: { item: any };
        delete: { item: any };
    }>();
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h2 class="text-3xl font-bold">{title}</h2> 
        <button
            on:click={() => dispatch('create')}
            class="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
            {createButtonLabel}
        </button>
    </div>

    {#if error}
        <div class="p-4 text-red-700 bg-red-100 rounded-md">
            {error}
        </div>
    {/if}

    {#if loading && !items.length}
        <div class="text-center py-8">
            <span class="inline-block animate-spin text-2xl">⌛</span>
            <p class="mt-2 text-gray-600">Loading {title.toLowerCase()}...</p>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <slot {items} />
        </div>
    {/if}
</div> 