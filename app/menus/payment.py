from datetime import datetime, timezone, timedelta

from app.client.engsel import get_transaction_history
from app.menus.util import clear_screen, print_header, pause, Style

def show_transaction_history(api_key, tokens):
    """Menampilkan riwayat transaksi pengguna."""
    in_transaction_menu = True
    while in_transaction_menu:
        clear_screen()
        print_header("📜 RIWAYAT TRANSAKSI 📜")
        
        history = []
        try:
            print("Mengambil riwayat transaksi...", end="\r")
            data = get_transaction_history(api_key, tokens)
            if data and data.get("status") == "SUCCESS":
                history = data.get("data", {}).get("list", [])
            else:
                print(f"{Style.RED}Gagal mengambil data: {data.get('message', 'Status bukan SUCCESS')}{Style.RESET}")
        except Exception as e:
            print(f"{Style.RED}Terjadi error: {e}{Style.RESET}")
        
        if not history:
            print("\nTidak ada riwayat transaksi ditemukan.")
        else:
            for idx, trx in enumerate(history, start=1):
                # Timestamp dalam milidetik, konversi ke detik dan sesuaikan ke zona waktu WIB (GMT+7)
                dt_object = datetime.fromtimestamp(trx.get("timestamp", 0) / 1000, tz=timezone.utc).astimezone(timezone(timedelta(hours=7)))
                formatted_time = dt_object.strftime("%d %B %Y, %H:%M:%S WIB")

                print(f"  {Style.CYAN}[{idx}]{Style.RESET}. {Style.BOLD}{trx.get('title', 'N/A')}{Style.RESET}")
                print(f"     - Harga           : {trx.get('price', 'N/A')}")
                print(f"     - Tanggal         : {formatted_time}")
                print(f"     - Metode Pembayaran: {trx.get('payment_method_label', 'N/A')}")
                print(f"     - Status Transaksi : {trx.get('status', 'N/A')}")
                print(f"     - Status Pembayaran: {trx.get('payment_status', 'N/A')}")
                print(f"{'-'*55}")

        print("\n  [0] Refresh")
        print("  [99] Kembali ke Menu Utama")
        choice = input("\nPilihan > ")
        if choice == "99":
            in_transaction_menu = False
        elif choice == "0":
            continue
        else:
            print("Pilihan tidak valid.")
            pause()