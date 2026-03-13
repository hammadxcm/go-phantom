// Presets.swift — 5 preset profiles matching Python presets.py

import Foundation

enum Preset: String, CaseIterable, Identifiable {
    case `default` = "default"
    case aggressive = "aggressive"
    case stealth = "stealth"
    case minimal = "minimal"
    case presentation = "presentation"

    var id: String { rawValue }

    var displayName: String {
        rawValue.capitalized
    }

    func apply(to config: inout PhantomConfig) {
        let allSimulators = ["mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"]

        switch self {
        case .default:
            let enabled: Set<String> = ["mouse", "keyboard", "scroll"]
            setEnabled(&config, only: enabled, all: allSimulators)
            config.timing.intervalMean = 8.0
            config.timing.intervalStddev = 4.0

        case .aggressive:
            let enabled: Set<String> = ["mouse", "keyboard", "scroll", "app_switcher", "browser_tabs"]
            setEnabled(&config, only: enabled, all: allSimulators)
            config.timing.intervalMean = 3.0
            config.timing.intervalStddev = 1.5

        case .stealth:
            let enabled: Set<String> = ["mouse", "scroll"]
            setEnabled(&config, only: enabled, all: allSimulators)
            config.timing.intervalMean = 15.0
            config.timing.intervalStddev = 5.0
            config.mouse.minDistance = 20
            config.mouse.maxDistance = 150

        case .minimal:
            let enabled: Set<String> = ["mouse"]
            setEnabled(&config, only: enabled, all: allSimulators)
            config.timing.intervalMean = 20.0
            config.timing.intervalStddev = 6.0

        case .presentation:
            let enabled: Set<String> = ["mouse", "scroll"]
            setEnabled(&config, only: enabled, all: allSimulators)
            config.timing.intervalMean = 5.0
            config.timing.intervalStddev = 2.0
        }
    }

    private func setEnabled(_ config: inout PhantomConfig, only enabled: Set<String>, all: [String]) {
        config.mouse.enabled = enabled.contains("mouse")
        config.keyboard.enabled = enabled.contains("keyboard")
        config.scroll.enabled = enabled.contains("scroll")
        config.appSwitcher.enabled = enabled.contains("app_switcher")
        config.browserTabs.enabled = enabled.contains("browser_tabs")
    }
}
