<script lang="ts">
    import TextLink from './TextLink.svelte';

    export let title: string;
    export let viewAllLink: string;
    export let viewAllText: string = "View all →";
    export let emptyMessage: string = "No items yet";
    export let items: any[] = [];
</script>

<div class="bg-white p-6 rounded-lg shadow">
    <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold">{title}</h2>
        <TextLink href={viewAllLink} size="sm">
            {viewAllText}
        </TextLink>
    </div>
    {#if items.length === 0}
        <p class="text-gray-500">{emptyMessage}</p>
    {:else}
        <div class="space-y-4">
            <slot {items} />
        </div>
    {/if}
</div> 