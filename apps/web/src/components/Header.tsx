"use client";

import { Sparkles, Download, RotateCcw } from "lucide-react";
import { useAppStore } from "@/lib/store";

export default function Header() {
    const { presentation, downloadUrl, isGenerating, reset, downloadPptx } =
        useAppStore();

    return (
        <header className="header">
            <div className="header-brand">
                <div className="header-logo">
                    <Sparkles size={22} />
                </div>
                <div>
                    <h1 className="header-title">SlideDeck AI</h1>
                    <p className="header-subtitle">
                        {presentation
                            ? presentation.title
                            : "AI-Powered Presentation Generator"}
                    </p>
                </div>
            </div>

            <div className="header-actions">
                {isGenerating && (
                    <div className="generating-badge">
                        <span className="pulse-dot" />
                        Generating…
                    </div>
                )}
                {presentation && (
                    <>
                        <button className="btn btn-ghost" onClick={reset} title="Reset">
                            <RotateCcw size={16} />
                            New
                        </button>
                        {downloadUrl && (
                            <button className="btn btn-primary" onClick={downloadPptx}>
                                <Download size={16} />
                                Download .pptx
                            </button>
                        )}
                    </>
                )}
            </div>
        </header>
    );
}
