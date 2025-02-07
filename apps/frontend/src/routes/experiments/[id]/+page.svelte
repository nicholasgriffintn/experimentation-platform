<script lang="ts">
	import type { PageData } from './$types';
	import { config } from '$lib/config';
	import { Button } from "$lib/components/ui/button";
	import { Badge } from "$lib/components/ui/badge";
	import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "$lib/components/ui/card";
	import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "$lib/components/ui/table";
	import { Separator } from "$lib/components/ui/separator";
	import { Play, Pause, StopCircle, CheckCircle } from 'lucide-svelte';

	export let data: PageData;

	$: experiment = data.experiment;

	function getStatusVariant(status: string): "default" | "destructive" | "outline" | "secondary" | "success" {
		switch (status.toLowerCase()) {
			case 'draft':
				return 'outline';
			case 'running':
				return 'success';
			case 'paused':
				return 'secondary';
			case 'completed':
				return 'default';
			case 'stopped':
				return 'destructive';
			default:
				return 'outline';
		}
	}

	async function handleStatusChange(newStatus: string) {
		try {
			const response = await fetch(`${config.api.experiments}/${experiment.id}/status`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ status: newStatus })
			});

			if (!response.ok) throw new Error('Failed to update experiment status');
			window.location.reload();
		} catch (error) {
			console.error('Error updating experiment status:', error);
			// TODO: Show error toast
		}
	}
</script>

<div class="container mx-auto p-8 space-y-8">
	<div class="flex justify-between items-start">
		<div class="space-y-2">
			<h1 class="scroll-m-20 text-4xl font-bold tracking-tight">{experiment.name}</h1>
			<p class="text-muted-foreground">{experiment.description}</p>
		</div>
		<div class="flex gap-2">
			{#if experiment.status === 'draft'}
				<Button variant="success" on:click={() => handleStatusChange('running')}>
					<Play class="mr-2 h-4 w-4" />
					Start Experiment
				</Button>
			{:else if experiment.status === 'running'}
				<Button variant="secondary" on:click={() => handleStatusChange('paused')}>
					<Pause class="mr-2 h-4 w-4" />
					Pause
				</Button>
				<Button variant="default" on:click={() => handleStatusChange('completed')}>
					<CheckCircle class="mr-2 h-4 w-4" />
					Complete
				</Button>
			{:else if experiment.status === 'paused'}
				<Button variant="success" on:click={() => handleStatusChange('running')}>
					<Play class="mr-2 h-4 w-4" />
					Resume
				</Button>
				<Button variant="destructive" on:click={() => handleStatusChange('stopped')}>
					<StopCircle class="mr-2 h-4 w-4" />
					Stop
				</Button>
			{/if}
		</div>
	</div>

	<Separator />

	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		<Card>
			<CardHeader>
				<CardTitle>Details</CardTitle>
				<CardDescription>Experiment configuration and metadata</CardDescription>
			</CardHeader>
			<CardContent>
				<div class="space-y-6">
					<div class="grid grid-cols-2 gap-4">
						<div class="space-y-1">
							<p class="text-sm font-medium leading-none">Type</p>
							<p class="text-sm text-muted-foreground capitalize">{experiment.type}</p>
						</div>
						<div class="space-y-1">
							<p class="text-sm font-medium leading-none">Status</p>
							<Badge variant={getStatusVariant(experiment.status)} class="mt-1">
								{experiment.status}
							</Badge>
						</div>
						<div class="space-y-1">
							<p class="text-sm font-medium leading-none">Created</p>
							<p class="text-sm text-muted-foreground">
								{new Date(experiment.created_at).toLocaleDateString()}
							</p>
						</div>
					</div>
					<Separator />
					<div class="space-y-1">
						<p class="text-sm font-medium leading-none">Hypothesis</p>
						<p class="text-sm text-muted-foreground mt-2">{experiment.hypothesis}</p>
					</div>
				</div>
			</CardContent>
		</Card>

		{#if experiment.parameters && Object.keys(experiment.parameters).length > 0}
			<Card>
				<CardHeader>
					<CardTitle>Parameters</CardTitle>
					<CardDescription>Configuration parameters for this experiment</CardDescription>
				</CardHeader>
				<CardContent>
					<div class="rounded-md border">
						<Table>
							<TableHeader>
								<TableRow>
									<TableHead>Parameter</TableHead>
									<TableHead>Value</TableHead>
								</TableRow>
							</TableHeader>
							<TableBody>
								{#each Object.entries(experiment.parameters) as [key, value]}
									<TableRow>
										<TableCell class="font-medium">{key}</TableCell>
										<TableCell>
											<code class="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm">
												{JSON.stringify(value)}
											</code>
										</TableCell>
									</TableRow>
								{/each}
							</TableBody>
						</Table>
					</div>
				</CardContent>
			</Card>
		{/if}
	</div>
</div> 