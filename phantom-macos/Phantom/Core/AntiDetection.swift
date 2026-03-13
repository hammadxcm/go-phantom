// AntiDetection.swift — Pattern blocking (consecutive + alternating)

import Foundation

final class AntiDetection {
    static let historySize = 100
    static let repetitionThreshold = 4

    private var history: [String] = []

    func record(_ action: String) {
        history.append(action)
        if history.count > Self.historySize {
            history.removeFirst(history.count - Self.historySize)
        }
    }

    func wouldBeRepetitive(_ action: String) -> Bool {
        if history.count < Self.repetitionThreshold {
            return false
        }

        // Check consecutive pattern: last 4 actions all the same
        let recent = Array(history.suffix(Self.repetitionThreshold))
        if recent.allSatisfy({ $0 == action }) {
            return true
        }

        // Detect alternating A-B-A-B pattern
        if history.count >= 6 {
            let last6 = Array(history.suffix(6))
            if last6[0] == last6[2] && last6[2] == last6[4] && last6[4] == action
                && last6[1] == last6[3] && last6[3] == last6[5] {
                return true
            }
        }

        return false
    }

    var historySnapshot: [String] {
        return history
    }
}
