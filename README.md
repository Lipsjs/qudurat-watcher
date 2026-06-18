
# qudurat-watcher
I fucking hate the Qiyas website and the constant search for the desired exam slot reservation date so I made this simple program that checks the Qiyas exam booking site for open slots and sends a Telegram alert when one opens up.

## How it works

A small Python script (`relay.py`) runs locally and checks slot availability for the dates you set, across every center in a given city, every 30 seconds. A browser dashboard (`watcher.html`) gives you a place to set things up, watch the live log, and hear an alarm when something opens. When a slot appears, you get a Telegram message with the details.

Login is never automated. You log into the real site yourself, in your own browser, the normal way. The tool reuses that already-authenticated session rather than handling credentials itself.

## Setup


1. Install Python 3 if you don't have it.
2. Download watcher.html, relay.py, and run.bat into the same folder.
3. Log into the Qiyas site and start a booking search for your exam until you reach the date/city page.
4. Open browser devtools, Network tab, find the GetAvailableCBTCentersBySessionId request.
5. From its Headers tab, copy the Cookie value. From its Payload tab, copy sessionId and candidateId.
6. Run run.bat from that same folder (Windows) or python relay.py directly (other platforms), which also opens watcher.html.
7. Paste in the values from step 5, set your target dates and city ID, add a Telegram bot token and chat ID, press Start.
8. If it dosent work its probably the shitty code and not a user error so dont worry 
## Notes

The session values expire periodically. If checks start failing, repeat steps 2-4 for fresh ones. I know its a pain in the ass but im too lazy to fix it, you could try to implement it in tampermonkey so you dont need to keep refreshing the stinky session ID but its gonna take some elbow grease to get that working.

City ID 4 is Riyadh im too lazy to check for other city IDs sorry homie. Target dates are comma-separated, `YYYY-MM-DD`.
