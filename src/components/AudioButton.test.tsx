import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AudioButton } from "./AudioButton";

const audio = { voice: "zh-CN-XiaoxiaoNeural", path: "abc.mp3" };

describe("AudioButton", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("AudioButton renders nothing without audio", () => {
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "https://cdn.example/audio/");
    const { container } = render(<AudioButton audio={null} label="Voz 1" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when the audio base URL is not configured", () => {
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "");
    const { container } = render(<AudioButton audio={audio} label="Voz 1" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a labelled button when audio and base URL exist", () => {
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "https://cdn.example/audio/");
    render(<AudioButton audio={audio} label="Voz 1" />);
    expect(screen.getByRole("button", { name: /Voz 1/ })).toBeInTheDocument();
  });
});
