### Gold price scraping 

### Setting up

```
git clone
crontab -e
```
#### Crontab
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1xxxNxxx.xxx

0 10,17 * * * cd /root/gold-price-spider-supabase/ && /usr/bin/python3 spider-d>
```