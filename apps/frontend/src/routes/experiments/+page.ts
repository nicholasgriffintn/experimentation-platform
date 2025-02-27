import type { PageLoad } from "./$types";
import { get } from "svelte/store";
import { experiments, experimentActions } from "$lib/stores/experiments";

export const load: PageLoad = async () => {
  const currentExperiments = get(experiments);

  if (!currentExperiments.length) {
    await experimentActions.loadExperiments();
  }

  return {
    experiments: get(experiments) || [],
  };
};
