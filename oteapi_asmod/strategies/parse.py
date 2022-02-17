"""Demo strategy class for text/json."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ase import Atoms
from ase.io import read
from ase.io.jsonio import MyEncoder
from oteapi.datacache import DataCache
from oteapi.models import SessionUpdate
from oteapi.plugins import create_strategy
from pydantic import BaseModel, Extra, Field

if TYPE_CHECKING:
    from typing import Any, Dict

    from oteapi.models import ResourceConfig


class SessionUpdateAtomisticParse(SessionUpdate):
    """Class for returning values from oteapi-asmod Parse using ASE."""

    cached_atoms: str = Field(
        ...,
        description="The key to the ase.Atoms object in the data cache.",
    )


class AtomisticParseDataModel(BaseModel):
    """Pydantic model for the Atomistic parse strategy"""

    fileformat: Optional[str] = Field(
        None,
        description=("Optional, to specify format as input to the ase reader."),
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
            The session.

        """
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
            ase.Atoms object in cache.

        """
        model = AtomisticParseDataModel(  # Checkout how to do this only once
            **self.parse_config.configuration, extra=Extra.ignore
        )

        downloader = create_strategy("download", self.parse_config)
        output = downloader.get()
        cache = DataCache(self.parse_config.configuration)
        content = cache.get(output["key"])

        if isinstance(content, Atoms):
            return SessionUpdateAtomisticParse(cached_atoms=output["key"])

        name = self.parse_config.downloadUrl.path.rsplit("/")[-1].split(".")
        with cache.getfile(
            key=output["key"], suffix=name[-1], prefix=name[0]
        ) as filename:
            atoms = read(filename, format=model.fileformat)
        key = cache.add(atoms, json_encoder=MyEncoder)

        return SessionUpdateAtomisticParse(cached_atoms=key)
