# NetProbe

NetProbe, Bilgisayar Ağları dersi dönem projesi için geliştirilen UDP tabanlı güvenilir dosya aktarımı, trafik izleme ve ağ performans analiz platformudur.

Proje; sequence number, ACK, timeout, retransmission, duplicate paket yönetimi, SHA-256 bütünlük doğrulaması, yapay loss/delay simülasyonu, deney otomasyonu, grafik üretimi ve web demo panelini tek repoda toplar.

GitHub bağlantısı: https://github.com/enesbabekoglu/netprobe.git

## Kurulum

Python bağımlılıkları:

```bash
python3 -m pip install -r requirements.txt
```

Web UI asset bağımlılıkları ve yerel CSS/font üretimi:

```bash
npm install
mkdir -p web/static/fonts/inter
cp node_modules/@fontsource/inter/files/inter-latin-400-normal.woff2 web/static/fonts/inter/
cp node_modules/@fontsource/inter/files/inter-latin-600-normal.woff2 web/static/fonts/inter/
cp node_modules/@fontsource/inter/files/inter-latin-700-normal.woff2 web/static/fonts/inter/
npm run build:css
```

Runtime sırasında Tailwind CDN veya harici font isteği kullanılmaz. Üretilmiş CSS `web/static/css/tailwind.css`, Inter fontları `web/static/fonts/inter/` altındadır.

## Hızlı Demo

Örnek dosyaları oluştur:

```bash
python3 -m netprobe.sample_data
```

Bir terminalde UDP server başlat:

```bash
python3 -m netprobe.server --host 127.0.0.1 --port 9999
```

İkinci terminalde dosya gönder:

```bash
python3 -m netprobe.client send data/sample_files/small_16kb.bin --host 127.0.0.1 --port 9999 --payload-size 1024 --timeout 0.5 --window-size 8 --loss-rate 0.05
```

Stop-and-wait davranışını göstermek için:

```bash
python3 -m netprobe.client send data/sample_files/small_16kb.bin --window-size 1
```

## Web Panel

```bash
python3 -m netprobe.web --port 5000
```

Tarayıcıda:

```text
http://127.0.0.1:5000
```

Panelde dosya aktarımı, canlı trafik logları, deney çalıştırma ve analiz grafiklerini görüntüleme alanları bulunur.

Web panel canlı logları periyodik sayfa yenilemesiyle değil, native WebSocket bağlantısı ile izler. Üst sağdaki `WS canli` etiketi görünüyorsa log tablosu ve grafik listesi anlık akışla güncellenir.

## Projeyi Nasıl Test Edeceğim?

En anlaşılır demo yolu web panelidir.

1. Kurulumu yap:

```bash
python3 -m pip install -r requirements.txt
npm install
npm run build:css
```

2. Web paneli başlat:

```bash
python3 -m netprobe.web --port 5000
```

3. Tarayıcıda aç:

```text
http://127.0.0.1:5000
```

4. Hazır örnek dosyayla hızlı başarılı test:

- `Dosya` listesinden `small_16kb.bin` seç.
- `Payload=1024`, `Timeout=0.5`, `Window=8`, `Max retry=5`, `Loss rate=0` bırak.
- `Transfer Baslat` butonuna bas.
- Beklenen sonuç: `Durum=success`, `SHA-256` dolu, canlı log tablosunda `packet_sent`, `ack_received`, `transfer_completed` olayları görünür.

5. Kendi dosyanla test:

- `Kendi dosyani yukle` alanından bilgisayarından küçük veya orta boy bir dosya seç.
- `Dosyayi Listeye Ekle` butonuna bas.
- Dosya, `Dosya` listesinin içine `yuklenen` etiketiyle eklenir.
- Bu dosya seçiliyken `Transfer Baslat` butonuna bas.
- Beklenen sonuç: dosya UDP ile `outputs/web_received/` içine aktarılır ve hash doğrulaması başarılı olur.

6. Kayıplı ağ testi:

- `Loss rate` değerini `0.05` yap.
- `Transfer Baslat` butonuna bas.
- Beklenen sonuç: aktarım çoğunlukla başarılı tamamlanır; canlı logda `packet_dropped_simulated`, `timeout` ve `retransmission=true` olayları görünür.

7. Hata senaryosu testi:

- `Loss rate` değerini `1.0` yap.
- `Max retry` değerini `1` veya `2` yap.
- `Transfer Baslat` butonuna bas.
- Beklenen sonuç: `Durum=failed`; mesajda max retry sınırının aşıldığı görünür. Bu ekran görüntüsü rapordaki max retry failure görseli için kullanılabilir.

8. Deney grafikleri:

- `Deneyleri Calistir` butonuna bas.
- Ardından `Analiz Uret` butonuna bas.
- Beklenen çıktı: `outputs/analysis/charts/` altında paket boyutu, timeout, loss rate, dosya boyutu ve TCP karşılaştırması SVG grafikleri oluşur.

CLI ile manuel test etmek istersen:

```bash
python3 -m netprobe.server --host 127.0.0.1 --port 9999
```

Ayrı terminal:

```bash
python3 -m netprobe.client send path/to/dosyan.bin --host 127.0.0.1 --port 9999 --payload-size 1024 --timeout 0.5 --window-size 8 --loss-rate 0.05
```

CLI çıktısında `status=success`, `sha256`, `server_sha256`, `throughput`, `goodput`, `retransmissions` ve `message=transfer completed and sha256 verified` satırları görünmelidir.

## Deney ve Analiz

Karşılaştırmalı deneyleri çalıştır:

```bash
python3 -m netprobe.experiments run --profile quick
```

Daha kapsamlı deney:

```bash
python3 -m netprobe.experiments run --profile full
```

Grafikleri ve analiz özetini tekrar üret:

```bash
python3 -m netprobe.analysis build
```

Çıktılar:

- `outputs/experiments/results.csv`
- `outputs/experiments/results.json`
- `outputs/analysis/analysis-summary.md`
- `outputs/analysis/charts/*.svg`
- `outputs/logs/**/*.jsonl`

## Testler

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
```

Test kapsamı:

- Packet encode/decode
- Checksum hatası yakalama
- Başarılı UDP dosya aktarımı
- Yapay kayıpta retransmission ile toparlanma
- Max retry sonrası kontrollü başarısızlık
- Duplicate paketin dosyaya ikinci kez yazılmaması

## Teslim Paketi

Önce deneyleri ve analizi üretin, sonra zip hazırlayın:

```bash
python3 -m netprobe.experiments run --profile quick
python3 -m netprobe.deliver
```

Teslim paketi:

```text
dist/netprobe-deliverable.zip
```

Paket; kaynak kodları, web assetlerini, testleri, rapor taslağını, örnek dosyaları, deney sonuçlarını, grafikleri ve logları içerir.

## Proje Yapısı

```text
netprobe/
  protocol.py       Paket formatı, checksum, SHA-256 yardımcıları
  client.py         Reliable UDP istemci ve sliding window aktarımı
  server.py         UDP server, ACK, duplicate yönetimi, dosya birleştirme
  simulator.py      Yapay loss/delay modülü
  metrics.py        Throughput, goodput, retransmission metrikleri
  experiments.py    Karşılaştırmalı deney matrisi
  analysis.py       Grafik ve teknik yorum üretimi
  tcp_compare.py    TCP baseline aktarımı
  web.py            Flask web paneli
web/
  templates/        HTML arayüz
  static/           Yerel Tailwind CSS, JS ve Inter fontları
docs/
  donem-projesi-foyu.md
  rapor-taslagi.md
tests/
  test_protocol.py
  test_transfer.py
```
