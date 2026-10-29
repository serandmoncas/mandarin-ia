// Generates the placeholder PWA icons (中 on a solid background).
// macOS only (AppKit/CoreText). Run from the repo root:
//   swift scripts/generate-icons.swift
import AppKit

let background = NSColor(srgbRed: 0xc6 / 255.0, green: 0x28 / 255.0, blue: 0x28 / 255.0, alpha: 1)
let glyph = "中"

func render(size: Int, to path: String) throws {
  guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8,
    samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
    bytesPerRow: 0, bitsPerPixel: 0)
  else { throw NSError(domain: "icons", code: 1) }
  NSGraphicsContext.saveGraphicsState()
  NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
  let s = CGFloat(size)
  background.setFill()
  NSRect(x: 0, y: 0, width: s, height: s).fill()
  // Glyph kept inside the maskable safe zone (~80% of the canvas).
  let font = NSFont(name: "PingFangSC-Semibold", size: s * 0.58)
    ?? NSFont(name: "STHeitiSC-Medium", size: s * 0.58)
    ?? NSFont.systemFont(ofSize: s * 0.58, weight: .semibold)
  let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: NSColor.white]
  let text = NSAttributedString(string: glyph, attributes: attrs)
  let bounds = text.boundingRect(with: NSSize(width: s, height: s), options: [.usesLineFragmentOrigin])
  text.draw(at: NSPoint(x: (s - bounds.width) / 2, y: (s - bounds.height) / 2))
  NSGraphicsContext.restoreGraphicsState()
  guard let png = rep.representation(using: .png, properties: [:])
  else { throw NSError(domain: "icons", code: 2) }
  try png.write(to: URL(fileURLWithPath: path))
  print("wrote \(path)")
}

for size in [192, 512] {
  try render(size: size, to: "public/icons/icon-\(size).png")
}
