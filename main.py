import os
import asyncio
import argparse
from typing import Dict, Any, Optional
from supabase import create_async_client, AsyncClient


async def initialize_supabase() -> Optional[AsyncClient]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        return None
    try:
        client = await create_async_client(url, key)
        print("Supabase client initialized successfully")
        return client
    except Exception as e:
        print("Failed to initialize Supabase client:", e)
        return None


async def fetch_credentials(supabase: AsyncClient) -> None:
    try:
        response = await supabase.table("credentials").select("*").execute()
        records = response.data
        print(f"Retrieved {len(records)} credentials record(s)")
        print("Credentials data:", records)
    except Exception as e:
        print("Error fetching credentials:", e)


async def insert_credential(supabase: AsyncClient, email: str, password: str) -> None:
    try:
        response = (
            await supabase.table("credentials")
            .insert({"email": email, "password": password})
            .execute()
        )
        print(f"Inserted credential for {email}")
        print("Insert response:", response.data)
    except Exception as e:
        print("Error inserting credential:", e)


async def update_credential(
    supabase: AsyncClient, email: str, new_password: str
) -> None:
    try:
        response = (
            await supabase.table("credentials")
            .update({"password": new_password})
            .eq("email", email)
            .execute()
        )
        print(f"Updated credential for {email}")
        print("Update response:", response.data)
    except Exception as e:
        print("Error updating credential:", e)


async def delete_credential(supabase: AsyncClient, email: str) -> None:
    try:
        response = (
            await supabase.table("credentials").delete().eq("email", email).execute()
        )
        print(f"Deleted credential for {email}")
        print("Delete response:", response.data)
    except Exception as e:
        print("Error deleting credential:", e)


def handle_record_updated(payload: Dict[str, Any]) -> None:
    data = payload.get("data", {})
    event_type = data.get("type", "unknown")
    print("Real-time event received:", event_type)
    if event_type == "DELETE":
        old_record = data.get("old_record", {})
        print("Record deleted:", old_record)
    else:
        record = data.get("record", {})
        print("Updated record:", record)


async def setup_realtime_subscription(supabase: AsyncClient) -> Optional[Any]:
    try:
        channel = (
            await supabase.channel("credentials_channel")
            .on_postgres_changes(
                event="*",
                schema="public",
                table="credentials",
                callback=handle_record_updated,
            )
            .subscribe()
        )
        print("Successfully subscribed to real-time updates")
        return channel
    except Exception as e:
        print("Error setting up real-time subscription:", e)
        return None


async def remove_realtime_subscription(supabase: AsyncClient, channel: Any) -> None:
    try:
        await supabase.remove_channel(channel)
        print("Real-time subscription removed")
    except Exception as e:
        print("Error removing real-time subscription:", e)


async def run_realtime() -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return
    channel = await setup_realtime_subscription(supabase)
    if not channel:
        return
    print(
        "Listening for real-time updates on the credentials table. Press Ctrl+C to exit."
    )
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Exiting realtime subscription...")
    finally:
        if channel:
            await remove_realtime_subscription(supabase, channel)


async def do_create(email: str, password: str) -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return
    await insert_credential(supabase, email, password)


async def do_update(email: str, password: str) -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return
    await update_credential(supabase, email, password)


async def do_delete(email: str) -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return
    await delete_credential(supabase, email)


async def do_list() -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return
    await fetch_credentials(supabase)


def main() -> None:
    parser = argparse.ArgumentParser(description="Supabase Python CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a credential")
    create_parser.add_argument("--email", required=True, help="Email address")
    create_parser.add_argument("--password", required=True, help="Password")

    # Update command
    update_parser = subparsers.add_parser(
        "update", help="Update a credential's password"
    )
    update_parser.add_argument("--email", required=True, help="Email address")
    update_parser.add_argument("--password", required=True, help="New password")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a credential")
    delete_parser.add_argument("--email", required=True, help="Email address")

    # List command
    list_parser = subparsers.add_parser("list", help="List all credentials")

    # Realtime command
    realtime_parser = subparsers.add_parser(
        "realtime", help="Subscribe to realtime updates"
    )

    args = parser.parse_args()

    if args.command == "create":
        asyncio.run(do_create(args.email, args.password))
    elif args.command == "update":
        asyncio.run(do_update(args.email, args.password))
    elif args.command == "delete":
        asyncio.run(do_delete(args.email))
    elif args.command == "list":
        asyncio.run(do_list())
    elif args.command == "realtime":
        asyncio.run(run_realtime())


if __name__ == "__main__":
    main()
