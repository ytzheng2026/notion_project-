import sys
from notion_client import Client
import os
from dotenv import load_dotenv

def get_notion_client():
    print("=" * 70)
    print("[INIT] Loading Notion API credentials...")
    load_dotenv(dotenv_path=".mcp_env")
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("[ERROR] EVAL_NOTION_API_KEY not found!")
        sys.exit(1)
    print("[OK] API key loaded.")
    return Client(auth=api_key)

def get_block_text(block):
    type_ = block.get("type", "")
    if type_ in block and "rich_text" in block[type_]:
        return "".join([t["plain_text"] for t in block[type_]["rich_text"]])
    return ""

def get_all_blocks_recursively(notion: Client, block_id: str):
    all_blocks = []
    try:
        resp = notion.blocks.children.list(block_id=block_id)
        results = resp.get("results", [])
        all_blocks.extend(results)
        for b in results:
            if b.get("has_children"):
                all_blocks.extend(get_all_blocks_recursively(notion, b["id"]))
    except Exception as e:
        print(f"  [WARN] Error fetching children: {e}")
    return all_blocks

def verify_task(notion: Client, config: dict):
    print("\n" + "=" * 70)
    print(f"[START] Verification: {config['child_page_title']}")
    print("=" * 70)
    
    total_checks = 0
    passed_checks = 0

    # CHECK 1: Find Main Page "Company In A Box"
    total_checks += 1
    print(f"\n[CHECK 1] Find Main Page 'Company In A Box'")
    
    try:
        res = notion.search(query="Company In A Box", filter={"property": "object", "value": "page"}).get("results", [])
    except Exception as e:
        print(f"  [ERROR] Search failed: {e}")
        return False
    
    main_page = None
    for p in res:
        if p.get("properties") and "title" in p["properties"]:
            title_list = p["properties"]["title"]["title"]
            if title_list:
                title = "".join([t["plain_text"] for t in title_list])
                if title == "Company In A Box":
                    main_page = p
                    break
    
    if not main_page:
        print(f"  [FAIL] 'Company In A Box' main page not found.")
        return False
    
    main_id = main_page["id"]
    print(f"  [PASS] Main page found.")
    passed_checks += 1

    # CHECK 2: Find Child Page
    total_checks += 1
    print(f"\n[CHECK 2] Find Child Page '{config['child_page_title']}'")
    
    try:
        children = notion.blocks.children.list(block_id=main_id).get("results", [])
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    
    child_page = None
    for b in children:
        if b["type"] == "child_page":
            child_title = b["child_page"]["title"]
            if config['child_page_title'] == child_title:
                child_page = b
                break
    
    if not child_page:
        print(f"  [FAIL] Child page '{config['child_page_title']}' not found.")
        return False
    
    page_id = child_page["id"]
    print(f"  [PASS] Child page found.")
    passed_checks += 1

    # Fetch all content
    print(f"\n[INFO] Fetching page content...")
    page_blocks = get_all_blocks_recursively(notion, page_id)
    print(f"[INFO] Fetched {len(page_blocks)} blocks.")

    indices = {}

    # CHECK 3: Projects Database (Inline)
    total_checks += 1
    print(f"\n[CHECK 3] Validating 'Projects' Inline Database")
    
    found_db = False
    db_index = -1
    for i, b in enumerate(page_blocks):
        if b["type"] == "child_database":
             title = b["child_database"]["title"]
             if title == "Projects":
                 found_db = True
                 db_index = i
                 break
    
    if found_db:
        print(f"  [PASS] 'Projects' database found.")
        indices['db'] = db_index
        print(f"  [NODE] child_database index={db_index} id={page_blocks[db_index]['id']}")
        passed_checks += 1
    else:
        print(f"  [FAIL] 'Projects' inline database missing.")

    # CHECK 4: Dashboard Header (Blue Callout)
    total_checks += 1
    print(f"\n[CHECK 4] Validating Dashboard Header (Blue Callout)")
    
    found_header = False
    header_index = -1
    for i, b in enumerate(page_blocks):
        if b["type"] == "callout":
            color = b["callout"].get("color", "")
            text = get_block_text(b)
            icon = b["callout"].get("icon", {})
            emoji = icon.get("emoji", "")
            
            # Text check might be partial match or strict
            if "blue" in color and config['header_text'] in text and emoji == "📊":
                found_header = True
                header_index = i
                break
    
    if found_header:
        print(f"  [PASS] Dashboard Header found.")
        indices['header'] = header_index
        print(f"  [NODE] callout index={header_index} id={page_blocks[header_index]['id']}")
        passed_checks += 1
    else:
        print(f"  [FAIL] Dashboard Header missing or incorrect (Expected: Blue, 📊, '{config['header_text']}').")

    # CHECK 5: Capacity Meter (Quote)
    total_checks += 1
    print(f"\n[CHECK 5] Validating Capacity Meter (Quote)")
    
    found_quote = False
    quote_index = -1
    for i, b in enumerate(page_blocks):
        if b["type"] == "quote":
            text = get_block_text(b)
            if config['quote_text'] in text:
                found_quote = True
                quote_index = i
                break
                
    if found_quote:
        print(f"  [PASS] Capacity Meter Quote found.")
        indices['quote'] = quote_index
        print(f"  [NODE] quote index={quote_index} id={page_blocks[quote_index]['id']}")
        passed_checks += 1
    else:
        print(f"  [FAIL] Capacity Meter Quote missing or incorrect (Expected: '{config['quote_text']}').")

    # CHECK 6: Strict Order
    total_checks += 1
    print(f"\n[CHECK 6] Verifying Logic Order")
    
    key_indices = [
        indices.get('db', -1),
        indices.get('header', -1),
        indices.get('quote', -1)
    ]
    
    present_indices = [idx for idx in key_indices if idx != -1]
    
    if present_indices == sorted(present_indices) and len(present_indices) > 0:
         print(f"  [PASS] Block order is correct: {present_indices}")
         passed_checks += 1
    else:
         print(f"  [FAIL] Block order is incorrect: {present_indices}")

    total_checks += 1
    print(f"\n[CHECK 7] Validating Database Schema Properties")
    schema_ok = False
    try:
        if 'db' in indices:
            db_block = page_blocks[indices['db']]
            db_id = db_block['id']
            db_schema = notion.databases.retrieve(db_id)
            props = db_schema.get('properties', {})
            name_ok = False
            status_ok = False
            owner_ok = False
            start_ok = False
            end_ok = False
            hours_ok = False
            if 'Name' in props and props['Name'].get('type') == 'title':
                name_ok = True
                print(f"  [NODE] property Name id={props['Name'].get('id','')} type=title")
            if 'Status' in props and props['Status'].get('type') == 'select':
                options = [o.get('name') for o in props['Status']['select'].get('options', [])]
                must = ["Not started", "In progress", "Done"]
                if all(m in options for m in must):
                    status_ok = True
                print(f"  [NODE] property Status id={props['Status'].get('id','')} type=select options={options}")
            if 'Owner' in props and props['Owner'].get('type') == 'people':
                owner_ok = True
                print(f"  [NODE] property Owner id={props['Owner'].get('id','')} type=people")
            if 'Start Date' in props and props['Start Date'].get('type') == 'date':
                start_ok = True
                print(f"  [NODE] property Start Date id={props['Start Date'].get('id','')} type=date")
            if 'End Date' in props and props['End Date'].get('type') == 'date':
                end_ok = True
                print(f"  [NODE] property End Date id={props['End Date'].get('id','')} type=date")
            if 'Effort Hours' in props and props['Effort Hours'].get('type') == 'number':
                hours_ok = True
                print(f"  [NODE] property Effort Hours id={props['Effort Hours'].get('id','')} type=number")
            schema_ok = all([name_ok, status_ok, owner_ok, start_ok, end_ok, hours_ok])
    except Exception as e:
        print(f"  [ERROR] Schema retrieval failed: {e}")
        schema_ok = False
    if schema_ok:
        print("  [PASS] Database schema strictly verified.")
        passed_checks += 1
    else:
        print("  [FAIL] Database schema mismatch or missing properties.")

    total_checks += 1
    print(f"\n[CHECK 8] Validating Computed Formulas")
    formula_ok = False
    try:
        if 'db' in indices:
            db_block = page_blocks[indices['db']]
            db_id = db_block['id']
            db_schema = notion.databases.retrieve(db_id)
            props = db_schema.get('properties', {})
            dr = props.get('Days Remaining')
            pb = props.get('Progress Bar')
            dr_ok = False
            pb_ok = False
            if dr and dr.get('type') == 'formula':
                expr = dr['formula'].get('expression', '').strip()
                print(f"  [NODE] property Days Remaining id={dr.get('id','')} type=formula")
                if expr == config['days_remaining_formula'].strip():
                    dr_ok = True
            if pb and pb.get('type') == 'formula':
                expr = pb['formula'].get('expression', '').strip()
                print(f"  [NODE] property Progress Bar id={pb.get('id','')} type=formula")
                if expr == config['progress_bar_formula'].strip():
                    pb_ok = True
            formula_ok = dr_ok and pb_ok
    except Exception as e:
        print(f"  [ERROR] Formula retrieval failed: {e}")
        formula_ok = False
    if formula_ok:
        print("  [PASS] Computed formulas strictly verified.")
        passed_checks += 1
    else:
        print("  [FAIL] Computed formulas mismatch or missing.")

    total_checks += 1
    print(f"\n[CHECK 9] Validating Sample Records")
    records_ok = True
    try:
        if 'db' in indices:
            db_block = page_blocks[indices['db']]
            db_id = db_block['id']
            pages = notion.databases.query(database_id=db_id).get('results', [])
            by_name = {}
            for pg in pages:
                props = pg.get('properties', {})
                nm = props.get('Name', {}).get('title', [])
                nm_text = ''.join([t.get('plain_text','') for t in nm])
                by_name[nm_text] = pg
            for rec in config['records']:
                name = rec['Name']
                expected = rec
                if name not in by_name:
                    print(f"  [FAIL] Missing record: {name}")
                    records_ok = False
                    continue
                pg = by_name[name]
                pid = pg.get('id')
                print(f"  [NODE] page '{name}' id={pid}")
                p = pg.get('properties', {})
                st = p.get('Status', {}).get('select')
                st_name = st.get('name') if st else None
                if st_name != expected['Status']:
                    print(f"  [FAIL] Status mismatch for {name}: got {st_name} expected {expected['Status']}")
                    records_ok = False
                dt = p.get('Start Date', {}).get('date')
                sd = dt.get('start') if dt else None
                if expected['Start'] == '—':
                    if sd is not None:
                        print(f"  [FAIL] Start Date should be empty for {name}")
                        records_ok = False
                else:
                    if sd != expected['Start']:
                        print(f"  [FAIL] Start Date mismatch for {name}: got {sd} expected {expected['Start']}")
                        records_ok = False
                dt2 = p.get('End Date', {}).get('date')
                ed = dt2.get('end') if dt2 and dt2.get('end') else (dt2.get('start') if dt2 else None)
                if expected['End'] == '—':
                    if ed is not None:
                        print(f"  [FAIL] End Date should be empty for {name}")
                        records_ok = False
                else:
                    if ed != expected['End']:
                        print(f"  [FAIL] End Date mismatch for {name}: got {ed} expected {expected['End']}")
                        records_ok = False
                eh = p.get('Effort Hours', {}).get('number')
                if eh != expected['Hours']:
                    print(f"  [FAIL] Effort Hours mismatch for {name}: got {eh} expected {expected['Hours']}")
                    records_ok = False
    except Exception as e:
        print(f"  [ERROR] Records retrieval failed: {e}")
        records_ok = False
    if records_ok:
        print("  [PASS] Sample records strictly verified.")
        passed_checks += 1
    else:
        print("  [FAIL] Sample records mismatch or missing.")

    # CHECK 7: Model Version Control (GitGraph)
    total_checks += 1
    print(f"\n[CHECK 7] Validating Model Version Control (GitGraph)")
    
    found_git = False
    for b in page_blocks:
        if b["type"] == "code" and b["code"].get("language") == "mermaid":
            text = get_block_text(b)
            # PEDANTIC CHECK: Exact byte match
            if text.strip() == config['gitgraph_code'].strip():
                found_git = True
                print(f"  [NODE] mermaid id={b.get('id')}")
                break
    
    if found_git:
        print(f"  [PASS] GitGraph strictly verified.")
        passed_checks += 1
    else:
        print(f"  [FAIL] GitGraph mismatch or missing.")

    # CHECK 8: Loss Convergence (LaTeX)
    total_checks += 1
    print(f"\n[CHECK 8] Validating Loss Convergence (LaTeX)")
    
    found_latex = False
    for b in page_blocks:
        if b["type"] == "equation":
            expression = b["equation"].get("expression", "")
            # PEDANTIC CHECK: Exact byte match
            if expression.strip() == config['loss_latex'].strip():
                found_latex = True
                print(f"  [NODE] equation id={b.get('id')}")
                break
                
    if found_latex:
        print(f"  [PASS] Loss Function strictly verified.")
        passed_checks += 1
    else:
        print(f"  [FAIL] Loss Function LaTeX mismatch or missing.")

    # FINAL SUMMARY
    print("\n" + "=" * 70)
    print(f"[SUMMARY] {config['child_page_title']}")
    print(f"  Passed: {passed_checks}/{total_checks}")
    print("=" * 70)
    
    return passed_checks == total_checks

def main():
    notion = get_notion_client()
    
    config = {
        "child_page_title": "Data Science Tracker",
        "header_text": "**Data Science Dashboard** | Total Effort: 240 hours | Active: 2",
        "quote_text": "Team Capacity: 160h/sprint | Utilization: 150%",
        "days_remaining_formula": """if(empty(prop(\"End Date\")), \"—\",
          let(rem, dateBetween(prop(\"End Date\"), now(), \"days\"),
            if(rem < 0, \"🔴 \" + format(abs(rem)) + \"d late\",
              if(rem <= 3, \"🟡 \" + format(rem) + \"d\",
                \"🟢 \" + format(rem) + \"d\"))))""",
        "progress_bar_formula": """if(prop(\"Status\") == \"Done\", \"██████████ 100%\",
          if(prop(\"Status\") == \"In progress\", \"█████░░░░░ 50%\", \"░░░░░░░░░░ 0%\"))""",
        "records": [
            {"Name": "ML Pipeline", "Status": "In progress", "Start": "2026-01-10", "End": "2026-01-25", "Hours": 120},
            {"Name": "Data Lake", "Status": "In progress", "Start": "2026-01-05", "End": "2026-01-20", "Hours": 80},
            {"Name": "Dashboards", "Status": "Not started", "Start": "—", "End": "—", "Hours": 40}
        ],
        "gitgraph_code": """gitGraph
   commit id: "Init"
   branch experiment
   checkout experiment
   commit id: "Train_v1"
   commit id: "Eval_v1"
   checkout main
   merge experiment
   commit id: "Deploy_v1"
""",
        "loss_latex": r"\lim_{epoch \to \infty} \mathcal{L}(\theta) = 0"
    }
    
    success = verify_task(notion, config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
