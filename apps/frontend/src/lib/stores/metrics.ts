import { writable } from 'svelte/store';

import type { MetricDefinition } from '../types/api';
import { api } from '../api';

export const metrics = writable<MetricDefinition[]>([]);
export const loading = writable(false);
export const error = writable<string | null>(null);

export const metricActions = {
    async loadMetrics() {
        loading.set(true);
        error.set(null);
        try {
            const data = await api.metrics.listMetrics();
            metrics.set(data);
        } catch (e) {
            error.set(e instanceof Error ? e.message : 'Failed to load metrics');
        } finally {
            loading.set(false);
        }
    },

    async createMetric(metric: MetricDefinition) {
        loading.set(true);
        error.set(null);
        try {
            const newMetric = await api.metrics.createMetric(metric);
            metrics.update(current => [...current, newMetric]);
            return newMetric;
        } catch (e) {
            error.set(e instanceof Error ? e.message : 'Failed to create metric');
            throw e;
        } finally {
            loading.set(false);
        }
    },

    async updateMetric(name: string, metric: Partial<MetricDefinition>) {
        loading.set(true);
        error.set(null);
        try {
            const updatedMetric = await api.metrics.updateMetric(name, metric);
            metrics.update(current => 
                current.map(m => m.name === name ? updatedMetric : m)
            );
            return updatedMetric;
        } catch (e) {
            error.set(e instanceof Error ? e.message : 'Failed to update metric');
            throw e;
        } finally {
            loading.set(false);
        }
    },

    async deleteMetric(name: string) {
        loading.set(true);
        error.set(null);
        try {
            await api.metrics.deleteMetric(name);
            metrics.update(current => current.filter(m => m.name !== name));
        } catch (e) {
            error.set(e instanceof Error ? e.message : 'Failed to delete metric');
            throw e;
        } finally {
            loading.set(false);
        }
    }
}; 