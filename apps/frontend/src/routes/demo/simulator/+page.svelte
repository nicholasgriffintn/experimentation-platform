<script lang="ts">
  import { onMount } from 'svelte';
  import Button from "../../../components/common/Button.svelte";
  import FormLayout from "../../../components/common/FormLayout.svelte";
  import { ExperimentsAPI } from "../../../lib/api";
  import type { Experiment, UserContext, VariantAssignment } from "../../../types/api";

  const api = new ExperimentsAPI();

  let loading = false;
  let error: string | null = null;
  let isRunning = false;
  let status: 'ready' | 'running' | 'completed' | 'error' = 'ready';

  let config = {
    numUsers: 100,
    durationMinutes: 5,
    requestIntervalMs: 1000,
    userProperties: {
      countries: ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP'],
      devices: ['web', 'mobile', 'tablet'],
      userTypes: ['new', 'registered', 'premium'],
      trafficSplit: {
        US: 0.4,
        UK: 0.3,
        CA: 0.2,
        AU: 0.1,
        web: 0.4,
        mobile: 0.5,
        tablet: 0.1,
        new: 0.3,
        registered: 0.4,
        premium: 0.3
      }
    }
  };

  let stats = {
    startTime: 0,
    totalAssignments: 0,
    totalExposures: 0,
    totalMetrics: 0,
    errors: 0
  };

  type SimulatedExperiment = Omit<Experiment, 'metrics'> & {
    assignments: number;
    exposures: number;
    metrics: Record<string, number>;
  };

  interface LogEntry {
    timestamp: string;
    type: 'info' | 'error' | 'success' | 'warning';
    message: string;
    details?: any;
  }

  let activeExperiments: SimulatedExperiment[] = [];
  let logs: LogEntry[] = [];
  let elapsedTime = 0;
  let remainingTime = 0;
  let progressPercentage = 0;
  let updateIntervalId: NodeJS.Timeout | null = null;

  interface UserAssignments {
    [userId: string]: {
      [experimentId: string]: VariantAssignment;
    };
  }

  onMount(async () => {
    const newLog: LogEntry = {
      timestamp: new Date().toISOString(),
      type: 'info',
      message: 'Simulator initialized. Ready to start.'
    };
    logs = [newLog, ...logs];
    await loadExperiments();
  });

  async function loadExperiments() {
    loading = true;
    error = null;
    try {
      const experiments = await api.listExperiments();
      activeExperiments = experiments
        .filter(exp => exp.status === 'running')
        .map(exp => ({
          ...exp,
          assignments: 0,
          exposures: 0,
          metrics: Object.fromEntries(exp.metrics.map(m => [m, 0]))
        }));

      if (activeExperiments.length === 0) {
        logs = [{
          timestamp: new Date().toISOString(),
          type: 'warning',
          message: 'Warning: No running experiments found. Make sure at least one experiment is in "running" state.'
        }, ...logs];
      } else {
        logs = [{
          timestamp: new Date().toISOString(),
          type: 'success',
          message: `Found ${activeExperiments.length} active experiments ready for simulation.`
        }, ...logs];
      }
    } catch (err) {
      console.error('Failed to load experiments:', err);
      error = err instanceof Error ? err.message : 'Failed to load experiments';
      logs = [{
        timestamp: new Date().toISOString(),
        type: 'error',
        message: `Error fetching experiments: ${error}`
      }, ...logs];
    } finally {
      loading = false;
    }
  }

  function getRandomWithWeight(weights: Record<string, number>, options: string[]): string {
    const r = Math.random();
    let sum = 0;
    for (const option of options) {
      sum += weights[option] || (1 / options.length);
      if (r <= sum) return option;
    }
    return options[options.length - 1];
  }

  function generateUserContext(): UserContext {
    const userId = `user${Math.floor(Math.random() * 10000)}`;
    const country = getRandomWithWeight(config.userProperties.trafficSplit, config.userProperties.countries);
    const device = getRandomWithWeight(config.userProperties.trafficSplit, config.userProperties.devices);
    const userType = getRandomWithWeight(config.userProperties.trafficSplit, config.userProperties.userTypes);

    return {
      user_id: userId,
      session_id: `session${Math.floor(Math.random() * 10000)}`,
      properties: {
        country,
        device,
        user_type: userType,
        timestamp: new Date().toISOString()
      }
    };
  }

  function generateUserPool() {
    const userPool = [];
    const countries = ['US', 'CA', 'UK', 'DE', 'FR', 'JP', 'AU'];
    const userTypes = ['new', 'registered', 'premium'];
    const platforms = ['web', 'mobile', 'tablet'];

    for (let i = 0; i < config.numUsers; i++) {
      userPool.push({
        user_id: `sim_user_${i}_${Date.now()}`,
        session_id: `sim_session_${i}_${Date.now()}`,
        properties: {
          country: countries[Math.floor(Math.random() * countries.length)],
          user_type: userTypes[Math.floor(Math.random() * userTypes.length)],
          platform: platforms[Math.floor(Math.random() * platforms.length)],
          visits: Math.floor(Math.random() * 30) + 1,
          signup_days: Math.floor(Math.random() * 365)
        }
      });
    }

    return userPool;
  }

  async function startSimulation() {
    if (isRunning) return;

    if (activeExperiments.length === 0) {
      await loadExperiments();
      if (activeExperiments.length === 0) {
        logs = [{
          timestamp: new Date().toISOString(),
          type: 'error',
          message: 'Cannot start simulation: No running experiments found.'
        }, ...logs];
        status = 'error';
        return;
      }
    }

    isRunning = true;
    status = 'running';
    stats = {
      ...stats,
      startTime: Date.now(),
      totalAssignments: 0,
      totalExposures: 0,
      totalMetrics: 0,
      errors: 0
    };

    logs = [{
      timestamp: new Date().toISOString(),
      type: 'info',
      message: `Starting simulation with ${config.numUsers} users for ${config.durationMinutes} minutes...`
    }, ...logs];

    activeExperiments = activeExperiments.map(exp => ({
      ...exp,
      assignments: 0,
      exposures: 0,
      metrics: Object.fromEntries(Object.keys(exp.metrics).map(m => [m, 0]))
    }));

    const endTime = Date.now() + (config.durationMinutes * 60 * 1000);
    updateIntervalId = setInterval(() => {
      const now = Date.now();
      elapsedTime = now - stats.startTime;
      remainingTime = Math.max(0, endTime - now);
      progressPercentage = (elapsedTime / (config.durationMinutes * 60 * 1000)) * 100;

      if (now >= endTime) {
        if (updateIntervalId) {
          clearInterval(updateIntervalId);
          updateIntervalId = null;
        }
        isRunning = false;
        status = 'completed';
        logs = [{
          timestamp: new Date().toISOString(),
          type: 'success',
          message: 'Simulation completed successfully'
        }, ...logs];
      }
    }, 100);

    const userPool = generateUserPool();
    const userAssignments: UserAssignments = {};

    try {
      while (isRunning && Date.now() < endTime) {
        for (const user of userPool) {
          if (!isRunning || Date.now() >= endTime) break;

          try {
            const exp = activeExperiments[Math.floor(Math.random() * activeExperiments.length)];
            if (!exp) continue;

            if (!userAssignments[user.user_id]) {
              userAssignments[user.user_id] = {};
            }

            let assignment = userAssignments[user.user_id][exp.id];

            if (!assignment) {
              assignment = await api.assignVariant(exp.id, user);
              if (assignment) {
                userAssignments[user.user_id][exp.id] = assignment;
                stats = { ...stats, totalAssignments: stats.totalAssignments + 1 };
                exp.assignments++;

                const newLog: LogEntry = {
                  timestamp: new Date().toISOString(),
                  type: 'info',
                  message: `User ${user.user_id} assigned to experiment ${exp.id}`,
                  details: {
                    variant: assignment.variant_name,
                    country: user.properties?.country,
                    device: user.properties?.platform,
                    metrics: []
                  }
                };
                logs = [newLog, ...logs];
              }
            }

            if (!assignment) continue;

            if (Math.random() < 0.7) {
              await api.recordExposure(exp.id, user);
              stats = { ...stats, totalExposures: stats.totalExposures + 1 };
              exp.exposures++;
            }

            const metricsToRecord = Object.keys(exp.metrics).filter(() => Math.random() > 0.5);
            for (const metric of metricsToRecord) {
              stats = { ...stats, totalMetrics: stats.totalMetrics + 1 };
              exp.metrics[metric]++;
            }

            if (metricsToRecord.length > 0) {
              logs[0].details.metrics = metricsToRecord;
              logs = [...logs];
            }

            if (logs.length > 100) {
              logs = logs.slice(0, 100);
            }

            await new Promise(resolve => setTimeout(resolve, config.requestIntervalMs));
          } catch (err) {
            stats = { ...stats, errors: stats.errors + 1 };
            logs = [{
              timestamp: new Date().toISOString(),
              type: 'error',
              message: err instanceof Error ? err.message : 'Unknown error occurred'
            }, ...logs];
          }
        }
      }

      if (status === 'running') {
        logs = [{
          timestamp: new Date().toISOString(),
          type: 'success',
          message: 'Simulation completed successfully'
        }, ...logs];
        status = 'completed';
      }
    } catch (error) {
      logs = [{
        timestamp: new Date().toISOString(),
        type: 'error',
        message: `Simulation error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }, ...logs];
      status = 'error';
      stats = { ...stats, errors: stats.errors + 1 };
    } finally {
      isRunning = false;
    }
  }

  function formatTime(ms: number) {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  function getExperimentAssignments(expId: string) {
    const exp = activeExperiments.find(e => e.id === expId);
    return exp ? exp.assignments : 0;
  }
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-1">Traffic Simulator</h1>
  <p class="text-lg text-gray-600 mb-8">
    The aim of this tool is to quickly add simulated traffic to your experiments, you should only use this for testing and not for production.
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
        title="Simulation Controls"
        description="Configure and control the traffic simulation"
      >
        <div class="space-y-4">
          <div>
            <label for="numUsers" class="block text-gray-700 mb-2">Number of Users</label>
            <input
              id="numUsers"
              type="number"
              bind:value={config.numUsers}
              min="1"
              max="500"
              class="w-full px-3 py-2 border rounded-md"
            />
            <p class="text-xs text-gray-500 mt-1">
              Number of simulated users (1-500)
            </p>
          </div>

          <div>
            <label for="durationMinutes" class="block text-gray-700 mb-2">Duration (minutes)</label>
            <input
              id="durationMinutes"
              type="number"
              bind:value={config.durationMinutes}
              min="1"
              max="60"
              class="w-full px-3 py-2 border rounded-md"
            />
            <p class="text-xs text-gray-500 mt-1">
              How long to run the simulation (1-60 min)
            </p>
          </div>

          <div>
            <label for="requestIntervalMs" class="block text-gray-700 mb-2">Request Interval (ms)</label>
            <input
              id="requestIntervalMs"
              type="number"
              bind:value={config.requestIntervalMs}
              min="100"
              max="5000"
              step="100"
              class="w-full px-3 py-2 border rounded-md"
            />
            <p class="text-xs text-gray-500 mt-1">
              Wait time between API calls
            </p>
          </div>

          <div class="pt-2">
            <Button
              on:click={startSimulation}
              disabled={isRunning}
              variant="primary"
              fullWidth={true}
            >
              Start Simulation
            </Button>
            {#if isRunning}
              <div class="mt-2">
                <Button
                  on:click={() => {
                    isRunning = false;
                    status = 'completed';
                    if (updateIntervalId) {
                      clearInterval(updateIntervalId);
                      updateIntervalId = null;
                    }
                    logs = [{
                      timestamp: new Date().toISOString(),
                      type: 'warning',
                      message: 'Simulation stopped by user'
                    }, ...logs];
                  }}
                  variant="danger"
                  fullWidth={true}
                >
                  Stop Simulation
                </Button>
              </div>
            {/if}
          </div>

          <div class="flex items-center justify-between pt-2">
            <span class="font-medium">Status:</span>
            <span>{status}</span>
          </div>
        </div>
      </FormLayout>
    </div>

    <div class="col-span-2">
      <FormLayout
        title="Simulation Statistics"
        description="Real-time metrics and experiment performance"
      >
        {#if !stats.startTime}
          <div class="text-gray-500">
            Simulation has not started yet. Statistics will appear here.
          </div>
        {:else}
          <div class="space-y-4">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-blue-50 p-4 rounded-md">
                <div class="text-sm text-blue-700">Total Assignments</div>
                <div class="text-2xl font-bold">{stats.totalAssignments}</div>
              </div>

              <div class="bg-green-50 p-4 rounded-md">
                <div class="text-sm text-green-700">Total Exposures</div>
                <div class="text-2xl font-bold">{stats.totalExposures}</div>
              </div>

              <div class="bg-purple-50 p-4 rounded-md">
                <div class="text-sm text-purple-700">Metrics Recorded</div>
                <div class="text-2xl font-bold">{stats.totalMetrics}</div>
              </div>

              <div class="bg-red-50 p-4 rounded-md">
                <div class="text-sm text-red-700">Errors</div>
                <div class="text-2xl font-bold">{stats.errors}</div>
              </div>
            </div>

            <div class="bg-gray-50 p-4 rounded-md">
              <div class="flex justify-between">
                <div>
                  <span class="font-medium">Runtime:</span>
                  <span>{formatTime(elapsedTime)}</span>
                </div>
                <div>
                  <span class="font-medium">Remaining:</span>
                  <span>{formatTime(remainingTime)}</span>
                </div>
              </div>

              <div class="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                <div
                  class="bg-blue-600 h-2.5 rounded-full transition-all duration-200"
                  style="width: {progressPercentage}%"
                />
              </div>
              <div class="text-right text-sm text-gray-500 mt-1">
                {progressPercentage.toFixed(1)}% complete
              </div>
            </div>

            <div>
              <h3 class="font-medium mb-2">Active Experiments</h3>
              <div class="overflow-x-auto">
                <table class="min-w-full bg-white border">
                  <thead>
                    <tr>
                      <th class="py-2 px-3 border-b text-left">Name</th>
                      <th class="py-2 px-3 border-b text-left">Type</th>
                      <th class="py-2 px-3 border-b text-right">Assignments</th>
                      <th class="py-2 px-3 border-b text-right">Exposures</th>
                      <th class="py-2 px-3 border-b text-right">Metrics</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each activeExperiments as exp}
                      <tr>
                        <td class="py-2 px-3 border-b">{exp.name}</td>
                        <td class="py-2 px-3 border-b">{exp.type}</td>
                        <td class="py-2 px-3 border-b text-right">
                          {exp.assignments}
                        </td>
                        <td class="py-2 px-3 border-b text-right">
                          {exp.exposures}
                        </td>
                        <td class="py-2 px-3 border-b text-right">
                          {Object.values(exp.metrics).reduce((a, b) => a + b, 0)}
                        </td>
                      </tr>
                    {/each}
                    {#if activeExperiments.length === 0}
                      <tr>
                        <td colspan="5" class="py-4 text-center text-gray-500">
                          No active experiments found
                        </td>
                      </tr>
                    {/if}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}
      </FormLayout>
    </div>
  </div>

  <div class="mt-6">
    <FormLayout
      title="Simulation Log"
      description="Detailed log of simulation events and actions"
    >
      <div class="flex justify-between items-center mb-4">
        {#if logs.length > 0}
          <Button
            on:click={() => logs = []}
            variant="danger"
            size="sm"
          >
            Clear
          </Button>
        {/if}
      </div>

      {#if !logs.length}
        <div class="text-gray-500">
          Log entries will appear here during simulation.
        </div>
      {:else}
        <div class="bg-gray-800 text-gray-100 p-3 rounded-md overflow-y-auto h-64 font-mono text-sm">
          {#each logs as log}
            <div class="border-b border-gray-700 pb-1 mb-1 last:border-0">
              <span class="text-gray-400 text-xs">{log.timestamp}</span>
              <span class="ml-2" class:text-green-400={log.type === 'success'} 
                                class:text-yellow-400={log.type === 'warning'}
                                class:text-red-400={log.type === 'error'}
                                class:text-blue-400={log.type === 'info'}>
                {log.message}
                {#if log.details}
                  <span class="text-gray-500">
                    ({log.details.variant}, {log.details.country}/{log.details.device})
                    {#if log.details.metrics?.length}
                      - Metrics: {log.details.metrics.join(', ')}
                    {/if}
                  </span>
                {/if}
              </span>
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