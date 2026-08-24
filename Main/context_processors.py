from django.urls import reverse, NoReverseMatch

ICONS = {
    "grid": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 13h6V4H4v9zM14 20h6v-9h-6v9zM14 4v6h6V4h-6zM4 20h6v-6H4v6z"/></svg>',
    "trending-up": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8M17 7h4v4"/></svg>',
    "trending-down": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7l6 6 4-4 8 8M17 17h4v-4"/></svg>',
    "receipt": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3.5h12v17l-3-2-3 2-3-2-3 2v-17z"/><path d="M9 8h6M9 12h6"/></svg>',
    "clock": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8.5"/><path d="M12 7v5.2l3.4 2"/></svg>',
    "file-text": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3.5h8l4 4V20a1 1 0 01-1 1H6a1 1 0 01-1-1V4.5a1 1 0 011-1z"/><path d="M13.5 3.6V8h4.3M8.5 13h7M8.5 16.5h4.5"/></svg>',
    "building": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 21V5a1 1 0 011-1h8a1 1 0 011 1v16M14 21h6V10l-6-4M8 7h.01M8 11h.01M8 15h.01M4 21h16"/></svg>',
    "users": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="8" r="3.2"/><path d="M2.6 19.5c0-3.3 2.9-5.7 6.4-5.7s6.4 2.4 6.4 5.7M16 8.5a3 3 0 110 6M18.5 14.3c2 .5 3.4 2.1 3.4 4.5"/></svg>',
    "shield": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z"/></svg>',
}


def _nav_url(name, *args):
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


def hotel_pallav_nav(request):
    """Supplies the shared sidebar's grouped navigation to every template
    rendered with base.html, active-state included."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}

    current = getattr(request.resolver_match, "url_name", None) if request.resolver_match else None

    def item(url_name, label, icon, active_names=None):
        active_names = active_names or [url_name]
        return {
            "url": _nav_url(url_name),
            "label": label,
            "icon_svg": ICONS[icon],
            "active": current in active_names,
        }

    groups = [
        {
            "label": "Overview",
            "items": [item("DashboardProfile", "Dashboard", "grid")],
        },
        {
            "label": "Money",
            "items": [
                item("RevenueProfile", "Revenue", "trending-up"),
                item("ExpenseProfile", "Expense", "trending-down"),
                item("BillMasterAdvanceProfile", "Bill Master", "receipt",
                     ["BillMasterAdvanceProfile", "BillMasterBillProfile", "BillMasterDebitBillProfile"]),
                item("ReportsProfile", "Reports", "file-text"),
            ],
        },
        {
            "label": "Operations",
            "items": [item("ShiftHandoverProfile", "Shift Handover", "clock")],
        },
        {
            "label": "People",
            "items": [
                item("CompanyProfile", "Company Profile", "building"),
                item("StaffProfileUserProfile", "Staff Profile", "users"),
            ],
        },
    ]

    if request.user.is_superuser or request.user.username == "SuperAdmin":
        groups.append({
            "label": "Admin",
            "items": [item("userprofile", "User Accounts", "shield")],
        })

    return {"nav_groups": groups}
