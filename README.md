# NAIL062 Homework - Subgraph Isomorphism using a SAT solver

## Popis problému
Problém, který jsem řešil, je *Izomorfizmus podgrafů*, tedy hledáme, zda se v nějakém zadaném grafu nachází podgraf
izomorfní s druhým zadaným grafem. Skript tento probém převádí na možná mapování vrcholů malého grafu `H` na vrcholy
velkého grafu `G` (ve kterém hledáme podgrafy).  
Každé takové mapování je reprezentované jednou proměnnou (vrchol v malém grafu -> vrchol ve velkém grafu). Jednotlivé
výstupní klauzule potom reprezentují různé podmínky takového mapování:
 - každý vrchol z hledaného (malého) grafu se musí namapovat na nějaký vrchol velkého (prohledávaného) grafu
   - tím vznikne `|V(H)| * |V(G)|` kaluzulí
 - žádné 2 vrcholy `H` se nenamapují na stejný vrchol `G`
   - tím vznikne až `|V(G)| * |V(H)|^2` klauzulí
 - pokud jsou 2 vrcholy namapované, musí mezi nimi vést hrana v `H`
   - tím vznikne až `|E(H)| * |V(G)|^2` kaluzulí
   - kaluzule se přidají jen pokud v G taková hrana neexistuuje

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

### Formát dat
Vstup se zadává v podobě 2 grafů; za každým grafem musí být prázdný řádek. Graf se zadává v podobě hran, kdy na každém
řádku je jedna hrana ve formátu `začátek konec`, kde `začátek` a `konec` jsou libovolné názvy vrcholů (textové i
číselné). Vždy se jako první zadává `G` (tedy velký, prohledávaný graf) a jako druhý `H` (tedy malý, hledaný graf).  
Všechny hrany jsou **orientované**
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

## Experimenty
### Generátor instancí
Soubor `generator.py` vytváří instance problémů zakódované ve stejném formátu, který očekává `solver.py`.
Nastavením `self_edges` v kódu se povolují smyčky v grafu, zbytek parametrů se přebírá z příkazové řádky. Výstupem je
vždy standardní výstup, chyby se tisknou na standardní chybový výstup.  
Použití: `generator.py <True|False guarantee subgraph> <n vertices in G> <n edges in G> <n vertices in H> <n edges in H>`