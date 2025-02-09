import { BaseAPI } from './base';
import type { FeatureDefinition } from '../types/api';

export class FeaturesAPI extends BaseAPI {
    constructor() {
        super('/features');
    }

    async listFeatures(): Promise<FeatureDefinition[]> {
        return this.get<FeatureDefinition[]>('/');
    }

    async createFeature(feature: Omit<FeatureDefinition, 'id'>): Promise<FeatureDefinition> {
        return this.post<FeatureDefinition>('/', feature);
    }

    async deleteFeature(name: string): Promise<void> {
        await this.delete(`/${name}`);
    }
}

export const featuresApi = new FeaturesAPI(); 