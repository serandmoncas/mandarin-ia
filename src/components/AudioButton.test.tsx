import { fireEvent, render, screen } from "@testing-library/react";
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

  it("joins the base URL and path with exactly one slash", () => {
    const played: string[] = [];
    vi.stubGlobal(
      "Audio",
      class {
        currentTime = 0;
        constructor(src: string) {
          played.push(src);
        }
        addEventListener() {}
        play() {
          return Promise.resolve();
        }
      },
    );
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "https://cdn.example/audio");
    render(<AudioButton audio={audio} label="Voz 1" />);
    fireEvent.click(screen.getByRole("button"));
    vi.unstubAllGlobals();
    expect(played).toEqual(["https://cdn.example/audio/abc.mp3"]);
  });

  it("uses a contextual accessible name when given", () => {
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "https://cdn.example/audio/");
    render(<AudioButton audio={audio} label="Escuchar" ariaLabel="Escuchar ejemplo: 你好吗" />);
    expect(screen.getByRole("button", { name: "Escuchar ejemplo: 你好吗" })).toBeInTheDocument();
  });

  it("defaults the accessible name to 'Escuchar <label>'", () => {
    vi.stubEnv("NEXT_PUBLIC_AUDIO_BASE_URL", "https://cdn.example/audio/");
    render(<AudioButton audio={audio} label="Voz 1" />);
    expect(screen.getByRole("button", { name: "Escuchar Voz 1" })).toBeInTheDocument();
  });
});
