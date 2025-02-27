import { BaseAPI } from "./base";
import { config } from "../config";
import type { MetricDefinition } from "../types/api";

export class MetricsAPI extends BaseAPI {
  constructor() {
    super("/metrics");
  }

  async createMetric(metric: MetricDefinition): Promise<MetricDefinition> {
    return this.post<MetricDefinition>("/", metric);
  }

  async getMetric(name: string): Promise<MetricDefinition> {
    return this.get<MetricDefinition>(`/${name}`);
  }

  async listMetrics(): Promise<MetricDefinition[]> {
    return this.get<MetricDefinition[]>("/");
  }

  async deleteMetric(name: string): Promise<void> {
    await this.delete(`/${name}`);
  }

  async updateMetric(
    name: string,
    metric: Partial<MetricDefinition>,
  ): Promise<MetricDefinition> {
    return this.put<MetricDefinition>(`/${name}`, metric);
  }
}
