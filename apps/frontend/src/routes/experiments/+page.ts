import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { config } from '$lib/config';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const response = await fetch(config.api.experiments);
		if (!response.ok) throw new Error('Failed to fetch experiments');
		const experiments = await response.json();
		return { experiments };
	} catch (e) {
		throw error(500, {
			message: 'Error loading experiments'
		});
	}
}; 