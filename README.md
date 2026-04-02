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
- algorithm definition loader: JSON/dict tanimlarini calistirilabilir algoritmaya donusturen katman
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
4. matrix yogunlugu ve critical label varligina gore `search_mode` sec
5. `condition` ile intensify veya diversify branch'ine git
6. sonraki heuristic stratejisini obje olarak yaz

Bu demo, kullanicinin sadece degerleri degil veri temsilini de secebildigi yone dogru attigimiz ilk ciddi adim.

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

1. definition validation
2. operator param schema'lari
3. expression DSL
4. daha zengin ref/path sistemi
5. reusable subgraph ve operator library yapisi

Ozellikle validation cok kritik. Cunku UI gelmeden once bile su sorulara cevap vermemiz gerekecek:

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
- `astro` demo calisiyor
- `matrix + label + branch` demo calisiyor
- testler geciyor

Bir sonraki mantikli hedef:

"Definition validation ve expression katmanini ekleyip, kullanicinin tanimladigi akisin dogrulugunu ve esnekligini artirmak."

Yani sonraki sohbette dogrudan su islere girilebilir:

- definition validator
- operator param schema modeli
- expression DSL taslagi
- UI'nin tukecegi daha net bir definition contract'i

## Ozet

Ballista artik sadece fikir notu degil.

Su an:

- algoritma motoru var
- veri tabanli algorithm definition var
- schema ile veri temsilini de ifade etmeye basladik
- branching ve parametreli operator katmani var

Henuz yok:

- tam kodsuz son kullanici urunu
- sinirsiz custom rule editor
- gorsel builder

Ama artik dogru omurgayi kuruyoruz.
