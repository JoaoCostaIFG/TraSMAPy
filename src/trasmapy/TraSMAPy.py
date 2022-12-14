import os
import sys
from typing import Union, Callable

# we need to import python modules from the $SUMO_HOME/tools directory
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    exit("Please declare environment variable 'SUMO_HOME'.")

from sumolib import checkBinary
import traci
import pyflwor

from trasmapy._Query import Query
from trasmapy.network._Network import Network
from trasmapy.users._Users import Users
from trasmapy.publicservices._PublicServices import PublicServices
from trasmapy.control._Control import Control


class TraSMAPy:
    def __init__(self, sumoCfg: str, useGui: bool = True) -> None:
        self._step: int = 0
        self._collectedStatistics: dict[int, dict] = {}
        self._queries: dict[str, Query] = {}

        self._startSimulation(sumoCfg, useGui)
        self._network: Network = Network()
        self._users: Users = Users()
        self._publicServices: PublicServices = PublicServices(self._users)
        self._control: Control = Control()

        self._queryMap = self._genQueryMap()

    @property
    def network(self) -> Network:
        return self._network

    @property
    def users(self) -> Users:
        return self._users

    @property
    def publicServices(self) -> PublicServices:
        return self._publicServices

    @property
    def control(self) -> Control:
        return self._control

    @property
    def step(self) -> int:
        return self._step

    @property
    def stepLength(self) -> float:
        """The length of one simulation step (s)."""
        return traci.simulation.getDeltaT()  # type: ignore

    @property
    def time(self) -> float:
        """The current simulation time (s)."""
        return traci.simulation.getTime()  # type: ignore

    @property
    def minExpectedNumber(self) -> int:
        """The minimum number of vehicles expected to be in the simulation."""
        return traci.simulation.getMinExpectedNumber()  # type: ignore

    @property
    def collectedStatistics(self) -> dict[int, dict]:
        """The accumulated statistics of the queries."""
        return self._collectedStatistics.copy()

    def query(self, query: Union[str, Callable]) -> dict:
        """Run a query once and get its current result."""
        if isinstance(query, str):
            return pyflwor.execute(query, self._genQueryMap())
        else:
            return query(self._genQueryMap())

    def registerQuery(
        self, queryName: str, query: Union[str, Callable], tickInterval: int = 1
    ) -> None:
        """Register query to be run every tick (by default).
        The tickInterval param can be customized to change the frequency of the statistics collection.
        Results are accumulated and can be obtained through the collectedStatistics property."""
        if queryName in self._queries:
            raise KeyError(
                f"There's a query with that name already registered: [queryName={queryName}]."
            )
        self._queries[queryName] = Query(
            pyflwor.compile(query) if isinstance(query, str) else query,
            tickInterval,
        )

    def doSimulationStep(self) -> None:
        self._step += 1
        traci.simulationStep()

        time = self.time
        self._network._doSimulationStep(step=self._step, time=time)
        self._users._doSimulationStep(step=self._step, time=time)
        self._publicServices._doSimulationStep(step=self._step, time=time)
        self._control._doSimulationStep(step=self._step, time=time)

        self._collectedStatistics[self._step] = {}
        for (queryName, query) in self._queries.items():
            if not query.tick():
                continue
            self._collectedStatistics[self._step][queryName] = query(
                self._genQueryMap()
            )

    def closeSimulation(self) -> None:
        traci.close()
        sys.stdout.flush()

    def _genQueryMap(self) -> dict:
        ret = {
            "network": self._network,
            "users": self._users,
            "publicServices": self._publicServices,
            "control": self._control,
        }
        ret.update(__builtins__)
        return ret

    def _startSimulation(self, sumoCfg: str, useGui: bool) -> None:
        # script has been called from the command line. It will start sumo as a
        # server, then connect and run
        if useGui:
            sumoBinary = checkBinary("sumo-gui")
        else:
            sumoBinary = checkBinary("sumo")

        # sumo is started as a subprocess and then the python script connects and runs
        traci.start([sumoBinary, "-c", sumoCfg])
