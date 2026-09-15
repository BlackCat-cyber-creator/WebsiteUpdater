"""
WhatsApp session and incoming replies command handlers.
"""

from pipeline.commands.context import CommandContext


def cmd_setup_wa(ctx: CommandContext, args) -> None:
    """Launches interactive WhatsApp Web QR setup for dedicated outreach account."""
    ctx.wa_disp.setup_dedicated_session()


def cmd_listen_replies(ctx: CommandContext, args) -> None:
    """Scans WhatsApp Web for incoming client replies and auto-dispatches demo/options."""
    replies = ctx.wa_disp.check_incoming_replies(auto_respond=True)
    print(f"[+] Selesai memeriksa balasan. Total balasan diproses: {len(replies)}")
