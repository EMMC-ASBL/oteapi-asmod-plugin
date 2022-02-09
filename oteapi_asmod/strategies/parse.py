"""Strategy class for parsing atomstic structures."""
# pylint: disable=unused-argument, no-self-use
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import dlite
from ase import Atoms
from ase.io import read
from oteapi.datacache.datacache import DataCache
from oteapi.plugins.factories import StrategyFactory, create_download_strategy
from pydantic import BaseModel, Extra, Field

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.models.resourceconfig import ResourceConfig


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
    datamodel: Optional[dlite.Instance] = Field(
        "Molecule.json",
        description("Optionally specify dlite datamodel to use"),
    )


@dataclass
@StrategyFactory.register(
    ("mediaType", "chemical/x-xyz"),
    ("mediaType", "chemical/x-vasp"),  # Not an official internet mediatype
    # Should we list all possible mediatypes that ase can read?
)
class AtomisticStructureParseStrategy:
    """Parse strategy for file continaing atomistic structures"""

    resource_config: "ResourceConfig"

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
        model = AtomisticParseDataModel(
            **self.resource_config.configuration, extra=Extra.ignore
        )
        if model.returntype == "dlitedatamodel" and model.returnformat == "datamodel":
            if "collection_id" in session:
                coll = dlite.get_collection(session["collection_id"])
            else:
                coll = dlite.Collection()
                dlite.get_collection(coll.uuid)
            return dict(collection_id=coll.uuid)
        return {}

    def parse(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
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
            **self.resource_config.configuration, extra=Extra.ignore
        )

        dlite.storage_path.append(str("/app/entities"))

        downloader = create_download_strategy(self.resource_config)
        output = downloader.get()
        cache = DataCache(self.resource_config.configuration)
        content = cache.get(output["key"])
        if isinstance(content, Atoms):
            return content

        name = self.resource_config.downloadUrl.path.rsplit("/")[-1].split(".")
        with cache.getfile(
            key=output["key"], suffix=name[-1], prefix=name[0]
        ) as filename:
            atoms = read(filename, format=model.fileformat)

        if model.returnformat == "datamodel":
            if model.datamodeltype == "dlitedatamodel":
                dlite.storage_path.append(str("/app/entities"))

                MoleculeModel = dlite.Instance(  # Need to fix storagepath
                    "json:///app/entities/Molecule.json"
                )  # DLite Metadata
                if "collection_id" in session:  # don't do this twice

                    coll = dlite.get_collection(session["collection_id"])

                else:
                    coll = dlite.Collection()
                    dlite.get_collection(coll.uuid)

                basename = ".".join(name)

                inst = MoleculeModel(
                    dims=[len(atoms), 3], id=basename
                )  # DLite instance
                inst.symbols = atoms.get_chemical_symbols()
                inst.masses = atoms.get_masses()
                inst.positions = atoms.positions

                inst.groundstate_energy = 0.0

                coll.add(label=basename, inst=inst)
                # Return uuid of the collection that now includes the new parsed
                # molecule.

                return dict(collection_id=coll.uuid, molecule_name=basename)
        return atoms
