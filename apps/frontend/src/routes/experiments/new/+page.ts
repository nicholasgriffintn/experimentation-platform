import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { config } from '$lib/config';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(config.api.metrics);
		if (!response.ok) throw new Error('Failed to fetch metrics');
		const metrics = await response.json();
		return { metrics };
	} catch (e) {
		throw error(500, {
			message: 'Error loading metrics'
		});
	}
}; 