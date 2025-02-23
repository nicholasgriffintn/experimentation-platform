import { writable } from 'svelte/store';
import type { FeatureDefinition } from '../../types/api';
import { featuresApi } from '$lib/api/features';

function createFeatureStore() {
    const { subscribe, set, update } = writable<FeatureDefinition[]>([]);

    return {
        subscribe,
        set,
        update,
        async loadFeatures() {
            try {
                const features = await featuresApi.listFeatures();
                set(features);
            } catch (error) {
                console.error('Failed to load features:', error);
                set([]);
            }
        },
        async createFeature(feature: Omit<FeatureDefinition, 'id'>) {
            try {
                const newFeature = await featuresApi.createFeature(feature);
                update(features => [...features, newFeature]);
                return newFeature;
            } catch (error) {
                console.error('Failed to create feature:', error);
                throw error;
            }
        },
        async deleteFeature(name: string) {
            try {
                await featuresApi.deleteFeature(name);
                update(features => features.filter(f => f.name !== name));
            } catch (error) {
                console.error('Failed to delete feature:', error);
                throw error;
            }
        }
    };
}

export const features = createFeatureStore();
export const featureActions = {
    loadFeatures: features.loadFeatures,
    createFeature: features.createFeature,
    deleteFeature: features.deleteFeature
}; 