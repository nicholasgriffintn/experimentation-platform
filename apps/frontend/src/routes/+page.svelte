<script lang="ts">
	import { Button } from "$lib/components/ui/button";
</script>

<div class="container h-full mx-auto flex justify-center items-center">
	<div class="space-y-10 text-center">
		<h2 class="h2 text-2xl font-bold mt-10">Welcome to the Experimentation Platform</h2>
		<div class="rounded-lg text-card-foreground">
			<p class="text-center">
				This platform helps you manage and analyze your experiments with ease.
				Get started by creating a new experiment or viewing existing ones.
			</p>
		</div>
		<div class="flex justify-center space-x-4">
			<Button variant="default" asChild>
				<a href="/experiments">View Experiments</a>
			</Button>
			<Button variant="secondary" asChild>
				<a href="/experiments/new">Create Experiment</a>
			</Button>
		</div>
	</div>
</div>
