import re,json,subprocess
p='/mnt/c/Users/Stagiare RSI/OneDrive/Documents/lims/2.6.0/custom.cfg'
u,pw=re.search(r'^user=(.+)$',open(p).read(),re.M).group(1).strip().split(':',1)
code='async page => { await page.getByRole("textbox").nth(0).fill('+json.dumps(u)+'); await page.getByRole("textbox").nth(1).fill('+json.dumps(pw)+'); await page.getByRole("button",{name:"Se connecter",exact:true}).click(); }'
r=subprocess.run(['bash','/mnt/c/Users/Stagiare RSI/.codex/skills/playwright/scripts/playwright_cli.sh','run-code',code],capture_output=True,text=True)
print('Login command exit:',r.returncode)
if '### Error' in r.stdout: print('Browser login failed')