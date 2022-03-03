"""Test parse strategies."""


def test_xyz_read(repo_dir: "Path") -> None:
    """Test `chemical/x-xyz` parse strategy.
    Tests that ase.Atoms obtained through parse strategy
    are the same as ase.Atoms optained from ASE directly."""
    from ase.io import read
    from oteapi.datacache import DataCache
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy

    config = ResourceConfig(
        downloadUrl=(
            "https://raw.githubusercontent.com/nutjunkie/IQmol/"
            "master/share/fragments/Molecules/Alkanes/Ethane.xyz"
        ),
        mediaType="chemical/x-xyz",
    )
    cache = DataCache()
    parser = AtomisticStructureParseStrategy(config)
    parsed_atoms_key = parser.get().cached_atoms_key
    parsed_atoms = cache.get(parsed_atoms_key)

    # Note that this Ethane.xyz file was downlaoded from the downloadUrl
    # specified in the config above. If the test fails, check that
    # the downlaoded file is still identical to that in the url
    filepath = repo_dir / "tests" / "testfiles" / "Ethane.xyz"
    atoms = read(filepath)
    assert atoms == parsed_atoms
