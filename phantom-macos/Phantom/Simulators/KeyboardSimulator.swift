// KeyboardSimulator.swift — CGEvent keyDown/keyUp modifier keys

import CoreGraphics
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "KeyboardSimulator")

final class KeyboardSimulator: Simulator {
    let name = "keyboard"

    // Safe modifier key virtual key codes (no visible output)
    private let safeKeys: [CGKeyCode] = [
        56,  // Shift
        59,  // Control
        58,  // Option
    ]
    private let capsLockKey: CGKeyCode = 57

    func execute(config: PhantomConfig) {
        let kbConfig = config.keyboard
        let numPresses = Int.random(in: 1...kbConfig.maxPresses)

        for _ in 0..<numPresses {
            if Double.random(in: 0..<1) < 0.15 {
                // CapsLock double-tap (on then off)
                pressKey(capsLockKey, holdSeconds: Double.random(in: 0.03...0.08))
                usleep(UInt32(Double.random(in: 0.05...0.12) * 1_000_000))
                pressKey(capsLockKey, holdSeconds: Double.random(in: 0.03...0.08))
            } else {
                let key = safeKeys.randomElement()!
                pressKey(key, holdSeconds: Double.random(in: 0.03...0.10))
            }

            usleep(UInt32(Randomizer.keystrokeDelay() * 1_000_000))
        }

        logger.debug("Keyboard: \(numPresses) modifier presses")
    }

    private func pressKey(_ keyCode: CGKeyCode, holdSeconds: Double) {
        if let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true) {
            keyDown.post(tap: .cghidEventTap)
        }
        usleep(UInt32(holdSeconds * 1_000_000))
        if let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false) {
            keyUp.post(tap: .cghidEventTap)
        }
    }
}
