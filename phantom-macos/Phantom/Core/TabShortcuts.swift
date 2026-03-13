// TabShortcuts.swift — Browser shortcut registry for macOS

import CoreGraphics
import Foundation

struct TabShortcut {
    struct KeyCombo {
        let keyCode: CGKeyCode
        let flags: CGEventFlags
    }

    let forward: [KeyCombo]
    let backward: [KeyCombo]
}

enum TabShortcuts {
    // Virtual key codes
    private static let kVK_RightBracket: CGKeyCode = 30
    private static let kVK_LeftBracket: CGKeyCode = 33
    private static let kVK_Tab: CGKeyCode = 48
    private static let kVK_RightArrow: CGKeyCode = 124
    private static let kVK_LeftArrow: CGKeyCode = 123

    // macOS: Cmd+Shift+] / Cmd+Shift+[
    static let macCmdBracket = TabShortcut(
        forward: [TabShortcut.KeyCombo(keyCode: kVK_RightBracket, flags: CGEventFlags([.maskCommand, .maskShift]))],
        backward: [TabShortcut.KeyCombo(keyCode: kVK_LeftBracket, flags: CGEventFlags([.maskCommand, .maskShift]))]
    )

    // Ctrl+Tab / Ctrl+Shift+Tab
    static let ctrlTab = TabShortcut(
        forward: [TabShortcut.KeyCombo(keyCode: kVK_Tab, flags: .maskControl)],
        backward: [TabShortcut.KeyCombo(keyCode: kVK_Tab, flags: CGEventFlags([.maskControl, .maskShift]))]
    )

    // Kitty: Ctrl+Shift+Right / Ctrl+Shift+Left
    static let kitty = TabShortcut(
        forward: [TabShortcut.KeyCombo(keyCode: kVK_RightArrow, flags: CGEventFlags([.maskControl, .maskShift]))],
        backward: [TabShortcut.KeyCombo(keyCode: kVK_LeftArrow, flags: CGEventFlags([.maskControl, .maskShift]))]
    )

    // Registry: pattern → shortcut (macOS only)
    private static let registry: [(pattern: String, shortcut: TabShortcut)] = [
        ("chrome|firefox|safari|edge|brave|arc|opera|chromium", macCmdBracket),
        ("code|cursor", ctrlTab),
        ("iterm", macCmdBracket),
        ("kitty", kitty),
        ("wezterm", ctrlTab),
        ("terminal", macCmdBracket),
    ]

    static let defaultShortcut = ctrlTab

    /// Look up the best tab-switching shortcut for an application.
    static func lookup(appName: String) -> TabShortcut {
        let normalized = appName.lowercased()
            .replacingOccurrences(of: " ", with: "-")
            .replacingOccurrences(of: ".", with: "-")
            .replacingOccurrences(of: "_", with: "-")

        for (pattern, shortcut) in registry {
            if normalized.range(of: pattern, options: .regularExpression) != nil {
                return shortcut
            }
        }
        return defaultShortcut
    }
}
