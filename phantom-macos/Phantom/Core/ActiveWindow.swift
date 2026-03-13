// ActiveWindow.swift — NSWorkspace + AXUIElement active window detection

import AppKit
import Foundation

struct WindowInfo {
    let appName: String
    let windowTitle: String
}

enum ActiveWindowDetector {
    private static var cache: (timestamp: TimeInterval, result: WindowInfo?) = (0, nil)
    private static let cacheTTL: TimeInterval = 0.5
    private static let lock = NSLock()

    /// Get the active window with 0.5s caching.
    static func getActiveWindow() -> WindowInfo? {
        lock.lock()
        defer { lock.unlock() }

        let now = ProcessInfo.processInfo.systemUptime
        if now - cache.timestamp < cacheTTL {
            return cache.result
        }

        let result = detect()
        cache = (now, result)
        return result
    }

    private static func detect() -> WindowInfo? {
        guard let frontApp = NSWorkspace.shared.frontmostApplication else {
            return nil
        }

        let appName = frontApp.localizedName ?? frontApp.bundleIdentifier ?? "unknown"

        // Try to get window title via Accessibility API
        let pid = frontApp.processIdentifier
        let appRef = AXUIElementCreateApplication(pid)
        var windowValue: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appRef, kAXFocusedWindowAttribute as CFString, &windowValue)

        var windowTitle = ""
        if result == .success, let window = windowValue {
            var titleValue: CFTypeRef?
            if AXUIElementCopyAttributeValue(window as! AXUIElement, kAXTitleAttribute as CFString, &titleValue) == .success,
               let title = titleValue as? String {
                windowTitle = title
            }
        }

        return WindowInfo(appName: appName, windowTitle: windowTitle)
    }
}
