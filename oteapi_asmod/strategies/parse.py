"""Strategy class for parsing atomstic structures."""
# pylint: disable=unused-argument, no-self-use
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

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
        model = AtomisticParseDataModel(
            **self.resource_config.configuration, extra=Extra.ignore
        )

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
        return atoms
