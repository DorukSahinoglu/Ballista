# Ballista

Ballista, kullanicilarin kod yazmadan kendi metaheuristic algoritmalarini kurabilmesi icin tasarlanan uygulama fikrinin Python cekirdegi.

Bu repo su an son kullaniciya acik bir UI urunu degil. Buradaki ana hedef, gelecekteki gorsel editorun altinda calisacak motoru, tanim dilini ve veri modelini saglam sekilde kurmak.

Bu README bilerek detayli tutuluyor. Amac sadece repo aciklamasi yazmak degil; token biterse veya yeni bir sohbete gecilirse projeyi hizli sekilde kaldigi yerden devam ettirebilecek bir teknik hafiza olusturmak.

## Vizyon

Ballista'nin uzun vadeli vizyonu su:

- kullanici kod yazmadan kendi metaheuristic fikrini kurabilsin
- bu fikir klasik algoritmalarla sinirli olmasin
- kullanici kendi veri temsilini secsin
- kendi kurallarini, formullerini ve ara heuristic akislarini tanimlayabilsin
- sistem bu tanimi dogrulasin, calistirsin, gozlemlesin ve UI'de duzenlenebilir tutsun

Yani hedef:

"Hazir algoritmalar galerisi yapmak" degil.

Asil hedef:

"Metaheuristic tasarlama dili ve editoru kurmak."

## Kisa Durus

Ballista ne olmak istiyor:

- composable
- expression-driven
- strongly inspectable
- UI-friendly
- research-friendly
- plugin-friendly

Ballista ne olmak istemiyor:

- sadece GA/SA/ACO secilen bir katalog
- sadece arka planda kod calistiran bir script wrapper
- tamamen kontrolsuz serbest kod yurutme ortami
- guzel gorunen ama kisitli bir workflow builder

## Sinirsiz Ozgurluk Konusu

Projede en kritik tasarim gercegi su:

Tam anlamiyla sinirsiz ozgurluk vermek istemiyoruz ve veremeyiz.

Cunku sinirsiz ozgurluk demek genelde su problemlere gider:

- guvenlik sorunu
- dogrulama yapamama
- UI tarafinda duzenlenemez tanimlar
- debug edilmesi zor akislar
- tekrar kullanilamayan yapilar

Bu yuzden hedef "sinirsiz kod ozgurlugu" degil.

Hedef su:

- metaheuristic tasarimi icin pratikte cok genis bir ifade alani sunmak
- bunu guvenli, denetlenebilir ve editorle uyumlu bir DSL/graph modeliyle yapmak

Kisa cevap:

- teorik olarak tam sinirsiz degil
- pratikte cok genis bir tasarim alani hedefleniyor
- cok uc durumlarda yine custom operator veya plugin ihtiyaci kalabilir

## Bugunku Durum

Repo su an fikir asamasini asti. Artik ortada calisan bir cekirdek var.

Bugun olanlar:

- ortak runtime state var
- slot schema var
- node tabanli algorithm graph var
- JSON/dict tabanli definition loader var
- operator registry var
- validation var
- expression DSL var
- reusable subgraph var
- parameterized subgraph var
- editor contract / compatibility output var
- transform operatorleri var

Bugun olmayanlar:

- drag-and-drop UI
- visual debugger
- graph editor
- user-defined operator authoring UI
- persistence / project management
- plugin marketplace
- experiment comparison paneli

## Mimari Ozeti

### 1. Runtime State

`BallistaContext` su bilgileri tasir:

- `slots`
- `slot_schema`
- `argument_stack`
- `metrics`
- `history`
- `iteration`
- `stopped`

Bu sayede algoritma tekil fonksiyonlardan degil, ortak bir blackboard state uzerinde calisan modullerden olusur.

### 2. Node Modeli

Desteklenen node tipleri:

- `operator`
- `sequence`
- `loop`
- `condition`
- `subgraph`

Anlamlari:

- `operator`: tek bir davranis adimi
- `sequence`: adimlari sirayla calistirir
- `loop`: iteratif optimisation dongusu
- `condition`: state'e gore branch secer
- `subgraph`: tekrar kullanilabilir block cagirir

### 3. Slot Schema

Slot schema, bir verinin sadece kendisini degil nasil dusunulecegini de tasir.

Ana alanlar:

- `name`
- `kind`
- `representation`
- `default`
- `metadata`

Ornekler:

- `kind: matrix`, `representation: binary`
- `kind: matrix`, `representation: weighted`
- `kind: mapping`, `representation: tag_map`
- `kind: object_collection`, `representation: labeled_graph_view`
- `kind: object_collection`, `representation: ranked_subset`
- `kind: mapping`, `representation: grouped_subset`

### 4. Registry

`OperatorRegistry` su isi yapar:

- operator ismini gercek Python handler'ina baglar
- operator param schema'sini saklar
- UI'nin gorecegi contract bilgisini tasir

### 5. Definition Loader

`definitions.py` su katmandir:

- JSON veya dict tanimi alir
- validate eder
- node graph'a compile eder
- initial slots ve slot schema'yi hazirlar

### 6. Validation

Validator bugun sunlari erkenden yakalayabiliyor:

- eksik `name`
- eksik `root`
- bilinmeyen node tipi
- bilinmeyen operator
- bilinmeyen stop condition
- bilinmeyen subgraph reference
- eksik zorunlu operator parametresi
- bozuk `$ref`
- unsupported expression operator
- slot kind / representation uyumsuzlugu

### 7. Expression DSL

Ballista'nin ifade gucunun kalbi burasi.

Bugun desteklenen operatorler:

- `ref`
- `if`
- `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- `and`, `or`, `not`
- `contains`, `in`
- `add`, `sub`, `mul`, `div`, `pow`, `mod`
- `abs`, `min`, `max`, `avg`, `round`
- `len`
- `get`
- `filter`
- `map`
- `sort_by`
- `group_by`
- `reduce`
- `sliding_window`
- `neighbors_of`
- `matrix_degrees`
- `connected_components`
- `edge_pairs`
- `neighborhood_overlap`
- `reachable_within`
- `shortest_path`
- `propagate_signal`
- `random_walk`
- `flow_profile`
- `triangle_patterns`
- `centrality_profile`
- `closeness_profile`
- `policy_walk`
- `star_patterns`
- `square_patterns`
- `count`
- `sum`

Bu DSL ile kullanici:

- kurallar yazabilir
- matematiksel formuller yazabilir
- listeyi filtreleyebilir
- yeni obje listesi uretebilir
- siralayabilir
- gruplayabilir
- tek bir ozet objeye katlayabilir
- kayan pencere mantigiyla lokal pattern cikarabilir
- matrix icinden komsuluk profili cikarabilir
- graph degree gorunumu uretebilir
- component yapisi cikarabilir
- edge listesi cikarabilir
- iki neighborhood arasindaki overlap'i hesaplayabilir
- multi-hop erisim alani cikarabilir
- iki node arasinda yol bulabilir
- graph uzerinde basit sinyal yayilimi hesaplayabilir
- deterministic random walk profili uretebilir
- source-target traffic / flow ozeti cikarabilir
- triangle motif/pattern tespiti yapabilir
- centrality profili cikarabilir
- closeness profili cikarabilir
- policy-guided walk tanimlayabilir
- star benzeri motifleri tespit edebilir
- square benzeri motifleri tespit edebilir
- ara heuristic gorunumleri yaratabilir

### 8. Reusable Block / Subgraph

Artik reusable heuristic block tanimlanabiliyor.

Bugunki model:

- top-level `subgraphs`
- her biri icin `name`
- altinda bir `node`
- call site'da `type: "subgraph"` ve `ref`
- opsiyonel `params`
- subgraph icinde `args.*` ile argument kullanimi

Bu tam fonksiyon sistemi degil ama ona giden ilk guclu adim.

### 9. Editor Contract / Compatibility

Bu katman UI icin cok kritik.

Sistem artik makine-okunur sekilde sunlari uretebiliyor:

- desteklenen node tipleri
- desteklenen expression operatorleri
- desteklenen reference root'lari
- operator listesi
- operator param semalari
- mevcut slot schema'ya gore compatible slot listeleri

Bu sayede gelecekte editor su sorulara backend sormadan cevap bulabilir:

- bu operator hangi parametreleri istiyor
- bu parametre icin hangi slotlar mantikli
- bu veri temsili hangi operatorle uyumlu

## Proje Yapisi

```text
src/ballista/
  engine.py       -> algoritma calistirici
  models.py       -> context, history, slot schema, args stack
  nodes.py        -> node tipleri
  registry.py     -> operator registry ve param schema
  definitions.py  -> definition parser / compiler
  expression.py   -> expression DSL evaluator
  validation.py   -> definition validator
  contracts.py    -> editor contract / compatibility ciktilari
  examples.py     -> builtin operatorler
examples/
  astro_definition.json
  labeled_matrix_definition.json
  run_astro_demo.py
  run_definition_demo.py
  run_matrix_demo.py
  run_contract_demo.py
tests/
  test_engine.py
```

## Calistirma

Astro demo:

```powershell
$env:PYTHONPATH="src"
python examples/run_astro_demo.py
```

Definition demo:

```powershell
$env:PYTHONPATH="src"
python examples/run_definition_demo.py
```

Matrix demo:

```powershell
$env:PYTHONPATH="src"
python examples/run_matrix_demo.py
```

Contract demo:

```powershell
$env:PYTHONPATH="src"
python examples/run_contract_demo.py
```

Testler:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## Demo'larin Amaci

### Astro Demo

`astro`, bilimsel olarak kanitlanmis bir algoritma iddiasi degil.

Bu demo sunu gostermek icin var:

- bir kullanici kafasinda ozel bir operator akisi kurabiliyorsa
- Ballista o akisi tasiyabiliyor mu

Yani `astro` burada bir "esneklik testi" gibi dusunulmeli.

### Matrix Demo

`labeled_matrix_definition.json` bugun sistemin en iyi capability demosu.

Bu demo su akisi tasir:

1. binary matrix tanimla
2. label map tanimla
3. matrix'ten `constructed_solution` uret
4. `filter` + `map` ile `priority_nodes` uret
5. `group_by` ile `priority_groups` uret
6. `sort_by` ile `ranked_priority_nodes` uret
7. `reduce` ile `priority_summary` uret
8. `sliding_window` ile `window_profiles` uret
9. `matrix_degrees` ile `degree_view` uret
10. `neighbors_of` ile `critical_neighbors` uret
11. `connected_components` ile cluster gorunumu uret
12. `edge_pairs` ile edge listesi uret
13. `neighborhood_overlap` ile kritik overlap profili uret
14. `reachable_within` ile multi-hop erisim profili uret
15. `shortest_path` ile yol profili uret
16. `propagate_signal` ile yayilim profili uret
17. `random_walk` ile walk profili uret
18. `flow_profile` ile traffic/flow profili uret
19. `triangle_patterns` ile motif tespiti yap
20. `centrality_profile` ile merkezilik profili uret
21. `closeness_profile` ile ikinci merkezilik ailesini uret
22. `policy_walk` ile yonlendirilmis walk profili uret
23. `star_patterns` ile star benzeri motifleri bul
24. `square_patterns` ile square benzeri motifleri bul
25. formul ile `heuristic_score` hesapla
26. expression ile `search_mode` sec
27. `condition` ile branch sec
28. parameterized subgraph ile strategy object uret

Bu demo bugun su seyi kanitliyor:

- veri temsilini tasiyabiliyoruz
- ara veri gorunumleri uretebiliyoruz
- neighborhood ve degree mantigini DSL icine tasiyabiliyoruz
- graph component ve overlap mantigini da ifade edebiliyoruz
- multi-hop reach, shortest path ve basic propagation mantigini da ifade edebiliyoruz
- random walk, traffic/flow ve basit motif tespitini de ifade edebiliyoruz
- centrality ve policy-guided walk mantigini da ifade edebiliyoruz
- ikinci merkezilik ailesi ve ikinci motif ailesi de geldi
- matematiksel formula yazabiliyoruz
- reusable heuristic block cagirabiliyoruz

## Tasarim Prensipleri

Bu repo icin karar alirken izledigimiz prensipler:

- UI once degil, motor once
- davranis koddan veriye dogru kaymali
- ifade gucu artarken validation da artmali
- editor contract'i basindan dusunulmeli
- tekrar kullanilabilir parcalar onemli
- sistem acik olmali ama kontrolsuz olmamali

## Yol Haritasi

Asagidaki roadmap, projeyi asama asama nereye goturmek istedigimizi gosteriyor.

### M0 - Foundation

Hedef:

- basic engine
- context
- node modeli
- test iskeleti

Durum:

- tamamlandi

### M1 - Definition Language

Hedef:

- algorithm definition'i veri olarak ifade etmek
- JSON/dict yukleme
- root graph compile etmek

Durum:

- tamamlandi

### M2 - Validation And Contracts

Hedef:

- definition validator
- operator param schema
- editor contract
- compatibility output

Durum:

- buyuk oranda tamamlandi

### M3 - Expression DSL

Hedef:

- kosul yazmak
- matematiksel formula yazmak
- slot/metric/schema/args referansi kullanmak

Durum:

- ilk guclu versiyon tamamlandi

### M4 - Transform DSL

Hedef:

- `filter`
- `map`
- `sort_by`
- `group_by`
- ara heuristic gorunumleri uretmek

Durum:

- ilk versiyon tamamlandi

### M5 - Heuristic Composition

Hedef:

- reusable subgraph
- parameterized subgraph
- generic heuristic block

Durum:

- ilk versiyon tamamlandi

### M6 - Advanced DSL

Hedef:

- daha zengin reduce operatorleri
- window/sliding operators
- graph-specific transforms
- cluster / neighborhood operators
- daha guclu path/reference sistemi

Durum:

- reduce ve sliding window ilk versiyonuyla basladi
- graph-specific transforms ilk versiyonuyla basladi
- cluster / neighborhood primitive'leri ilk versiyonuyla basladi
- path / propagation primitive'leri ilk versiyonuyla basladi
- flow, walk ve graph-pattern primitive'leri ilk versiyonuyla basladi
- centrality, walk policy ve star motifleri ilk versiyonuyla basladi
- closeness ve square motifleri ilk versiyonuyla basladi
- daha zengin centrality aileleri, walk policy secenekleri ve motif aileleri hala siradaki mantikli buyuk adim

### M7 - Authoring Experience

Hedef:

- CLI authoring tools
- better error messages
- definition formatter
- definition linter
- stronger compatibility rules

Durum:

- henuz baslanmadi

### M8 - Visual Product

Hedef:

- drag-and-drop graph editor
- operator palette
- slot editor
- formula editor
- run monitor
- trace / metrics explorer

Durum:

- uzun vadeli hedef

### M9 - Ecosystem

Hedef:

- plugin system
- operator packs
- saved templates
- experiment comparison
- maybe marketplace

Durum:

- uzun vadeli hedef

## Yakin Rota

Bugunden sonra teknik olarak en mantikli yakin rota su:

1. cluster / neighborhood operatorlerini buyutmek
2. path / propagation operatorlerini buyutmek
3. flow / walk / graph pattern primitive'lerini buyutmek
4. centrality / motif ailelerini buyutmek
5. walk policy seceneklerini buyutmek
6. operator compatibility kurallarini daha akilli hale getirmek
7. stronger definition contract
8. CLI tabanli authoring / inspect tooling
9. sonra UI prototipi

## Milestone Mantigi

Milestone'lar arasindaki iliski:

- M0-M2 olmadan editor akli olmaz
- M3-M6 olmadan kullaniciya gercek ifade ozgurlugu verilemez
- M7 olmadan authoring aci verici olur
- M8 olmadan urun hissi gelmez
- M9 olmadan ekosistem olmaz

## Su An Neler Eksik?

Repo ilerledi ama henuz tam urun degil.

Eksik olan ana parcalar:

- daha zengin DSL
- domain-specific heuristic primitive'ler
- graph / neighborhood transform'larini derinlestirmek
- better diagnostics
- persistence layer
- visual editor
- run trace viewer
- result comparison UI

## Sonraki Sohbet Icin Handoff

Bu bolum dogrudan sonraki chat icin.

Su anki calisan capability listesi:

- algorithm definition yukleme
- slot schema
- parametreli operator
- condition
- expression DSL
- formula DSL
- filter/map/sort/group transforms
- reduce/window transforms
- graph/neighborhood transforms
- connected component / edge / overlap transforms
- path / reach / propagation transforms
- walk / flow / triangle pattern transforms
- centrality / policy walk / star pattern transforms
- closeness / square pattern transforms
- parameterized subgraph
- contract export
- compatibility output

En mantikli bir sonraki teknik hedef:

- graph-specific transforms
- cluster / neighborhood transforms
- graph pattern primitive'leri
- path / propagation primitive'leri
- walk / flow primitive'leri
- centrality / policy primitive'leri
- closeness / square motif primitive'leri
- daha guclu reduce patterns

Neden?

Cunku su an kullanici:

- veri secip donusturebiliyor
- ama graph yapisi, neighborhood iliskileri ve daha domain-specific search mechanics tarafini hala kisitli primitive'lerle ifade ediyor
- path bulma ve basit propagation ilk versiyonuyla geldi
- random walk, flow ve triangle pattern detection ilk versiyonuyla geldi
- centrality, policy walk ve star motifleri ilk versiyonuyla geldi
- closeness ve square motifleri de ilk versiyonuyla geldi
- ama richer centrality families, daha zengin walk policy control ve daha genis motif aileleri henuz yok

Yani bir sonraki adim ifade alanini "ara heuristic view" seviyesinden "gercek search mechanics" seviyesine buyutmeli.

## Kisa Ozet

Ballista su an:

- sadece fikir degil
- sadece script degil
- sadece demo da degil

Bugun artik:

- engine var
- definition dili var
- validation var
- expression DSL var
- reusable heuristic block var
- editor contract var

Henuz yok:

- tam urun
- visual builder
- tamamen kodsuz son kullanici deneyimi

Ama omurga dogru kuruluyor.
