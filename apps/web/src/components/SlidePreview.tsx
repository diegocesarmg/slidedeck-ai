"use client";

import { useAppStore } from "@/lib/store";
import { getPreviewUrl } from "@/lib/api";
import {
    ChevronLeft,
    ChevronRight,
    Layers,
    FileText,
    MessageSquare,
} from "lucide-react";
import type { Slide, TextBox } from "@/types/schema";

/* ── Slide Card (JSON-based preview) ──────────────────────────────────── */

function SlideCard({ slide, index }: { slide: Slide; index: number }) {
    const textElements = slide.elements.filter(
        (el): el is TextBox => el.type === "text",
    );
    const titleEl = textElements.find((el) => el.is_title);
    const bodyEls = textElements.filter((el) => !el.is_title);

    return (
        <div
            className="slide-card"
            style={{ backgroundColor: slide.background_color }}
        >
            <div className="slide-number">Slide {index + 1}</div>

            {titleEl && (
                <h3
                    className="slide-title"
                    style={{
                        color: titleEl.font_color,
                        fontSize: `${Math.min(titleEl.font_size * 0.7, 28)}px`,
                        fontWeight: titleEl.font_bold ? 700 : 400,
                        textAlign: titleEl.alignment as "left" | "center" | "right",
                    }}
                >
                    {titleEl.content}
                </h3>
            )}

            <div className="slide-body">
                {bodyEls.slice(0, 4).map((el, i) => (
                    <p
                        key={i}
                        className="slide-text"
                        style={{
                            color: el.font_color,
                            fontSize: `${Math.min(el.font_size * 0.55, 13)}px`,
                            fontWeight: el.font_bold ? 600 : 400,
                        }}
                    >
                        {el.content.length > 120
                            ? el.content.slice(0, 120) + "…"
                            : el.content}
                    </p>
                ))}
                {bodyEls.length > 4 && (
                    <p className="slide-more">+{bodyEls.length - 4} more elements</p>
                )}
            </div>

            {slide.speaker_notes && (
                <div className="slide-notes-indicator" title={slide.speaker_notes}>
                    <MessageSquare size={12} />
                    <span>Notes</span>
                </div>
            )}
        </div>
    );
}

/* ── Main Preview Panel ───────────────────────────────────────────────── */

export default function SlidePreview() {
    const { presentation, previewUrls, presentationId, activeSlideIndex, setActiveSlide } =
        useAppStore();

    if (!presentation) {
        return (
            <div className="preview-empty">
                <div className="preview-empty-icon">
                    <Layers size={56} strokeWidth={1} />
                </div>
                <h2>Your presentation will appear here</h2>
                <p>
                    Describe what you want in the chat panel, hit <strong>Enter</strong>, and
                    watch the magic happen.
                </p>
            </div>
        );
    }

    const slides = presentation.slides;
    const activeSlide = slides[activeSlideIndex];

    const goNext = () =>
        setActiveSlide(Math.min(activeSlideIndex + 1, slides.length - 1));
    const goPrev = () => setActiveSlide(Math.max(activeSlideIndex - 1, 0));

    const hasPreview =
        previewUrls.length > 0 &&
        presentationId &&
        previewUrls[activeSlideIndex];

    return (
        <section className="preview-panel">
            {/* ── Main slide view ─────────────────────────────────────────── */}
            <div className="preview-main">
                <div className="preview-stage">
                    {hasPreview ? (
                        <img
                            src={getPreviewUrl(presentationId!, activeSlideIndex)}
                            alt={`Slide ${activeSlideIndex + 1}`}
                            className="preview-image"
                        />
                    ) : (
                        activeSlide && <SlideCard slide={activeSlide} index={activeSlideIndex} />
                    )}
                </div>

                {/* Navigation */}
                <div className="preview-nav">
                    <button
                        className="btn btn-ghost btn-sm"
                        onClick={goPrev}
                        disabled={activeSlideIndex === 0}
                    >
                        <ChevronLeft size={18} />
                    </button>
                    <span className="preview-counter">
                        {activeSlideIndex + 1} / {slides.length}
                    </span>
                    <button
                        className="btn btn-ghost btn-sm"
                        onClick={goNext}
                        disabled={activeSlideIndex >= slides.length - 1}
                    >
                        <ChevronRight size={18} />
                    </button>
                </div>
            </div>

            {/* ── Slide thumbnails strip ──────────────────────────────────── */}
            <div className="preview-thumbs">
                {slides.map((slide, idx) => {
                    const title = slide.elements.find(
                        (el): el is TextBox => el.type === "text" && el.is_title,
                    );
                    return (
                        <button
                            key={idx}
                            className={`thumb ${idx === activeSlideIndex ? "thumb-active" : ""}`}
                            onClick={() => setActiveSlide(idx)}
                            style={{ borderLeftColor: slide.background_color }}
                        >
                            <FileText size={14} />
                            <span className="thumb-label">
                                {title ? title.content.slice(0, 30) : `Slide ${idx + 1}`}
                            </span>
                        </button>
                    );
                })}
            </div>
        </section>
    );
}
