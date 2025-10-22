import asyncio
import os
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from services.telegram_client import TelegramClientWrapper
from models.channel import Channel
from db.mysql import connection, get_cursor
from utils.logger import Logger
from config.config import Config

console = Console()
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
class BotServiceManager:
    def __init__(self, db_conn, telegram_client: TelegramClientWrapper):
        self.db_conn = db_conn
        self.telegram_client = telegram_client

    async def process_channel(self, channel):
        start = time.time()
        try:
            await self.telegram_client.fetch_new_messages_for_channel(self.db_conn, channel)
            duration = round(time.time() - start, 2)
            return {
                "id": channel.channel_id,
                "status": "✅ Thành công",
                "duration": f"{duration}s"
            }
        except Exception as e:
            duration = round(time.time() - start, 2)
            return {
                "id": channel.channel_id,
                "status": f"❌ {str(e)[:25]}",
                "duration": f"{duration}s"
            }

    async def run_all_channels(self):
        cursor = get_cursor()
        channels = Channel.list_channels(cursor, status="active")
        cursor.close()
        if not channels:
            console.print("[yellow]⚠️  Không tìm thấy channel nào đang hoạt động.[/yellow]")
            return []
        await self.telegram_client.start_all()

        results = await asyncio.gather(*(self.process_channel(ch) for ch in channels))

       
        await self.telegram_client.disconnect_all()

        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in results:
            r["time"] = scan_time

        show_results_table(results, scan_time)


def show_results_table(results, scan_time):
    

    console.print(
        Panel.fit(
            "🚀 [bold cyan]Telegram Reposter Bot - Scheduler Mode[/bold cyan]\n"
            "[dim]Tự động xử lý & cập nhật trạng thái liên tục[/dim]",
            border_style="cyan",
        )
    )
    console.print(f"⏳ [bold yellow]Bắt đầu vòng quét mới:[/bold yellow] {scan_time}\n")

    table = Table(
        title="📊 [bold cyan]Kết quả xử lý kênh Telegram[/bold cyan]",
        box=box.SQUARE_DOUBLE_HEAD,
        header_style="bold magenta",
        title_style="bold blue",
    )

    table.add_column("Channel ID", justify="center", style="bold cyan")
    table.add_column("Trạng thái", justify="center")
    table.add_column("Thời gian xử lý", justify="center", style="yellow")
    table.add_column("Thời gian quét", justify="center", style="bold white")

    for r in results:
        color = "green" if "✅" in r["status"] else "red"
        table.add_row(
            str(r["id"]),
            f"[{color}]{r['status']}[/{color}]",
            r["duration"],
            r["time"]
        )

    console.print(table)
    console.print("\n")
async def main():
  
    config = Config()
    API_ID = config.get("telegram.api_id", 28288961)
    API_HASH = config.get("telegram.api_hash", "616b006a2ba5538ad6ec731844ebc05a")
    SESSION_FETCH = config.get("telegram.session_fetch", "session_fetch")

    SESSION_SEND = config.get("telegram.session_send", "session_send")

    INTERVAL_SECONDS = config.get("scheduler.interval", 60)

    telegram_client = TelegramClientWrapper(API_ID, API_HASH, SESSION_FETCH, SESSION_SEND)
    manager = BotServiceManager(connection, telegram_client)

    try:
        while True:
            await manager.run_all_channels()
            console.print(f"[dim]⏰ Đợi {INTERVAL_SECONDS} giây trước vòng quét tiếp theo...[/dim]")
            await asyncio.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        console.print("[yellow]🛑 Dừng scheduler (người dùng yêu cầu).[/yellow]")
    except Exception as e:
        console.print(f"[red]🚨 Lỗi tổng quát trong scheduler: {e}[/red]")
    finally:
        try:
            connection.close()
            console.print("[green]🛑 Đóng kết nối MySQL thành công.[/green]")
        except Exception as e:
            console.print(f"[red]❌ Lỗi khi đóng kết nối MySQL: {e}[/red]")


if __name__ == "__main__":

    asyncio.run(main())
