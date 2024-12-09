# NAIL062 Homework - Subgraph Isomorphism using a SAT solver

## Popis problému
Problém, který jsem řešil, je *Izomorfizmus podgrafů*, tedy hledáme, zda se v nějakém zadaném grafu nachází podgraf
izomorfní s druhým zadaným grafem. Skript tento probém převádí na možná mapování vrcholů malého grafu `H` na vrcholy
velkého grafu `G` (ve kterém hledáme podgrafy).  
Každé takové mapování je reprezentované jednou proměnnou (vrchol v malém grafu -> vrchol ve velkém grafu). Jednotlivé
výstupní klauzule potom reprezentují různé podmínky takového mapování:
 - každý vrchol z hledaného (malého) grafu se musí namapovat na nějaký vrchol velkého (prohledávaného) grafu
   - $$ \forall s \in V(\text{sub}): \bigvee_{m \in V(\text{main})} x_{sm} $$
   - tím vznikne `|V(H)| * |V(G)|` kaluzulí
 - žádné 2 vrcholy `H` se nenamapují na stejný vrchol `G`
   - $$ \forall m \in V(\text{main}): \forall s1 \ne s2 \in V(\text{sub}): \neg x_{s1m} \vee \neg x_{s2m} $$
   - tím vznikne až `|V(G)| * |V(H)|^2` klauzulí
 - pokud jsou 2 vrcholy namapované, musí mezi nimi vést hrana v `H`
   - $$ x_{s1m1} \wedge x_{s2m2} \implies (m1, m2) \in E(\text{main}) $$
   - $$ \neg x_{s1m1} \vee \neg x_{s2m2} \vee (m1, m2) \in E(\text{main}) $$
   - $$ \forall (s1, s2) \in E(\text{sub}): \forall m1 \ne m2 \in V(\text{main}): \text{if} (m1, m2) \notin E(\text{main}): \neg x_{s1m1} \vee \neg x_{s2m2} $$
   - tím vznikne až `|E(H)| * |V(G)|^2` kaluzulí
   - kaluzule se přidají jen pokud v G taková hrana neexistuuje

### Optimalizace
Takto vygenerované klauzule je možné ještě optimalizovat. Pokud stupeň vrcholu v `G` < stupeň vrcholu v `H`, tyto
vrcholy na sebe nemohou být nikdy namapované. Tím pádem všechny proměnné, které kódují takovéto mapování mohou být
odstraněny. Pokud se nachází v klauzuli **neznegovaně**, jednoduše se odstraní. Pokud se nachází **negovaně**, celou
klauzuli je možné odstranit, jelikož bude vždy pravdivá. Pokud se někdy narazí na prázdnou klauzuli, je automaticky
celý problém neřešitelný a tudíž se neprovádí žádné další zpracování - vygeneruje se CNF s 0 klauzulemi, o kterém
prohlásí SAT solver, že je nesplnitelný.

## Použití skriptu
Skript přebírá z příkazové řádky několik parametrů:
 - `-i`, `--input` - jméno vstupního souboru (nebo `-` pro načítání ze standardního vstupu)
 - `-o`, `--output` - jméno výstupního souboru, kam se uloží převedený problém do DIMACS CNF
 - `-s`, `--solver` - cesta k solveru, který se má spouštět
 - `-r`, `--run-solver`, `--no-run-solver` - zda se má zadaný solver automaticky zavolat
 - `-v`, `--verb` - verbozita solveru
 - `-p`, `--print` - zda se má vytisknout veškerý výstup solveru
 - `-h`, `--help` - nápověda

Výchozí hodnoty:
 - vstup ze standardního vstupu
 - výstup `formula.cnf`
 - solver `glucose-syrup`
 - run solver `True`
 - verbosity `1`
 - print `False`

Samotný SAT solver není součástí řešení, je třeba použít systémovou instalaci nebo stáhnout a zkompilovat z
[GitHubu](https://github.com/audemard/glucose/).

Vygenerovaná CNF formule je k přečtení v souboru, který je určen jako výstupní (`-o`, výchozí hodnota `formula.cnf`).

### Formát dat
Vstup se zadává v podobě 2 grafů; za každým grafem musí být prázdný řádek. Graf se zadává v podobě hran, kdy na každém
řádku je jedna hrana ve formátu `začátek konec`, kde `začátek` a `konec` jsou libovolné názvy vrcholů (textové i
číselné). Na prvním řádku popisu grafu musí být seznam všech vrcholů. Vždy se jako první zadává `G` (tedy velký, prohledávaný graf) a jako druhý `H` (tedy malý, hledaný graf).  
Všechny hrany jsou **orientované**.

---
Výstup (v pŕípadě, že byl spuštěn solver) má 2 podoby:  
V případě, že v `G` existuje podgraf izomorfní s `H`, vytiskne se na výstup:
```
The given graph DOES contain a subgraph isomorphic to the other graph
Vertex mapping:

x -> d
y -> a
z -> c

Processing took approx. 0.006386756896972656 seconds
Preprocessing took 0.00038433074951171875 seconds
```
Jednotlivé řádky `x -> d`, `y -> a`, `z -> c` znamenají výstupní mapování vrcholů `H -> G`.

Pokud takové mapování **není** nalezeno (tedy `G` nemá podgraf izomorfní s `H`), je výstup následující:
```
The given graph DOES NOT contain a subgraph isomorphic to the other graph

Processing took approx. 0.003989458084106445 seconds
Preprocessing took 0.0005240440368652344 seconds
```
Pokud se má tisknout i výstup solveru, je vytištěn **před** finálním vyhodnocením.

## Příklady (složka `samples`)
`small-solvable.txt` obsahuje graf podoby
```
a--b
| \|
d--c

x--y
  \|
   z
```
Tedy se ve čtverci s úhlopříčkou hledá trojúhelník

---
`small-unsolvable.txt` obsahuje graf podoby
```
a--b
|  |
d--c

x--y
  \|
   z
```
Tedy se ve čtverci bez úhlopříčky hledá trojúhelník

---
`long1.txt` obsahuje uměle vytvořený náhodný problém (splnitelný, který běží zhruba 5s)  
G = 50 vrcholů, 800 hran  
H = 40 vrcholů, 160 hran

---
`long2.txt` obsahuje uměle vytvořený náhodný problém (splnitelný, který běží zhruba 25s)  
G = 70 vrcholů, 1200 hran  
H = 45 vrcholů, 250 hran

---
`long3.txt` obsahuje uměle vytvořený náhodný problém (splnitelný, který běží zhruba 12s)  
G = 55 vrcholů, 1000 hran  
H = 40 vrcholů, 250 hran

---
`medium1.txt` obsahuje ručně vytvořený splnitelný graf na 6 vrcholech (5-kružnice s vrcholy a spojkami navíc); hledá se
podgraf izomorfní k 5-kružnici

## Experimenty
### Generátor instancí
Soubor `generator.py` vytváří instance problémů zakódované ve stejném formátu, který očekává `solver.py`.
Nastavením `self_edges` v kódu se povolují smyčky v grafu, zbytek parametrů se přebírá z příkazové řádky. Výstupem je
vždy standardní výstup, chyby se tisknou na standardní chybový výstup.  
Použití: `generator.py <True|False guarantee subgraph> <n vertices in G> <n edges in G> <n vertices in H> <n edges in H>`  
Generátor má 2 režimy provozu, buď generuje 2 naprosto náhodné grafy, nebo vygeneruje 1, který poté rozšíří na větší.
Tyto režimy se vybírají prvním argumentem generátoru.

Všechny velké instance problémů byly vygenerovány skriptem `generator.py`.  
*Nutno podotknout, že kvůli způsobu, jakým se uměle generují instance problémů často vzniká mapování* `u1 -> v1` *,*
`u2 -> v2` *atd.*

---
Skript dokázal vyřesit problém |V(G)| = 100, |E(G)| = 1600, |V(H)| = 55, |E(H)| = 300 za asi 85 sekund (13 předzpracování
a 70 samotný SAT solver).

Pro problém |V(G)| = 120, |E(G)| = 2000, |V(H)| = 60, |E(H)| = 800 si Python alokoval 4,5 GB paměti, zpracování trvalo
35 sekund a SAT solver běžel opět 70.

Problém o velikosti |G| = (120, 3000) |H| = (60, 1700) si vyžádal v Pythonu 9 GB paměti a minutu zpracovávání, a v SAT
solveru 90 sekund. CNF formule pro tento problém měla 2388991 řádků, 3255 proměnných a 2388990 kaluzulí. SAT solver si
vyžádal 1444 MB paměti.

Problém o velikosti |G| = (200, 10000) |H| = (80, 6000) si vyžádal v Pythonu přes 40 GB paměti, čímž mému počítači došly
prostředky (32 GB RAM + 8 GB swap) a zpracování nebylo dokončeno.
