import type { PageLoad } from "./$types";
import { error } from "@sveltejs/kit";
import { get } from "svelte/store";
import { metrics, metricActions } from "$lib/stores/metrics";

export const load: PageLoad = async ({ params }) => {
  try {
    const currentMetrics = get(metrics);
    let metric = currentMetrics.find((m) => m.name === params.name);

    if (!metric) {
      await metricActions.loadMetrics();
      metric = get(metrics).find((m) => m.name === params.name);
    }

    if (!metric) {
      throw error(404, "Metric not found");
    }

    return {
      metric,
    };
  } catch (e) {
    console.error("Failed to load metric:", e);
    throw error(404, "Metric not found");
  }
};
