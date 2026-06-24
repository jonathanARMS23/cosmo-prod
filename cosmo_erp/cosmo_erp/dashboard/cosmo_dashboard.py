"""Méthodes de données pour les Cosmo Dashboard Charts — appelées par Frappe Dashboard."""
import frappe
from frappe.utils import add_days, nowdate, flt


@frappe.whitelist()
def get_sales_last_30_days():
    """Bar chart : CA quotidien sur les 30 derniers jours.

    Returns:
        dict: format Frappe chart {labels: [...], datasets: [{name, values}]}
    """
    end_date = nowdate()
    start_date = add_days(end_date, -29)

    rows = frappe.db.sql("""
        SELECT
            DATE(posting_date) AS day,
            COALESCE(SUM(grand_total), 0) AS revenue,
            COUNT(*) AS transactions
        FROM `tabSales Invoice`
        WHERE docstatus = 1
          AND posting_date BETWEEN %(start)s AND %(end)s
        GROUP BY DATE(posting_date)
        ORDER BY day
    """, {"start": start_date, "end": end_date}, as_dict=True)

    # Construit un dict date → valeurs pour combler les jours vides
    data_by_day = {str(r.day): (flt(r.revenue), int(r.transactions)) for r in rows}

    labels = []
    revenues = []
    transactions = []

    current = start_date
    for _ in range(30):
        labels.append(current[5:])  # "MM-DD"
        rev, txn = data_by_day.get(str(current), (0, 0))
        revenues.append(rev)
        transactions.append(txn)
        current = add_days(current, 1)

    return {
        "labels": labels,
        "datasets": [
            {"name": "CA (Ar)", "values": revenues},
            {"name": "Transactions", "values": transactions},
        ],
    }


@frappe.whitelist()
def get_top_products(limit=10, period="month"):
    """Pie chart : top produits par CA sur la période.

    Args:
        limit: nombre de produits (défaut 10)
        period: "today" | "week" | "month" | "year"

    Returns:
        dict: format Frappe chart {labels, datasets}
    """
    date_clause, date_params = _get_date_filter(period)

    rows = frappe.db.sql(f"""
        SELECT
            sii.item_name,
            SUM(sii.amount) AS total_revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.docstatus = 1
          AND si.posting_date {date_clause}
        GROUP BY sii.item_code
        ORDER BY total_revenue DESC
        LIMIT %(limit)s
    """, {**date_params, "limit": int(limit)}, as_dict=True)

    return {
        "labels": [r.item_name for r in rows],
        "datasets": [{"name": "CA", "values": [flt(r.total_revenue) for r in rows]}],
    }


@frappe.whitelist()
def get_category_breakdown(period="month"):
    """Donut chart : répartition du CA par cosmo_category.

    Returns:
        dict: format Frappe chart {labels, datasets}
    """
    date_clause, date_params = _get_date_filter(period)

    rows = frappe.db.sql(f"""
        SELECT
            COALESCE(i.cosmo_category, 'Non catégorisé') AS category,
            SUM(sii.amount) AS total_revenue
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        JOIN `tabItem` i ON i.item_code = sii.item_code
        WHERE si.docstatus = 1
          AND si.posting_date {date_clause}
        GROUP BY i.cosmo_category
        ORDER BY total_revenue DESC
    """, date_params, as_dict=True)

    return {
        "labels": [r.category for r in rows],
        "datasets": [{"name": "CA", "values": [flt(r.total_revenue) for r in rows]}],
    }


@frappe.whitelist()
def get_revenue_summary(period="today"):
    """KPI complet pour le Dashboard Manager : CA, transactions, panier moyen, delta vs période précédente.

    Returns:
        dict: {revenue, transactions, avg_basket, delta_revenue_pct, delta_transactions_pct}
    """
    date_clause, date_params = _get_date_filter(period)
    prev_clause, prev_params = _get_previous_date_filter(period)

    current = frappe.db.sql(f"""
        SELECT
            COALESCE(SUM(grand_total), 0) AS revenue,
            COUNT(*) AS transactions,
            COALESCE(AVG(grand_total), 0) AS avg_basket
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND posting_date {date_clause}
    """, date_params, as_dict=True)[0]

    previous = frappe.db.sql(f"""
        SELECT COALESCE(SUM(grand_total), 0) AS revenue, COUNT(*) AS transactions
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND posting_date {prev_clause}
    """, prev_params, as_dict=True)[0]

    def delta_pct(current_val, prev_val):
        if not prev_val:
            return None
        return round(((current_val - prev_val) / prev_val) * 100, 1)

    return {
        "revenue": flt(current.revenue),
        "transactions": int(current.transactions),
        "avg_basket": flt(current.avg_basket),
        "delta_revenue_pct": delta_pct(current.revenue, previous.revenue),
        "delta_transactions_pct": delta_pct(current.transactions, previous.transactions),
    }


@frappe.whitelist()
def get_stock_critical_items():
    """Retourne les items en stock critique (sous le seuil de réapprovisionnement).

    Returns:
        dict: {count, items[]}
    """
    items = frappe.db.sql("""
        SELECT
            i.item_code,
            i.item_name,
            i.cosmo_brand,
            i.cosmo_reorder_level,
            i.cosmo_preferred_supplier,
            COALESCE(SUM(bin.actual_qty), 0) AS stock_qty
        FROM `tabItem` i
        LEFT JOIN `tabBin` bin ON bin.item_code = i.item_code
        WHERE i.disabled = 0
          AND i.is_stock_item = 1
          AND i.cosmo_reorder_level > 0
        GROUP BY i.item_code
        HAVING stock_qty < i.cosmo_reorder_level
        ORDER BY (stock_qty / i.cosmo_reorder_level)
        LIMIT 50
    """, as_dict=True)

    return {"count": len(items), "items": items}


@frappe.whitelist()
def get_expiring_items(days_ahead=30):
    """Retourne les items dont la date d'expiration est dans moins de N jours.

    Returns:
        dict: {count, items[]}
    """
    cutoff = add_days(nowdate(), int(days_ahead))
    items = frappe.db.sql("""
        SELECT
            item_code, item_name, cosmo_brand, cosmo_expiry_date,
            DATEDIFF(cosmo_expiry_date, CURDATE()) AS days_remaining
        FROM `tabItem`
        WHERE disabled = 0
          AND cosmo_expiry_date IS NOT NULL
          AND cosmo_expiry_date <= %(cutoff)s
          AND cosmo_expiry_date >= CURDATE()
        ORDER BY cosmo_expiry_date
        LIMIT 50
    """, {"cutoff": cutoff}, as_dict=True)

    return {"count": len(items), "items": items}


@frappe.whitelist()
def get_crm_summary():
    """Résumé CRM : nouveaux clients ce mois + clients inactifs depuis 60 jours.

    Returns:
        dict: {new_customers_count, inactive_customers_count, inactive_customers[]}
    """
    from frappe.utils import get_first_day

    month_start = str(get_first_day(nowdate()))
    cutoff_60d = add_days(nowdate(), -60)

    new_count = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabCustomer`
        WHERE creation >= %(month_start)s AND disabled = 0
    """, {"month_start": month_start})[0][0]

    inactive = frappe.db.sql("""
        SELECT c.customer_name, MAX(si.posting_date) AS last_purchase
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si
            ON si.customer = c.name AND si.docstatus = 1
        WHERE c.disabled = 0
        GROUP BY c.name
        HAVING last_purchase < %(cutoff)s OR last_purchase IS NULL
        ORDER BY last_purchase
        LIMIT 20
    """, {"cutoff": cutoff_60d}, as_dict=True)

    return {
        "new_customers_count": int(new_count),
        "inactive_customers_count": len(inactive),
        "inactive_customers": inactive,
    }


@frappe.whitelist()
def get_stock_value_total():
    """Retourne la valeur totale du stock Cosmo.

    Returns:
        dict: {total_value}
    """
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(bin.actual_qty * bin.valuation_rate), 0) AS total_value
        FROM `tabBin` bin
        JOIN `tabItem` i ON i.item_code = bin.item_code
        WHERE i.disabled = 0 AND i.is_stock_item = 1
    """, as_dict=True)
    return {"total_value": flt(result[0].total_value) if result else 0}


# ── Helpers privés ────────────────────────────────────────────────────────────

def _get_date_filter(period):
    """Retourne un tuple (clause_sql, params_dict) pour la période demandée."""
    today = nowdate()
    if period == "today":
        return "= %(date_val)s", {"date_val": today}
    elif period == "week":
        return ">= %(date_val)s", {"date_val": add_days(today, -7)}
    elif period == "month":
        return ">= %(date_val)s", {"date_val": add_days(today, -30)}
    elif period == "year":
        return ">= %(date_val)s", {"date_val": add_days(today, -365)}
    return "= %(date_val)s", {"date_val": today}


def _get_previous_date_filter(period):
    """Retourne un tuple (clause_sql, params_dict) pour la période précédente."""
    today = nowdate()
    if period == "today":
        return "= %(prev_date)s", {"prev_date": add_days(today, -1)}
    elif period == "week":
        return "BETWEEN %(prev_start)s AND %(prev_end)s", {
            "prev_start": add_days(today, -14), "prev_end": add_days(today, -8),
        }
    elif period == "month":
        return "BETWEEN %(prev_start)s AND %(prev_end)s", {
            "prev_start": add_days(today, -60), "prev_end": add_days(today, -31),
        }
    return "= %(prev_date)s", {"prev_date": add_days(today, -1)}
