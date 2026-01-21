import type { PageServerLoad } from './$types';
import { getAllFilters } from '$lib/server/filters';
import { getAllSettings } from '$lib/server/settings';

export const load: PageServerLoad = async () => {
  const filters = getAllFilters();
  const settings = getAllSettings();

  return {
    filters,
    settings
  };
};
