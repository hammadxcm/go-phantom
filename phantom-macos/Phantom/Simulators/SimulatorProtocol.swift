// SimulatorProtocol.swift — Protocol with execute() method

import Foundation

protocol Simulator {
    var name: String { get }
    func execute(config: PhantomConfig)
}
