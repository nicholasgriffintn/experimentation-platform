<script lang="ts">
	import type { PageData } from './$types';
	import { Button } from "$lib/components/ui/button";
	import { Input } from "$lib/components/ui/input";
	import { Badge } from "$lib/components/ui/badge";
	import { Card, CardContent, CardHeader, CardTitle } from "$lib/components/ui/card";
	import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "$lib/components/ui/table";
	import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "$lib/components/ui/select";
	import { Search, Plus } from 'lucide-svelte';

	export let data: PageData;

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
</script>

<div class="container mx-auto p-8 space-y-8">
	<div class="flex justify-between items-center">
		<h2 class="scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0">Experiments</h2>
		<Button variant="default" asChild>
			<a href="/experiments/new" class="flex items-center gap-2">
				<Plus class="h-4 w-4" />
				<span>New Experiment</span>
			</a>
		</Button>
	</div>

	{#if data.experiments && data.experiments.length > 0}
		<Card>
			<CardHeader>
				<div class="flex justify-between items-center gap-4">
					<div class="flex-1 flex gap-4">
						<div class="relative flex-1">
							<Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
							<Input type="search" placeholder="Search experiments..." class="pl-8" />
						</div>
						<Select>
							<SelectTrigger class="w-[180px]">
								<SelectValue placeholder="All Types" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="all">All Types</SelectItem>
								<SelectItem value="ab_test">A/B Test</SelectItem>
								<SelectItem value="multivariate">Multivariate</SelectItem>
								<SelectItem value="feature_flag">Feature Flag</SelectItem>
							</SelectContent>
						</Select>
					</div>
				</div>
			</CardHeader>
			<CardContent>
				<div class="rounded-md border">
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Name</TableHead>
								<TableHead>Type</TableHead>
								<TableHead>Status</TableHead>
								<TableHead>Created</TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{#each data.experiments as experiment}
								<TableRow>
									<TableCell>
										<a
											href="/experiments/{experiment.id}"
											class="hover:underline text-foreground font-medium"
										>
											{experiment.name}
										</a>
									</TableCell>
									<TableCell class="capitalize">{experiment.type}</TableCell>
									<TableCell>
										<Badge variant={getStatusVariant(experiment.status)}>
											{experiment.status}
										</Badge>
									</TableCell>
									<TableCell>{new Date(experiment.created_at).toLocaleDateString()}</TableCell>
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
				<p class="text-muted-foreground">No experiments found.</p>
				<Button variant="outline" asChild>
					<a href="/experiments/new" class="flex items-center gap-2">
						<Plus class="h-4 w-4" />
						<span>Create your first experiment</span>
					</a>
				</Button>
			</CardContent>
		</Card>
	{/if}
</div> 