"""Demo filter strategy."""
# pylint: disable=no-self-use,unused-argument
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from oteapi.plugins.factories import StrategyFactory
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from oteapi.models.filterconfig import FilterConfig


class AtomsDliteModel(BaseModel):
    """Demo filter data model."""

    molecule_model: Optional[str] = Field(None, description="DLite data model.")


@dataclass
@StrategyFactory.register(("filterType", "filter/ASEAtomsToDLite"))
class ASEAtomsDliteFilter:
    """Filter Strategy."""

    filter_config: "FilterConfig"

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
        return {"result": "collectionid"}

    def get(self, session: "Optional[Dict[str, Any]]" = None) -> "Dict[str, Any]":
        """Execute the strategy.

        This method will be called through the strategy-specific endpoint of the
        OTE-API Services.

        Parameters:
            session: A session-specific dictionary context.

        Returns:
            Dictionary of key/value-pairs to be stored in the sessions-specific
            dictionary context.

        """
        model = AtomsDliteDataModel(**self.filter_config.configuration)

        if model.molecule_model == None:
            model.molecule_model = dlite.Instance(  # Need to fix storagepath
                "json:///app/entities/Molecule.json"
            )  # DLite Metadata

        basename = os.path.splitext(f"{self.filename}")[0]

        inst = MoleculeModel(dims=[len(atoms), 3], id=basename)  # DLite instance
        inst.symbols = atoms.get_chemical_symbols()
        inst.masses = atoms.get_masses()
        inst.positions = atoms.positions

        inst.groundstate_energy = 0.0

        coll.add(label=basename, inst=inst)
        # Return uuid of the collection that now includes the new parsed
        # molecule.

        return dict(collection_id=coll.uuid, molecule_name=basename)

        return {"key": model.demo_data}
