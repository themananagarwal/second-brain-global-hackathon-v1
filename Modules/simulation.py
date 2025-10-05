# Modules/simulation.py
# ------------------------------------------------------------
# Day-by-day simulation with:
# - Robust date parsing (auto dayfirst detection)
# - Removes literal "MDF" token from Particular in sales
# - Reorder triggers using ROP + target cover (mu*45 + safety_stock)
# - Integer inventories (no fractional pieces)
# - Backorders persist and count towards order sizing
# - 10–12 ton batching; packs items by needed weight
# - Daily summaries + backorder ratios (today + cumulative)
# - Full inventory print at each order prompt
# - Writes final inventory and daily summary CSVs
# ------------------------------------------------------------

import os, sys, math, re
from collections import defaultdict
from typing import Dict, List
import numpy as np
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------
SALES_FILE     = "data/AprJun2024.csv"
INVENTORY_FILE = "data/latest_inventory.csv"
ROP_FILE       = "data/reorder_evaluation.csv"
EOQ_FILE       = "outputs/eoq_results.csv"

TRUCK_MIN_TONS = 10
TRUCK_MAX_TONS = 12
DEFAULT_LEAD_DAYS = 7
INTERACTIVE = True

# -----------------------------
# Helpers
# -----------------------------
def as_int(x) -> int:
    """Coerce to non-negative whole pieces."""
    try:
        return max(0, int(math.floor(float(x) + 1e-9)))
    except Exception:
        return 0

def clean_particular_mdf(name: str) -> str:
    """Remove the literal token 'MDF' appearing between thickness and spec."""
    if not isinstance(name, str):
        return name
    # Remove standalone MDF token (surrounded by word boundaries/spaces)
    return re.sub(r"\bMDF\b\s*", "", name.strip(), flags=re.IGNORECASE)

def piece_weight_kg(sku: str, weight_map: Dict[str, float]) -> float:
    """Return per-piece weight in kg; fallback thickness*2.24 if not provided."""
    if sku in weight_map and weight_map[sku] > 0:
        return float(weight_map[sku])
    m = re.search(r'(\d+(?:\.\d+)?)\s*MM', (sku or "").upper())
    if m:
        return float(m.group(1)) * 2.24
    return 40.0  # conservative fallback

def qty_to_tons(sku, q, weight_map):
    return (piece_weight_kg(sku, weight_map) * as_int(q)) / 1000.0

def print_full_inventory(title: str,
                         skus: List[str],
                         on_hand: dict,
                         on_order: dict,
                         backorders: dict,
                         rop_map: dict,
                         mu_map: dict,
                         ss_map: dict,
                         weight_map: dict):
    """Print all SKUs sorted by 'needed weight' descending."""
    rows = []
    for s in skus:
        ip = as_int(on_hand[s] + on_order[s] - backorders[s])
        target = mu_map[s] * 45 + ss_map[s]
        gap = max(0.0, target - ip)
        needed_units = as_int(backorders[s]) + as_int(gap)
        need_tons = qty_to_tons(s, needed_units, weight_map)
        rows.append((s, as_int(on_hand[s]), as_int(on_order[s]), as_int(backorders[s]),
                     ip, as_int(rop_map[s]), need_tons))

    rows.sort(key=lambda r: r[6], reverse=True)

    print(f"\n📦 {title} (sorted by needed weight):")
    print(" SKU".ljust(22), "| on_hand".rjust(9), "on_order".rjust(9), "backorder".rjust(10),
          "| IP".rjust(6), "ROP".rjust(6), "| need_tons".rjust(11))
    for s, oh, oo, bo, ip, rp, nt in rows:
        print(f" {s[:22].ljust(22)} | {str(oh).rjust(7)} {str(oo).rjust(8)} {str(bo).rjust(9)} |"
              f" {str(ip).rjust(4)} {str(rp).rjust(5)} | {nt:>9.2f}")

# -----------------------------
# Robust date parsing
# -----------------------------
def _smart_parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates without dropping rows; auto-detect dayfirst using a heuristic."""
    raw = series.astype(str).str.strip().str.replace(r"[./]", "-", regex=True)

    dt_us = pd.to_datetime(raw, errors="coerce", dayfirst=False)  # mm-dd
    dt_eu = pd.to_datetime(raw, errors="coerce", dayfirst=True)   # dd-mm

    def score(dt: pd.Series) -> tuple:
        v = dt.dropna()
        if v.empty:
            return (-1_000_000, 0.0)
        span = (v.max() - v.min()).days
        conc = v.dt.to_period("M").value_counts(normalize=True).head(3).sum()
        return (-span, conc)

    su, se = score(dt_us), score(dt_eu)
    choose_eu = se > su
    chosen = dt_eu if choose_eu else dt_us

    v = chosen.dropna()
    if not v.empty:
        print(
            f"🗓 Date parse chosen: dayfirst={choose_eu} | "
            f"window {v.min().date()} → {v.max().date()} "
            f"(span={(v.max()-v.min()).days} days)"
        )
    else:
        print("🗓 WARNING: no valid dates parsed; please check the file formatting.")
    return chosen

# -----------------------------
# Core simulation
# -----------------------------
def simulate(interactive: bool = INTERACTIVE):
    os.makedirs("data", exist_ok=True)

    # Load inputs
    sales = pd.read_csv(SALES_FILE)
    inv   = pd.read_csv(INVENTORY_FILE)
    rop   = pd.read_csv(ROP_FILE)
    eoq   = pd.read_csv(EOQ_FILE)

    # Normalize columns
    for df in (sales, inv, rop, eoq):
        df.columns = df.columns.str.strip()

    # Sales column normalization
    if "Particulars" in sales.columns:
        sales = sales.rename(columns={"Particulars": "Particular"})
    if "Quantity_Sold" in sales.columns and "Quantity" not in sales.columns:
        sales = sales.rename(columns={"Quantity_Sold": "Quantity"})

    # Remove literal 'MDF' token from Particulars in the SALES file only
    sales["Particular"] = sales["Particular"].astype(str).apply(clean_particular_mdf)

    # Parse dates robustly
    sales["Date"] = _smart_parse_dates(sales["Date"])
    parsed_mask = sales["Date"].notna()
    if not parsed_mask.all():
        bad = (~parsed_mask).sum()
        print(f"⚠️ {bad} row(s) had unparseable dates; keeping rows but excluding them from the timeline.")

    # Build day range from parsed dates only
    if parsed_mask.any():
        start_d = sales.loc[parsed_mask, "Date"].min().normalize()
        end_d   = sales.loc[parsed_mask, "Date"].max().normalize()
    else:
        start_d = pd.Timestamp("2024-04-01")
        end_d   = pd.Timestamp("2024-06-30")

    all_days = pd.date_range(start_d, end_d, freq="D")

    # Aggregate demand (use parsed dates only)
    sales_parsed = sales.loc[parsed_mask].copy()
    demand = (
        sales_parsed
        .groupby(["Particular", sales_parsed["Date"].dt.normalize()])["Quantity"]
        .sum()
        .unstack(fill_value=0)
    ).reindex(columns=all_days, fill_value=0)

    # Build maps (note: keep names as-is from ROP/EOQ; they should match INVENTORY names)
    mu_map  = defaultdict(float, dict(zip(rop["Particular"], pd.to_numeric(rop["mu_daily"], errors="coerce").fillna(0))))
    ss_map  = defaultdict(float, dict(zip(rop["Particular"], pd.to_numeric(rop["safety_stock"], errors="coerce").fillna(0))))
    rop_map = defaultdict(float, dict(zip(rop["Particular"], pd.to_numeric(rop["reorder_point"], errors="coerce").fillna(0))))
    eoq_map = defaultdict(float, dict(zip( eoq["Particular"], pd.to_numeric( eoq["EOQ"], errors="coerce").fillna(0))))

    # Robust weight map (use provided column if present; else zeros)
    if "unit_weight" in eoq.columns:
        weight_series = pd.to_numeric(eoq["unit_weight"], errors="coerce").fillna(0)
    else:
        weight_series = pd.Series([0]*len(eoq), index=eoq.index)
    weight_map = defaultdict(float, dict(zip(eoq["Particular"], weight_series)))

    # State
    on_hand    = defaultdict(int, {r["Particular"]: as_int(r["Quantity"]) for _, r in inv.iterrows()})
    on_order   = defaultdict(int)
    backorders = defaultdict(int)
    pending_batch = defaultdict(int)
    pos_in_transit: List[Dict] = []

    # SKU universe (union of names across files)
    skus = sorted(set(demand.index) | set(inv["Particular"]) | set(rop["Particular"]) | set(eoq["Particular"]))

    # Daily logging
    daily_rows: List[Dict] = []

    # Cumulative trackers for fill-rate
    cum_demand = 0
    cum_shipped = 0

    # Utilities
    def inventory_position(sku):
        return as_int(on_hand[sku] + on_order[sku] - backorders[sku])

    def order_need_qty(sku):
        """Qty to order when triggered: backorders + gap-to-target, floored at EOQ."""
        ip = inventory_position(sku)
        target = mu_map[sku] * 45 + ss_map[sku]
        gap = max(0.0, target - ip)
        structural_need = as_int(backorders[sku]) + as_int(gap)
        return max(as_int(eoq_map[sku]), structural_need)

    def batch_tons(batch):
        return sum(qty_to_tons(s, q, weight_map) for s, q in batch.items())

    def propose_batch():
        """Pack items by needed weight until TRUCK_MAX_TONS."""
        if not pending_batch:
            return False, {}, 0.0
        items = sorted(pending_batch.items(), key=lambda x: -qty_to_tons(x[0], x[1], weight_map))
        total_pending = batch_tons(pending_batch)
        if total_pending < TRUCK_MIN_TONS:
            return False, {}, total_pending

        chosen: Dict[str, int] = {}
        total_tons = 0.0
        for s, q in items:
            q = as_int(q)
            if q <= 0:
                continue
            unit_kg = piece_weight_kg(s, weight_map)
            cur_tons = qty_to_tons(s, q, weight_map)
            if total_tons + cur_tons <= TRUCK_MAX_TONS:
                chosen[s] = q
                total_tons += cur_tons
            else:
                remaining_kg = max(0.0, TRUCK_MAX_TONS * 1000.0 - total_tons * 1000.0)
                allowed = as_int(remaining_kg / unit_kg) if unit_kg > 0 else 0
                if allowed > 0:
                    chosen[s] = allowed
                    total_tons += qty_to_tons(s, allowed, weight_map)
                break

        if total_tons >= TRUCK_MIN_TONS:
            return True, chosen, total_tons
        return False, {}, total_tons

    def place_order(today, proposal):
        """Create a PO; increase on_order now; receive after DEFAULT_LEAD_DAYS."""
        eta = today + pd.Timedelta(days=DEFAULT_LEAD_DAYS)
        for s, q in proposal.items():
            q = as_int(q)
            on_order[s] += q
        pos_in_transit.append({"eta": eta.normalize(), "items": proposal})
        print(f"🚛 Order placed ({today.date()}), ETA {eta.date()}, total {batch_tons(proposal):.2f} t")
        for s in list(proposal.keys()):
            pending_batch.pop(s, None)

    # -----------------------------
    # Simulation loop
    # -----------------------------
    for day in all_days:
        # Receive arrivals
        arrivals = [po for po in pos_in_transit if po["eta"] == day.normalize()]
        if arrivals:
            for po in arrivals:
                for s, q in po["items"].items():
                    q = as_int(q)
                    on_hand[s] += q
                    on_order[s] -= q
            pos_in_transit = [po for po in pos_in_transit if po["eta"] != day.normalize()]

        todays = demand.get(day, pd.Series(0, index=demand.index))

        # Day counters
        day_demand = 0
        day_shipped = 0
        triggered_today = []
        day_order_placed = False
        day_order_tons = 0.0

        # Process demand and triggers
        for s in skus:
            sold = as_int(todays.get(s, 0))
            if sold > 0:
                day_demand += sold
                if on_hand[s] >= sold:
                    on_hand[s] -= sold
                    day_shipped += sold
                else:
                    shipped = on_hand[s]
                    day_shipped += shipped
                    short = sold - shipped
                    on_hand[s] = 0
                    backorders[s] += short

            # Trigger check after shipping
            if inventory_position(s) <= rop_map[s]:
                need = order_need_qty(s)
                if need > 0:
                    prev = as_int(pending_batch[s])
                    if need > prev:
                        pending_batch[s] = need
                    if s not in triggered_today:
                        triggered_today.append(f"{s}:{as_int(need)}")

        # Update cumulative fill
        cum_demand += day_demand
        cum_shipped += day_shipped
        today_backordered = max(0, day_demand - day_shipped)
        today_bo_ratio = (today_backordered / day_demand * 100.0) if day_demand > 0 else 0.0
        open_backorders_units = int(sum(backorders.values()))
        cum_fill_rate = (cum_shipped / cum_demand * 100.0) if cum_demand > 0 else 100.0
        cum_bo_ratio = 100.0 - cum_fill_rate  # % of cumulative demand not shipped

        # Daily summary print
        pend_tons = batch_tons(pending_batch)
        print(f"\n=== {day.date()} ===")
        print(f"Demand: {day_demand} | Shipped: {day_shipped} | Triggers: {len(triggered_today)}")
        if triggered_today:
            print("Triggered today:", ", ".join(triggered_today[:8]) + (" ..." if len(triggered_today) > 8 else ""))
        print(f"Pending batch: {pend_tons:.2f} tons")
        print(f"Backordered today: {today_backordered} ({today_bo_ratio:.1f}%) | "
              f"Open BO: {open_backorders_units} | Cum fill rate: {cum_fill_rate:.1f}% "
              f"(Cum BO ratio: {cum_bo_ratio:.1f}%)")

        # Propose order if we can make a truck
        can_make, proposal, tons = propose_batch()
        if can_make:
            print(f"🔔 Batch ready: {tons:.2f} tons")
            print("Items:", ", ".join([f"{s}:{int(q)}" for s, q in proposal.items()]))

            # Full inventory BEFORE decision
            print_full_inventory("Inventory BEFORE order proposal", skus, on_hand, on_order, backorders,
                                 rop_map, mu_map, ss_map, weight_map)

            ans = "y" if not interactive else input("Place this order? [y/N]: ").strip().lower()
            if ans == "y":
                place_order(day, proposal)
                day_order_placed = True
                day_order_tons = tons

                # Full inventory AFTER decision
                print_full_inventory("Inventory AFTER order decision", skus, on_hand, on_order, backorders,
                                     rop_map, mu_map, ss_map, weight_map)
            else:
                print("   (Skipped; will keep accumulating.)")

        # Log daily row
        daily_rows.append({
            "Date": day.date().isoformat(),
            "demand_total": day_demand,
            "shipped_total": day_shipped,
            "backordered_today": today_backordered,
            "backorder_ratio_today_pct": round(today_bo_ratio, 2),
            "open_backorders_units": open_backorders_units,
            "cum_demand": cum_demand,
            "cum_shipped": cum_shipped,
            "cum_fill_rate_pct": round(cum_fill_rate, 2),
            "cum_backorder_ratio_pct": round(cum_bo_ratio, 2),
            "pending_batch_tons": round(pend_tons, 3),
            "triggers_count": len(triggered_today),
            "order_placed": day_order_placed,
            "order_tons": round(day_order_tons, 3) if day_order_placed else 0.0
        })

    # -----------------------------
    # End summary
    # -----------------------------
    final_inv = pd.DataFrame({
        "Particular": skus,
        "final_on_hand": [as_int(on_hand[s]) for s in skus],
        "on_order": [as_int(on_order[s]) for s in skus],
        "backorders": [as_int(backorders[s]) for s in skus],
    })
    final_inv.to_csv("data/sim_final_inventory.csv", index=False)

    daily_df = pd.DataFrame(daily_rows)
    daily_df.to_csv("data/sim_daily_summary.csv", index=False)

    overall_cum_fill = (daily_df["cum_shipped"].iloc[-1] / max(1, daily_df["cum_demand"].iloc[-1])) * 100.0
    overall_bo_ratio = 100.0 - overall_cum_fill

    print("\n✅ Simulation complete.")
    print(" - data/sim_final_inventory.csv")
    print(" - data/sim_daily_summary.csv")
    print(f"Overall cumulative fill rate: {overall_cum_fill:.2f}% | Overall BO ratio: {overall_bo_ratio:.2f}%")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.width", 220)
    simulate(interactive=INTERACTIVE)
