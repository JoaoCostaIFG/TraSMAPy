from typing import Union
from typing_extensions import override

import traci
from traci.constants import VAR_STOPSTATE

from trasmapy._SimUpdatable import SimUpdatable
from trasmapy.users._Vehicle import Vehicle
from trasmapy.users._VehicleType import VehicleType
from trasmapy.users._Route import Route
from trasmapy.network._Edge import Edge


class Users(SimUpdatable):
    def __init__(self):
        # the vehicles being tracked
        self._vehicles: dict[str, Vehicle] = {}

    def getAllVehicleIds(self) -> list[str]:
        return traci.vehicle.getIDList()  # type: ignore

    def getAllPendingVehicleIds(self) -> list[str]:
        return traci.simulation.getPendingVehicles()  # type: ignore

    def getAllVehicleTypeIds(self) -> list[str]:
        return traci.vehicletype.getIDList()  # type: ignore

    @property
    def vehicles(self) -> list[Vehicle]:
        """Retrieves an object for each vehicle currently in the simulation.
        The API doesn't keep track of the liveness of the references returned
        from this method. As such, the values returned from this method should
        only be kept for one tick of the simulation (e.g., for querries)."""
        return list(map(lambda id: Vehicle(id), self.getAllVehicleIds()))

    @property
    def pendingVehicles(self) -> list[Vehicle]:
        """Retrieves an object for each pending vehicle currently in the simulation.
        The API doesn't keep track of the liveness of the references returned
        from this method. As such, the values returned from this method should
        only be kept for one tick of the simulation (e.g., for querries)."""
        return list(map(lambda id: Vehicle(id), self.getAllPendingVehicleIds()))

    @property
    def vehicleTypes(self) -> list[VehicleType]:
        return list(map(lambda id: VehicleType(id), self.getAllVehicleTypeIds()))

    def getVehicleType(self, vehicleTypeId: str) -> VehicleType:
        """Retrieves an object for each vehicle type currently in the simulation."""
        if vehicleTypeId not in self.getAllVehicleTypeIds():
            raise KeyError(
                f"The vehicle type with the given ID does not exist: [vehicleTypeId={vehicleTypeId}]."
            )
        return VehicleType(vehicleTypeId)

    def getVehicle(self, vehicleId: str) -> Vehicle:
        """Retrieve a registered vehicle reference to a vehicle in the network.
        See createVehicle."""
        try:
            return self._vehicles[vehicleId]
        except KeyError:
            if (
                vehicleId in self.getAllVehicleIds()
                or vehicleId in self.getAllPendingVehicleIds()
            ):
                return self._registerVehicle(vehicleId)
            raise KeyError(
                f"There are no vehicles with the given ID in the simulation: [vehicleId={vehicleId}]"
            )

    def createVehicle(
        self,
        vehicleId: str,
        route: Union[Route, None] = None,
        vehicleType: VehicleType = VehicleType("DEFAULT_VEHTYPE"),
        personNumber: int = 0,
        personCapacity: int = 0,
        departTime: Union[str, float] = "now",
    ) -> Vehicle:
        """Creates a registered vehicle and adds it to the network.
        Registered vehicles are vehicle objects whose liveness is checked (safe).
        If the route is None, the vehicle will be added to a random network edge.
        If the route consists of two disconnected edges, the vehicle will be treated like
        a <trip> and use the fastest route between the two edges.
        If depart time is the string 'now', the depart time is the same as the vehicle spawn.
        Negative values for depart time have special meanings:
            -1: 'triggered'
            -2: 'containerTriggered'
        """
        try:
            traci.vehicle.add(
                vehicleId,
                route.id if isinstance(route, Route) else "",
                typeID=vehicleType.id,
                personNumber=personNumber,
                personCapacity=personCapacity,
                depart=str(departTime),
            )
            return self._registerVehicle(vehicleId)
        except traci.TraCIException as e:
            raise KeyError(
                f"A error occured while adding the vehicle with the given ID: [vehicleId={vehicleId}], [error={e}]."
            )

    def getRoute(self, routeId: str) -> Route:
        if routeId not in traci.route.getIDList():
            raise KeyError(
                f"The given route ID doesn't belong to any registered route: [routeId={routeId}]"
            )
        return Route(routeId)

    def createRouteFromIds(self, routeId: str, edgesIds: list[str]) -> Route:
        try:
            traci.route.add(routeId, edgesIds)
        except traci.TraCIException as e:
            raise KeyError(
                f"A error occured while adding the route with the given ID: [vehicleId={routeId}], [error={e}]."
            )
        return Route(routeId)

    def createRouteFromEdges(self, routeId: str, edges: list[Edge]) -> Route:
        return self.createRouteFromIds(routeId, list(map(lambda x: x.id, edges)))

    def _registerVehicle(self, vehicleId) -> Vehicle:
        # subscribe stoped state byte (check liveness)
        traci.vehicle.subscribe(vehicleId, [VAR_STOPSTATE])

        v = Vehicle(vehicleId)
        self._vehicles[vehicleId] = v
        return v

    @override
    def _doSimulationStep(self, *args, step: int, time: float) -> None:
        res: dict[str, dict] = traci.vehicle.getAllSubscriptionResults()  # type: ignore
        # the vehicles that exited the simulation on this step
        vehiclesThatDied: set[str] = self._vehicles.keys() - res.keys()

        for vehicleId in vehiclesThatDied:
            # garanteed to be in the map (doesn't need catch)
            v = self._vehicles.pop(vehicleId)
            v._dead = True
