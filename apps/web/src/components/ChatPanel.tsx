"use client";

import { useState, useRef } from "react";
import {
    Send,
    Loader2,
    Wand2,
    Upload,
    FileUp,
    X,
    RefreshCw,
    MessageCircle,
} from "lucide-react";
import { useAppStore } from "@/lib/store";
import type { GenerationMode } from "@/types/schema";

const EXAMPLE_PROMPTS = [
    "Create a 5-slide pitch deck for a SaaS startup that automates invoicing",
    "Design a 4-slide presentation about climate change impact on agriculture",
    "Make a 6-slide product launch presentation for a smart fitness watch",
    "Build a 3-slide company quarterly results summary with key metrics",
];

const MODE_LABELS: Record<GenerationMode, { label: string; desc: string }> = {
    from_scratch: { label: "From Scratch", desc: "AI designs everything" },
    template: { label: "Template", desc: "Fill an existing .pptx" },
    reference: { label: "Reference", desc: "Match a .pptx style" },
};

export default function ChatPanel() {
    const {
        prompt,
        setPrompt,
        generate,
        refine,
        isGenerating,
        isRefining,
        error,
        presentation,
        generationMode,
        setGenerationMode,
        templateFile,
        setTemplateFile,
        promptHistory,
        downloadPptx,
        downloadUrl,
        reset,
    } = useAppStore();

    const [numSlides, setNumSlides] = useState<number | undefined>(undefined);
    const [refineInput, setRefineInput] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim() || isGenerating) return;
        await generate(prompt.trim(), numSlides);
    };

    const handleRefine = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!refineInput.trim() || isRefining) return;
        await refine(refineInput.trim());
        setRefineInput("");
    };

    const handleExample = (example: string) => {
        setPrompt(example);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setTemplateFile(file);
        }
    };

    const handleFileDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && file.name.endsWith(".pptx")) {
            setTemplateFile(file);
        }
    };

    const showFileUpload =
        generationMode === "template" || generationMode === "reference";
    const isBusy = isGenerating || isRefining;

    return (
        <aside className="chat-panel">
            <div className="chat-panel-header">
                <Wand2 size={18} />
                <span>
                    {presentation
                        ? "Refine Your Presentation"
                        : "Describe Your Presentation"}
                </span>
            </div>

            <div className="chat-panel-body">
                {/* ── Mode Selector (pre-generation only) ─────────────── */}
                {!presentation && (
                    <div className="mode-selector">
                        {(
                            Object.entries(MODE_LABELS) as [
                                GenerationMode,
                                { label: string; desc: string },
                            ][]
                        ).map(([mode, { label, desc }]) => (
                            <button
                                key={mode}
                                className={`mode-tab ${generationMode === mode ? "mode-tab-active" : ""}`}
                                onClick={() => setGenerationMode(mode)}
                            >
                                <span className="mode-tab-label">{label}</span>
                                <span className="mode-tab-desc">{desc}</span>
                            </button>
                        ))}
                    </div>
                )}

                {/* ── File Upload (template/reference mode) ────────── */}
                {!presentation && showFileUpload && (
                    <div
                        className="file-upload-zone"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleFileDrop}
                    >
                        {templateFile ? (
                            <div className="file-selected">
                                <FileUp size={18} />
                                <span className="file-name">
                                    {templateFile.name}
                                </span>
                                <button
                                    className="file-remove-btn"
                                    onClick={() => setTemplateFile(null)}
                                >
                                    <X size={14} />
                                </button>
                            </div>
                        ) : (
                            <button
                                className="file-upload-btn"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <Upload size={22} />
                                <span>
                                    Drop a <strong>.pptx</strong> file here
                                    or click to browse
                                </span>
                            </button>
                        )}
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pptx"
                            className="file-input-hidden"
                            onChange={handleFileChange}
                        />
                    </div>
                )}

                {/* ── Example Prompts (pre-generation) ────────────── */}
                {!presentation && (
                    <div className="example-section">
                        <p className="example-label">Try an example:</p>
                        <div className="example-grid">
                            {EXAMPLE_PROMPTS.map((ex, i) => (
                                <button
                                    key={i}
                                    className="example-chip"
                                    onClick={() => handleExample(ex)}
                                >
                                    {ex}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* ── Post-generation: Info + Actions ─────────────── */}
                {presentation && (
                    <>
                        <div className="generation-info">
                            <div className="info-card">
                                <span className="info-label">Title</span>
                                <span className="info-value">
                                    {presentation.title}
                                </span>
                            </div>
                            <div className="info-card">
                                <span className="info-label">Slides</span>
                                <span className="info-value">
                                    {presentation.slides.length}
                                </span>
                            </div>
                            <div className="info-card">
                                <span className="info-label">Theme</span>
                                <div className="color-swatches">
                                    <span
                                        className="swatch"
                                        style={{
                                            background:
                                                presentation.theme
                                                    .primary_color,
                                        }}
                                        title={`Primary: ${presentation.theme.primary_color}`}
                                    />
                                    <span
                                        className="swatch"
                                        style={{
                                            background:
                                                presentation.theme
                                                    .secondary_color,
                                        }}
                                        title={`Secondary: ${presentation.theme.secondary_color}`}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Quick actions */}
                        <div className="post-gen-actions">
                            {downloadUrl && (
                                <button
                                    className="btn btn-primary btn-sm"
                                    onClick={downloadPptx}
                                >
                                    Download .pptx
                                </button>
                            )}
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={reset}
                            >
                                <RefreshCw size={14} />
                                Start Over
                            </button>
                        </div>

                        {/* ── Prompt History ───────────────────────── */}
                        {promptHistory.length > 0 && (
                            <div className="prompt-history">
                                <p className="history-label">
                                    <MessageCircle size={14} />
                                    Conversation
                                </p>
                                <div className="history-list">
                                    {promptHistory.map((msg, i) => (
                                        <div key={i} className="history-item">
                                            <span className="history-badge">
                                                {i === 0
                                                    ? "Original"
                                                    : `Edit ${i}`}
                                            </span>
                                            <span className="history-text">
                                                {msg}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}

                {error && (
                    <div className="error-banner">
                        <p>{error}</p>
                    </div>
                )}
            </div>

            {/* ── Input Form ─────────────────────────────────────── */}
            {!presentation ? (
                <form className="chat-input-form" onSubmit={handleSubmit}>
                    <div className="slides-selector">
                        <label htmlFor="num-slides">Slides:</label>
                        <select
                            id="num-slides"
                            value={numSlides ?? "auto"}
                            onChange={(e) =>
                                setNumSlides(
                                    e.target.value === "auto"
                                        ? undefined
                                        : Number(e.target.value),
                                )
                            }
                        >
                            <option value="auto">Auto</option>
                            {[3, 4, 5, 6, 8, 10].map((n) => (
                                <option key={n} value={n}>
                                    {n}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="chat-input-wrapper">
                        <textarea
                            className="chat-textarea"
                            placeholder="Describe the presentation you want to create…"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmit(e);
                                }
                            }}
                            rows={3}
                            disabled={isBusy}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary chat-send-btn"
                            disabled={!prompt.trim() || isBusy}
                        >
                            {isGenerating ? (
                                <Loader2 size={18} className="spin" />
                            ) : (
                                <Send size={18} />
                            )}
                        </button>
                    </div>
                </form>
            ) : (
                /* ── Refinement Input (post-generation) ─────────── */
                <form className="chat-input-form" onSubmit={handleRefine}>
                    <div className="chat-input-wrapper">
                        <textarea
                            className="chat-textarea"
                            placeholder="What would you like to change? e.g. 'Make the title bigger' or 'Add a slide about pricing'"
                            value={refineInput}
                            onChange={(e) => setRefineInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleRefine(e);
                                }
                            }}
                            rows={2}
                            disabled={isBusy}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary chat-send-btn"
                            disabled={!refineInput.trim() || isBusy}
                        >
                            {isRefining ? (
                                <Loader2 size={18} className="spin" />
                            ) : (
                                <Send size={18} />
                            )}
                        </button>
                    </div>
                </form>
            )}
        </aside>
    );
}
