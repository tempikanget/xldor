import json
import base64
import qrcode
from app.client.engsel import get_package_details
from app.client.ewallet import settlement_multipayment_v2
from app.menus.util import clear_screen, print_header, pause, Style
from app.client.qris import settlement_qris_v2, get_qris_code
from app.service.auth import AuthInstance

# Definisi bundle paket
BUNDLES = [
    {
        "menu_title": "Kuota Edukasi +7GB (QRIS)",
        "payment_method": "QRIS",
        "data": {
            "name": "Add On Youtube 24GB (Gandengan Xtra Combo)",
            "price": "Rp.1000",
            "detail": "Support E-Wallet & QRIS.\\nHanya bisa dibeli kalau punya XCP/XCVP tertentu.\\nTidak akumulasi, beli ulang jika sudah habis.\\nMasa aktif mengikuti paket XCP/XCVP.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 5GB",
                    "order": 5
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 2GB",
                    "order": 6
                }
            ]
        }
    },
    {
        "menu_title": "Kuota Edukasi +7GB (ShopeePay)",
        "payment_method": "SHOPEEPAY",
        "data": {
            "name": "Add On Youtube 24GB (Gandengan Xtra Combo)",
            "price": "Rp.1000",
            "detail": "Support E-Wallet & QRIS.\\nHanya bisa dibeli kalau punya XCP/XCVP tertentu.\\nTidak akumulasi, beli ulang jika sudah habis.\\nMasa aktif mengikuti paket XCP/XCVP.",
            "packages": [
                {
                    "family_name": "Kuota Bersama",
                    "family_code": "d018a3ad-172f-433c-b291-f574f4b6fbad",
                    "is_enterprise": None,
                    "variant_name": "Kuota Bersama",
                    "option_name": "Kuota HP Sekeluarga 50GB",
                    "order": 3
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 5GB",
                    "order": 5
                },
                {
                    "family_name": "Work & School",
                    "family_code": "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                    "is_enterprise": False,
                    "variant_name": "Work & School",
                    "variant_code": "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                    "option_name": "Education 2GB",
                    "order": 6
                }
            ]
        }
    }
]

def execute_autobuy(bundle_data, payment_method):
    """Mengeksekusi pembelian bundle dan menampilkan link pembayaran."""
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print("Silakan login terlebih dahulu.")
        pause()
        return

    print(f"Memproses pembelian bundle '{bundle_data['name']}'...")
    
    # 1. Ambil detail setiap paket untuk membuat payment_items
    payment_items = []
    total_bundle_price = 0
    for package in bundle_data["packages"]:
        package_detail = get_package_details(
            AuthInstance.api_key,
            active_user["tokens"],
            package.get("family_code"),
            package.get("variant_code") or package.get("variant_name"),
            package.get("order"),
            package.get("is_enterprise"),
        )
        if not package_detail:
            print(f"\n{Style.RED}Gagal mengambil detail untuk paket: {package.get('option_name')}{Style.RESET}")
            pause()
            return

        item_price = package_detail["package_option"]["price"]
        total_bundle_price += item_price
        payment_items.append({
            "item_code": package_detail["package_option"]["package_option_code"],
            "product_type": "",
            "item_price": item_price,
            "item_name": f"{package_detail.get('package_detail_variant', {}).get('name', '')} {package_detail['package_option']['name']}".strip(),
            "tax": 0,
            "token_confirmation": package_detail["token_confirmation"],
        })

    # 2. Lakukan settlement berdasarkan metode pembayaran
    if payment_method == "QRIS":
        print("Memproses pembayaran dengan QRIS...")
        transaction_id = settlement_qris_v2(
            AuthInstance.api_key,
            active_user["tokens"],
            payment_items,
            "BUY_PACKAGE",
            ask_overwrite=False,
            amount_overwrite=total_bundle_price
        )

        if not transaction_id:
            print(f"\n{Style.RED}Gagal membuat transaksi QRIS.{Style.RESET}")
        else:
            print("Mengambil kode QRIS...")
            qris_data = get_qris_code(AuthInstance.api_key, active_user["tokens"], transaction_id)
            if qris_data:
                print(f"\n{Style.GREEN}Kode QRIS berhasil dibuat! Silakan scan.{Style.RESET}")
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
                qr.add_data(qris_data)
                qr.make(fit=True)
                qr.print_ascii(invert=True)
                qris_b64 = base64.urlsafe_b64encode(qris_data.encode()).decode()
                print(f"\nAtau buka link berikut untuk melihat QRIS:\nhttps://ki-ar-kod.netlify.app/?data={qris_b64}")
            else:
                print(f"\n{Style.RED}Gagal mengambil data QRIS setelah transaksi dibuat.{Style.RESET}")

    elif payment_method == "SHOPEEPAY":
        print("Memproses pembayaran dengan ShopeePay...")
        settlement_response = settlement_multipayment_v2(
            AuthInstance.api_key, active_user["tokens"], payment_items, "", "SHOPEEPAY", "BUY_PACKAGE", 
            ask_overwrite=False, amount_overwrite=total_bundle_price
        )
        
        if not settlement_response or settlement_response.get("status") != "SUCCESS":
            print(f"\n{Style.RED}Gagal membuat transaksi ShopeePay.{Style.RESET}")
            print(f"Error: {settlement_response}")
        else:
            deeplink = settlement_response["data"].get("deeplink", "")
            if deeplink:
                print(f"\n{Style.GREEN}Silakan selesaikan pembayaran melalui link berikut:{Style.RESET}\n{deeplink}")
            else:
                print(f"\n{Style.RED}Gagal mendapatkan link pembayaran ShopeePay.{Style.RESET}")
    else:
        print(f"\n{Style.RED}Metode pembayaran '{payment_method}' tidak didukung.{Style.RESET}")

    pause()

def show_autobuy_bundle_menu():
    """Menampilkan menu untuk auto-buy bundle."""
    clear_screen()
    print_header("✨ AUTOBUY BUNDLE (HIDDEN) ✨")
    for i, bundle in enumerate(BUNDLES, 1):
        print(f"  [{i}] {bundle['menu_title']}")
    print("\n  [99] Kembali ke Menu Utama")
    print(f"{'-'*55}")
    choice = input("Pilihan > ")

    if choice.isdigit() and 1 <= int(choice) <= len(BUNDLES):
        selected_bundle = BUNDLES[int(choice) - 1]
        execute_autobuy(selected_bundle["data"], selected_bundle["payment_method"])
    elif choice == "99":
        return
    else:
        print("Pilihan tidak valid.")
        pause()