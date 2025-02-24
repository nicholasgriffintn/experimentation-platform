<script lang="ts">
  import { onMount } from 'svelte';
  import Button from "../../../components/common/Button.svelte";
  import FormLayout from "../../../components/common/FormLayout.svelte";
  import StatusBadge from "../../../components/common/StatusBadge.svelte";
  import { ExperimentsAPI } from "../../../lib/api";
  import type { Experiment, UserContext, VariantAssignment } from "../../../types/api";

  const api = new ExperimentsAPI();

  const initialUserId = `user_${Math.floor(Math.random() * 10000)}`;
  const initialSessionId = `session_${Math.floor(Math.random() * 10000)}`;
  const initialProperties = { country: "US", user_type: "registered" };

  let loading = false;
  let error: string | null = null;
  let userContext: UserContext = {
    user_id: initialUserId,
    session_id: initialSessionId,
    properties: initialProperties
  };
  let userAttributesJson = JSON.stringify(initialProperties, null, 2);
  let experiments: Experiment[] = [];
  let selectedExperiment: Experiment | null = null;
  let assignedVariant: VariantAssignment | null = null;
  let exposureRecorded = false;
  let apiResponses: Array<{
    endpoint: string;
    success: boolean;
    data: any;
    timestamp: string;
  }> = [];

  onMount(async () => {
    await loadExperiments();
  });

  function logApiResponse(endpoint: string, success: boolean, data: any) {
    apiResponses = [{
      endpoint,
      success,
      data,
      timestamp: new Date().toLocaleTimeString()
    }, ...apiResponses].slice(0, 10);
  }

  async function loadExperiments() {
    loading = true;
    error = null;
    try {
      experiments = await api.listExperiments();
      logApiResponse('GET /experiments/', true, experiments);
    } catch (err) {
      console.error('Failed to load experiments:', err);
      error = err instanceof Error ? err.message : 'Failed to load experiments';
      logApiResponse('GET /experiments/', false, { error });
    } finally {
      loading = false;
    }
  }

  async function assignVariant() {
    if (!selectedExperiment || !userContext.user_id) return;
    
    loading = true;
    error = null;
    try {
      assignedVariant = await api.assignVariant(selectedExperiment.id, userContext);
      logApiResponse(`POST /experiments/${selectedExperiment.id}/assign`, true, assignedVariant);
    } catch (err) {
      console.error('Failed to assign variant:', err);
      error = err instanceof Error ? err.message : 'Failed to assign variant';
      logApiResponse(`POST /experiments/${selectedExperiment.id}/assign`, false, { error });
    } finally {
      loading = false;
    }
  }

  async function recordExposure() {
    if (!selectedExperiment || !assignedVariant) return;
    
    loading = true;
    error = null;
    try {
      await api.recordExposure(selectedExperiment.id, userContext);
      exposureRecorded = true;
      logApiResponse(`POST /experiments/${selectedExperiment.id}/exposure`, true, { success: true });
      setTimeout(() => {
        exposureRecorded = false;
      }, 3000);
    } catch (err) {
      console.error('Failed to record exposure:', err);
      error = err instanceof Error ? err.message : 'Failed to record exposure';
      logApiResponse(`POST /experiments/${selectedExperiment.id}/exposure`, false, { error });
    } finally {
      loading = false;
    }
  }

  function selectExperiment(exp: Experiment) {
    selectedExperiment = exp;
    assignedVariant = null;
    exposureRecorded = false;
    error = null;
  }

  function updateUserAttributes() {
    try {
      const newProperties = JSON.parse(userAttributesJson);
      userContext = {
        ...userContext,
        properties: newProperties
      };
    } catch (err) {
      console.error('Invalid JSON:', err);
      error = 'Invalid JSON in user attributes';
    }
  }
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-1">Platform Demo</h1>
  <p class="text-lg text-gray-600 mb-8">
    Try out the core platform without having to setup your own site on this page, please note that this is for testing and not for production.
  </p>

  {#if loading}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="loader"></div>
    </div>
  {/if}

  {#if error}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
      {error}
    </div>
  {/if}

  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div>
      <FormLayout 
        title="User Context"
        description="Configure the user context for experiment assignment"
      >
        <div class="grid grid-cols-1 gap-4">
          <div>
            <label class="block text-gray-700 mb-2" for="userId">User ID</label>
            <input
              type="text"
              id="userId"
              bind:value={userContext.user_id}
              class="w-full px-3 py-2 border rounded-md"
              placeholder="user123"
            />
          </div>
          <div>
            <label class="block text-gray-700 mb-2" for="sessionId">Session ID (optional)</label>
            <input
              type="text"
              id="sessionId"
              bind:value={userContext.session_id}
              class="w-full px-3 py-2 border rounded-md"
              placeholder="session456"
            />
          </div>
          <div>
            <label for="userAttributes" class="block text-gray-700 mb-2">User Attributes (JSON)</label>
            <textarea
              id="userAttributes"
              bind:value={userAttributesJson}
              on:change={updateUserAttributes}
              class="w-full px-3 py-2 border rounded-md h-24 font-mono"
              placeholder={`{
  "country": "US",
  "user_type": "registered"
}`}
            />
          </div>
          <div class="text-sm text-gray-500">
            Note: Some experiments may have targeting rules based on these attributes
          </div>
        </div>
      </FormLayout>
    </div>

    <div class="col-span-2">
      <FormLayout 
        title="Available Experiments" 
        description="Select an experiment to test with"
      >
        <div class="overflow-x-auto">
          <table class="min-w-full bg-white border">
            <thead>
              <tr>
                <th class="py-2 px-4 border-b text-left">Name</th>
                <th class="py-2 px-4 border-b text-left">Type</th>
                <th class="py-2 px-4 border-b text-left">Status</th>
                <th class="py-2 px-4 border-b text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {#each experiments as exp}
                <tr class:bg-blue-50={selectedExperiment?.id === exp.id}>
                  <td class="py-2 px-4 border-b">{exp.name}</td>
                  <td class="py-2 px-4 border-b">{exp.type}</td>
                  <td class="py-2 px-4 border-b">
                    <StatusBadge status={exp.status} />
                  </td>
                  <td class="py-2 px-4 border-b">
                    <Button
                      on:click={() => selectExperiment(exp)}
                      disabled={exp.status !== 'running'}
                      variant={selectedExperiment?.id === exp.id ? 'secondary' : 'primary'}
                    >
                      Select
                    </Button>
                  </td>
                </tr>
              {/each}
              {#if experiments.length === 0}
                <tr>
                  <td colspan="4" class="py-4 text-center text-gray-500">
                    No experiments available
                  </td>
                </tr>
              {/if}
            </tbody>
          </table>
        </div>
      </FormLayout>
    </div>
  </div>

  {#if selectedExperiment}
    <div class="mt-6">
      <FormLayout 
        title="Experiment Actions"
        description="Perform actions on the selected experiment"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-gray-50 p-4 rounded-md">
            <h3 class="font-medium text-lg mb-2">Experiment Details</h3>
            <div class="space-y-2">
              <div>
                <span class="font-medium">ID:</span>
                <span>{selectedExperiment.id}</span>
              </div>
              <div>
                <span class="font-medium">Hypothesis:</span>
                <span>{selectedExperiment.hypothesis || 'N/A'}</span>
              </div>
              <div>
                <span class="font-medium">Traffic:</span>
                <span>{selectedExperiment.traffic_allocation}%</span>
              </div>

              <h4 class="font-medium mt-4 mb-2">Variants:</h4>
              <ul class="list-disc pl-5">
                {#each selectedExperiment.variants as variant}
                  <li>
                    {variant.name} ({variant.traffic_percentage}%)
                    {#if variant.type === 'control'}
                      <span class="text-xs bg-gray-200 px-1 rounded">Control</span>
                    {/if}
                  </li>
                {/each}
              </ul>

              <h4 class="font-medium mt-4 mb-2">Metrics:</h4>
              <ul class="list-disc pl-5">
                {#each selectedExperiment.metrics as metric}
                  <li>{metric}</li>
                {/each}
              </ul>
            </div>
          </div>

          <div class="space-y-4">
            <div class="p-4 border rounded-md">
              <h3 class="font-medium mb-2">Assign Variant</h3>
              <p class="text-sm text-gray-600 mb-2">
                Assigns this user to a variant based on targeting rules
              </p>
              <Button
                on:click={assignVariant}
                disabled={!userContext.user_id}
                variant="primary"
                fullWidth={true}
              >
                Assign Variant
              </Button>

              {#if assignedVariant}
                <div class="mt-3 p-3 bg-green-50 rounded-md">
                  <p class="font-medium">
                    Assigned to: {assignedVariant.variant_name}
                  </p>
                  <p class="text-sm">
                    Variant ID: {assignedVariant.variant_id}
                  </p>
                  <pre class="text-xs bg-gray-100 p-2 mt-2 rounded overflow-x-auto">
                    <code>{JSON.stringify(assignedVariant.config, null, 2)}</code>
                  </pre>
                </div>
              {/if}
            </div>

            <div class="p-4 border rounded-md">
              <h3 class="font-medium mb-2">Record Exposure</h3>
              <p class="text-sm text-gray-600 mb-2">
                Record that user was exposed to experiment
              </p>
              <Button
                on:click={recordExposure}
                disabled={!userContext.user_id || !assignedVariant}
                variant="primary"
                fullWidth={true}
              >
                Record Exposure
              </Button>

              {#if exposureRecorded}
                <div class="mt-3 p-3 bg-green-50 rounded-md">
                  <p class="font-medium">Exposure recorded successfully!</p>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </FormLayout>
    </div>
  {/if}

  <div class="mt-6">
    <FormLayout 
      title="API Response Console"
      description="View recent API interactions"
    >
      <div class="flex justify-between items-center mb-4">
        {#if apiResponses.length > 0}
          <Button
            on:click={() => apiResponses = []}
            variant="danger"
            size="sm"
          >
            Clear
          </Button>
        {/if}
      </div>

      {#if !apiResponses.length}
        <div class="text-gray-500">
          API responses will appear here after interactions.
        </div>
      {/if}

      {#if apiResponses.length > 0}
        <div class="bg-gray-800 text-gray-100 p-3 rounded-md overflow-y-auto h-64 font-mono text-sm">
          {#each apiResponses as response}
            <div class="border-b border-gray-700 pb-2 mb-2 last:border-0">
              <div class="flex justify-between text-sm mb-1">
                <span class:text-green-400={response.success} class:text-red-400={!response.success} class="font-medium">
                  {response.endpoint}
                </span>
                <span class="text-gray-400">{response.timestamp}</span>
              </div>
              <pre class="text-xs overflow-x-auto"><code>{JSON.stringify(response.data, null, 2)}</code></pre>
            </div>
          {/each}
        </div>
      {/if}
    </FormLayout>
  </div>
</div>

<style>
  .loader {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3B82F6;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style> 