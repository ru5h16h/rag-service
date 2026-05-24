import click


@click.group()
def cli() -> None:
    """CLI entrypoint for ingestion workflows."""


if __name__ == "__main__":
    cli()
