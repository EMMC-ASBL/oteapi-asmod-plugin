"""Function strategy class for mapping ase.Atoms to dlite metadata."""
# pylint: disable=no-self-use,unused-argument
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

from dlite import Instance, get_collection
from oteapi.datacache import DataCache
from oteapi.models import SessionUpdate
from pydantic import BaseModel, Field, HttpUrl

from oteapi_asmod.utils import OteapiAsmodError

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.models import FunctionConfig


class ASEDliteConfig(BaseModel):  # why is this not a FunctionConfig?
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
    # functionType: str = Field(
    #        "asedlite/atoms", # shouldn't this be recognized automatically?
    #        description=("Type of function"),
    #        )


@dataclass
class ASEDliteFunctionStrategy:
    """Mapping Strategy."""

    function_config: "FunctionConfig"

    def initialize(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> "Dict[str, Any]":
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTE-API
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        return {}

    def get(self, session: "Dict" = None) -> SessionUpdate:
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

        # In ResourceConfig there is a DataCache called configuration
        # that is used to get out key/value pairs. Is this something that
        # should be in all Configs?
        # model = ASEDliteConfig(
        #    **self.function_config.configuration, extra=Extra.ignore,
        # )

        # There should be a local folder with entitites at least until onto-ns is up
        # dlite.storage_path.append(str(pathlib.Path(__file__).parent.resolve()))

        # Create dlite instance of metadata
        moleculemodel = Instance.create_from_url(
            "json://" + str(model.datamodel),
        )  # DLite Metadata

        # Get ase.Atoms obejct from cache
        cache = DataCache()
        atoms = cache.get(model.datacacheKey)

        # Creat dlite instance from metadata and populate
        inst = moleculemodel(dims=[len(atoms), 3], id=model.label)  # DLite instance
        inst.symbols = atoms.get_chemical_symbols()
        inst.masses = atoms.get_masses()
        inst.positions = atoms.positions
        inst.groundstate_energy = 0.0

        # Get collection from session and place  molecule in it
        if isinstance(session, dict):
            coll = get_collection(session["collection_id"])
        else:
            raise OteapiAsmodError("Missing session")

        coll.add(label=model.label, inst=inst)

        return SessionUpdate()
