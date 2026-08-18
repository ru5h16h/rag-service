import asyncio

import click

from src.pipeline.flows import ingest_directory, ingest_document


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--path", required=True, help="Path to file or directory")
@click.option("--tenant", default="default", help="Tenant ID")
def run(path: str, tenant: str) -> None:
    import pathlib

    p = pathlib.Path(path)
    if p.is_dir():
        asyncio.run(ingest_directory(str(p), tenant))
    else:
        asyncio.run(ingest_document(str(p), tenant))


if __name__ == "__main__":
    cli()
