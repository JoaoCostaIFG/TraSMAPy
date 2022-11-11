import traci

from trasmapy._IdentifiedObject import IdentifiedObject

class Detector(IdentifiedObject):
    def __init__(self, detectorId: str) -> None:
        super().__init__(detectorId)
        self._listeners = []

    @property
    def timeSinceLastDetection(self) -> float:
        """Returns how many seconds elapsed since the last detection."""
        return traci.inductionloop.getTimeSinceDetection(self.id)

    @property
    def laneId(self) -> str:
        """Returns the ID of the lane where the detector is placed."""
        return traci.inductionloop.getLaneID(self.id)

    @property
    def position(self) -> float:
        """Returns the position of the detection on its containing lane."""
        return traci.inductionloop.getPosition(self.id)

    def listen(self, listener):
        """Hooks into the detector. The given function will be called with the IDs of the detected vehicles there's a detection."""
        self._listeners.append(listener)

    def _doSimulationStep(self):
        if traci.inductionloop.getLastStepVehicleNumber(self.id) == 0:
            # nothing happened
            return

        detectedVehicles = traci.inductionloop.getLastStepVehicleIDs(self.id)
        for listener in self._listeners:
            listener(detectedVehicles)
