"""
Dashboard server launcher command handler.
"""

from pipeline.commands.context import CommandContext


def cmd_dashboard(ctx: CommandContext, args) -> None:
    """Launches interactive Review & Approval dashboard server on localhost."""
    from pipeline.outreach.dashboard_server import start_dashboard_server
    start_dashboard_server()
