#!/data/data/com.termux/files/usr/bin/python3
import json
import os
import random
from collections import defaultdict
from decimal import Decimal, InvalidOperation

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

DB_FILE = 'database.json'

# DEFCON Security Status Dictionary
STATUS_LEVELS = {
    "1": "Clean - Verified Valid",
    "2": "FLAGGED - Suspicious / Pending Audit",
    "3": "FLAGGED - Stolen / Do Not Honor",
    "4": "FLAGGED - Counterfeit / Known Forgery",
    "5": "Burned - Removed from Circulation"
}

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            print("[!] ERROR: Corrupted JSON file. Starting fresh.")
            return {}

def save_db(data):
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=4)
    print("[+] SYSTEM: Ledger saved successfully to database.json")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def select_status():
    print("\n--- SECURITY STATUS ADJUSTER ---")
    for key, val in STATUS_LEVELS.items():
        print(f"{key}. {val}")
    choice = input("Select Status Level (1-5) [Default: 1]: ").strip()
    return STATUS_LEVELS.get(choice, STATUS_LEVELS["1"])

def create_directory_structure(note_type, forever_status, denomination):
    forever_dir = "forever" if forever_status == "Forever PLC" else "limited"
    output_dir = f"outputs-serial/{note_type}/{forever_dir}/{denomination}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def generate_pdf_batch(batch_num, serials, output_path, batch_code):
    if not REPORTLAB_AVAILABLE:
        print("[!] ERROR: reportlab not installed. Install with: pip install reportlab")
        return False

    filename = os.path.join(output_path, f"batch_{batch_code}_{batch_num:03d}.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica", 12)
    y_position = height - 40

    c.drawString(40, y_position, f"Batch {batch_code} - Part {batch_num}")
    y_position -= 20
    c.drawString(40, y_position, f"Generated: {len(serials)} Serial Numbers")
    y_position -= 30

    c.setFont("Courier", 10)
    for serial in serials:
        if y_position < 40:
            c.showPage()
            y_position = height - 40
            c.setFont("Courier", 10)
        c.drawString(40, y_position, serial)
        y_position -= 15

    c.save()
    return True

def get_print_number(serial):
    """
    Extracts the 4-digit serial print number from the format AAA123412345.
    Returns an integer for accurate small vs greater filtering comparisons.
    """
    try:
        return int(serial[3:7])
    except (ValueError, IndexError):
        return 0

def safe_decimal_parse(val):
    """
    Safely parses any input value into a Decimal to preserve extreme precision.
    """
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError):
        return Decimal('0')

def get_common_mint_data():
    amount_raw = input("Enter Denomination Amount (e.g., 100 or 1.00000000000000000001): ").strip()
    amount = str(safe_decimal_parse(amount_raw))
    
    is_forever = input("Is this a Forever Note? (y/n): ").strip().lower()
    if is_forever == 'y':
        note_type = "Forever PLC"
        expiry = "N/A (Never Expires)"
        img_path = f"images/plc_{amount}_forever.jpg"
    else:
        note_type = "Time Limited PLC"
        expiry = input("Enter Expiry Date (e.g., '15 June 2026'): ").strip()
        img_path = f"images/plc_{amount}_limited.jpg"

    area = input("Enter Local Area / Issued To: ").strip()
    status = select_status()
    
    return amount, note_type, expiry, img_path, area, status

def main():
    db = load_db()

    while True:
        print("\n" + "="*50)
        print("   PLONHFG CENTRAL BANK - ERP ROOT ACCESS v6.0")
        print("="*50)
        print("1. [MINT] Single Note Generation")
        print("2. [BULK MINT] Mass Assembly Line")
        print("3. [PDF MINT] Batch PDF Generation")
        print("4. [MOVE] Update Location (Single/Bulk)")
        print("5. [SECURE] Adjust Threat Status (Single/Bulk)")
        print("6. [QA] Mint Correction (Fix Prefix Collisions)")
        print("7. [DASHBOARD] Hierarchical Asset Analytics")
        print("8. [FILTER] Advanced Dashboard (Filter by Location & Batch)")
        print("9. [DUMP] View Raw JSON Ledger")
        print("10. [EDIT] Modify Existing Note Details")
        print("11. [EXIT] Save and Shutdown Terminal")
        print("="*50)
        
        choice = input("root@plonhfg-vault:~# Select Operation: ")

        if choice == '1':
            print("\n--- SINGLE MINT PROTOCOL ---")
            batch_code = input("Enter 3-Letter Batch Code (e.g., ABC): ").strip().upper()
            note_num = input("Enter 4-Digit Note Sequence (e.g., 45): ").strip().zfill(4)
            nonce = str(random.randint(10000, 99999))
            serial = f"{batch_code}{note_num}{nonce}"
            
            if serial in db:
                print("[!] ERROR: Hash collision!")
                continue
                
            amount, note_type, expiry, img_path, area, status = get_common_mint_data()
            
            db[serial] = {
                "amount": amount,
                "type": note_type,
                "expiryDate": expiry,
                "localArea": area,
                "fraudStatus": status,
                "imagePath": img_path
            }
            save_db(db)
            print("\n" + "="*40)
            print(f" MINT SUCCESS! SERIAL TO WRITE:")
            print(f" ---> {serial} <---")
            print("="*40)
            input("\n[SYSTEM PAUSE] Write this exact serial on the physical note. Press ENTER when done...")

        elif choice == '2':
            print("\n--- BULK MINT ASSEMBLY LINE ---")
            batch_code = input("Enter 3-Letter Batch Code (e.g., ABC): ").strip().upper()
            start_num = int(input("Enter STARTING Note Number (1-9999): ").strip())
            end_num = int(input("Enter ENDING Note Number (1-9999): ").strip())

            print("\n[CONFIGURE MASTER PAYLOAD]")
            amount, note_type, expiry, img_path, area, status = get_common_mint_data()

            success_count = 0
            generated_serials = []

            for i in range(start_num, end_num + 1):
                note_num = str(i).zfill(4)
                nonce = str(random.randint(10000, 99999))
                serial = f"{batch_code}{note_num}{nonce}"

                if serial not in db:
                    db[serial] = {
                        "amount": amount,
                        "type": note_type,
                        "expiryDate": expiry,
                        "localArea": area,
                        "fraudStatus": status,
                        "imagePath": img_path
                    }
                    generated_serials.append(serial)
                    success_count += 1

            save_db(db)
            print("\n" + "="*40)
            print(f" BULK MINT COMPLETE: {success_count} NOTES")
            print("="*40)
            for s in generated_serials:
                print(f" [ ] {s}")
            print("="*40)
            input("\n[SYSTEM PAUSE] Copy these serials to your physical batch. Press ENTER when finished...")

        elif choice == '3':
            if not REPORTLAB_AVAILABLE:
                print("[!] ERROR: PDF MINT requires reportlab library.")
                print("[!] Install with: pip install reportlab")
                input("\n[SYSTEM] Press ENTER to continue...")
                continue

            print("\n--- PDF BATCH MINT GENERATION ---")
            note_category = input("Is this Old or New batch? (old/new): ").strip().lower()
            if note_category not in ['old', 'new']:
                print("[!] ERROR: Please enter 'old' or 'new'")
                continue

            batch_size = 10 if note_category == 'old' else 8
            batch_code = input("Enter 3-Letter Batch Code (e.g., ABC): ").strip().upper()
            amount_raw = input("Enter Denomination Amount (e.g., 100): ").strip()
            amount = str(safe_decimal_parse(amount_raw))

            is_forever = input("Is this a Forever Note? (y/n): ").strip().lower()
            if is_forever == 'y':
                note_type = "Forever PLC"
                forever_status_key = "Forever PLC"
            else:
                note_type = "Time Limited PLC"
                forever_status_key = "Time Limited PLC"

            area = input("Enter Local Area / Issued To: ").strip()
            status = select_status()
            img_path = f"images/plc_{amount}_{('forever' if is_forever == 'y' else 'limited')}.jpg"

            num_notes = int(input("Enter total number of notes to generate: ").strip())

            output_dir = create_directory_structure(note_category, forever_status_key, amount)

            success_count = 0
            generated_serials = []
            batch_num = 1
            current_batch = []

            for i in range(1, num_notes + 1):
                note_num = str(i).zfill(4)
                nonce = str(random.randint(10000, 99999))
                serial = f"{batch_code}{note_num}{nonce}"

                if serial not in db:
                    db[serial] = {
                        "amount": amount,
                        "type": note_type,
                        "expiryDate": "N/A (Never Expires)" if is_forever == 'y' else input(f"Enter Expiry Date for batch [{i}/{num_notes}] (e.g., '15 June 2026'): ").strip(),
                        "localArea": area,
                        "fraudStatus": status,
                        "imagePath": img_path
                    }
                    generated_serials.append(serial)
                    current_batch.append(serial)
                    success_count += 1

                    if len(current_batch) == batch_size or i == num_notes:
                        if generate_pdf_batch(batch_num, current_batch, output_dir, batch_code):
                            print(f"[+] PDF created: batch_{batch_code}_{batch_num:03d}.pdf ({len(current_batch)} serials)")
                        batch_num += 1
                        current_batch = []

            save_db(db)
            print("\n" + "="*40)
            print(f" PDF BATCH MINT COMPLETE: {success_count} NOTES")
            print(f" Location: {output_dir}")
            print("="*40)
            print(" Generated Serials:")
            for s in generated_serials:
                print(f" {s}")
            print("="*40)
            input("\n[SYSTEM PAUSE] PDFs generated successfully. Press ENTER to continue...")

        elif choice == '4':
            print("\n--- ASSET ROUTING (SINGLE/BULK) ---")
            serials = input("Enter Serial Codes (comma separated): ").strip().split(',')
            new_area = input("Enter New Location / State Bank: ").strip()

            count = 0
            for s in serials:
                s = s.strip()
                if s in db:
                    db[s]['localArea'] = new_area
                    count += 1
                else:
                    print(f"[!] 404: {s} Not Found.")
            print(f"[+] ROUTING SUCCESS: {count} assets moved to {new_area}.")
            save_db(db)

        elif choice == '5':
            print("\n--- THREAT STATUS ADJUSTER (SINGLE/BULK) ---")
            serials = input("Enter Serial Codes (comma separated): ").strip().split(',')
            status = select_status()

            count = 0
            for s in serials:
                s = s.strip()
                if s in db:
                    db[s]['fraudStatus'] = status
                    count += 1
                else:
                    print(f"[!] 404: {s} Not Found.")
            print(f"[+] SECURITY OVERRIDE: {count} assets updated to '{status}'.")
            save_db(db)

        elif choice == '6':
            print("\n--- MINT CORRECTION QA (Orphan Node Sweeper) ---")
            prefix_map = defaultdict(list)
            for serial in db.keys():
                prefix = serial[:7] # AAA + 1234 covers the printing batch identifier
                prefix_map[prefix].append(serial)

            collisions_found = False
            for prefix, serial_list in prefix_map.items():
                if len(serial_list) > 1:
                    collisions_found = True
                    print(f"\n[!] COLLISION DETECTED for Physical Note: {prefix}")
                    for idx, s in enumerate(serial_list):
                        print(f"  [{idx + 1}] {s} (Area: {db[s].get('localArea', '')}, Status: {db[s].get('fraudStatus', '')})")

                    keep_idx = input(f"Which one is the REAL physical note? (1-{len(serial_list)}, or 'skip'): ").strip()
                    if keep_idx.isdigit() and 1 <= int(keep_idx) <= len(serial_list):
                        real_serial = serial_list[int(keep_idx) - 1]
                        for s in serial_list:
                            if s != real_serial:
                                del db[s]
                                print(f"[-] PURGED ghost record: {s}")

            if not collisions_found:
                print("[+] SYSTEM CLEAN: No physical note collisions detected.")
            else:
                save_db(db)

        elif choice == '7':
            print("\n" + "="*50)
            print("   MACRO-ECONOMIC DASHBOARD v3.0 (HIGH-PRECISION)")
            print("="*50)

            total_notes = len(db)
            total_value = Decimal('0')

            grouped_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

            for serial, data in db.items():
                amt = safe_decimal_parse(data.get('amount', 0))
                total_value += amt

                is_forever = "Yes" if "Forever" in data.get('type', '') else "No (Time Limited)"
                batch = serial[:3]

                grouped_data[is_forever][amt][batch].append(serial)

            print(f"TOTAL CIRCULATING SUPPLY: {total_value} PLC across {total_notes} notes.\n")

            for forever_status in sorted(grouped_data.keys(), reverse=True):
                print(f"■ FOREVER STATUS: {forever_status}")
                for amt in sorted(grouped_data[forever_status].keys(), reverse=True):
                    print(f"  ├─ Denomination: {amt} PLC")
                    for batch in sorted(grouped_data[forever_status][amt].keys()):
                        serials = grouped_data[forever_status][amt][batch]
                        print(f"  │  ├─ Batch Group [{batch}]")
                        
                        # Sorted purely by the 4-digit serial print sequence (ignoring the random 5 digits)
                        sorted_serials = sorted(serials, key=get_print_number)
                        for s in sorted_serials:
                            print(f"  │  │   - {s}")
                        print(f"  │  │  (Total count for {batch}: {len(serials)})")
                print("  │")

            input("\n[SYSTEM] Press ENTER to return to the main menu...")

        elif choice == '8':
            print("\n" + "="*50)
            print("   ADVANCED FILTER DASHBOARD (HIGH-PRECISION)")
            print("="*50)

            batches = sorted(set(serial[:3] for serial in db.keys()))
            locations = sorted(set(entry.get('localArea', '') for entry in db.values()))

            print("\nAvailable Batches:", ", ".join(batches))
            print("Available Locations:", ", ".join(locations))

            batch_filter = input("\nFilter by Batch (leave empty for all): ").strip().upper()
            location_filter = input("Filter by Location (leave empty for all): ").strip()

            filtered_notes = []
            for serial, data in db.items():
                batch = serial[:3]
                location = data.get('localArea', '')

                batch_match = not batch_filter or batch == batch_filter
                location_match = not location_filter or location == location_filter

                if batch_match and location_match:
                    filtered_notes.append((serial, data))

            if not filtered_notes:
                print("\n[!] No notes found matching the filters.")
            else:
                print("\n" + "="*50)
                print(f"   FILTER RESULTS: {len(filtered_notes)} NOTE(S) FOUND")
                print("="*50)

                # Track metrics using Decimal and 4-digit print rules
                batch_stats = defaultdict(lambda: {'count': 0, 'max_amount': Decimal('0'), 'max_serial': '', 'type': '', 'max_print_num': -1})
                
                for serial, data in filtered_notes:
                    batch = serial[:3]
                    batch_stats[batch]['count'] += 1
                    amount = safe_decimal_parse(data.get('amount', 0))
                    print_num = get_print_number(serial)

                    # Check highest denomination, then highest print sequence code if amounts are tied
                    if amount > batch_stats[batch]['max_amount'] or \
                       (amount == batch_stats[batch]['max_amount'] and print_num > batch_stats[batch]['max_print_num']):
                        batch_stats[batch]['max_amount'] = amount
                        batch_stats[batch]['max_serial'] = serial
                        batch_stats[batch]['type'] = data.get('type', '')
                        batch_stats[batch]['max_print_num'] = print_num

                print("\n[ BATCH SUMMARY ]")
                print(f"{'Batch':<8} {'Count':<8} {'Max Denom':<25} {'Highest Serial':<20} {'Type':<20}")
                print("-" * 85)
                for batch in sorted(batch_stats.keys()):
                    stats = batch_stats[batch]
                    print(f"{batch:<8} {stats['count']:<8} {str(stats['max_amount']):<25} {stats['max_serial']:<20} {stats['type']:<20}")

                print("\n[ DETAILED NOTES LIST ]")
                print(f"{'Serial':<15} {'Amount':<25} {'Type':<20} {'Status':<30} {'Location':<15}")
                print("-" * 110)

                # Sorting via Decimal amount value then print sequence number
                sorted_notes = sorted(
                    filtered_notes, 
                    key=lambda x: (safe_decimal_parse(x[1].get('amount', 0)), get_print_number(x[0])), 
                    reverse=True
                )
                for serial, data in sorted_notes:
                    amount = data.get('amount', 0)
                    note_type = data.get('type', '')
                    status = data.get('fraudStatus', '')
                    location = data.get('localArea', '')
                    print(f"{serial:<15} {str(amount):<25} {note_type:<20} {status:<30} {location:<15}")

                total_value = sum(safe_decimal_parse(data.get('amount', 0)) for _, data in filtered_notes)
                print("-" * 110)
                print(f"TOTAL FILTERED VALUE: {total_value} PLC")

            input("\n[SYSTEM] Press ENTER to return to the main menu...")

        elif choice == '9':
            print("\n--- MASTER LEDGER DUMP ---")
            print(json.dumps(db, indent=4))
            print("--------------------------")
            input("\n[SYSTEM] Press ENTER to return to the main menu...")

        elif choice == '10':
            serial = input("Enter Serial Code to Modify: ").strip()
            if serial in db:
                print("\n[SYSTEM] Press ENTER to keep current data, or type new data.")
                for key in db[serial].keys():
                    new_val = input(f"Update {key} [{db[serial][key]}]: ").strip()
                    if new_val != "":
                        if key == "amount":
                            db[serial][key] = str(safe_decimal_parse(new_val))
                        else:
                            db[serial][key] = new_val
                print(f"[+] OVERWRITE SUCCESS: {serial} updated.")
                save_db(db)
            else:
                print("[!] ERROR: 404 Serial Not Found.")

        elif choice == '11':
            save_db(db)
            print("Shutting down ERP interface. Goodbye, Lead SysAdmin.")
            break
            
        else:
            print("[!] Invalid command.")

if __name__ == "__main__":
    clear_screen()
    main()