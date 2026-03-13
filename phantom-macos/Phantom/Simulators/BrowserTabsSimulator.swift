// BrowserTabsSimulator.swift — Context-aware tab switching

import CoreGraphics
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "BrowserTabsSimulator")

final class BrowserTabsSimulator: Simulator {
    let name = "browser_tabs"

    // Fallback keys
    private let kVK_Tab: CGKeyCode = 48

    func execute(config: PhantomConfig) {
        let btConfig = config.browserTabs
        let tabs = Int.random(in: 1...4)
        var appName = "unknown"

        var shortcut: TabShortcut?
        if btConfig.contextAware {
            if let window = ActiveWindowDetector.getActiveWindow() {
                appName = window.appName
                shortcut = TabShortcuts.lookup(appName: appName)
            }
        }

        let backward = Double.random(in: 0..<1) < btConfig.backwardChance

        if let shortcut = shortcut {
            let keys = backward ? shortcut.backward : shortcut.forward
            let direction = backward ? "backward" : "forward"

            for _ in 0..<tabs {
                for combo in keys {
                    if let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: combo.keyCode, keyDown: true) {
                        keyDown.flags = combo.flags
                        keyDown.post(tap: .cghidEventTap)
                    }
                    usleep(UInt32(Double.random(in: 0.02...0.06) * 1_000_000))
                }
                // Release in reverse order
                for combo in keys.reversed() {
                    if let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: combo.keyCode, keyDown: false) {
                        keyUp.flags = combo.flags
                        keyUp.post(tap: .cghidEventTap)
                    }
                }
                usleep(UInt32(Double.random(in: 0.20...0.50) * 1_000_000))
            }
            logger.debug("Browser tab switch: \(tabs) tabs (\(appName), \(direction))")
        } else {
            // Fallback: blind Ctrl+Tab
            for _ in 0..<tabs {
                if let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Tab, keyDown: true) {
                    keyDown.flags = .maskControl
                    keyDown.post(tap: .cghidEventTap)
                }
                usleep(UInt32(Double.random(in: 0.03...0.08) * 1_000_000))
                if let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Tab, keyDown: false) {
                    keyUp.flags = .maskControl
                    keyUp.post(tap: .cghidEventTap)
                }
                usleep(UInt32(Double.random(in: 0.20...0.50) * 1_000_000))
            }
            logger.debug("Browser tab switch: \(tabs) tabs (fallback)")
        }
    }
}
