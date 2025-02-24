<script lang="ts">
    export let title: string = "";
    export let description: string = "";
    export let error: string | null = null;
</script>

<div class="form-container">
    {#if title}
        <div class="mb-8">
            <h2 class="text-2xl font-bold">{title}</h2>
            {#if description}
                <p class="text-lg text-gray-600">{description}</p>
            {/if}
        </div>
    {/if}

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