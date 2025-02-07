import { config } from '$lib/config';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
    const response = await fetch(config.api.experiments);
    const experiments = await response.json();

    return {
        experiments
    };
}; 