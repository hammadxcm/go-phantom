// ScrollSimulator.swift — CGEvent scrollWheelEvent2

import CoreGraphics
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "ScrollSimulator")

final class ScrollSimulator: Simulator {
    let name = "scroll"

    func execute(config: PhantomConfig) {
        let scrollConfig = config.scroll
        let clicks = Int.random(in: scrollConfig.minClicks...scrollConfig.maxClicks)
        let direction = Bool.random() ? 1 : -1  // up or down

        for _ in 0..<clicks {
            let amount = Int32(direction * Int.random(in: 1...3))

            if Double.random(in: 0..<1) < 0.1 {
                // Horizontal scroll (10% chance)
                if let event = CGEvent(scrollWheelEvent2Source: nil, units: .pixel,
                                       wheelCount: 2, wheel1: 0, wheel2: amount, wheel3: 0) {
                    event.post(tap: .cghidEventTap)
                }
            } else {
                // Vertical scroll
                if let event = CGEvent(scrollWheelEvent2Source: nil, units: .pixel,
                                       wheelCount: 1, wheel1: amount, wheel2: 0, wheel3: 0) {
                    event.post(tap: .cghidEventTap)
                }
            }
            usleep(UInt32(Double.random(in: 0.05...0.15) * 1_000_000))
        }

        logger.debug("Scroll: \(clicks) clicks, direction=\(direction)")
    }
}
