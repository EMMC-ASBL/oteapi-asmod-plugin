"""Test function strategies."""


def test_ASEDlite(  # pylint: disable=invalid-name, too-many-locals
    repo_dir: "Path",
) -> None:  # pylint: disable=too-many-locals
    """Test converting ase.Atoms, placed in datacache by AtomisticStructureParseStrategy,
    to dlite metadata strategy."""
    import numpy as np
    from dlite import Collection
    from oteapi.models import SessionUpdate
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_asmod.strategies.function import (
        ASEDliteConfig,
        ASEDliteFunctionStrategy,
    )
    from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy

    # Use parsestrategy to place molecule in datacache
    config = ResourceConfig(
        downloadUrl=(
            "https://raw.githubusercontent.com/nutjunkie/IQmol/"
            "master/share/fragments/Molecules/Alkanes/Ethane.xyz"
        ),
        mediaType="chemical/x-xyz",
    )
    parser = AtomisticStructureParseStrategy(config)
    parsed_atoms_key = parser.get().cached_atoms

    # Create dlite collection
    coll = Collection()

    # Create session an place collection in it
    session = {}
    session.update(SessionUpdate(collection_id=coll.uuid))
    print("*" * 60)
    print(type(session))
    # Define configuration for the function
    modelpath = repo_dir / "tests" / "testfiles" / "Molecule.json"
    config2 = ASEDliteConfig(
        label="molecule", datacacheKey=parsed_atoms_key, datamodel=modelpath
    )

    # Instantiate function
    dlitefyer = ASEDliteFunctionStrategy(config2)
    session.update(dlitefyer.initialize())  # just in case initialize does something
    # Run function
    dlitefyer.get(session)

    # Find the molecule which is now placed in the collection
    dlite_instance = coll.get("molecule")

    assert np.array_equal(
        dlite_instance.symbols, ["H", "C", "H", "H", "C", "H", "H", "H"]
    )