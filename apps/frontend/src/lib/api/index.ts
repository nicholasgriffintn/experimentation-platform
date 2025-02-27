import { ExperimentsAPI } from "./experiments";
import { MetricsAPI } from "./metrics";

export * from "./experiments";
export * from "./metrics";
export * from "./base";

export class API {
  experiments: ExperimentsAPI;
  metrics: MetricsAPI;

  constructor() {
    this.experiments = new ExperimentsAPI();
    this.metrics = new MetricsAPI();
  }
}

export const api = new API();
