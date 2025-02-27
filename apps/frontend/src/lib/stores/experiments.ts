import { writable, derived } from "svelte/store";

import type {
  Experiment,
  ExperimentResults,
  ExperimentCreate,
  ExperimentSchedule,
} from "../types/api";
import { api } from "../api";

export const experiments = writable<Experiment[]>([]);
export const experimentResults = writable<Record<string, ExperimentResults>>(
  {},
);
export const loading = writable(false);
export const error = writable<string | null>(null);

export const activeExperiments = derived(experiments, ($experiments) =>
  $experiments.filter((exp) => exp.status === "running"),
);

export const completedExperiments = derived(experiments, ($experiments) =>
  $experiments.filter((exp) => exp.status === "completed"),
);

export const experimentActions = {
  async loadExperiments() {
    loading.set(true);
    error.set(null);
    try {
      const data = await api.experiments.listExperiments();
      experiments.set(data);
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to load experiments");
    } finally {
      loading.set(false);
    }
  },

  async loadExperiment(id: string) {
    loading.set(true);
    error.set(null);
    try {
      const experiment = await api.experiments.getExperiment(id);
      experiments.update((current) => {
        const index = current.findIndex((e) => e.id === id);
        if (index >= 0) {
          current[index] = experiment;
          return [...current];
        }
        return [...current, experiment];
      });
      return experiment;
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to load experiment");
      throw e;
    } finally {
      loading.set(false);
    }
  },

  async createExperiment(experiment: ExperimentCreate) {
    loading.set(true);
    error.set(null);
    try {
      const newExperiment = await api.experiments.createExperiment(experiment);
      experiments.update((current) => [...current, newExperiment]);
      return newExperiment;
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to create experiment");
      throw e;
    } finally {
      loading.set(false);
    }
  },

  async loadExperimentResults(experimentId: string, metrics?: string[]) {
    try {
      const results = await api.experiments.getResults(experimentId, metrics);
      experimentResults.update((current) => ({
        ...current,
        [experimentId]: results,
      }));
    } catch (e) {
      error.set(
        e instanceof Error ? e.message : "Failed to load experiment results",
      );
    }
  },

  async stopExperiment(experimentId: string, reason?: string) {
    try {
      await api.experiments.stopExperiment(experimentId, reason);
      experiments.update((current) =>
        current.map((exp) =>
          exp.id === experimentId
            ? { ...exp, status: "stopped", stopped_reason: reason }
            : exp,
        ),
      );
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to stop experiment");
    }
  },

  async pauseExperiment(experimentId: string, reason?: string) {
    try {
      await api.experiments.pauseExperiment(experimentId, reason);
      experiments.update((current) =>
        current.map((exp) =>
          exp.id === experimentId ? { ...exp, status: "paused" } : exp,
        ),
      );
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to pause experiment");
    }
  },

  async resumeExperiment(experimentId: string) {
    try {
      await api.experiments.resumeExperiment(experimentId);
      experiments.update((current) =>
        current.map((exp) =>
          exp.id === experimentId ? { ...exp, status: "running" } : exp,
        ),
      );
    } catch (e) {
      error.set(e instanceof Error ? e.message : "Failed to resume experiment");
    }
  },

  async updateSchedule(experimentId: string, schedule: ExperimentSchedule) {
    try {
      await api.experiments.updateSchedule(experimentId, schedule);
      experiments.update((current) =>
        current.map((exp) =>
          exp.id === experimentId ? { ...exp, schedule } : exp,
        ),
      );
    } catch (e) {
      error.set(
        e instanceof Error ? e.message : "Failed to update experiment schedule",
      );
    }
  },
};
