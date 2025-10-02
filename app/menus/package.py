import json
import sys
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_family_v2, get_package, get_addons, get_package_details, purchase_package, send_api_request
from app.service.bookmark import BookmarkInstance
from app.client.purchase import show_qris_payment, settlement_bounty
from app.client.ewallet import show_multipayment
from app.menus.util import clear_screen, pause, display_html, print_header, Style
from app.client.qris import show_qris_payment_v2
from app.client.ewallet import show_multipayment_v2
from app.client.balance import settlement_balance
from app.service.family_bookmark import FamilyBookmarkInstance
from app.type_dict import PaymentItem


def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    package = get_package(api_key, tokens, package_option_code)
    # print(f"[SPD-202]:\n{json.dumps(package, indent=1)}")
    if not package:
        print("Failed to load package details.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","") #Vidio
    family_name = package.get("package_family", {}).get("name","") #Unlimited Turbo
    variant_name = package.get("package_detail_variant", "").get("name","") #For Xtra Combo
    option_name = package.get("package_option", {}).get("name","") #Vidio
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()

    clear_screen()
    print_header(f"📦 Detail Paket: {title}")
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    print(f"  Harga       : Rp {price}")
    print(f"  Masa Aktif  : {validity}")
    print(f"  Tipe        : {package['package_family']['plan_type']}")
    print(f"  Payment For : {payment_for}")
    print(f"  Point       : {package['package_option']['point']}")
    print(f"{'-'*55}")
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        print("Benefit Paket:")
        for benefit in benefits:
            print(f" Name: {benefit['name']}")
            print(f"  Item id: {benefit['item_id']}")
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']/60} menit")
            elif data_type == "TEXT" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']} SMS")
            elif data_type == "DATA" and benefit['total'] > 0:
                if benefit['total'] > 0:
                    quota = int(benefit['total'])
                    # It is in byte, make it in GB
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        print(f"  Quota: {quota_gb:.2f} GB")
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        print(f"  Quota: {quota_mb:.2f} MB")
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        print(f"  Quota: {quota_kb:.2f} KB")
                    else:
                        print(f"  Total: {quota}")
            elif data_type not in ["DATA", "VOICE", "TEXT"]:
                print(f"  Total: {benefit['total']} ({data_type})")
            
            if benefit["is_unlimited"]:
                print("  Unlimited: Yes")
            print(f"{'-'*55}")
    addons = get_addons(api_key, tokens, package_option_code)
    

    bonuses = addons.get("bonuses", [])
    
    # Pick 1st bonus if available, need more testing
    # if len(bonuses) > 0:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonuses[0]["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonuses[0]["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )
    
    # Pick all bonuses, need more testing
    # for bonus in bonuses:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonus["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonus["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )

    print(f"Addons:\n{json.dumps(addons, indent=2)}")
    print(f"{'-'*55}")
    print(f"SnK MyXL:\n{detail}")
    print(f"{'-'*55}")
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        print("\nOpsi Pembelian:")
        print(f"  {Style.CYAN}[1]{Style.RESET}. 💰 Beli dengan Pulsa")
        print(f"  {Style.CYAN}[2]{Style.RESET}. 💳 Beli dengan E-Wallet")
        print(f"  {Style.CYAN}[3]{Style.RESET}. 📱 Bayar dengan QRIS")
        
        # Sometimes payment_for is empty, so we set default to BUY_PACKAGE
        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        
        if payment_for == "REDEEM_VOUCHER":
            print(f"  {Style.CYAN}[4]{Style.RESET}. 🎁 Ambil sebagai bonus (jika tersedia)")
        
        if option_order != -1:
            print(f"  {Style.CYAN}[0]{Style.RESET}. 🔖 Tambah ke Bookmark")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke daftar paket")
        print(f"{'-'*25}")

        choice = input("Pilihan > ")
        if choice == "00":
            return False
        if choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print("Paket berhasil ditambahkan ke bookmark.")
            else:
                print("Paket sudah ada di bookmark.")
            pause()
            continue
        
        if choice == '1':
            # purchase_package(api_key, tokens, package_option_code, is_enterprise)
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first"
            )
            input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '2':
            # show_multipayment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
            show_multipayment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first"
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '3':
            # show_qris_payment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
            show_qris_payment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used="first"
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '9':
            # Decoy
            pd = get_package_details(
                api_key,
                tokens,
                "5d63dddd-4f90-4f4c-8438-2f005c20151f",
                "5b59c55b-0dc7-4f34-a6e9-6afa233ad53b",
                6,
                False,
                "NONE",
            )
            
            payment_items.append(
                PaymentItem(
                    item_code=pd["package_option"]["package_option_code"],
                    product_type="",
                    item_price=pd["package_option"]["price"],
                    item_name=pd["package_option"]["name"],
                    tax=0,
                    token_confirmation=pd["token_confirmation"],
                )
            )

            show_qris_payment_v2(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
                amount_used=""
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '4':
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
        else:
            print("Purchase cancelled.")
            return False
    pause()
    sys.exit(0)

def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    return_package_detail: bool = False
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    packages = []
    
    # data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    data = get_family_v2(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )
    if not data:
        print("Failed to load family data.")
        return None    
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        print_header(f"🛍️ Daftar Paket: {data['package_family']['name']}")
        print(f"  Family Code: {family_code}")
        print(f"  Tipe       : {data['package_family']['package_family_type']}")
        print(f"{'-'*55}")
        package_variants = data["package_variants"]
        
        option_number = 1
        variant_number = 1
        
        for variant in package_variants:
            variant_name = variant["name"]
            variant_code = variant["package_variant_code"]
            print(f"💠 Variant {variant_number}: {variant_name}")
            # print(f" Code: {variant_code}")
            for option in variant["package_options"]:
                option_name = option["name"]
                
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                
                # print(json.dumps(option, indent=2))
                
                print(f"  {Style.CYAN}[{option_number:2d}]{Style.RESET}. {option_name} - Rp {option['price']}")
                
                option_number += 1
            
            if variant_number < len(package_variants):
                print(f"{'-'*55}")
            variant_number += 1
        print(f"{'-'*55}")
        print("  🔢  Pilih nomor untuk melihat detail paket")
        print(f"  {Style.CYAN}[s]{Style.RESET}. 💾 Simpan Family Code ini")
        print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
        print(f"{'-'*55}")
        pkg_choice = input("Pilihan > ")
        if pkg_choice == "00":
            in_package_menu = False
            return None
        elif pkg_choice.lower() == 's':
            family_name = data.get('package_family', {}).get('name', 'Unknown Family')
            if FamilyBookmarkInstance.add_bookmark(family_code, family_name):
                print(f"✅ Family Code '{family_name}' berhasil disimpan.")
            else:
                print(f"ℹ️ Family Code '{family_name}' sudah ada di bookmark.")
            pause()
            continue

        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        
        if not selected_pkg:
            print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
            continue

        if return_package_detail:
            print("Mengambil detail paket...")
            package_detail = get_package(api_key, tokens, selected_pkg["code"])
            if package_detail:
                display_name = f"{data['package_family']['name']} - {selected_pkg['variant_name']} - {selected_pkg['option_name']}"
                return package_detail, display_name
            else:
                print("Gagal mengambil detail paket.")
                pause()
                return None, None
        else:
            is_done = show_package_details(api_key, tokens, selected_pkg["code"], is_enterprise, option_order=selected_pkg["option_order"])
            if is_done:
                in_package_menu = False
                return None
            else:
                continue
        
    return packages

def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None
    
    id_token = tokens.get("id_token")
    
    path = "api/v8/packages/quota-details"
    
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    
    print("Fetching my packages...")
    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        print("Failed to fetch packages")
        print("Response:", res)
        pause()
        return None
    
    quotas = res["data"]["quotas"]
    
    clear_screen()
    print_header("📦 Paket Saya")
    my_packages =[]
    num = 1
    for quota in quotas:
        quota_code = quota["quota_code"] # Can be used as option_code
        group_code = quota["group_code"]
        name = quota["name"]
        
        print(f"fetching package no. {num} details...")
        package_details = get_package(api_key, tokens, quota_code)
        
        print(f"{'-'*55}")
        print(f"Paket #{num}")
        print(f"  Nama       : {name}")
        print(f"  Quota Code : {quota_code}")
        if package_details:
            family_code = package_details.get("package_family", {}).get("package_family_code", "N/A")
            print(f"  Family Code: {family_code}")
        print(f"  Group Code : {group_code}")
        
        my_packages.append({
            "number": num,
            "quota_code": quota_code,
        })
        
        num += 1
    
    print(f"{'-'*55}")
    print("  🔢  Pilih nomor untuk membeli ulang (Rebuy)")
    print(f"  {Style.CYAN}[00]{Style.RESET}. ↩️  Kembali ke Menu Utama")
    print(f"{'-'*55}")
    choice = input("Pilihan > ")
    if choice == "00":
        return None
    selected_pkg = next((pkg for pkg in my_packages if str(pkg["number"]) == choice), None)
    
    if not selected_pkg:
        print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
        return None
    
    is_done = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
    if is_done:
        return None
        
    pause()
