// PhantomConfig.swift — Codable structs mirroring Python schema.py
// Uses snake_case JSON keys for compatibility with ~/.phantom/config.json

import Foundation

struct TimingConfig: Codable, Equatable {
    var intervalMean: Double = 8.0
    var intervalStddev: Double = 4.0
    var intervalMin: Double = 0.5
    var idleChance: Double = 0.10
    var idleMin: Double = 15.0
    var idleMax: Double = 120.0

    mutating func validate() {
        idleChance = max(0.0, min(1.0, idleChance))
        intervalMin = max(0.01, intervalMin)
        intervalMean = max(intervalMin, intervalMean)
        intervalStddev = max(0.0, intervalStddev)
        idleMin = max(0.0, idleMin)
        idleMax = max(idleMin, idleMax)
    }

    enum CodingKeys: String, CodingKey {
        case intervalMean = "interval_mean"
        case intervalStddev = "interval_stddev"
        case intervalMin = "interval_min"
        case idleChance = "idle_chance"
        case idleMin = "idle_min"
        case idleMax = "idle_max"
    }
}

struct MouseConfig: Codable, Equatable {
    var enabled: Bool = true
    var weight: Double = 40.0
    var minDistance: Int = 50
    var maxDistance: Int = 500
    var bezierSteps: Int = 100

    mutating func validate() {
        weight = max(0.0, weight)
        minDistance = max(0, minDistance)
        maxDistance = max(minDistance, maxDistance)
        bezierSteps = max(1, bezierSteps)
    }

    enum CodingKeys: String, CodingKey {
        case enabled, weight
        case minDistance = "min_distance"
        case maxDistance = "max_distance"
        case bezierSteps = "bezier_steps"
    }
}

struct KeyboardConfig: Codable, Equatable {
    var enabled: Bool = true
    var weight: Double = 30.0
    var maxPresses: Int = 3

    mutating func validate() {
        weight = max(0.0, weight)
        maxPresses = max(1, maxPresses)
    }

    enum CodingKeys: String, CodingKey {
        case enabled, weight
        case maxPresses = "max_presses"
    }
}

struct ScrollConfig: Codable, Equatable {
    var enabled: Bool = true
    var weight: Double = 15.0
    var minClicks: Int = 1
    var maxClicks: Int = 5

    mutating func validate() {
        weight = max(0.0, weight)
        minClicks = max(1, minClicks)
        maxClicks = max(minClicks, maxClicks)
    }

    enum CodingKeys: String, CodingKey {
        case enabled, weight
        case minClicks = "min_clicks"
        case maxClicks = "max_clicks"
    }
}

struct AppSwitcherConfig: Codable, Equatable {
    var enabled: Bool = false
    var weight: Double = 10.0

    mutating func validate() {
        weight = max(0.0, weight)
    }
}

struct BrowserTabsConfig: Codable, Equatable {
    var enabled: Bool = false
    var weight: Double = 5.0
    var contextAware: Bool = true
    var backwardChance: Double = 0.3

    mutating func validate() {
        weight = max(0.0, weight)
        backwardChance = max(0.0, min(1.0, backwardChance))
    }

    enum CodingKeys: String, CodingKey {
        case enabled, weight
        case contextAware = "context_aware"
        case backwardChance = "backward_chance"
    }
}

struct HotkeyConfig: Codable, Equatable {
    var toggle: String = "<ctrl>+<alt>+s"
    var quit: String = "<ctrl>+<alt>+q"
    var hideTray: String = "<ctrl>+<alt>+h"

    enum CodingKeys: String, CodingKey {
        case toggle, quit
        case hideTray = "hide_tray"
    }
}

struct StealthConfig: Codable, Equatable {
    var renameProcess: Bool = true
    var processName: String = "system_service"
    var hideTray: Bool = false

    enum CodingKeys: String, CodingKey {
        case renameProcess = "rename_process"
        case processName = "process_name"
        case hideTray = "hide_tray"
    }
}

struct PhantomConfig: Codable, Equatable {
    var timing: TimingConfig = TimingConfig()
    var mouse: MouseConfig = MouseConfig()
    var keyboard: KeyboardConfig = KeyboardConfig()
    var scroll: ScrollConfig = ScrollConfig()
    var appSwitcher: AppSwitcherConfig = AppSwitcherConfig()
    var browserTabs: BrowserTabsConfig = BrowserTabsConfig()
    var hotkeys: HotkeyConfig = HotkeyConfig()
    var stealth: StealthConfig = StealthConfig()

    mutating func validate() {
        timing.validate()
        mouse.validate()
        keyboard.validate()
        scroll.validate()
        appSwitcher.validate()
        browserTabs.validate()
    }

    /// Returns mapping of enabled simulator names to their weights.
    func simulatorWeights() -> [(String, Double)] {
        var sims: [(String, Double)] = []
        if mouse.enabled { sims.append(("mouse", mouse.weight)) }
        if keyboard.enabled { sims.append(("keyboard", keyboard.weight)) }
        if scroll.enabled { sims.append(("scroll", scroll.weight)) }
        if appSwitcher.enabled { sims.append(("app_switcher", appSwitcher.weight)) }
        if browserTabs.enabled { sims.append(("browser_tabs", browserTabs.weight)) }
        return sims
    }

    enum CodingKeys: String, CodingKey {
        case timing, mouse, keyboard, scroll
        case appSwitcher = "app_switcher"
        case browserTabs = "browser_tabs"
        case hotkeys, stealth
    }
}
