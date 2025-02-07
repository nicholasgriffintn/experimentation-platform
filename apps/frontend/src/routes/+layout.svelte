<!-- Main Layout -->
<script lang="ts">
	import '../app.postcss';
	import { Button } from "$lib/components/ui/button";
	import { FlaskConical, LineChart } from 'lucide-svelte';
</script>

<div class="min-h-screen flex flex-col">
	<header class="border-b">
		<div class="container mx-auto flex h-16 items-center px-4 sm:px-8">
			<div class="mr-8">
				<a href="/" class="flex items-center space-x-2">
					<FlaskConical class="h-6 w-6" />
					<span class="font-bold text-xl">Experimentation Platform</span>
				</a>
			</div>
			<nav class="flex items-center space-x-4 lg:space-x-6">
				<Button variant="ghost" asChild>
					<a href="/" class="flex items-center space-x-2">
						<FlaskConical class="h-4 w-4" />
						<span>Experiments</span>
					</a>
				</Button>
				<Button variant="ghost" asChild>
					<a href="/metrics" class="flex items-center space-x-2">
						<LineChart class="h-4 w-4" />
						<span>Metrics</span>
					</a>
				</Button>
			</nav>
		</div>
	</header>

	<main class="flex-1 bg-background">
		<slot />
	</main>
</div> 