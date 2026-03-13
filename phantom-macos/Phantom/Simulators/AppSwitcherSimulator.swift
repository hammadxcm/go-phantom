// AppSwitcherSimulator.swift — CGEvent Cmd+Tab

import CoreGraphics
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "AppSwitcherSimulator")

final class AppSwitcherSimulator: Simulator {
    let name = "app_switcher"

    // Virtual key codes
    private let kVK_Command: CGKeyCode = 55
    private let kVK_Tab: CGKeyCode = 48

    func execute(config: PhantomConfig) {
        let tabs = Int.random(in: 1...3)

        // Press Cmd
        if let cmdDown = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Command, keyDown: true) {
            cmdDown.post(tap: .cghidEventTap)
        }

        usleep(UInt32(Double.random(in: 0.05...0.10) * 1_000_000))

        for _ in 0..<tabs {
            // Press Tab
            if let tabDown = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Tab, keyDown: true) {
                tabDown.flags = .maskCommand
                tabDown.post(tap: .cghidEventTap)
            }
            usleep(UInt32(Double.random(in: 0.03...0.08) * 1_000_000))
            // Release Tab
            if let tabUp = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Tab, keyDown: false) {
                tabUp.flags = .maskCommand
                tabUp.post(tap: .cghidEventTap)
            }
            usleep(UInt32(Double.random(in: 0.15...0.40) * 1_000_000))
        }

        // Release Cmd
        if let cmdUp = CGEvent(keyboardEventSource: nil, virtualKey: kVK_Command, keyDown: false) {
            cmdUp.post(tap: .cghidEventTap)
        }

        logger.debug("App switch: \(tabs) tabs")
    }
}
