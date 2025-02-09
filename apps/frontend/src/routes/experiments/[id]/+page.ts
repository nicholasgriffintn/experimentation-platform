import type { PageLoad } from './$types';
import { error } from '@sveltejs/kit';
import { get } from 'svelte/store';
import { experiments, experimentActions } from '$lib/stores/experiments';

export const load: PageLoad = async ({ params }) => {
    try {
        const experiment = await experimentActions.loadExperiment(params.id);
        
        if (!experiment) {
            throw error(404, 'Experiment not found');
        }

        await experimentActions.loadExperimentResults(experiment.id);

        return {
            experiment,
            experiments: get(experiments) || []
        };
    } catch (e) {
        console.error('Failed to load experiment:', e);
        throw error(404, 'Experiment not found');
    }
}; 