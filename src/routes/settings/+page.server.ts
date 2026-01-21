import type { PageServerLoad } from './$types';
import { getAllFilters } from '$lib/server/filters';

export const load: PageServerLoad = async () => {
  const filters = getAllFilters();

  return {
    filters
  };
};
