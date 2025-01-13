"""Function strategy class for mapping ase.Atoms to dlite metadata."""

# pylint: disable=no-self-use,unused-argument
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from dlite import Instance, get_collection
from oteapi.datacache import DataCache
from oteapi.models import AttrDict, DataCacheConfig, FunctionConfig, SessionUpdate
from pydantic import Field, HttpUrl

from oteapi_asmod.utils import OteapiAsmodError

if TYPE_CHECKING:
    from typing import Any, Dict


class ASEDliteConfig(AttrDict):
    """ASE to Dlite entity configuration"""

    # The datamodel should ideally be an HttpUrl
    # Currently can also be set as a path
    # The datamodel can currently only be provided as path to json
    # Also, only one model is possible so this should maybe not be
    # an option.
    datamodel: Optional[Union[HttpUrl, pathlib.Path]] = Field(
        "http://onto-ns.com/meta/0.1/Molecule",
        description=("The dlite datamodel for the structure."),
    )
    label: str = Field(
        ...,
        description=("Label of the molecule in the dlite collection."),
    )
    datacacheKey: str = Field(
        ...,
        description=("Key to ase.Atoms obejct in datacache"),
    )
    datacache_config: Optional[DataCacheConfig] = Field(
        None,
        description="Configuration options for the local data cache.",
    )


class ASEDliteFunctionConfig(FunctionConfig):
    """ASEDlite function specific configuration."""

    configuration: ASEDliteConfig = Field(
        ..., description="ASE-Dlite converter function specific configuration."
    )


class SessionUpdateASEDliteFunction(SessionUpdate):
    """Class for returning value from ASEDlite function."""

    collection_id: str = Field(..., description="Dlite collection id.")


@dataclass
class ASEDliteFunctionStrategy:
    """Mapping Strategy."""

    function_config: ASEDliteFunctionConfig

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTE-API
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            SessionUpdate()

        """
        return SessionUpdate()

    def get(self, session: "Dict" = None) -> SessionUpdateASEDliteFunction:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:

            session: A session-specific dictionary context.

        Returns:
            Populates session collection with molecule.
            Returns SessionUpdate()

        """
        model = self.function_config

        # There should be a local folder with entitites at least until onto-ns is up
        # dlite.storage_path.append(str(pathlib.Path(__file__).parent.resolve()))

        # Create dlite instance of metadata
        moleculemodel = Instance.create_from_url(
            "json://" + str(model.datamodel),
        )  # DLite Metadata

        # Get ase.Atoms obejct from cache
        cache = DataCache(model.datacache_config)
        atoms = cache.get(model.datacacheKey)

        # Creat dlite instance from metadata and populate
        inst = moleculemodel(dims=[len(atoms), 3], id=model.label)  # DLite instance
        inst.symbols = atoms.get_chemical_symbols()
        inst.masses = atoms.get_masses()
        inst.positions = atoms.positions
        inst.groundstate_energy = 0.0

        # Get collection from session and place  molecule in it
        if session is not None:
            coll = get_collection(session["collection_id"])
        else:
            raise OteapiAsmodError("Missing session")

        coll.add(label=model.label, inst=inst)

        return SessionUpdateASEDliteFunction(collection_id=session["collection_id"])
