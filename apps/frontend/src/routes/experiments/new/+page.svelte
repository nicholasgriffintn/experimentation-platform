<script lang="ts">
	import { goto } from '$app/navigation';
	import { config } from '$lib/config';
	import type { PageData } from './$types';
	import { Button } from "$lib/components/ui/button";
	import { Input } from "$lib/components/ui/input";
	import { Label } from "$lib/components/ui/label";
	import { Textarea } from "$lib/components/ui/textarea";
	import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "$lib/components/ui/card";
	import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select";
	import { Checkbox } from "$lib/components/ui/checkbox";

	export let data: PageData;

	let formData = {
		name: '',
		description: '',
		type: 'ab_test',
		hypothesis: '',
		target_metrics: [] as string[],
		parameters: {}
	};

	let errors = {
		name: '',
		description: '',
		type: '',
		hypothesis: ''
	};

	let selectedMetrics = new Set<string>();

	function validateForm() {
		let isValid = true;
		errors = {
			name: '',
			description: '',
			type: '',
			hypothesis: ''
		};

		if (!formData.name) {
			errors.name = 'Name is required';
			isValid = false;
		}

		if (!formData.description) {
			errors.description = 'Description is required';
			isValid = false;
		}

		if (!formData.type) {
			errors.type = 'Type is required';
			isValid = false;
		}

		if (!formData.hypothesis) {
			errors.hypothesis = 'Hypothesis is required';
			isValid = false;
		}

		return isValid;
	}

	function handleMetricToggle(metricName: string) {
		if (selectedMetrics.has(metricName)) {
			selectedMetrics.delete(metricName);
		} else {
			selectedMetrics.add(metricName);
		}
		formData.target_metrics = Array.from(selectedMetrics);
	}

	async function handleSubmit() {
		if (!validateForm()) return;

		try {
			const response = await fetch(config.api.experiments, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(formData)
			});

			if (!response.ok) throw new Error('Failed to create experiment');

			const result = await response.json();
			goto('/experiments/' + result.id);
		} catch (error) {
			console.error('Error creating experiment:', error);
			// TODO: Show error toast
		}
	}
</script>

<div class="container mx-auto p-8 space-y-8">
	<div class="flex justify-between items-center">
		<h1 class="scroll-m-20 text-4xl font-bold tracking-tight">Create New Experiment</h1>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>New Experiment</CardTitle>
			<CardDescription>Create a new experiment to test your hypothesis</CardDescription>
		</CardHeader>
		<CardContent>
			<form on:submit|preventDefault={handleSubmit} class="space-y-6">
				<div class="space-y-4">
					<div class="grid gap-2">
						<Label for="name">Name</Label>
						<Input
							id="name"
							type="text"
							bind:value={formData.name}
							placeholder="My Awesome Experiment"
							class="w-full"
						/>
						{#if errors.name}
							<p class="text-sm text-destructive">{errors.name}</p>
						{/if}
					</div>

					<div class="grid gap-2">
						<Label for="description">Description</Label>
						<Textarea
							id="description"
							bind:value={formData.description}
							placeholder="Describe your experiment..."
							class="min-h-[100px]"
						/>
						{#if errors.description}
							<p class="text-sm text-destructive">{errors.description}</p>
						{/if}
					</div>

					<div class="grid gap-2">
						<Label for="type">Type</Label>
						<Select bind:value={formData.type}>
							<SelectTrigger>
								<SelectValue placeholder="Select experiment type" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="ab_test">A/B Test</SelectItem>
								<SelectItem value="multivariate">Multivariate Test</SelectItem>
								<SelectItem value="feature_flag">Feature Flag</SelectItem>
							</SelectContent>
						</Select>
						{#if errors.type}
							<p class="text-sm text-destructive">{errors.type}</p>
						{/if}
					</div>

					<div class="grid gap-2">
						<Label for="hypothesis">Hypothesis</Label>
						<Textarea
							id="hypothesis"
							bind:value={formData.hypothesis}
							placeholder="What are you testing?"
							class="min-h-[100px]"
						/>
						{#if errors.hypothesis}
							<p class="text-sm text-destructive">{errors.hypothesis}</p>
						{/if}
					</div>

					<div class="grid gap-4">
						<Label>Target Metrics</Label>
						{#if data.metrics && data.metrics.length > 0}
							<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
								{#each data.metrics as metric}
									<div class="flex items-center space-x-2">
										<Checkbox
											checked={selectedMetrics.has(metric.name)}
											onCheckedChange={() => handleMetricToggle(metric.name)}
										/>
										<Label class="text-sm font-normal">{metric.name}</Label>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-sm text-destructive">No metrics available. Please create some metrics first.</p>
						{/if}
					</div>
				</div>
			</form>
		</CardContent>
		<CardFooter class="flex justify-between">
			<Button variant="outline" asChild>
				<a href="/experiments">Cancel</a>
			</Button>
			<Button type="submit" on:click={handleSubmit}>Create Experiment</Button>
		</CardFooter>
	</Card>
</div> 