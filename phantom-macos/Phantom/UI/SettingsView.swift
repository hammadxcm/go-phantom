// SettingsView.swift — SwiftUI tabbed settings

import ServiceManagement
import SwiftUI

struct SettingsView: View {
    @ObservedObject var appState: AppState

    var body: some View {
        TabView {
            GeneralTab(appState: appState)
                .tabItem {
                    Label("General", systemImage: "gear")
                }

            SimulatorsTab(appState: appState)
                .tabItem {
                    Label("Simulators", systemImage: "cpu")
                }

            StatusTab(appState: appState)
                .tabItem {
                    Label("Status", systemImage: "chart.bar")
                }

            HotkeysTab()
                .tabItem {
                    Label("Hotkeys", systemImage: "keyboard")
                }

            StealthTab(appState: appState)
                .tabItem {
                    Label("Stealth", systemImage: "eye.slash")
                }

            AboutTab()
                .tabItem {
                    Label("About", systemImage: "info.circle")
                }
        }
        .frame(width: 480, height: 440)
    }
}

// MARK: - General Tab

struct GeneralTab: View {
    @ObservedObject var appState: AppState

    var body: some View {
        Form {
            Section("Preset") {
                Picker("Profile", selection: $appState.selectedPreset) {
                    Text("Custom").tag(Optional<Preset>.none)
                    ForEach(Preset.allCases) { preset in
                        Text(preset.displayName).tag(Optional(preset))
                    }
                }
                .onChange(of: appState.selectedPreset) { newValue in
                    if let preset = newValue {
                        appState.applyPreset(preset)
                    }
                }
            }

            Section("Timing") {
                HStack {
                    Text("Interval Mean")
                    Spacer()
                    Text("\(appState.config.timing.intervalMean, specifier: "%.1f")s")
                        .foregroundStyle(.secondary)
                }
                Slider(value: $appState.config.timing.intervalMean, in: 1...60, step: 0.5)

                HStack {
                    Text("Interval Stddev")
                    Spacer()
                    Text("\(appState.config.timing.intervalStddev, specifier: "%.1f")s")
                        .foregroundStyle(.secondary)
                }
                Slider(value: $appState.config.timing.intervalStddev, in: 0...20, step: 0.5)

                HStack {
                    Text("Idle Chance")
                    Spacer()
                    Text("\(Int(appState.config.timing.idleChance * 100))%")
                        .foregroundStyle(.secondary)
                }
                Slider(value: $appState.config.timing.idleChance, in: 0...1, step: 0.05)
            }

            Section("System") {
                Toggle("Launch at Login", isOn: $appState.launchAtLogin)
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

// MARK: - Simulators Tab

struct SimulatorsTab: View {
    @ObservedObject var appState: AppState

    var body: some View {
        Form {
            SimulatorRow(
                name: "Mouse",
                enabled: $appState.config.mouse.enabled,
                weight: $appState.config.mouse.weight
            )
            SimulatorRow(
                name: "Keyboard",
                enabled: $appState.config.keyboard.enabled,
                weight: $appState.config.keyboard.weight
            )
            SimulatorRow(
                name: "Scroll",
                enabled: $appState.config.scroll.enabled,
                weight: $appState.config.scroll.weight
            )
            SimulatorRow(
                name: "App Switcher",
                enabled: $appState.config.appSwitcher.enabled,
                weight: $appState.config.appSwitcher.weight
            )
            SimulatorRow(
                name: "Browser Tabs",
                enabled: $appState.config.browserTabs.enabled,
                weight: $appState.config.browserTabs.weight
            )
        }
        .formStyle(.grouped)
        .padding()
    }
}

struct SimulatorRow: View {
    let name: String
    @Binding var enabled: Bool
    @Binding var weight: Double

    var body: some View {
        Section(name) {
            Toggle("Enabled", isOn: $enabled)
            if enabled {
                HStack {
                    Text("Weight")
                    Spacer()
                    Text("\(weight, specifier: "%.0f")")
                        .foregroundStyle(.secondary)
                }
                Slider(value: $weight, in: 1...100, step: 1)
            }
        }
    }
}

// MARK: - Status Tab

struct StatusTab: View {
    @ObservedObject var appState: AppState

    var body: some View {
        Form {
            Section("Current State") {
                HStack {
                    Circle()
                        .fill(appState.isRunning ? Color.green : Color.orange)
                        .frame(width: 10, height: 10)
                    Text(appState.isRunning ? "Running" : "Paused")
                        .fontWeight(.medium)
                }

                HStack {
                    Text("Uptime")
                    Spacer()
                    Text(formatUptime(appState.uptime))
                        .foregroundStyle(.secondary)
                        .font(.system(.body, design: .monospaced))
                }
            }

            Section("Actions") {
                HStack {
                    Text("Total Actions")
                    Spacer()
                    Text("\(appState.totalActions)")
                        .foregroundStyle(.secondary)
                        .font(.system(.body, design: .monospaced))
                }

                ForEach(appState.actionsBySimulator.sorted(by: { $0.key < $1.key }), id: \.key) { name, count in
                    HStack {
                        Text(displayName(for: name))
                        Spacer()
                        Text("\(count)")
                            .foregroundStyle(.secondary)
                            .font(.system(.body, design: .monospaced))
                    }
                }
            }
        }
        .formStyle(.grouped)
        .padding()
    }

    private func formatUptime(_ interval: TimeInterval) -> String {
        let total = Int(interval)
        let hours = total / 3600
        let minutes = (total % 3600) / 60
        let seconds = total % 60
        return String(format: "%02d:%02d:%02d", hours, minutes, seconds)
    }

    private func displayName(for key: String) -> String {
        switch key {
        case "mouse": return "Mouse"
        case "keyboard": return "Keyboard"
        case "scroll": return "Scroll"
        case "app_switcher": return "App Switcher"
        case "browser_tabs": return "Browser Tabs"
        default: return key
        }
    }
}

// MARK: - Hotkeys Tab

struct HotkeysTab: View {
    var body: some View {
        Form {
            Section("Global Hotkeys") {
                HStack {
                    Text("Toggle (Start/Pause)")
                    Spacer()
                    Text("Ctrl + Option + S")
                        .font(.system(.body, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                HStack {
                    Text("Quit")
                    Spacer()
                    Text("Ctrl + Option + Q")
                        .font(.system(.body, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                HStack {
                    Text("Hide Menu Bar Icon")
                    Spacer()
                    Text("Ctrl + Option + H")
                        .font(.system(.body, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

// MARK: - Stealth Tab

struct StealthTab: View {
    @ObservedObject var appState: AppState

    var body: some View {
        Form {
            Section("Process") {
                Toggle("Rename Process", isOn: $appState.config.stealth.renameProcess)
                if appState.config.stealth.renameProcess {
                    TextField("Process Name", text: $appState.config.stealth.processName)
                }
            }

            Section("Tray") {
                Toggle("Hide Menu Bar Icon on Launch", isOn: $appState.config.stealth.hideTray)
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}

// MARK: - About Tab

struct AboutTab: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(nsImage: NSApp.applicationIconImage)
                .resizable()
                .frame(width: 64, height: 64)

            Text("Phantom")
                .font(.title)
                .fontWeight(.bold)

            Text("Native macOS Activity Simulator")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            if let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String {
                Text("Version \(version)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Divider()

            HStack(spacing: 4) {
                Text("Accessibility:")
                if AccessibilityPrompt.isTrusted {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Text("Granted")
                        .foregroundStyle(.green)
                } else {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.red)
                    Text("Not Granted")
                        .foregroundStyle(.red)
                    Button("Grant Access") {
                        AccessibilityPrompt.openAccessibilitySettings()
                    }
                    .buttonStyle(.link)
                }
            }
            .font(.caption)

            Spacer()
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
