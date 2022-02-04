"""Test parse strategies."""


def test_xyz_read(repo_dir: "Path") -> None:
    """Test `chemical/x-xyz` parse strategy."""
    from ase.io import read
    from oteapi.models.resourceconfig import ResourceConfig

    from oteapi_asmod.strategies.parse import AtomisticStructureParseStrategy

    filepath = repo_dir / "tests" / "testfiles" / "Ethane.xyz"

    config = ResourceConfig(
        downloadUrl=(
            "https://raw.githubusercontent.com/nutjunkie/IQmol/"
            "master/share/fragments/Molecules/Alkanes/Ethane.xyz"
        ),
        mediaType="chemical/x-xyz",
    )
    parser = AtomisticStructureParseStrategy(config)
    atoms = parser.parse()

    assert atoms == read(filepath)
