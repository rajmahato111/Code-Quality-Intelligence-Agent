"""CLI command to start the web server."""

import click
import uvicorn
import logging
from pathlib import Path

from ..web.api import app
from ..web.auth import create_demo_api_key

logger = logging.getLogger(__name__)


@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--log-level', default='info', help='Log level')
@click.option('--workers', default=1, help='Number of worker processes')
@click.option('--create-demo-key', is_flag=True, help='Create a demo API key on startup')
def server(host, port, reload, log_level, workers, create_demo_key):
    """Start the Code Quality Intelligence Agent web server."""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Code Quality Intelligence Agent web server...")
    
    if create_demo_key:
        demo_key = create_demo_api_key()
        click.echo(f"\n🔑 Demo API Key created: {demo_key}")
        click.echo("Use this key in the Authorization header: Bearer <api_key>")
        click.echo("Or visit /demo/api-key to get a new one\n")
    
    click.echo(f"🚀 Server starting on http://{host}:{port}")
    click.echo(f"📚 API Documentation: http://{host}:{port}/docs")
    click.echo(f"🔍 Alternative Docs: http://{host}:{port}/redoc")
    click.echo(f"❤️  Health Check: http://{host}:{port}/health")
    
    # Start the server
    uvicorn.run(
        "code_quality_agent.web.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=workers if not reload else 1  # Reload doesn't work with multiple workers
    )


if __name__ == "__main__":
    server()