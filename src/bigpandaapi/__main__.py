"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """The Unofficial BigPanda API Python Library."""


if __name__ == "__main__":
    main(prog_name="bigpandaapi")  # pragma: no cover
