#DISCLAMIER

This was primarily built for a common app project; however, it's still useful and will be used later on.

#Budget Tracker

A simple Flask web app to track income and expenses across different accounts(HYSA, ROTH, and CHECKING).

#Features
- Add, view, and delete transactions
- Track transactions by month and week
- View income and expense summaries by account

Clone the repo:
   git clone https://github.com/username/budget_tracker.git
   cd budget_tracker

IMPORTANT: 
- You must use venv and install -r requirements.txt using cmd pip.
- It should run on your http://host:5000, use HTTP, not HTTPS.
- To view transactions by month and year, use http://host:5000/transaction. I'll add it to the index.html in the future.
- I don't want to pay for a domain, so I used Cloudflare temp URL using cloudflare tunnel --url http://host:5000 result: https://pray-china-wings-suggest.trycloudflare.com/, if you want this temp URL to be permanent, just simply keep the terminal running at all times.
- I also use cloudflared.service and flaskapp.service to keep the services running at all times in the background. Unfortunately, the Cloudflare URL does not work like that unless you have a domain.
