// HotkeyManager.swift — NSEvent.addGlobalMonitorForEvents

import AppKit
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "HotkeyManager")

final class HotkeyManager {
    private var globalMonitor: Any?
    private var localMonitor: Any?

    var onToggle: (() -> Void)?
    var onQuit: (() -> Void)?
    var onHideTray: (() -> Void)?

    func start() {
        // Global monitor for when app is not focused
        globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handleKeyEvent(event)
        }

        // Local monitor for when app is focused
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handleKeyEvent(event)
            return event
        }

        logger.info("Hotkey manager started")
    }

    func stop() {
        if let globalMonitor {
            NSEvent.removeMonitor(globalMonitor)
            self.globalMonitor = nil
        }
        if let localMonitor {
            NSEvent.removeMonitor(localMonitor)
            self.localMonitor = nil
        }
    }

    private func handleKeyEvent(_ event: NSEvent) {
        let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        let requiredFlags: NSEvent.ModifierFlags = [.control, .option]

        guard flags.contains(requiredFlags) else { return }

        switch event.charactersIgnoringModifiers?.lowercased() {
        case "s":
            logger.debug("Toggle hotkey triggered")
            onToggle?()
        case "q":
            logger.debug("Quit hotkey triggered")
            onQuit?()
        case "h":
            logger.debug("Hide tray hotkey triggered")
            onHideTray?()
        default:
            break
        }
    }
}
