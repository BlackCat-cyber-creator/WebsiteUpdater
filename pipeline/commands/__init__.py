"""
Pipeline commands registry and unified dispatcher.
"""

from pipeline.commands.context import CommandContext
from pipeline.commands.cmd_wa import cmd_setup_wa, cmd_listen_replies
from pipeline.commands.cmd_dashboard import cmd_dashboard
from pipeline.commands.cmd_deploy import cmd_deploy_vercel, cmd_package
from pipeline.commands.cmd_invoice import cmd_create_invoice, cmd_simulate_payment
from pipeline.commands.cmd_lead_ops import cmd_approve, cmd_discard, cmd_generate_queue, cmd_test_email
from pipeline.commands.cmd_auto_modernize import cmd_auto_modernize
from pipeline.commands.cmd_harvest import cmd_harvest, MID_TIER_CATEGORIES

__all__ = [
    "CommandContext",
    "cmd_setup_wa",
    "cmd_listen_replies",
    "cmd_dashboard",
    "cmd_deploy_vercel",
    "cmd_package",
    "cmd_create_invoice",
    "cmd_simulate_payment",
    "cmd_approve",
    "cmd_discard",
    "cmd_generate_queue",
    "cmd_test_email",
    "cmd_auto_modernize",
    "cmd_harvest",
    "MID_TIER_CATEGORIES",
    "dispatch_cli"
]


def dispatch_cli(args) -> None:
    """Dispatches parsed CLI arguments to the appropriate command handler."""
    is_live = bool(getattr(args, "live", False))
    ctx = CommandContext(is_live=is_live)

    # 1. Setup WhatsApp Session
    if args.setup_wa:
        cmd_setup_wa(ctx, args)
        return

    # 2. Launch Interactive Web Dashboard Server
    if args.dashboard:
        cmd_dashboard(ctx, args)
        return

    # 3. Listen for Incoming WhatsApp Replies
    if args.listen_replies:
        cmd_listen_replies(ctx, args)
        return

    # 4. Programmatic Vercel Deploy CLI
    if args.deploy_vercel:
        cmd_deploy_vercel(ctx, args)
        return

    # 5. Package Source Code .ZIP CLI
    if args.package:
        cmd_package(ctx, args)
        return

    # 6. Create $100 Invoice CLI
    if args.create_invoice:
        cmd_create_invoice(ctx, args)
        return

    # 7. Simulate Payment Webhook CLI
    if args.simulate_payment:
        cmd_simulate_payment(ctx, args)
        return

    # 8. Approve specific lead via CLI
    if args.approve:
        cmd_approve(ctx, args)
        return

    # 9. Discard specific lead via CLI
    if args.discard:
        cmd_discard(ctx, args)
        return

    # 10. Regenerate Dashboard Queue Only
    if args.generate_queue:
        cmd_generate_queue(ctx, args)
        return

    # 11. Test Email Sending
    if args.test_email:
        cmd_test_email(ctx, args)
        return

    # 12. Batch Auto-Modernize
    if args.auto_modernize:
        cmd_auto_modernize(ctx, args)
        return

    # 13. Lead Harvesting & Outreach Engine
    cmd_harvest(ctx, args)
