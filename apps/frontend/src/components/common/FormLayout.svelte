<script lang="ts">
    export let title: string;
    export let error: string | null = null;
</script>

<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">{title}</h1>
    </div>

    {#if error}
        <div class="p-4 mb-6 text-red-700 bg-red-100 rounded-md">
            {error}
        </div>
    {/if}

    <div class="bg-white rounded-lg shadow">
        <div class="p-6">
            <slot />
        </div>
    </div>
</div> 