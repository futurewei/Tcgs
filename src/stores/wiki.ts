// src/stores/wiki.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { WikiDirection, WikiPage, WikiRevision, WikiPageCreateRequest } from '@/types';
import { wikiApi } from '@/api/wiki';
import { mockDirections } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useWikiStore = defineStore('wiki', () => {
  const directions = ref<WikiDirection[]>([]);
  const currentDirection = ref<WikiDirection | null>(null);
  const currentPage = ref<WikiPage | null>(null);
  const revisions = ref<WikiRevision[]>([]);
  const loading = ref(false);

  // track last viewed ids so refresh after mutation keeps view stable
  const lastDirectionId = ref<number | null>(null);
  const lastPageId = ref<number | null>(null);

  async function fetchDirections() {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        directions.value = mockDirections;
        return;
      }
      directions.value = await wikiApi.listDirections();
    } catch (error) {
      console.error('Failed to fetch directions:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchDirection(id: number) {
    loading.value = true;
    lastDirectionId.value = id;
    try {
      if (DEMO_MODE) {
        // demo mode only: pick from mock list
        const d = mockDirections.find(x => x.id === id) || null;
        currentDirection.value = d as any;
        return;
      }
      const direction = await wikiApi.getDirection(id);
      currentDirection.value = direction;

      // 同步更新 directions 数组中对应的项
      const index = directions.value.findIndex(d => d.id === id);
      if (index !== -1) {
        directions.value[index] = direction;
      }
    } catch (error) {
      console.error('Failed to fetch direction:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createDirection(data: { name: string; description: string; icon?: string }) {
    loading.value = true;
    try {
      const direction = await wikiApi.createDirection(data);

      // refresh list + current view
      await fetchDirections();
      await fetchDirection(direction.id);

      return direction;
    } catch (error) {
      console.error('Failed to create direction:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchPage(id: number) {
    loading.value = true;
    lastPageId.value = id;
    try {
      if (DEMO_MODE) {
        // demo mode: do nothing special (mock pages not maintained here)
        currentPage.value = null;
        return;
      }
      currentPage.value = await wikiApi.getPage(id);
    } catch (error) {
      console.error('Failed to fetch page:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createPage(data: WikiPageCreateRequest) {
    loading.value = true;
    try {
      const page = await wikiApi.createPage(data);

      // refresh direction (page list usually lives under direction)
      await fetchDirection(data.directionId);

      // open the newly created page
      await fetchPage(page.id);

      return page;
    } catch (error) {
      console.error('Failed to create page:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchRevisions(pageId: number) {
    loading.value = true;
    try {
      revisions.value = await wikiApi.listRevisions(pageId);
    } catch (error) {
      console.error('Failed to fetch revisions:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createRevision(pageId: number, content: string) {
    loading.value = true;
    try {
      const revision = await wikiApi.createRevision({ pageId, content });

      // refresh revision list + current page (so UI shows latest revision)
      await fetchRevisions(pageId);
      if (currentPage.value?.id === pageId) {
        await fetchPage(pageId);
      }

      return revision;
    } catch (error) {
      console.error('Failed to create revision:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  // optional: quick refresh current view (handy after route change)
  async function refreshCurrent() {
    if (DEMO_MODE) {
      await fetchDirections();
      return;
    }
    await fetchDirections();
    if (lastDirectionId.value != null) await fetchDirection(lastDirectionId.value);
    if (lastPageId.value != null) await fetchPage(lastPageId.value);
  }

  return {
    directions,
    currentDirection,
    currentPage,
    revisions,
    loading,
    fetchDirections,
    fetchDirection,
    createDirection,
    fetchPage,
    createPage,
    fetchRevisions,
    createRevision,
    refreshCurrent,
  };
});
