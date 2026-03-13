// StatusBarController.swift — NSStatusItem + NSMenu

import AppKit
import SwiftUI

final class StatusBarController {
    private var statusItem: NSStatusItem?
    private weak var appState: AppState?
    private var isHidden = false

    init(appState: AppState) {
        self.appState = appState
        setupStatusItem()
    }

    func show() {
        if statusItem == nil {
            setupStatusItem()
        }
        isHidden = false
    }

    func hide() {
        if let item = statusItem {
            NSStatusBar.system.removeStatusItem(item)
            statusItem = nil
        }
        isHidden = true
    }

    func toggleVisibility() {
        if isHidden {
            show()
        } else {
            hide()
        }
    }

    func updateIcon(running: Bool) {
        let iconName = running ? "play.circle.fill" : "pause.circle"
        statusItem?.button?.image = NSImage(systemSymbolName: iconName, accessibilityDescription: "Phantom")
    }

    // MARK: - Private

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.image = NSImage(systemSymbolName: "pause.circle", accessibilityDescription: "Phantom")
        statusItem?.button?.imagePosition = .imageLeading

        buildMenu()
    }

    func buildMenu() {
        let menu = NSMenu()
        let running = appState?.isRunning ?? false

        let toggleItem = NSMenuItem(
            title: running ? "Pause" : "Start",
            action: #selector(toggleAction),
            keyEquivalent: ""
        )
        toggleItem.target = self
        menu.addItem(toggleItem)

        menu.addItem(NSMenuItem.separator())

        let settingsItem = NSMenuItem(
            title: "Settings...",
            action: #selector(openSettings),
            keyEquivalent: ","
        )
        settingsItem.target = self
        menu.addItem(settingsItem)

        let hideTrayItem = NSMenuItem(
            title: "Hide Menu Bar Icon",
            action: #selector(hideTrayAction),
            keyEquivalent: ""
        )
        hideTrayItem.target = self
        menu.addItem(hideTrayItem)

        menu.addItem(NSMenuItem.separator())

        let quitItem = NSMenuItem(
            title: "Quit Phantom",
            action: #selector(quitAction),
            keyEquivalent: "q"
        )
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem?.menu = menu
    }

    @objc private func toggleAction() {
        appState?.toggle()
        buildMenu()
    }

    @objc private func openSettings() {
        // Open settings window
        if #available(macOS 14.0, *) {
            NSApp.activate()
        } else {
            NSApp.activate(ignoringOtherApps: true)
        }
        // Send notification for settings window
        NotificationCenter.default.post(name: .openSettings, object: nil)
    }

    @objc private func hideTrayAction() {
        hide()
    }

    @objc private func quitAction() {
        appState?.shutdown()
        NSApp.terminate(nil)
    }
}

extension Notification.Name {
    static let openSettings = Notification.Name("com.phantom.openSettings")
}
