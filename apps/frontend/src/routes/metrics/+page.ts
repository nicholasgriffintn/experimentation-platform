import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { config } from '$lib/config';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(config.api.metrics);
		if (!response.ok) {
			console.error('Failed to fetch metrics:', response.statusText);
			return { metrics: [] };
		}
		const metrics = await response.json();
		// Ensure we have an array and all items have the required properties
		const validMetrics = Array.isArray(metrics) ? metrics.filter(m => 
			m && 
			typeof m === 'object' && 
			'name' in m && 
			'description' in m && 
			'unit' in m && 
			'aggregation_method' in m
		) : [];
		return { metrics: validMetrics };
	} catch (e) {
		console.error('Error loading metrics:', e);
		return { metrics: [] };
	}
}; 