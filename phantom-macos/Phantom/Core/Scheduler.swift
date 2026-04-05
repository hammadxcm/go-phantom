// Scheduler.swift — DispatchQueue-based weighted loop

import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "Scheduler")

final class Scheduler {
    private let configManager: ConfigManager
    private let simulators: [String: Simulator]
    private let antiDetection = AntiDetection()
    private let queue = DispatchQueue(label: "com.phantom.scheduler", qos: .utility)
    private let lock = NSLock()

    private var _isRunning = false
    private var _pausedSims: Set<String> = []
    private var workItem: DispatchWorkItem?

    // Stats
    private(set) var totalActions: Int = 0
    private(set) var actionsBySimulator: [String: Int] = [:]
    private(set) var lastActionName: String?

    /// Called on each action with the simulator name.
    var onAction: ((String) -> Void)?

    var isRunning: Bool {
        lock.lock()
        defer { lock.unlock() }
        return _isRunning
    }

    var pausedSims: Set<String> {
        lock.lock()
        defer { lock.unlock() }
        return _pausedSims
    }

    init(configManager: ConfigManager, simulators: [String: Simulator]) {
        self.configManager = configManager
        self.simulators = simulators
    }

    func start() {
        lock.lock()
        guard !_isRunning else { lock.unlock(); return }
        _isRunning = true
        lock.unlock()
        logger.info("Scheduler started")
        scheduleNext()
    }

    func stop() {
        lock.lock()
        _isRunning = false
        workItem?.cancel()
        workItem = nil
        lock.unlock()
        logger.info("Scheduler stopped")
    }

    func toggle() -> Bool {
        if isRunning {
            stop()
            return false
        } else {
            start()
            return true
        }
    }

    func toggleSimPause(_ name: String) -> Bool {
        lock.lock()
        defer { lock.unlock() }
        if _pausedSims.contains(name) {
            _pausedSims.remove(name)
            return false
        } else {
            _pausedSims.insert(name)
            return true
        }
    }

    func shutdown() {
        stop()
    }

    // MARK: - Private

    private func scheduleNext() {
        lock.lock()
        guard _isRunning else { lock.unlock(); return }
        lock.unlock()

        let item = DispatchWorkItem { [weak self] in
            self?.tick()
        }
        lock.lock()
        workItem = item
        lock.unlock()

        // Schedule immediately for first tick
        queue.async(execute: item)
    }

    private func tick() {
        lock.lock()
        guard _isRunning else { lock.unlock(); return }
        lock.unlock()

        let config = configManager.config

        // Get enabled simulator weights (excluding paused sims)
        lock.lock()
        let paused = _pausedSims
        lock.unlock()

        let weights = config.simulatorWeights().filter { !paused.contains($0.0) }
        if weights.isEmpty {
            logger.warning("No simulators enabled, waiting...")
            scheduleAfter(seconds: 2.0)
            return
        }

        // Check for idle period (10% chance)
        if Randomizer.shouldIdle() {
            let idleTime = Randomizer.idleDuration()
            logger.debug("Idle period: \(idleTime, format: .fixed(precision: 1))s")
            scheduleAfter(seconds: idleTime)
            return
        }

        // Weighted random choice among enabled simulators
        var chosen = Randomizer.weightedChoice(options: weights)

        // Anti-detection check
        if antiDetection.wouldBeRepetitive(chosen) {
            let remaining = weights.filter { $0.0 != chosen }
            if !remaining.isEmpty {
                chosen = Randomizer.weightedChoice(options: remaining)
            }
        }

        guard let sim = simulators[chosen] else {
            scheduleAfter(seconds: 1.0)
            return
        }

        // Execute chosen simulator
        sim.execute(config: config)
        antiDetection.record(chosen)

        lock.lock()
        totalActions += 1
        actionsBySimulator[chosen, default: 0] += 1
        lastActionName = chosen
        lock.unlock()

        onAction?(chosen)

        // Schedule next tick after Gaussian interval
        let interval = Randomizer.actionInterval(
            mean: config.timing.intervalMean,
            stddev: config.timing.intervalStddev,
            minimum: config.timing.intervalMin
        )
        scheduleAfter(seconds: interval)
    }

    private func scheduleAfter(seconds: Double) {
        lock.lock()
        guard _isRunning else { lock.unlock(); return }
        lock.unlock()

        let item = DispatchWorkItem { [weak self] in
            self?.tick()
        }
        lock.lock()
        workItem = item
        lock.unlock()

        queue.asyncAfter(deadline: .now() + seconds, execute: item)
    }
}
