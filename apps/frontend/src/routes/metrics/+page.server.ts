import { config } from '$lib/config';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
    const response = await fetch(config.api.metrics);
    const metrics = await response.json();

    return {
        metrics
    };
}; 