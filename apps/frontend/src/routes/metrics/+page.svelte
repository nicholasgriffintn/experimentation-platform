<script lang="ts">
	import type { PageData } from './$types';
	import { config } from '$lib/config';
	import { Button } from "$lib/components/ui/button";
	import { Input } from "$lib/components/ui/input";
	import { Label } from "$lib/components/ui/label";
	import { Textarea } from "$lib/components/ui/textarea";
	import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "$lib/components/ui/table";
	import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "$lib/components/ui/card";
	import * as Dialog from "$lib/components/ui/dialog";
	import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select";
	import { Plus } from 'lucide-svelte';

	export let data: PageData;

	let formData = {
		name: '',
		description: '',
		unit: '',
		aggregation_method: 'sum',
		query_template: ''
	};

	let errors = {
		name: '',
		description: '',
		unit: '',
		query_template: ''
	};

	let dialogOpen = false;

	function validateForm() {
		let isValid = true;
		errors = {
			name: '',
			description: '',
			unit: '',
			query_template: ''
		};

		if (!formData.name) {
			errors.name = 'Name is required';
			isValid = false;
		} else if (!/^[a-z0-9_]+$/.test(formData.name)) {
			errors.name = 'Name must contain only lowercase letters, numbers, and underscores';
			isValid = false;
		}

		if (!formData.description) {
			errors.description = 'Description is required';
			isValid = false;
		}

		if (!formData.unit) {
			errors.unit = 'Unit is required';
			isValid = false;
		}

		if (!formData.query_template) {
			errors.query_template = 'Query template is required';
			isValid = false;
		}

		return isValid;
	}

	async function handleCreateMetric() {
		if (!validateForm()) return;

		try {
			const response = await fetch(config.api.metrics, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(formData)
			});

			if (!response.ok) throw new Error('Failed to create metric');
			
			dialogOpen = false;
			window.location.reload();
		} catch (error) {
			console.error('Error creating metric:', error);
			// TODO: Show error toast
		}
	}

	function handleAggregationChange(value: string | undefined) {
		if (value) {
			formData.aggregation_method = value;
		}
	}
</script>

<div class="container mx-auto p-8 space-y-8">
	<div class="flex justify-between items-center">
		<h1 class="scroll-m-20 text-4xl font-bold tracking-tight">Metrics</h1>
		<Dialog.Root bind:open={dialogOpen}>
			<Dialog.Trigger asChild let:builder>
				<Button builders={[builder]}>
					<Plus class="mr-2 h-4 w-4" />
					New Metric
				</Button>
			</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[600px]">
				<Dialog.Header>
					<Dialog.Title>Create New Metric</Dialog.Title>
					<Dialog.Description>
						Add a new metric to track in your experiments. Make sure to provide a clear description and SQL query template.
					</Dialog.Description>
				</Dialog.Header>
				<div class="grid gap-4 py-4">
					<div class="grid gap-2">
						<Label for="name">Name</Label>
						<Input
							id="name"
							type="text"
							bind:value={formData.name}
							placeholder="conversion_rate"
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
							placeholder="Percentage of users who completed the desired action"
						/>
						{#if errors.description}
							<p class="text-sm text-destructive">{errors.description}</p>
						{/if}
					</div>

					<div class="grid gap-2">
						<Label for="unit">Unit</Label>
						<Input
							id="unit"
							type="text"
							bind:value={formData.unit}
							placeholder="%"
						/>
						{#if errors.unit}
							<p class="text-sm text-destructive">{errors.unit}</p>
						{/if}
					</div>

					<div class="grid gap-2">
						<Label for="aggregation">Aggregation Method</Label>
						<select
							id="aggregation"
							class="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
							bind:value={formData.aggregation_method}
						>
							<option value="sum">Sum</option>
							<option value="average">Average</option>
							<option value="count">Count</option>
							<option value="ratio">Ratio</option>
						</select>
					</div>

					<div class="grid gap-2">
						<Label for="query">Query Template</Label>
						<Textarea
							id="query"
							bind:value={formData.query_template}
							placeholder="SELECT COUNT(*) FROM events WHERE event_type = 'conversion' AND experiment_id = :experiment_id"
							class="font-mono text-sm"
							rows={4}
						/>
						{#if errors.query_template}
							<p class="text-sm text-destructive">{errors.query_template}</p>
						{/if}
					</div>
				</div>
				<Dialog.Footer>
					<Button variant="outline" type="button" on:click={() => dialogOpen = false}>Cancel</Button>
					<Button type="button" on:click={handleCreateMetric}>Create Metric</Button>
				</Dialog.Footer>
			</Dialog.Content>
		</Dialog.Root>
	</div>

	{#if data.metrics && data.metrics.length > 0}
		<Card>
			<CardHeader>
				<CardTitle>Available Metrics</CardTitle>
				<CardDescription>List of metrics that can be tracked in your experiments</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="rounded-md border">
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Name</TableHead>
								<TableHead>Description</TableHead>
								<TableHead>Unit</TableHead>
								<TableHead>Aggregation</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{#each data.metrics as metric}
								<TableRow>
									<TableCell class="font-medium font-mono">{metric.name}</TableCell>
									<TableCell>{metric.description}</TableCell>
									<TableCell>{metric.unit}</TableCell>
									<TableCell class="capitalize">{metric.aggregation_method}</TableCell>
								</TableRow>
							{/each}
						</TableBody>
					</Table>
				</div>
			</CardContent>
		</Card>
	{:else}
		<Card>
			<CardContent class="flex flex-col items-center justify-center min-h-[200px] text-center space-y-4">
				<p class="text-muted-foreground">No metrics defined yet.</p>
				<Button variant="outline" on:click={() => dialogOpen = true}>
					<Plus class="mr-2 h-4 w-4" />
					Create your first metric
				</Button>
			</CardContent>
		</Card>
	{/if}
</div> 