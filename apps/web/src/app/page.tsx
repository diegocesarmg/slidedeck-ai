"use client";

import Header from "@/components/Header";
import ChatPanel from "@/components/ChatPanel";
import SlidePreview from "@/components/SlidePreview";

export default function Home() {
  return (
    <div className="app-shell">
      <Header />
      <main className="app-main">
        <ChatPanel />
        <SlidePreview />
      </main>
    </div>
  );
}
