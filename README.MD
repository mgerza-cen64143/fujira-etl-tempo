# ETL pro reporting vykazovaného času v Tempo modulu
Tento skript přes REST API extrahuje data o logovaném čase z FUJIRA, doplní k němu metadata a uloží do .csv souboru.


### Použití
1. vydefinujte squad v souboru uvedeného v klíči _my_squads_
2. zalogujte v tiketech ve FUJIRA čas
3. nastavte klíč _start_date_
4. pusťte skript 
```./etl-vykazovani.py -p profile_name```
5. v souboru se základem _base_csv_ najdete hotový extrakt dat.
6. při nahrávání do Excelu importujte bez definované znakové sady

#### Popis algoritmu:
1. Podle definovaného dotazu do FUJIRA se získá seznam tiketů se zalogovaným časem.
   1. Pokud jsme definovali klíč _jira_query_ jako JQL, výstupem je seznam tiketů podle tohoto dotazu. 
   2. Pokud jsme definovali klíč _jira_query_ jako '\_\_SQUADS\_\_', aplikace vygeneruje JQL dotaz ve formátu _"issueFunction in workLogged('by CENXXXXX after YYYY-MM-DD')"_ pro každého uživatele definovaného v souboru pod klíčem _my_squads_ a klíčem _start_date_.
2. Pro každý získaný tiket se získá seznam zalogovaných worklogů.
3. Každý worklog po datumu definovaném v klíči _start_date_ se obohatí o metadata.
    1. Rekurzivně se zjistí jeho TOP parent (s výjimkami přetíženými klíčem _issues_top_overload_)
    2. Vyhodnotí se typ logované práce (label RTB, CTB, Folder type, produkční defekty atd)

4.každý worklog obohacený o metadata se uloží do výsledného CSV souboru.

#### Parametr pro spuštění skrpitu -p:
profile_name: název profilu konfigurace

#### Popis konfiguračního souboru etl.conf
- formát: klíč=hodnota

popis:
```
[profile_name] název profilu konfigurace
base_url= REST endpoint pro JIRA API
jira_username= username technického uživatele
jira_password= password technického uživatele
auth_cookies= cesta k souboru s Chrome cookies. Pokud specifikujeme, autorizujeme se k JIRA REST API pomocí cookies, nikoli technickým uživatelem.
my_squads= cesta k csv souboru s definicí členů týmu.
jira_query= JQL definující tikety na které se vykazovalo, nebo klíčové slovo __SQUADS__ - pak se JQL generuje podle seznamu členů squadu.
start_date= od kdy se má worklog brát do reportingu
issues_top_overload= které tikety definují TOP tiket oproti standardní hierarchii. Uvedený tiket je pak brán jako TOP s možností definice typu workloadu.
# {"UF-3738": "Řízení dodávky", "SL-4": "Řízení dodávky"}
simplify= Redukuje výsledný report o o některé sloupce. 
base_csv=základ názvu csv souboru do kterého se uloží report.
```

#### Popis souborů v projektu
```
etl.py: skript pro spuštění
etl.conf: konfigurační soubor
etl_utils.py: pomocné obecné funkce (parsování, logging)
jira_utils.py: pomocné JIRA funkce (dotazy přes REST api, logické vztahy mezi tikety)
global_vars.py: persistence načtených konfigurací, primitivní caching
squads*.csv: definice squadů / jejich členů
```


#### Pokud chcete:
- Přidat nový parent (třeba přidáváte nový epik pro produkční defekty): editujte klíč *issues_top_overload* v etl.conf
- přidat dalšího člena týmu: upravte squads.csv



## Instalace
1. zažádejte si v REDIMu o skupinu INET_DEVELOPERS
2. zažádejte si ve SNow o instalaci
   -  Pythonu 3
   - Pycharmu (poslední verze, community edition)
   - GIT klienta   
3. naklonujte si repozitář s projektem:
```git clone <url_to_project>```
4. nakonfiugujte si PIP

v adresáři $HOME\pip vytvořte soubor **pip.ini**:
```global]
trusted-host = pypi.python.org
              pypi.org
              files.pythonhosted.org
              sdf.csin.cz
index-url = https://sdf.csin.cz/artifactory/api/pypi/pypi/simple
```
5. nainstalujte si knihovny:
- requests
- browser_cookie3
- pandas

v aplikaci Pycharm: File>Settings > Project > Python Interpreter

v příkazové řádce:
```
pip install requests --user
pip install browser_cookie3 --user
pip install pandas --user
```


## TODO
Aplikace není laděna pro Linux - cesty ke Cookinám, znakové sady...

Není zde robustnost na abnormální situace (práva zápisu, nečekané odpovědi z REST api)

Zdrojové csv pro squady musí být bez chyb (jinak aplikace havaruje)

Autentikace přes browser cookies: pokud se vám podaří nainstalovat broser_cookie3, jinak ne.


## Odkazy
Confluence pro popis detailů ke GITHubu: https://cnfl.csin.cz/display/GITHUB/GITHUB+Home
Confluence pro instalaci Pycharmu: https://cnfl.csin.cz/display/Automatizovanetestovanisoftwaru/PyCharm
Confluence pro práci s GITem v Pycharmu: https://cnfl.csin.cz/display/Automatizovanetestovanisoftwaru/Git+v+PyCharmu

