// src/stores/templates.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { StageTemplate } from '@/types';
import { templatesApi, type StageTemplateCreateRequest } from '@/api/templates';
import { mockTemplates } from '@/api/mock';

const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export const useTemplatesStore = defineStore('templates', () => {
  const templates = ref<StageTemplate[]>([]);
  const currentTemplate = ref<StageTemplate | null>(null);
  const loading = ref(false);

  // remember last focused template to keep view stable after refresh
  const lastTemplateId = ref<number | null>(null);

  async function fetchTemplates() {
    loading.value = true;
    try {
      if (DEMO_MODE) {
        templates.value = mockTemplates;
        return;
      }
      templates.value = await templatesApi.list();
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchTemplate(id: number) {
    loading.value = true;
    lastTemplateId.value = id;
    try {
      if (DEMO_MODE) {
        currentTemplate.value = (mockTemplates.find(t => t.id === id) as any) || null;
        return;
      }
      currentTemplate.value = await templatesApi.get(id);
    } catch (error) {
      console.error('Failed to fetch template:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createTemplate(data: StageTemplateCreateRequest) {
    loading.value = true;
    try {
      const created = await templatesApi.create(data);

      // IMPORTANT: refresh list + current template from backend
      await fetchTemplates();
      await fetchTemplate(created.id);

      return created;
    } catch (error) {
      console.error('Failed to create template:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateTemplate(id: number, data: Partial<StageTemplateCreateRequest>) {
    loading.value = true;
    try {
      const updated = await templatesApi.update(id, data);

      // refresh list + detail so UI definitely matches backend
      await fetchTemplates();
      if (currentTemplate.value?.id === id || lastTemplateId.value === id) {
        await fetchTemplate(id);
      }

      return updated;
    } catch (error) {
      console.error('Failed to update template:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function deleteTemplate(id: number) {
    loading.value = true;
    try {
      await templatesApi.delete(id);

      // refresh list
      await fetchTemplates();

      // if current deleted, clear it
      if (currentTemplate.value?.id === id) {
        currentTemplate.value = null;
      }
      if (lastTemplateId.value === id) {
        lastTemplateId.value = null;
      }
    } catch (error) {
      console.error('Failed to delete template:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function refreshCurrent() {
    if (DEMO_MODE) {
      await fetchTemplates();
      return;
    }
    await fetchTemplates();
    if (lastTemplateId.value != null) {
      await fetchTemplate(lastTemplateId.value);
    }
  }

  return {
    templates,
    currentTemplate,
    loading,
    fetchTemplates,
    fetchTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    refreshCurrent,
  };
});
