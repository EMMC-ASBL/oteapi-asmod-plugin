"""Test parse strategies."""


def test_xyz_read(repo_dir: "Path") -> None:
    """Test `chemical/x-xyz` parse strategy."""
    from ase.io import read
    from oteapi.models.resourceconfig import ResourceConfig
    from oteapi.datacache import DataCache
    from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy

    filepath = repo_dir / "tests" / "testfiles" / "Ethane.xyz"

    config = ResourceConfig(
        downloadUrl=(
            "https://raw.githubusercontent.com/nutjunkie/IQmol/"
            "master/share/fragments/Molecules/Alkanes/Ethane.xyz"
        ),
        mediaType="chemical/x-xyz",
    )
    cache=DataCache()
    parser = AtomisticStructureParseStrategy(config)
    parsed_atoms_key = parser.get().cached_atoms
    parsed_atoms = cache.get(parsed_atoms_key)
    atoms = read(filepath)
    assert atoms == parsed_atoms
