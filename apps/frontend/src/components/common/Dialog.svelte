<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import Button from './Button.svelte';

    export let title: string;
    export let isOpen: boolean = false;
    export let description: string | undefined = undefined;
    export let confirmLabel: string = 'Confirm';
    export let cancelLabel: string = 'Cancel';

    export let inputLabel: string | undefined = undefined;
    export let inputPlaceholder: string | undefined = undefined;
    export let inputValue: string = '';

    export let inputs: Array<{
        label: string;
        placeholder?: string;
        value: string;
        required?: boolean;
    }> | undefined = undefined;

    const dispatch = createEventDispatcher<{
        confirmSingle: string;
        confirmMultiple: Record<string, string>;
        cancel: void;
    }>();

    function handleConfirm() {
        if (inputs) {
            const values = inputs.reduce((acc, input, index) => {
                acc[`input${index}`] = input.value;
                return acc;
            }, {} as Record<string, string>);
            dispatch('confirmMultiple', values);
        } else {
            dispatch('confirmSingle', inputValue);
        }
        isOpen = false;
        resetValues();
    }

    function handleCancel() {
        dispatch('cancel');
        isOpen = false;
        resetValues();
    }

    function resetValues() {
        inputValue = '';
        if (inputs) {
            inputs.forEach(input => input.value = '');
        }
    }

    function handleOutsideClick(event: MouseEvent) {
        if (event.target === event.currentTarget) {
            handleCancel();
        }
    }
</script>

{#if isOpen}
    <div
      role="presentation"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        on:click={handleOutsideClick}
        on:keydown={(e) => e.key === 'Escape' && handleCancel()}
        on:keydown={(e) => e.key === 'Enter' && handleConfirm()}
    >
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-4" role="dialog" aria-labelledby="dialog-title">
            <h2 class="text-xl font-semibold" id="dialog-title">{title}</h2>
            
            {#if description}
                <p class="text-gray-600">{description}</p>
            {/if}

            {#if inputs}
                <div class="space-y-4">
                    {#each inputs as input}
                        <div class="space-y-2">
                            <label for={input.label} class="block text-sm font-medium text-gray-700">
                                {input.label}
                            </label>
                            <input
                                id={input.label}
                                type="text"
                                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder={input.placeholder}
                                bind:value={input.value}
                                required={input.required}
                                on:keydown={(e) => e.key === 'Enter' && !e.shiftKey && handleConfirm()}
                            />
                        </div>
                    {/each}
                </div>
            {:else if inputLabel}
                <div class="space-y-2">
                    <label for={inputLabel} class="block text-sm font-medium text-gray-700">
                        {inputLabel}
                    </label>
                    <input
                        id={inputLabel}
                        type="text"
                        class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={inputPlaceholder}
                        bind:value={inputValue}
                        on:keydown={(e) => e.key === 'Enter' && handleConfirm()}
                    />
                </div>
            {/if}

            <div class="flex justify-end space-x-3 pt-4">
                <Button
                    variant="secondary"
                    on:click={handleCancel}
                >
                    {cancelLabel}
                </Button>
                <Button
                    variant="primary"
                    on:click={handleConfirm}
                >
                    {confirmLabel}
                </Button>
            </div>
        </div>
    </div>
{/if} 