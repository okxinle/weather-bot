def run_morning():
    """Called at 7am SGT — checks 9:30–10am slot only."""
    today = datetime.now(SGT).date()
    slot_930am = datetime(today.year, today.month, today.day, 9, 30, tzinfo=SGT)
    alerts = check_slot("9:30–10am", slot_930am)

    if alerts:
        msg = (
            "🌧️ Morning Walk Alert!\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n\n"
            "🕘 9:30–10am window:\n"
            + "\n".join(alerts)
            + "\n\nBring your umbrella! ☂️"
        )
    else:
        msg = (
            "✅ Morning walk looks clear!\n"
            "Dover Blk 28 → Galaxis via Fairfield Methodist\n"
            "No rain expected at 9:30am. 🌤️"
        )
    send_telegram(msg)

def run_evening():
    """Called at 6:30pm SGT — checks 6:30–7pm slot only."""
    today = datetime.now(SGT).date()
    slot_630pm = datetime(today.year, today.month, today.day, 18, 30, tzinfo=SGT)
    alerts = check_slot("6:30–7pm", slot_630pm)

    if alerts:
        msg = (
            "🌧️ Evening Walk Alert!\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n\n"
            "🕡 6:30–7pm window:\n"
            + "\n".join(alerts)
            + "\n\nBring your umbrella! ☂️"
        )
    else:
        msg = (
            "✅ Evening walk looks clear!\n"
            "Galaxis → Dover Blk 28 via Fairfield Methodist\n"
            "No rain expected at 6:30pm. 🌤️"
        )
    send_telegram(msg)
