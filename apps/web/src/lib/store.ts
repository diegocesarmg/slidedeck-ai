/**
 * Zustand store for the SlideDeck AI frontend.
 */

import { create } from "zustand";
import type { GenerationMode, Presentation } from "@/types/schema";
import {
    generatePresentation,
    getDownloadUrl,
    refinePresentation,
} from "@/lib/api";

interface AppState {
    // ── State ──────────────────────────────────────────────────────────────
    prompt: string;
    isGenerating: boolean;
    isRefining: boolean;
    presentation: Presentation | null;
    presentationId: string | null;
    previewUrls: string[];
    downloadUrl: string | null;
    error: string | null;
    activeSlideIndex: number;

    // ── Template / Reference ──────────────────────────────────────────────
    generationMode: GenerationMode;
    templateFile: File | null;

    // ── Prompt history (Phase 4) ──────────────────────────────────────────
    promptHistory: string[];

    // ── Actions ────────────────────────────────────────────────────────────
    setPrompt: (prompt: string) => void;
    setActiveSlide: (index: number) => void;
    setGenerationMode: (mode: GenerationMode) => void;
    setTemplateFile: (file: File | null) => void;
    generate: (prompt: string, numSlides?: number) => Promise<void>;
    refine: (instruction: string) => Promise<void>;
    reset: () => void;
    downloadPptx: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
    // ── Initial state ──────────────────────────────────────────────────────
    prompt: "",
    isGenerating: false,
    isRefining: false,
    presentation: null,
    presentationId: null,
    previewUrls: [],
    downloadUrl: null,
    error: null,
    activeSlideIndex: 0,
    generationMode: "from_scratch",
    templateFile: null,
    promptHistory: [],

    // ── Actions ────────────────────────────────────────────────────────────
    setPrompt: (prompt) => set({ prompt }),

    setActiveSlide: (index) => set({ activeSlideIndex: index }),

    setGenerationMode: (mode) => set({ generationMode: mode }),

    setTemplateFile: (file) => set({ templateFile: file }),

    generate: async (prompt, numSlides) => {
        const { generationMode, templateFile } = get();
        set({ isGenerating: true, error: null });

        try {
            const response = await generatePresentation(
                {
                    prompt,
                    num_slides: numSlides,
                    generation_mode: generationMode,
                },
                templateFile || undefined,
            );

            set({
                isGenerating: false,
                presentation: response.presentation,
                presentationId: response.presentation_id,
                previewUrls: response.preview_urls,
                downloadUrl: getDownloadUrl(response.presentation_id),
                activeSlideIndex: 0,
                promptHistory: [prompt],
            });
        } catch (err) {
            set({
                isGenerating: false,
                error: err instanceof Error ? err.message : "Generation failed",
            });
        }
    },

    refine: async (instruction) => {
        const { presentationId, promptHistory } = get();
        if (!presentationId) return;

        set({ isRefining: true, error: null });

        try {
            const response = await refinePresentation(
                presentationId,
                instruction,
            );

            set({
                isRefining: false,
                presentation: response.presentation,
                previewUrls: response.preview_urls,
                downloadUrl: getDownloadUrl(response.presentation_id),
                activeSlideIndex: 0,
                promptHistory: [...promptHistory, instruction],
            });
        } catch (err) {
            set({
                isRefining: false,
                error: err instanceof Error ? err.message : "Refinement failed",
            });
        }
    },

    reset: () =>
        set({
            prompt: "",
            isGenerating: false,
            isRefining: false,
            presentation: null,
            presentationId: null,
            previewUrls: [],
            downloadUrl: null,
            error: null,
            activeSlideIndex: 0,
            generationMode: "from_scratch",
            templateFile: null,
            promptHistory: [],
        }),

    downloadPptx: () => {
        const { downloadUrl } = get();
        if (downloadUrl) {
            window.open(downloadUrl, "_blank");
        }
    },
}));
