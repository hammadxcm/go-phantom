// ConfigManager.swift — JSON load/save from ~/.phantom/config.json

import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "ConfigManager")

final class ConfigManager {
    static let configFilename = "config.json"

    private let lock = NSLock()
    private var _config: PhantomConfig
    private let path: URL

    init(configPath: String? = nil) {
        if let configPath {
            path = URL(fileURLWithPath: configPath)
        } else {
            path = Self.resolvePath()
        }
        _config = Self.load(from: path)
    }

    var config: PhantomConfig {
        lock.lock()
        defer { lock.unlock() }
        return _config
    }

    func save() {
        lock.lock()
        defer { lock.unlock() }

        let dir = path.deletingLastPathComponent()
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        do {
            let data = try encoder.encode(_config)
            try data.write(to: path, options: .atomic)
            logger.info("Config saved to \(self.path.path)")
        } catch {
            logger.error("Failed to save config: \(error.localizedDescription)")
        }
    }

    func update(_ mutate: (inout PhantomConfig) -> Void) {
        lock.lock()
        mutate(&_config)
        lock.unlock()
    }

    func updateAndSave(_ mutate: (inout PhantomConfig) -> Void) {
        update(mutate)
        save()
    }

    // MARK: - Private

    private static func resolvePath() -> URL {
        let homeDir = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(".phantom")
        let homePath = homeDir.appendingPathComponent(configFilename)
        if FileManager.default.fileExists(atPath: homePath.path) {
            return homePath
        }
        // Default to ~/.phantom/config.json even if it doesn't exist yet
        return homePath
    }

    private static func load(from url: URL) -> PhantomConfig {
        guard FileManager.default.fileExists(atPath: url.path) else {
            logger.info("No config file found at \(url.path), using defaults")
            return PhantomConfig()
        }

        do {
            let data = try Data(contentsOf: url)
            let decoder = JSONDecoder()
            var config = try decoder.decode(PhantomConfig.self, from: data)
            config.validate()
            return config
        } catch {
            logger.error("Failed to read config \(url.path): \(error.localizedDescription). Using defaults.")
            return PhantomConfig()
        }
    }
}
