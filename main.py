import os
import asyncio
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


async def run_demo(demo_mode: bool = False) -> None:
    supabase = await initialize_supabase()
    if not supabase:
        return

    await fetch_credentials(supabase)

    if demo_mode:
        await insert_credential(supabase, "demo@example.com", "azerty")

    channel = await setup_realtime_subscription(supabase)
    if not channel:
        return

    print("Listening for changes on the credentials table. Press Ctrl+C to exit.")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Exiting gracefully...")
    finally:
        if channel:
            await remove_realtime_subscription(supabase, channel)


def main() -> None:
    try:
        asyncio.run(run_demo(demo_mode=True))
    except KeyboardInterrupt:
        print("Program interrupted by user")


if __name__ == "__main__":
    main()
