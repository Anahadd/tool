import argparse
import asyncio
import os
import sys
from pathlib import Path

import integrations as integrations_mod


def cmd_connect_sheets(args: argparse.Namespace) -> int:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    client_path = args.client_secrets or os.getenv("GOOGLE_OAUTH_CLIENT") or str(
        Path.home() / ".tool_google" / "oauth_client.json"
    )
    try:
        token_path = integrations_mod.connect_sheets_oauth(scopes=scopes, client_secrets_path=client_path)
        print(f"Connected. Token saved at: {token_path}")
        print("Tip: You can now run `impressions update-sheets` without GOOGLE_SHEETS_CREDS.")
        return 0
    except Exception as exc:
        print(f"Failed to connect Google Sheets: {exc}")
        return 1


def cmd_update_sheets(_args: argparse.Namespace) -> int:
    try:
        # Parse disabled columns if provided
        disabled_cols = []
        if hasattr(_args, 'disable') and _args.disable:
            disabled_cols = [col.strip().lower() for col in _args.disable.split(',')]
        
        # Parse row range if provided
        start_row = None
        end_row = None
        if hasattr(_args, 'rows') and _args.rows:
            try:
                parts = _args.rows.split(':')
                if len(parts) != 2:
                    raise ValueError("Row range must be in format 'start:end'")
                start_row = int(parts[0])
                end_row = int(parts[1])
                if start_row < 2:
                    raise ValueError("Start row must be >= 2 (row 1 is header)")
                if end_row < start_row:
                    raise ValueError("End row must be >= start row")
            except ValueError as e:
                print(f"Invalid row range: {e}", file=sys.stderr)
                return 1
        
        asyncio.run(
            integrations_mod.update_sheet_views_likes_comments(
                spreadsheet=_args.spreadsheet,
                worksheet=_args.worksheet,
                creds_path=_args.creds,
                disabled_columns=disabled_cols,
                override=_args.override,
                start_row=start_row,
                end_row=end_row,
            )
        )
        return 0
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1




def build_parser() -> argparse.ArgumentParser:
    epilog_text = """
Environment Variables:
  APIFY_TOKEN          API token for Instagram scraping (required for Instagram posts)
                       Get your token at: https://console.apify.com/account/integrations
                       
                       Usage:
                         export APIFY_TOKEN=your_token_here
    """
    p = argparse.ArgumentParser(
        prog="impressions", 
        description="Impressions CLI",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_conn = sub.add_parser("connect-sheets", help="Connect your Google account via OAuth")
    p_conn.add_argument(
        "--client-secrets",
        help="Path to OAuth client secrets JSON (Desktop App)",
        default="",
    )
    p_conn.set_defaults(func=cmd_connect_sheets)

    p_upd = sub.add_parser("update-sheets", help="Update views/likes/comments in your Google Sheet")
    p_upd.add_argument("--spreadsheet", help="Sheet URL or ID (optional; otherwise uses saved default)")
    p_upd.add_argument("--worksheet", help="Tab name (optional; otherwise uses saved default)")
    p_upd.add_argument("--creds", help="Service account JSON path (optional; overrides env)")
    p_upd.add_argument(
        "--disable",
        help="Comma-separated list of columns to skip updating (e.g., 'name,impressions,channel')",
        default="",
    )
    p_upd.add_argument(
        "--override",
        help="Whether to override existing data (default: true). Set to false to only fill empty cells.",
        type=lambda x: x.lower() in ['true', '1', 'yes'],
        default=True,
    )
    p_upd.add_argument(
        "--rows",
        help="Row range to process in format 'start:end' (e.g., '2:10' to process rows 2-10). Row 1 is the header.",
        default="",
    )
    p_upd.set_defaults(func=cmd_update_sheets)

    p_set = sub.add_parser("set-defaults", help="Save default Sheet URL/ID and worksheet for future runs")
    p_set.add_argument("spreadsheet", metavar="GOOGLE_SHEET_URL_LINK", help="Sheet URL or ID to store")
    p_set.add_argument("worksheet", metavar="SHEET_NAME", help="Worksheet/tab name to store")
    def _cmd_set(args: argparse.Namespace) -> int:
        try:
            integrations_mod.set_sheet_defaults(args.spreadsheet, args.worksheet)
            print("Defaults saved. Future runs of update-sheets can omit --spreadsheet/--worksheet.")
            return 0
        except Exception as exc:
            print(f"Failed to save defaults: {exc}")
            return 1
    p_set.set_defaults(func=_cmd_set)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()


