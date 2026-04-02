# Ballista

Ballista, kullanicilarin kod yazmadan kendi metaheuristic algoritmalarini kurabilmesi icin tasarlanan uygulama fikrinin Python cekirdegi.

Bu repo su an bir UI urunu degil. Buradaki amac, gelecekteki gorsel uygulamanin altinda calisacak motoru, veri modelini ve algorithm definition katmanini dogru kurmak.

## Cekirdek Fikir

Ballista'nin hedefi su:

- kullanici kendi metaheuristic fikrini ifade etsin
- population, matrix, binary structure, label map, custom object gibi veri temsillerini tanimlayabilsin
- operatorleri baglayabilsin
- kosullara gore farkli branch'lere gidebilsin
- sonra engine bunu calistirsin

Yani proje hazir algoritmalar listesi degil. Hedef, metaheuristic tasarlama dili kurmak.

## Bugun Neye Sahibiz?

Bu repoda su an su katmanlar var:

- ortak runtime state: `BallistaContext`
- slot schema: bir verinin ne oldugunu ve nasil temsil edildigini anlatan metadata
- composable node'lar: `operator`, `sequence`, `loop`, `condition`
- operator registry: string isimleri gercek Python davranislarina baglayan katman
- operator param schema: operatorlerin hangi parametreleri bekledigini anlatan katman
- algorithm definition loader: JSON/dict tanimlarini calistirilabilir algoritmaya donusturen katman
- validation katmani: bozuk veya uyumsuz definition'lari erkenden yakalayan katman
- expression / rule DSL: kurallari kod yerine veriyle yazabilen katman
- demo operatorler ve iki demo algoritma

Bu sayede artik algoritmalar sadece Python class olarak degil, veri olarak da tanimlanabiliyor.

## Neden Bu Sirayla Gidiyoruz?

UI'yi once yapmak kolay gorunur ama yanlistir. Eger motor ve definition katmani zayif olursa, ortaya guzel gorunen ama hizla kisitlanan bir workflow builder cikar.

Bu yuzden sira su:

1. engine
2. definition dili
3. schema / params / condition
4. validation ve DSL
5. UI

Bu repo su an ilk uc adimi baslatmis durumda.

## Proje Yapisi

```text
src/ballista/
  engine.py       -> algoritma calistirici
  models.py       -> context, history ve slot schema modelleri
  nodes.py        -> node tipleri: sequence, loop, operator, condition
  registry.py     -> operator ve stop condition registry
  definitions.py  -> JSON/dict tabanli definition parser
  expression.py   -> expression / rule evaluator
  validation.py   -> definition validator
  examples.py     -> builtin operatorler ve demo algoritmalar
examples/
  astro_definition.json
  labeled_matrix_definition.json
  run_astro_demo.py
  run_definition_demo.py
  run_matrix_demo.py
tests/
  test_engine.py
```

## Hizli Baslangic

Astro demosu:

```powershell
$env:PYTHONPATH="src"
python examples/run_astro_demo.py
```

JSON definition demosu:

```powershell
$env:PYTHONPATH="src"
python examples/run_definition_demo.py
```

Matrix + label + condition demosu:

```powershell
$env:PYTHONPATH="src"
python examples/run_matrix_demo.py
```

Testler:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## Mimari Ozeti

### 1. Runtime State

`BallistaContext` su bilgileri tasir:

- `slots`: algoritmanin aktif verileri
- `slot_schema`: slot'larin tur/representation tanimlari
- `metrics`: iterasyon sirasinda uretilecek metrikler
- `history`: node bazli calisma kaydi
- `iteration`
- `stopped`

Bu yapi sayesinde algoritma tek tek fonksiyonlar degil, ortak bir blackboard state uzerinde calisan parcalar haline geliyor.

### 2. Node Modeli

Su an desteklenen node tipleri:

- `operator`
- `sequence`
- `loop`
- `condition`

Kisaca:

- `operator`: tek bir islem adimi
- `sequence`: adimlari sirayla calistirir
- `loop`: iterative metaheuristic akisini tasir
- `condition`: runtime state'e bakip branch secer

Bu set daha sonra buyuyebilir:

- `parallel`
- `subgraph`
- `termination`
- `event_hook`

### 3. Registry

`OperatorRegistry`, definition dosyasindaki string isimleri gercek Python operatorlerine baglar.

Ornek:

- definition icinde `operator: "apply_attraction"`
- registry icinde `apply_attraction -> Python function`

Bu, UI ile engine arasindaki temel koprudur.

Registry artik sadece handler tutmuyor. Ayni zamanda operatorlerin parametre semasini da tutuyor.

Bu sayede sistem su sorulari sormaya baslayabiliyor:

- bu operator hangi parametreleri bekliyor
- hangileri zorunlu
- bir parametre bir `matrix` slot'u mu bekliyor
- belirli bir representation gerekiyor mu

### 4. Definition Loader

`definitions.py`, JSON veya dict tanimini alip calisabilir node agacina cevirir.

Bugun destekledigi ana parcalar:

- `slot_definitions`
- `initial_slots`
- `root`
- `operator`
- `sequence`
- `loop`
- `condition`
- `$ref` tabanli deger cozme

## Slot Schema Neden Onemli?

Senin ihtiyacin sadece "bir matrix olsun" degil. Kullanici ayni zamanda bu verinin nasil dusunulecegini de secebilmeli.

Bu yuzden slot schema'da iki ayri kavram var:

- `kind`: teknik kategori
- `representation`: anlamsal veya kullanici secimli sunum bicimi

Ornekler:

- `kind: matrix`, `representation: binary`
- `kind: matrix`, `representation: weighted`
- `kind: mapping`, `representation: tag_map`
- `kind: object_collection`, `representation: labeled_graph_view`
- `kind: object`, `representation: execution_hint`

Bu tasarim kasti olarak biraz gevsek tutuldu. Cunku amac erken asamada kullaniciyi sabit veri tiplerine kilitlememek.

Bugun sistemde slot schema su alanlari tasiyabiliyor:

- `name`
- `kind`
- `representation`
- `default`
- `metadata`

Bu, ileride UI tarafinda su seyleri mumkun kilar:

- veri tanim ekranlari
- representation seciciler
- node editorde sadece uyumlu slot'lari onerme
- validation katmani

## Parametreli Operatorler

Operatorler artik sadece isimle cagrilmiyor; definition icinden parametre de alabiliyor.

Bu cok onemli cunku ayni operator farkli algoritmalarda farkli sekilde kullanilabilir.

Ornek:

```json
{
  "type": "operator",
  "name": "construct_labeled_solution",
  "operator": "construct_labeled_solution",
  "params": {
    "matrix": { "$ref": "slots.affinity_matrix" },
    "labels": { "$ref": "slots.node_labels" },
    "output_slot": "constructed_solution"
  }
}
```

Burada operator parametreleri:

- literal olabilir
- slot referansi olabilir
- metric referansi olabilir
- schema referansi olabilir
- nested obje/list yapisi olabilir

Su an desteklenen referans kokleri:

- `slots`
- `metrics`
- `schema`
- `iteration`

## Validation Katmani

Artik Ballista definition yuklemeden once temel dogrulama yapiyor.

Bu validator su tip problemleri erken yakalamaya calisiyor:

- eksik `name` veya `root`
- bilinmeyen node tipi
- bilinmeyen operator
- bilinmeyen stop condition
- eksik zorunlu operator parametresi
- gecersiz `$ref`
- bir operator parametresinin bekledigi slot turu ile verilen slot turunun uyusmamasi

Ornek olarak `construct_labeled_solution` operatoru `matrix` turunde bir slot bekliyor. Sen ona `mapping` turunde bir slot verirsen validator bunu yukleme asamasinda hata olarak isaretler.

Bu katman henuz baslangic halinde. Ama UI'ya gecmeden once cok degerli, cunku kullanicinin yaptigi tanimi daha calistirmadan once anlayip geri bildirim verebilmemizi saglar.

## Condition Node

`condition` node ile artik algoritma lineer akisa mahkum degil.

Ornek kullanim:

- bir matrix yogunsa intensify branch'ine git
- belirli bir etikete sahip cluster varsa baska local search sec
- bir metric esigi gecmisse perturb uygula

Desteklenen condition operatorleri:

- `equals`
- `not_equals`
- `gt`
- `gte`
- `lt`
- `lte`
- `contains`
- `in`
- `truthy`
- `all`
- `any`
- `not`

Bu su an temel bir katman. Daha sonra expression DSL ile cok daha guclu hale gelecek.

## Expression / Rule DSL

Bu adim, Ballista'nin "sinirsiz ozgurluge ne kadar yaklasabilecegi" sorusunda en kritik esiklerden biri.

Artik parametrelerde ve condition'larda expression kullanabiliyoruz. Bu sayede kullanici su tip kurallari veriyle ifade etmeye yaklasiyor:

- "eger critical label'a sahip ve 3'ten fazla baglantisi olan en az bir eleman varsa intensify et"
- "eger dense_rows metrikleri 2'nin ustundeyse farkli branch'e git"
- "bir liste icinden kosula uyan kac eleman var hesapla"

Su an desteklenen expression operatorleri:

- `ref`
- `if`
- `eq`, `neq`, `gt`, `gte`, `lt`, `lte`
- `and`, `or`, `not`
- `contains`, `in`
- `add`, `sub`, `mul`, `div`, `pow`, `mod`
- `abs`, `min`, `max`, `avg`, `round`
- `len`
- `get`
- `count`
- `sum`

Expression'lar hem `$ref` kullanabiliyor hem de iterasyon icinde `vars.item` gibi gecici degiskenler kullanabiliyor.

Ornek:

```json
{
  "$expr": {
    "op": "if",
    "condition": {
      "op": "gte",
      "left": {
        "op": "count",
        "source": { "$ref": "slots.constructed_solution" },
        "as": "item",
        "where": {
          "op": "eq",
          "left": { "op": "ref", "path": "vars.item.label" },
          "right": "critical"
        }
      },
      "right": 1
    },
    "then": "intensify",
    "else": "diversify"
  }
}
```

Bu su an son nokta degil ama ilk kez "Python operator yazmadan kural yazma" tarafina gercekten gecmeye basladik.

### Matematiksel Formula Konusu

Ballista'nin sonunda kullanici kendi matematiksel formullerini tanimlayabilecek mi?

Kisa cevap: evet, ama kontrollu bir DSL icinde.

Yani hedef su:

- kullanici agirliklar, skorlar, cezalar, yogunluklar, threshold'lar, olasilik benzeri hesaplari yazabilsin
- bunlari slot, metric ve gecici degiskenlerden hesaplayabilsin
- bunu Python kodu yazmadan yapabilsin

Ama hedef su degil:

- kullaniciya tamamen sinirsiz ham kod calistirma yetkisi vermek

Bu fark cok onemli. Cunku Ballista'nin uzun vadede guclu olmasi icin sadece esnek degil, ayni zamanda:

- guvenli
- dogrulanabilir
- UI tarafindan duzenlenebilir
- debug edilebilir

olmasi gerekiyor.

Yani "sinirsiz ozgurluk"e teorik olarak hicbir zaman tam ulasamayiz. Ama amac, kullanicinin metaheuristic tasarlama alaninda pratikte cok genis bir ozgurluk alani yasamasi.

## Demo'lar

### Astro Demo

`astro`, senin anlattigin tarza yakin oyuncak bir metaheuristic prototipi:

1. population olustur
2. en iyi bireye dogru cekim uygula
3. yakin bireyleri merge et
4. local search yap
5. best'i guncelle
6. hedef skora gelindiyse dur

Buradaki amac akademik olarak guclu bir algoritma gostermek degil; motorun ozel operator akisini tasiyabildigini gostermek.

### Matrix Demo

`labeled_matrix_definition.json` daha da kritik bir seyi gosteriyor:

1. binary bir matrix tanimla
2. bu matrix icin label map tanimla
3. matrix'ten labeled solution view uret
4. matematiksel bir expression ile `heuristic_score` hesapla
5. o skora gore `search_mode` hesapla
6. `condition` ile intensify veya diversify branch'ine git
7. sonraki heuristic stratejisini obje olarak yaz

Bu demo, kullanicinin sadece degerleri degil veri temsilini de secebildigi yone dogru attigimiz ilk ciddi adim.

Bu demo artik bir seyi daha gosteriyor:

- karar mantigi Python fonksiyonuna gomulu olmak zorunda degil
- kuralin kendisi de definition dosyasinda tasinabiliyor

## Su An Neler Eksik?

Simdiki sistem gucleniyor ama henuz tam urun degil.

Eksik olan temel katmanlar:

- definition validation
- daha guvenli ve daha zengin expression / rule DSL
- user-defined operator authoring
- operator param schema'lari
- branching'in daha zengin turleri
- reusable subgraph'lar
- UI / drag-and-drop editor
- trace visualization
- plugin tabanli operator marketplace

Yani bugun "motorun ciddi bir prototipi" var; "son kullanici uygulamasi" daha yok.

## Bir Sonraki Mantikli Teknik Adim

Buradan sonra en mantikli is sirasiyla:

1. expression DSL
2. daha zengin ref/path sistemi
3. reusable subgraph ve operator library yapisi
4. operator compatibility kurallari
5. UI tarafina uygun daha net definition contract'i

Validation ve param schema katmani artik basladi. Bir sonraki buyuk esik expression/rule tarafi.

Yine de validatori daha da guclendirmemiz gerekecek. Ozellikle su sorular icin:

- bu slot bu operator icin uygun mu
- bu branch condition'i gecerli mi
- bu representation ile bu operator birlikte kullanilabilir mi
- bu definition eksik veya bozuk mu

## Sonraki Sohbet Icin Durum Hafizasi

Bu bolum, baska chate gecildiginde hizli devam etmek icin.

Su anki durum:

- repo Python tabanli Ballista cekirdegi
- engine, context, history ve node sistemi hazir
- algorithm definition JSON/dict olarak yuklenebiliyor
- `slot_schema` ile veri temsili metadata'si tasinabiliyor
- operatorler runtime parametre alabiliyor
- `condition` node ile branching var
- expression DSL ile kurallar veri olarak yazilabiliyor
- `astro` demo calisiyor
- `matrix + label + branch` demo calisiyor
- testler geciyor

Bir sonraki mantikli hedef:

"Expression DSL'i genisletip daha guclu user-defined heuristic mekanizmalarina gecmek."

Yani sonraki sohbette dogrudan su islere girilebilir:

- expression DSL'de list/object transform operatorleri
- reusable subgraph/operator composition
- user-defined heuristic block'lari
- UI'nin tukecegi daha net bir definition contract'i

## Ozet

Ballista artik sadece fikir notu degil.

Su an:

- algoritma motoru var
- veri tabanli algorithm definition var
- schema ile veri temsilini de ifade etmeye basladik
- branching ve parametreli operator katmani var
- expression tabanli kural yazimi basladi

Henuz yok:

- tam kodsuz son kullanici urunu
- sinirsiz custom rule editor
- gorsel builder

Ama artik dogru omurgayi kuruyoruz.
