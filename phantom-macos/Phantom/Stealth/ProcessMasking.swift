// ProcessMasking.swift — ProcessInfo name override

import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "ProcessMasking")

enum ProcessMasking {
    /// Attempt to mask the process name.
    /// On macOS, uses `ProcessInfo.processInfo.processName`.
    static func mask(name: String) -> Bool {
        ProcessInfo.processInfo.processName = name
        logger.info("Process name masked to: \(name)")
        return true
    }
}
