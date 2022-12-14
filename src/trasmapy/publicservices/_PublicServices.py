from typing import Union
from typing_extensions import override

from traci.constants import INVALID_DOUBLE_VALUE

from trasmapy._SimUpdatable import SimUpdatable
from trasmapy.publicservices._Fleet import Fleet
from trasmapy.users.ScheduledStop import ScheduledStop
from trasmapy.users._Route import Route
from trasmapy.users._Users import Users
from trasmapy.users._VehicleType import VehicleType


class PublicServices(SimUpdatable):
    def __init__(self, users: Users) -> None:
        self._users: Users = users
        self._fleets: dict[str, Fleet] = {}

    @property
    def fleets(self) -> dict[str, Fleet]:
        return self._fleets.copy()

    def createFleet(
        self,
        fleetId: str,
        fleetRoute: Union[Route, None],
        vehicleType: VehicleType,
        fleetStops: list[ScheduledStop],
        period: float,
        start: float = 0,
        end: float = INVALID_DOUBLE_VALUE,
    ) -> Fleet:
        """Create a fleet.
        If the fleetRoute is None, a Route is calculated from the given fleetStops.
        If the fleetRoute is None, the list of FleetStops can't be empty.
        """
        if fleetRoute is None:
            if len(fleetStops) == 0:
                raise ValueError(
                    f"If the given fleet route is None, there needs to be at least one stop: [fleetId={fleetId}]."
                )
            routeId = f"fleet{fleetId}Route"
            route = self._users.createRouteFromEdges(
                routeId,
                [
                    fleetStops[0].stop.lane.parentEdge,
                    fleetStops[-1].stop.lane.parentEdge,
                ],
            )
        else:
            route = fleetRoute

        newFleet = Fleet(fleetId, route, vehicleType, fleetStops, period=period, start=start, end=end)
        self._fleets[fleetId] = newFleet
        return newFleet

    def getFleet(self, fleetId: str) -> Fleet:
        return self._fleets[fleetId]

    @override
    def _doSimulationStep(self, *args, step: int, time: float) -> None:
        for fleet in self._fleets.values():
            fleet._doSimulationStep(self._users, step=step, time=time)
