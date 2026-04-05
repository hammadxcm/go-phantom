// AppState.swift — ObservableObject, wires all components

import Combine
import Foundation
import ServiceManagement
import SwiftUI
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "AppState")

final class AppState: ObservableObject {
    @Published var config: PhantomConfig
    @Published var isRunning = false
    @Published var selectedPreset: Preset?
    @Published var launchAtLogin = false
    @Published var totalActions: Int = 0
    @Published var uptime: TimeInterval = 0
    @Published var actionsBySimulator: [String: Int] = [:]

    let configManager: ConfigManager
    let scheduler: Scheduler
    let hotkeyManager = HotkeyManager()
    var statusBar: StatusBarController?

    private var configSaveTimer: Timer?
    private var uptimeTimer: Timer?
    private var startTime: Date?

    init() {
        configManager = ConfigManager()
        config = configManager.config

        let simulators: [String: Simulator] = [
            "mouse": MouseSimulator(),
            "keyboard": KeyboardSimulator(),
            "scroll": ScrollSimulator(),
            "app_switcher": AppSwitcherSimulator(),
            "browser_tabs": BrowserTabsSimulator(),
        ]

        scheduler = Scheduler(configManager: configManager, simulators: simulators)

        // Wire action count callback
        scheduler.onAction = { [weak self] name in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.totalActions += 1
                self.actionsBySimulator[name, default: 0] += 1
            }
        }

        // Start uptime timer
        startTime = Date()
        uptimeTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self = self, let start = self.startTime else { return }
            self.uptime = Date().timeIntervalSince(start)
        }

        // Apply stealth settings
        if config.stealth.renameProcess {
            _ = ProcessMasking.mask(name: config.stealth.processName)
        }

        // Setup hotkeys
        hotkeyManager.onToggle = { [weak self] in
            DispatchQueue.main.async { self?.toggle() }
        }
        hotkeyManager.onQuit = { [weak self] in
            DispatchQueue.main.async {
                self?.shutdown()
                NSApp.terminate(nil)
            }
        }
        hotkeyManager.onHideTray = { [weak self] in
            DispatchQueue.main.async { self?.statusBar?.toggleVisibility() }
        }
        hotkeyManager.start()

        // Watch for config changes and auto-save
        setupConfigObserver()

        // Launch at login state
        if #available(macOS 13.0, *) {
            launchAtLogin = (SMAppService.mainApp.status == .enabled)
        }

        logger.info("AppState initialized")
    }

    func toggle() {
        let running = scheduler.toggle()
        isRunning = running
        statusBar?.updateIcon(running: running)
        statusBar?.buildMenu()
    }

    func shutdown() {
        uptimeTimer?.invalidate()
        uptimeTimer = nil
        scheduler.shutdown()
        hotkeyManager.stop()
        configManager.updateAndSave { [config] cfg in
            cfg = config
        }
    }

    func applyPreset(_ preset: Preset) {
        preset.apply(to: &config)
        syncConfigToManager()
    }

    // MARK: - Private

    private func setupConfigObserver() {
        // Debounced save: when config changes, save after 1s of inactivity
        $config
            .debounce(for: .seconds(1), scheduler: RunLoop.main)
            .sink { [weak self] newConfig in
                self?.syncConfigToManager()
            }
            .store(in: &cancellables)
    }

    private var cancellables = Set<AnyCancellable>()

    private func syncConfigToManager() {
        configManager.updateAndSave { [config] cfg in
            cfg = config
        }
    }

    func setLaunchAtLogin(_ enabled: Bool) {
        if #available(macOS 13.0, *) {
            do {
                if enabled {
                    try SMAppService.mainApp.register()
                } else {
                    try SMAppService.mainApp.unregister()
                }
                launchAtLogin = enabled
            } catch {
                logger.error("Failed to set launch at login: \(error.localizedDescription)")
            }
        }
    }
}
