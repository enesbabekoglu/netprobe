# NetProbe Teknik Rapor Taslağı

Bu dosya Word'e taşınacak rapor metni ve görsel yerleşim yönergelerini içerir. PDF üretimi bu proje kodu tarafından yapılmaz. Word'e aktarırken her "Görsel Yerleşimi" bloğundaki ekran görüntüsü, grafik veya diyagram ilgili başlığın hemen altına eklenmelidir.

## Kapak

**Proje Başlığı:** NetProbe: UDP Tabanlı Güvenilir Dosya Aktarımı, Trafik İzleme ve Ağ Performans Analiz Platformu

**Ders:** Bilgisayar Ağları

**Üniversite / Bölüm:** Bursa Teknik Üniversitesi, Bilgisayar Mühendisliği Bölümü

**Grup Üyeleri:** Üye 1, Üye 2, Üye 3

**Teslim İçeriği:** Kaynak kod, GitHub bağlantısı, Markdown rapor taslağı, deney çıktıları, grafikler, log dosyaları ve demo paneli

**Görsel Yerleşimi:** Kapakta görsel şart değildir. İstenirse web dashboard'un küçük ve temiz bir ekran görüntüsü başlığın altında kullanılabilir. Görsel çok büyük olmamalı; kapak sayfasının teknik ve sade görünmesi tercih edilir.

## 1. Giriş

Bilgisayar ağlarında TCP ve UDP taşıma katmanı protokolleri farklı tasarım hedefleriyle kullanılır. TCP, bağlantı yönetimi, sıralama, güvenilir teslim, yeniden gönderim ve akış kontrolü gibi mekanizmaları kendi içinde sunarken UDP daha hafif, bağlantısız ve güvenilirlik garantisi vermeyen bir protokoldür. Bu nedenle UDP, düşük gecikme ve basitlik gerektiren uygulamalarda avantaj sağlarken, güvenilir teslim gerektiren senaryolarda ek mekanizmaların uygulama katmanında tasarlanmasını gerektirir.

Bu projede geliştirilen NetProbe sistemi, UDP üzerinde çalışan güvenilir bir dosya aktarım platformudur. Sistem yalnızca dosya göndermekle kalmaz; aktarım sırasında oluşan paket gönderimi, ACK alımı, timeout, yeniden gönderim ve duplicate paket olaylarını da kayıt altına alır. Bu veriler daha sonra throughput, goodput, completion time, packet loss rate ve retransmission rate gibi performans metriklerine dönüştürülür.

NetProbe'un temel amacı, UDP'nin doğal olarak sunmadığı güvenilirlik davranışlarını uygulama katmanında görünür ve ölçülebilir hale getirmektir. Projede istemci-sunucu mimarisi, paket tabanlı özel protokol, Selective Repeat sliding window yaklaşımı, yapay ağ kaybı simülasyonu, TCP karşılaştırması ve web tabanlı demo paneli birlikte tasarlanmıştır.

**Görsel Yerleşimi:** Bu bölümün sonuna web dashboard'un genel ekran görüntüsü konulmalıdır. Ekran görüntüsünde üst metrik kartları, transfer paneli ve canlı trafik logu aynı karede görünmelidir. Önerilen başlık: "Şekil 1. NetProbe web dashboard genel görünümü".

## 2. Problem Tanımı

UDP socket programlama ile dosya aktarımı yapıldığında gönderilen datagramların karşı tarafa ulaşıp ulaşmadığı, doğru sırada alınıp alınmadığı veya tekrar gelip gelmediği garanti edilmez. Ayrıca UDP'de bağlantı kurulumu, ACK üretimi, timeout kontrolü ve kaybolan paketlerin yeniden gönderimi gibi mekanizmalar standart olarak bulunmaz.

Bu proje kapsamında çözülmesi gereken ana problem, UDP'nin bağlantısız yapısını koruyarak güvenilir dosya aktarımı gerçekleştirmektir. Bunun için dosya parçalara bölünmeli, her parçaya sequence number atanmalı, alıcı her doğru paket için ACK üretmeli, gönderici belirli süre içinde ACK alamazsa paketi yeniden göndermeli ve aktarım sonunda dosya bütünlüğü SHA-256 hash ile doğrulanmalıdır.

Ek olarak, yalnızca çalışan bir dosya aktarımı yeterli değildir. Aktarım sürecinin ölçülebilir olması gerekir. Bu nedenle NetProbe, her ağ olayını JSONL formatında loglar ve deney sonuçlarını CSV/JSON özetlerine dönüştürür. Böylece farklı paket boyutu, timeout değeri, yapay kayıp oranı ve dosya boyutu gibi değişkenlerin protokol davranışına etkisi teknik olarak yorumlanabilir.

**Görsel Yerleşimi:** Bu bölümde görsel zorunlu değildir. İstenirse UDP ve TCP'nin temel farklarını gösteren küçük bir karşılaştırma tablosu eklenebilir. Tablo metinsel olacağı için Word içinde elle hazırlanabilir.

## 3. Kullanılan Teknolojiler

NetProbe, ağ protokolü geliştirme, ölçüm ve demo sunumu için birbirini tamamlayan açık kaynak teknolojilerle geliştirilmiştir. Proje tek bir monolitik uygulama yerine modüler Python paketleri, yerel web arayüzü ve otomatik analiz çıktıları üzerine kuruludur.

### 3.1. Geliştirme Dili ve Çalışma Ortamı

| Teknoloji | Kullanım Amacı |
| --- | --- |
| Python 3 | UDP istemci/sunucu, protokol, deney, analiz ve web backend geliştirme |
| Python `socket` modülü | UDP ve TCP tabanlı ağ iletişimi |
| `threading` | UDP sunucusunun arka planda çalıştırılması |
| `dataclasses`, `pathlib`, `json`, `csv` | Yapılandırma, dosya yönetimi ve sonuç üretimi |
| Git / GitHub | Sürüm kontrolü ve proje teslimi |

### 3.2. Ağ, Protokol ve Güvenilirlik Katmanı

| Teknoloji / Yöntem | Kullanım Amacı |
| --- | --- |
| UDP (User Datagram Protocol) | Bağlantısız temel taşıma katmanı |
| Özel NetProbe uygulama protokolü | START, DATA, ACK, END, RESULT, ERROR paket tipleri |
| Selective Repeat sliding window | Eşzamanlı paket gönderimi ve ACK takibi |
| CRC32 checksum | Paket payload bütünlük kontrolü |
| SHA-256 | Dosya düzeyinde bütünlük doğrulaması |
| Yapay loss/delay simülatörü | Kontrollü paket kaybı ve gecikme deneyleri |
| TCP baseline karşılaştırması | İşletim sistemi TCP davranışı ile kıyaslama |

### 3.3. Web Paneli ve Kullanıcı Arayüzü

| Teknoloji | Kullanım Amacı |
| --- | --- |
| Flask 3.x | Web dashboard backend ve REST API |
| Flask-Sock | Canlı log akışı için WebSocket (`/ws/events`) |
| HTML5 + Vanilla JavaScript | İstemci tarafı panel mantığı ve API çağrıları |
| Tailwind CSS 3.x | Yerel, derlenmiş ve minimal arayüz stilleri |
| Inter font (`@fontsource/inter`) | Türkçe karakter destekli yerel tipografi |
| react-icons (Heroicons / `hi2`) | Panel ikonlarının SVG olarak üretilmesi |
| Node.js / npm | CSS, font ve ikon asset derleme süreci |

Web arayüzü demo sırasında CDN veya harici internet bağlantısı gerektirmeyecek şekilde tasarlanmıştır. Üretilen CSS, font ve ikon dosyaları `web/static/` altında yerel olarak sunulur.

### 3.4. Veri Kaydı, Analiz ve Görselleştirme

| Teknoloji / Format | Kullanım Amacı |
| --- | --- |
| JSONL | Client/server olay kayıtları |
| CSV / JSON | Deney sonuçlarının özetlenmesi |
| Python tabanlı SVG üretimi | Performans grafiklerinin otomatik oluşturulması |
| Markdown | Rapor taslağı ve analiz özeti |

### 3.5. Test ve Teslim

| Teknoloji | Kullanım Amacı |
| --- | --- |
| pytest | Protokol ve aktarım davranışı testleri |
| ZIP teslim paketi | Kaynak kod, çıktılar, grafikler ve dokümantasyonun paketlenmesi |

**Görsel Yerleşimi:** Bu bölümde görsel zorunlu değildir. İstenirse kullanılan teknolojileri özetleyen sade bir tablo Word'e aktarılabilir. Tablo bu bölümdeki alt başlıklardan türetilebilir.

## 4. Sistem Mimarisi

NetProbe dört ana katmandan oluşur. Birinci katman UDP istemci ve sunucu bileşenleridir. İstemci dosyayı paketlere böler, paketleri pencere mantığı ile gönderir ve ACK yanıtlarını takip eder. Sunucu gelen paketleri session id ve sequence number değerlerine göre saklar, duplicate paketleri ayıklar ve aktarım sonunda dosyayı yeniden oluşturur.

İkinci katman uygulama protokolüdür. Bu katman START, DATA, ACK, END, RESULT ve ERROR paket tiplerini tanımlar. Her paket NetProbe magic değeri, protokol versiyonu, paket tipi, session id, sequence number, total packet count, payload length ve checksum alanlarıyla kodlanır.

Üçüncü katman trafik izleme ve analiz katmanıdır. Client ve server tarafındaki olaylar JSONL dosyalarına yazılır. Deney çalıştırma modülü bu loglardan ve aktarım sonuçlarından CSV/JSON özetleri üretir. Analiz modülü bu sonuçları grafiklere ve teknik yorumlara dönüştürür.

Dördüncü katman demo ve kullanım arayüzüdür. Flask tabanlı web paneli, yerel Tailwind CSS ve yerel Inter fontu ile internet bağlantısı olmadan çalışır. Panel üzerinden dosya aktarımı başlatılabilir, yapay loss/delay parametreleri değiştirilebilir, canlı loglar izlenebilir ve deney grafikleri görüntülenebilir.

**Görsel Yerleşimi:** Bu bölümün ortasına mimari diyagram eklenmelidir. Diyagramda solda "Client", ortada "Reliable UDP Protocol + Loss/Delay Simulator", sağda "Server" bulunmalıdır. Alt tarafta "JSONL Logs", "Metrics CSV/JSON", "Analysis Charts" ve "Web Dashboard" kutuları yer almalıdır. Önerilen başlık: "Şekil 2. NetProbe sistem mimarisi".

## 5. Protokol Tasarımı

NetProbe protokolü, UDP datagramları içinde taşınan özel bir uygulama katmanı paket formatı kullanır. Her paket sabit uzunluklu bir header ve değişken uzunluklu payload alanından oluşur. Header alanı paketin türünü, ait olduğu session bilgisini, sırasını ve payload bütünlüğünü taşır.

| Alan | Açıklama |
| --- | --- |
| Magic | Paketin NetProbe protokolüne ait olduğunu gösterir. |
| Version | Protokol sürümünü belirtir. |
| Packet Type | START, DATA, ACK, END, RESULT veya ERROR değerlerinden biridir. |
| Session ID | Aynı dosya aktarımına ait paketleri gruplamak için kullanılır. |
| Sequence Number | DATA paketlerinde dosya parçasının sırasını, ACK paketlerinde onaylanan paketi gösterir. |
| Total Packet Count | Dosyanın toplam kaç parçaya ayrıldığını belirtir. |
| Payload Length | Payload alanının byte cinsinden uzunluğudur. |
| Checksum | Payload üzerinde hesaplanan CRC32 değeridir. |
| Payload | Metadata, dosya parçası veya sonuç bilgisidir. |

Aktarım START paketi ile başlar. START payload'u dosya adı, dosya boyutu, SHA-256 hash, payload size, toplam paket sayısı ve pencere boyutu gibi metadata değerlerini içerir. Ardından DATA paketleri gönderilir. Alıcı her DATA paketi için aynı sequence number değerine sahip ACK döndürür. Tüm DATA paketleri onaylandıktan sonra istemci END paketi gönderir. Sunucu dosyayı birleştirir, SHA-256 doğrulaması yapar ve RESULT paketi ile sonucu bildirir.

**Görsel Yerleşimi:** Paket formatı tablosunun hemen altına sequence/ACK akış diyagramı eklenmelidir. Diyagramda START, ACK, DATA[0..n], ACK[0..n], END ve RESULT sırası gösterilmelidir. Önerilen başlık: "Şekil 3. NetProbe paket ve ACK akışı".

## 6. Güvenilir Aktarım Mekanizması

NetProbe, varsayılan olarak Selective Repeat sliding window yaklaşımını kullanır. Gönderici aynı anda pencere boyutu kadar paketi beklemede tutabilir. Varsayılan pencere boyutu 8'dir. Bir paket için ACK geldiğinde yalnızca ilgili sequence number onaylanır; diğer paketler bağımsız olarak beklemeye devam eder. Bu yapı, stop-and-wait yaklaşımına göre daha yüksek verim sağlar.

Varsayılan parametreler şu şekildedir:

| Parametre | Varsayılan Değer |
| --- | ---: |
| Payload size | 1024 byte |
| Timeout | 0.5 saniye |
| Max retries | 5 |
| Window size | 8 |

ACK belirlenen timeout süresi içinde gelmezse gönderici ilgili paket için timeout olayı üretir ve paketi yeniden gönderir. Her veri paketi için en fazla 5 yeniden gönderim denemesi yapılır. Bu sınır aşılırsa aktarım başarısız kabul edilir ve hata hem kullanıcıya hem log dosyalarına yazılır.

Duplicate paketler sunucu tarafında sequence number ile tespit edilir. Sunucu aynı sequence number değerine ait veriyi daha önce aldıysa bu payload'u dosyaya ikinci kez yazmaz. Bunun yerine aynı ACK'i tekrar gönderir ve duplicate_packet olayını loglar. Bu davranış, UDP ortamında gecikmiş veya tekrar gelen paketlerin dosya bütünlüğünü bozmasını engeller.

**Görsel Yerleşimi:** Bu bölümde timeout ve retransmission zaman çizelgesi kullanılmalıdır. İlk çizgide DATA packet gönderimi, ACK gelmemesi, timeout ve retransmission gösterilmelidir. İkinci küçük çizgide duplicate DATA gelişi ve tekrar ACK gönderimi gösterilmelidir. Önerilen başlık: "Şekil 4. Timeout, retransmission ve duplicate paket davranışı".

## 7. Gerçekleme, Deney ve Ölçüm

Proje Python modülleriyle geliştirilmiştir: `protocol`, `client`, `server`, `simulator`, `metrics`, `experiments`, `analysis`, `tcp_compare` ve `web`. Aktarım olayları JSONL olarak kaydedilir; web paneli transfer, deney, metrik, canlı log ve grafikleri tek ekranda sunar.

```bash
python3 -m netprobe.server --host 127.0.0.1 --port 9999
python3 -m netprobe.client send data/sample_files/small_16kb.bin --host 127.0.0.1 --port 9999
python3 -m netprobe.experiments run --profile quick
python3 -m netprobe.analysis build
python3 -m netprobe.web --port 5000
```

Deneyler loopback üzerinde çalıştırılmış; paket kaybı yapay simülatör ile kontrol edilmiştir. Ölçülen temel metrikler: throughput, goodput, completion time, loss rate, retransmission rate ve RTT.

| Senaryo | Parametreler |
| --- | --- |
| Paket boyutu | 512, 1024, 2048, 4096 byte |
| Timeout | 0.2, 0.5, 1.0, 1.5 s |
| Kayıp oranı | 0%, 2%, 5%, 10% |
| Dosya boyutu | 16 KB, 128 KB, 512 KB |
| TCP karşılaştırması | Reliable UDP ve TCP |

Sonuçlar `outputs/experiments/results.csv`, grafikler `outputs/analysis/charts/` altında üretilir. Rapora eklenecek 5 SVG grafiği: paket boyutu, timeout, kayıp oranı, dosya boyutu ve TCP karşılaştırması.

**Görsel:** Modül diyagramı, CLI aktarım ekran görüntüsü, canlı log paneli ve analiz grafikleri.

## 8. Sonuç ve Tartışma

Deneyler; sequence number, ACK, timeout ve retransmission mekanizmalarının birlikte çalışması gerektiğini göstermiştir. Selective Repeat düşük kayıplı ortamda daha verimlidir; kayıp ve timeout arttıkça süre uzar, goodput düşer.

Karşılaşılan başlıca sorunlar ACK/timeout, sequence tabanlı duplicate yönetimi, yapay simülatör ve otomatik CSV/grafik üretimi ile giderilmiştir.

NetProbe, UDP üzerinde güvenilir aktarımı uygulama katmanında gösterir. Gelecekte adaptif timeout, congestion control, çoklu istemci, Wireshark entegrasyonu ve gerçek ağ deneyleri eklenebilir.

**Görsel:** Başarılı hash doğrulama ve isteğe bağlı max retry failure ekran görüntüsü.

## 9. Grup ve Ekler

| Üye | Sorumluluk |
| --- | --- |
| Üye 1 | Protokol, client/server, ACK/timeout |
| Üye 2 | Loglama, deney, metrik, grafik |
| Üye 3 | Web UI, rapor, demo ve teslim |

Teslim paketi: kaynak kod, README, JSONL loglar, deney CSV dosyası, web ekran görüntüleri ve analiz grafikleri.
