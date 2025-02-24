<script lang="ts">
  import ResourceCard from "../../components/common/ResourceCard.svelte";
</script>

<div class="container mx-auto px-4 py-8">
	<h1 class="text-3xl font-bold mb-1">Experimentation Platform Demo</h1>
  <p class="text-lg text-gray-600 mb-8">Explore and test the platform's capabilities</p>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <ResourceCard
      title="Platform Demo"
      description="Test core platform features like experiment assignment, variant allocation, and metric recording"
      href="/demo/platform"
    >
      <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
        <li>User context management</li>
        <li>Experiment assignment</li>
        <li>Variant allocation</li>
        <li>Exposure recording</li>
        <li>Real-time feedback</li>
      </ul>
    </ResourceCard>

    <ResourceCard
      title="Traffic Simulator"
      description="Simulate multiple users and traffic patterns to test platform performance"
      href="/demo/simulator"
    >
      <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
        <li>Multi-user simulation</li>
        <li>Configurable traffic patterns</li>
        <li>Real-time statistics</li>
        <li>Performance monitoring</li>
        <li>Detailed logging</li>
      </ul>
    </ResourceCard>
  </div>
</div> 