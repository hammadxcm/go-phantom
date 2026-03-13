// PhantomApp.swift — @main, MenuBarExtra, Settings scene

import SwiftUI

@main
struct PhantomApp: App {
    @StateObject private var appState = AppState()
    @State private var showAccessibilityAlert = false
    @State private var showSettings = false

    var body: some Scene {
        // Settings window
        Settings {
            SettingsView(appState: appState)
        }

        // Menu bar — using MenuBarExtra for macOS 13+
        MenuBarExtra("Phantom", systemImage: appState.isRunning ? "play.circle.fill" : "pause.circle") {
            Button(appState.isRunning ? "Pause" : "Start") {
                appState.toggle()
            }
            .keyboardShortcut("s", modifiers: [.control, .option])

            Divider()

            if #available(macOS 14.0, *) {
                SettingsLink {
                    Text("Settings...")
                }
            } else {
                Button("Settings...") {
                    NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
                }
            }

            Button("Hide Menu Bar Icon") {
                appState.statusBar?.hide()
            }

            Divider()

            Button("Quit Phantom") {
                appState.shutdown()
                NSApplication.shared.terminate(nil)
            }
            .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }

    init() {
        // Check accessibility on launch
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            if !AccessibilityPrompt.isTrusted {
                _ = AccessibilityPrompt.checkWithPrompt()
            }
        }
    }
}
