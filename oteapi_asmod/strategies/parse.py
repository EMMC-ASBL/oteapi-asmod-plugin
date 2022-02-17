"""Demo strategy class for text/json."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from ase import Atoms
from ase.io import read
from dlite import Collection, Instance, get_collection, storage_path
from oteapi.datacache import DataCache
from oteapi.models import AttrDict, SessionUpdate
from oteapi.plugins import create_strategy
from pydantic import BaseModel, Extra, Field, HttpUrl

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.models import ResourceConfig


class SessionUpdateAtomisticParse(SessionUpdate):
    """Class for returning values from XLSXParse."""

    symbols: List[str] = Field(
        ...,
        description="The chemical symbol of each atom in the atomstic structure. "
        "This determines the dimension number of atoms.",
    )
    # atoms.positions is a np.ndarray , condire making custom pydantic validator
    positions: List[List[float]] = Field(
        ...,
        description="Positions of the atoms in cartesian coordinates. Unit: Å. ",
        unit="Å",
    )


class AtomisticParseDataModel(BaseModel):
    """Pydantic model for the Atomistic parse strategy"""

    fileformat: Optional[str] = Field(
        None,
        description=("Optional to specify format as input to the ase reader."),
    )
    returnformat: Optional[str] = Field(
        "dict",
        description=("Optional to specify return type. Default 'dict'"),
        # Find out how to print alternatives,
    )
    datamodeltype: Optional[str] = Field(
        "dlitedatamodel",
        description=("Optional to specify type of data model. Default is" "'dlite'"),
    )
    datamodel: Optional[HttpUrl] = Field(
        "http://onto-ns.com/meta/0.1/Molecule",
        descriptioni=("Optionally specify dlite datamodel to use, for now the uid"),
    )


@dataclass
class AtomisticStructureParseStrategy:
    """Parse Strategyi for files describing atomstic models/structures."""

    parse_config: "ResourceConfig"

    def initialize(self, session: "Optional[Dict[str, Any]]" = None) -> SessionUpdate:
        """Initialize strategy.

        This method will be called through the `/initialize` endpoint of the OTE-API
        Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        model = AtomisticParseDataModel(
            **self.parse_config.configuration, extra=Extra.ignore
        )
        if model.returntype == "dlitedatamodel" and model.returnformat == "datamodel":
            if isinstance(session, AttrDict) and "collection_id" in session:
                coll = get_collection(session["collection_id"])
            else:
                coll = Collection()
                get_collection(coll.uuid)
            return dict(collection_id=coll.uuid)
        return SessionUpdate

    def get(
        self, session: "Optional[Dict[str, Any]]" = None
    ) -> SessionUpdateAtomisticParse:
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        model = AtomisticParseDataModel(  # Checkout how to do this only once
            **self.parse_config.configuration, extra=Extra.ignore
        )

        storage_path.append(str("/app/entities"))

        downloader = create_strategy("download", self.parse_config)
        output = downloader.get()
        cache = DataCache(self.parse_config.configuration)
        content = cache.get(output["key"])
        if isinstance(content, Atoms):
            return content

        name = self.parse_config.downloadUrl.path.rsplit("/")[-1].split(".")
        with cache.getfile(
            key=output["key"], suffix=name[-1], prefix=name[0]
        ) as filename:
            atoms = read(filename, format=model.fileformat)

        if model.returnformat == "datamodel":
            if model.datamodeltype == "dlitedatamodel":
                storage_path.append(str("/app/entities"))

                moleculemodel = Instance(  # Need to fix storagepath
                    "json:///app/entities/Molecule.json"
                )  # DLite Metadata

                if isinstance(session, AttrDict) and "collection_id" in session:
                    coll = get_collection(session["collection_id"])

                else:
                    coll = Collection()
                    get_collection(coll.uuid)

                basename = ".".join(name)

                inst = moleculemodel(
                    dims=[len(atoms), 3], id=basename
                )  # DLite instance
                inst.symbols = atoms.get_chemical_symbols()
                inst.masses = atoms.get_masses()
                inst.positions = atoms.positions

                inst.groundstate_energy = 0.0

                coll.add(label=basename, inst=inst)
                # Return uuid of the collection that now includes the new parsed
                # molecule.

                #  return SessionUpdateAtomisticParse(
                #    data={"collection_id": coll.uuid, "molecule_name": basename}
                # )
        return SessionUpdateAtomisticParse(
            symbols=atoms.get_chemical_symbols(), positions=atoms.positions.tolist()
        )
