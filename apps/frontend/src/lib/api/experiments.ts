import { BaseAPI } from './base';
import { config } from '../config';
import type {
    Experiment,
    ExperimentCreate,
    VariantAssignment,
    UserContext,
    ExperimentResults,
    ExperimentSchedule
} from '../types/api';

export class ExperimentsAPI extends BaseAPI {
    constructor() {
        super('/experiments');
    }

    async createExperiment(experiment: ExperimentCreate): Promise<Experiment> {
        return this.post<Experiment>('/', experiment);
    }

    async getExperiment(id: string): Promise<Experiment> {
        return this.get<Experiment>(`/${id}`);
    }

    async listExperiments(): Promise<Experiment[]> {
        return this.get<Experiment[]>('/');
    }

    async assignVariant(
        experimentId: string,
        userContext: UserContext
    ): Promise<VariantAssignment> {
        return this.post<VariantAssignment>(
            `/${experimentId}/assign`,
            userContext
        );
    }

    async recordExposure(
        experimentId: string,
        userContext: UserContext,
        metadata?: Record<string, any>
    ): Promise<void> {
        await this.post(
            `/${experimentId}/exposure`,
            { ...userContext, metadata }
        );
    }

    async getResults(
        experimentId: string,
        metrics?: string[]
    ): Promise<ExperimentResults> {
        const query = metrics?.length 
            ? `?metrics=${metrics.join(',')}`
            : '';
        return this.get<ExperimentResults>(`/${experimentId}/results${query}`);
    }

    async updateSchedule(
        experimentId: string,
        schedule: ExperimentSchedule
    ): Promise<void> {
        await this.put(`/${experimentId}/schedule`, schedule);
    }

    async stopExperiment(
        experimentId: string,
        reason?: string
    ): Promise<void> {
        await this.post(`/${experimentId}/stop`, { reason });
    }

    async pauseExperiment(
        experimentId: string,
        reason?: string
    ): Promise<void> {
        await this.post(`/${experimentId}/pause`, { reason });
    }

    async resumeExperiment(
        experimentId: string
    ): Promise<void> {
        await this.post(`/${experimentId}/resume`, {});
    }
} 