<script lang="ts">
    export let title: string;
    export let value: number;
    export let valueColor: string = "text-gray-900";
</script>

<div class="bg-white p-6 rounded-lg shadow">
    <h3 class="text-lg font-medium text-gray-900">{title}</h3>
    <p class="mt-2 text-3xl font-semibold {valueColor}">{value}</p>
</div> 