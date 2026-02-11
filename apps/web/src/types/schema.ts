/**
 * Auto-generated TypeScript interfaces for the SlideDeck AI IR.
 *
 * ⚠️  DO NOT EDIT MANUALLY — run `./scripts/gen-types.sh` to regenerate.
 *
 * (This initial version is hand-written to match the Python models;
 *  it will be overwritten by the code generator once the tooling is set up.)
 */

// ── Enums ──────────────────────────────────────────────────────────────────

export type HorizontalAlignment = "left" | "center" | "right";
export type VerticalAlignment = "top" | "middle" | "bottom";
export type ChartType = "bar" | "line" | "pie" | "doughnut";
export type LayoutType =
    | "title"
    | "title_content"
    | "two_column"
    | "blank"
    | "section_header"
    | "image_full";

export type GenerationMode = "from_scratch" | "template" | "reference";

// ── Design Tokens ──────────────────────────────────────────────────────────

export interface DesignTokens {
    primary_color: string;
    secondary_color: string;
    background_color: string;
    font_heading: string;
    font_body: string;
    layout_names: string[];
    extracted_colors: string[];
    extracted_fonts: string[];
}

// ── Element Models ─────────────────────────────────────────────────────────

export interface TextBox {
    type: "text";
    content: string;
    is_title: boolean;
    x: number;
    y: number;
    width: number;
    height: number;
    font_name: string;
    font_size: number;
    font_bold: boolean;
    font_italic: boolean;
    font_color: string;
    alignment: HorizontalAlignment;
    vertical_alignment: VerticalAlignment;
}

export interface ImageElement {
    type: "image";
    url?: string;
    path?: string;
    alt_text: string;
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface ChartElement {
    type: "chart";
    chart_type: ChartType;
    title: string;
    categories: string[];
    series: { name: string; values: number[] }[];
    x: number;
    y: number;
    width: number;
    height: number;
}

export type SlideElement = TextBox | ImageElement | ChartElement;

// ── Slide & Presentation ───────────────────────────────────────────────────

export interface Slide {
    layout: LayoutType;
    background_color: string;
    elements: SlideElement[];
    speaker_notes: string;
}

export interface ThemeSettings {
    primary_color: string;
    secondary_color: string;
    background_color: string;
    font_heading: string;
    font_body: string;
}

export interface Presentation {
    title: string;
    subtitle: string;
    author: string;
    theme: ThemeSettings;
    slides: Slide[];
}

// ── API Schemas ────────────────────────────────────────────────────────────

export interface GenerateRequest {
    prompt: string;
    num_slides?: number;
    generation_mode?: GenerationMode;
}

export interface GenerateResponse {
    presentation_id: string;
    presentation: Presentation;
    download_url: string;
    preview_urls: string[];
    generation_mode: GenerationMode;
    design_tokens?: DesignTokens;
}

export interface RefineRequest {
    instruction: string;
}

export interface RefineResponse {
    presentation_id: string;
    presentation: Presentation;
    download_url: string;
    preview_urls: string[];
}
