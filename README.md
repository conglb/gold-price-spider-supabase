### Gold price scraping 
Tracking the gold price from multiple sources.
![supabase database stored](doc/Screenshot.png "supabase database")
### Setting up

```
git clone
crontab -e
```
#### Crontab
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1xxxNxxx.xxx

0 10,17 * * * cd /root/gold-price-spider-supabase/ && /usr/bin/python3 spider-doji.vn.py >> /var/log/spider-doji.log 2>&1
```