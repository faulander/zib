import type { PageServerLoad } from './$types';
import { getAllFilters } from '$lib/server/filters';
import { getAllSettings } from '$lib/server/settings';
import { getFeedsWithErrors } from '$lib/server/feeds';

export const load: PageServerLoad = async () => {
  const filters = getAllFilters();
  const settings = getAllSettings();
  const errorFeeds = getFeedsWithErrors();

  return {
    filters,
    settings,
    errorFeeds
  };
};
