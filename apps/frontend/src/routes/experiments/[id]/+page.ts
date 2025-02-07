import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { config } from '$lib/config';

export const load: PageLoad = async ({ fetch, params }) => {
	try {
		const [experimentResponse] = await Promise.all([
			fetch(`${config.api.experiments}/${params.id}`),
		]);

		if (!experimentResponse.ok) throw new Error('Failed to fetch experiment');

		const experiment = await experimentResponse.json();

		return { experiment };
	} catch (e) {
		throw error(500, {
			message: 'Error loading experiment details'
		});
	}
}; 