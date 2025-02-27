import type { PageLoad } from "./$types";
import { get } from "svelte/store";
import { metrics, metricActions } from "$lib/stores/metrics";

export const load: PageLoad = async () => {
  const currentMetrics = get(metrics);

  if (!currentMetrics.length) {
    await metricActions.loadMetrics();
  }

  return {
    metrics: get(metrics),
  };
};
