'''
CLI commands for database management and other operations
'''

import click
from rich.console import Console
from rich.table import Table
from .core.database import init_database, health_check
from .core.migrations import migration_manager
from .core.logging import setup_logging, get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def cli():
    '''Zib RSS Reader CLI'''
    setup_logging()


@cli.group()
def db():
    '''Database management commands'''
    pass


@db.command()
def init():
    '''Initialize database and run migrations'''
    console.print('[blue]Initializing database...[/blue]')
    
    try:
        init_database()
        console.print('[green]✓ Database initialized successfully![/green]')
    except Exception as e:
        console.print(f'[red]✗ Database initialization failed: {e}[/red]')
        raise click.Abort()


@db.command()
def migrate():
    '''Run pending migrations'''
    console.print('[blue]Running migrations...[/blue]')
    
    try:
        if migration_manager.migrate():
            console.print('[green]✓ Migrations completed successfully![/green]')
        else:
            console.print('[red]✗ Migration failed![/red]')
            raise click.Abort()
    except Exception as e:
        console.print(f'[red]✗ Migration failed: {e}[/red]')
        raise click.Abort()


@db.command()
@click.argument('version', type=int)
def rollback(version):
    '''Rollback to a specific version'''
    console.print(f'[blue]Rolling back to version {version}...[/blue]')
    
    try:
        if migration_manager.rollback_to_version(version):
            console.print(f'[green]✓ Rolled back to version {version}![/green]')
        else:
            console.print('[red]✗ Rollback failed![/red]')
            raise click.Abort()
    except Exception as e:
        console.print(f'[red]✗ Rollback failed: {e}[/red]')
        raise click.Abort()


@db.command()
def status():
    '''Show migration status'''
    console.print('[blue]Checking migration status...[/blue]')
    
    status = migration_manager.get_migration_status()
    
    if 'error' in status:
        console.print(f'[red]✗ Error: {status["error"]}[/red]')
        return
    
    console.print(f'[green]Current version: {status["current_version"]}[/green]')
    
    if status['pending_migrations']:
        console.print(f'[yellow]Pending migrations: {len(status["pending_migrations"])}[/yellow]')
    else:
        console.print('[green]No pending migrations[/green]')
    
    # Show migration table
    table = Table(title='Migration Status')
    table.add_column('Version', style='cyan')
    table.add_column('Description', style='white')
    table.add_column('Applied', style='green')
    
    for migration in status['available_migrations']:
        applied_status = '✓' if migration['applied'] else '✗'
        table.add_row(
            str(migration['version']),
            migration['description'],
            applied_status
        )
    
    console.print(table)


@db.command()
def health():
    '''Check database health'''
    console.print('[blue]Checking database health...[/blue]')
    
    result = health_check()
    
    if result['status'] == 'healthy':
        console.print('[green]✓ Database is healthy[/green]')
        console.print(f'Status: {result["database"]}')
    else:
        console.print('[red]✗ Database is unhealthy[/red]')
        console.print(f'Error: {result["error"]}')


if __name__ == '__main__':
    cli()