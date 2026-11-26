import type { Metadata, Viewport } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Mandarín IA", template: "%s · Mandarín IA" },
  description:
    "Diccionario de mandarín para hispanohablantes: pinyin con colores por tono, audio, ejemplos y frases de viaje.",
  applicationName: "Mandarín IA",
  appleWebApp: { capable: true, title: "Mandarín IA", statusBarStyle: "default" },
  icons: { icon: "/icons/icon-192.png", apple: "/icons/icon-192.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f7f5" },
    { media: "(prefers-color-scheme: dark)", color: "#111111" },
  ],
};

const NAV = [
  { href: "/", label: "Diccionario" },
  { href: "/frases", label: "Frases" },
  { href: "/creditos", label: "Créditos" },
] as const;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <header className="sticky top-0 z-10 border-b border-line bg-background/90 backdrop-blur">
          <nav className="mx-auto flex max-w-2xl items-center gap-1 px-2" aria-label="Principal">
            <Link href="/" className="mr-auto flex min-h-12 items-center px-2 text-lg font-bold">
              <span lang="zh-CN" className="font-hanzi mr-1 text-accent">
                中
              </span>
              Mandarín IA
            </Link>
            {NAV.slice(1).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex min-h-12 items-center rounded-lg px-3 text-sm font-medium text-subtle"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 pt-4 pb-12">{children}</main>
      </body>
    </html>
  );
}
