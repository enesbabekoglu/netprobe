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

## 3. Sistem Mimarisi

NetProbe dört ana katmandan oluşur. Birinci katman UDP istemci ve sunucu bileşenleridir. İstemci dosyayı paketlere böler, paketleri pencere mantığı ile gönderir ve ACK yanıtlarını takip eder. Sunucu gelen paketleri session id ve sequence number değerlerine göre saklar, duplicate paketleri ayıklar ve aktarım sonunda dosyayı yeniden oluşturur.

İkinci katman uygulama protokolüdür. Bu katman START, DATA, ACK, END, RESULT ve ERROR paket tiplerini tanımlar. Her paket NetProbe magic değeri, protokol versiyonu, paket tipi, session id, sequence number, total packet count, payload length ve checksum alanlarıyla kodlanır.

Üçüncü katman trafik izleme ve analiz katmanıdır. Client ve server tarafındaki olaylar JSONL dosyalarına yazılır. Deney çalıştırma modülü bu loglardan ve aktarım sonuçlarından CSV/JSON özetleri üretir. Analiz modülü bu sonuçları grafiklere ve teknik yorumlara dönüştürür.

Dördüncü katman demo ve kullanım arayüzüdür. Flask tabanlı web paneli, yerel Tailwind CSS ve yerel Inter fontu ile internet bağlantısı olmadan çalışır. Panel üzerinden dosya aktarımı başlatılabilir, yapay loss/delay parametreleri değiştirilebilir, canlı loglar izlenebilir ve deney grafikleri görüntülenebilir.

**Görsel Yerleşimi:** Bu bölümün ortasına mimari diyagram eklenmelidir. Diyagramda solda "Client", ortada "Reliable UDP Protocol + Loss/Delay Simulator", sağda "Server" bulunmalıdır. Alt tarafta "JSONL Logs", "Metrics CSV/JSON", "Analysis Charts" ve "Web Dashboard" kutuları yer almalıdır. Önerilen başlık: "Şekil 2. NetProbe sistem mimarisi".

## 4. Protokol Tasarımı

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

## 5. Güvenilir Aktarım Mekanizması

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

## 6. Gerçekleme Detayları

Proje Python ile modüler şekilde geliştirilmiştir. `protocol.py` paket kodlama ve çözme işlemlerini, `client.py` güvenilir UDP istemcisini, `server.py` UDP sunucusunu, `simulator.py` yapay loss/delay davranışını, `metrics.py` performans metriklerini, `experiments.py` karşılaştırmalı deneyleri, `analysis.py` grafik üretimini, `tcp_compare.py` TCP baseline aktarımını ve `web.py` Flask demo panelini içerir.

Komut satırı kullanımı şu şekildedir:

```bash
python3 -m netprobe.server --host 127.0.0.1 --port 9999
python3 -m netprobe.client send data/sample_files/small_16kb.bin --host 127.0.0.1 --port 9999
python3 -m netprobe.experiments run --profile quick
python3 -m netprobe.analysis build
python3 -m netprobe.web --port 5000
```

Web arayüzü Flask backend, vanilla JavaScript, yerel Tailwind CSS ve yerel Inter font dosyalarıyla hazırlanmıştır. Böylece demo sırasında CDN veya internet bağlantısına ihtiyaç duyulmaz. Arayüz siyah, beyaz ve gri tonlarıyla minimal tutulmuştur. Transfer paneli, deney paneli, metrik kartları, canlı log tablosu ve analiz grafikleri aynı ekranda gösterilir.

**Görsel Yerleşimi:** Bu bölümde iki görsel önerilir. İlk görsel proje modül yapısı diyagramıdır; modüller ve görevleri gösterilmelidir. İkinci görsel başarılı CLI aktarım ekran görüntüsüdür. CLI ekran görüntüsünde status, session id, SHA-256, destination, throughput, goodput ve retransmission satırları görünmelidir.

## 7. Trafik İzleme ve Olay Kayıtları

NetProbe, aktarım sürecindeki olayları JSONL formatında kayıt altına alır. Her satır tek bir olayı temsil eder ve timestamp, role, event, session id, sequence number ve ilgili ek alanları içerir. Bu format hem insan tarafından okunabilir hem de analiz araçları tarafından kolayca işlenebilir.

Kaydedilen temel olaylar şunlardır:

| Olay | Açıklama |
| --- | --- |
| packet_sent | Client tarafında START, DATA veya END paketi gönderildi. |
| packet_received | Server tarafında DATA paketi alındı. |
| ack_sent | Server ilgili paket için ACK gönderdi. |
| ack_received | Client ilgili ACK'i aldı. |
| timeout | Client belirlenen sürede ACK alamadı. |
| packet_dropped_simulated | Yapay kayıp modülü paketi göndermedi. |
| duplicate_packet | Server aynı sequence number değerini ikinci kez aldı. |
| transfer_completed | Aktarım ve hash doğrulaması başarıyla tamamlandı. |
| transfer_failed | Max retry, eksik paket veya hash uyuşmazlığı nedeniyle aktarım başarısız oldu. |

Bu loglar sayesinde yalnızca sonuç metrikleri değil, metriklere yol açan protokol davranışı da incelenebilir. Örneğin yüksek loss rate değerinde packet_dropped_simulated ve timeout sayılarının arttığı; bunun retransmission rate ve completion time değerlerini yükselttiği doğrudan gözlemlenebilir.

**Görsel Yerleşimi:** Bu bölümde web panelindeki canlı trafik logu ekran görüntüsü kullanılmalıdır. Ayrıca JSONL log dosyasından 5-6 satırlık küçük bir tablo kesiti Word içine eklenebilir. Önerilen başlıklar: "Şekil 5. Canlı trafik log paneli" ve "Tablo 3. Örnek JSONL olay kayıtları".

## 8. Deney Ortamı

Deneyler yerel makinede loopback ağ arayüzü üzerinden çalıştırılmıştır. Gerçek ağda oluşabilecek paket kaybını kontrollü şekilde incelemek için istemci tarafında yapay loss/delay simülatörü kullanılmıştır. Böylece aynı deney parametreleri tekrar çalıştırıldığında benzer sonuçlar üretilebilir.

Deneylerde kullanılan temel senaryolar:

| Senaryo | Değiştirilen Parametreler | Amaç |
| --- | --- | --- |
| Paket boyutu etkisi | 512, 1024, 2048, 4096 byte | Header yükü ve paket sayısının throughput/goodput etkisini görmek |
| Timeout etkisi | 0.2, 0.5, 1.0, 1.5 saniye | Gereksiz retransmission ve bekleme süresi dengesini yorumlamak |
| Kayıp oranı etkisi | 0%, 2%, 5%, 10% | Paket kaybının retry, goodput ve completion time etkisini ölçmek |
| Dosya boyutu etkisi | 16 KB, 128 KB, 512 KB | Dosya büyüklüğünün verimlilik üzerindeki etkisini gözlemlemek |
| TCP karşılaştırması | Reliable UDP ve TCP | Uygulama katmanı güvenilirlik yaklaşımını TCP baseline ile karşılaştırmak |

**Görsel Yerleşimi:** Bu bölümde deney matrisi tablosu mutlaka kullanılmalıdır. Ek olarak `data/sample_files` veya `outputs/sample_files` klasöründeki dosya boyutlarını gösteren küçük tablo eklenmelidir. Görsel ekran görüntüsü gerekmiyorsa tablo yeterlidir.

## 9. Performans Metrikleri

Bu projede kullanılan ana performans metrikleri şunlardır:

| Metrik | Tanım |
| --- | --- |
| Throughput | Uygulama seviyesinde gönderilen toplam byte miktarının süreye oranıdır. Retransmission paketlerini de etkiler. |
| Goodput | Başarıyla aktarılan faydalı dosya verisinin süreye oranıdır. |
| Completion time | START ile RESULT arasında geçen toplam süredir. |
| Packet loss rate | Simüle edilen kayıp paketlerin toplam gönderim girişimlerine oranıdır. |
| Retransmission rate | Yeniden gönderilen paket sayısının toplam veri paketlerine oranıdır. |
| Average RTT | DATA gönderimi ile ACK alımı arasında ölçülen ortalama süredir. |

Throughput ve goodput birlikte yorumlanmalıdır. Örneğin retransmission arttığında ağ üzerinden daha fazla byte gönderildiği için throughput yüksek görünebilir, ancak faydalı veri aktarım verimi düştüğü için goodput azalabilir. Bu nedenle yalnızca throughput değerine bakmak protokol başarımını doğru yorumlamak için yeterli değildir.

**Görsel Yerleşimi:** Bu bölümde görsel yerine metrik formüllerini içeren sade bir tablo kullanılmalıdır. İstenirse throughput ve goodput farkını gösteren küçük bir açıklama diyagramı eklenebilir.

## 10. Performans Sonuçları

Deney çıktıları `outputs/experiments/results.csv` dosyasında saklanır. Grafikler `outputs/analysis/charts/` klasöründe SVG olarak üretilir. Word raporuna aşağıdaki grafikler bu sırayla eklenmelidir. Word sürümünüz SVG eklemeyi desteklemiyorsa SVG dosyasını tarayıcıda açıp ekran görüntüsü olarak rapora koyabilirsiniz.

### 10.1. Paket Boyutunun Etkisi

Paket boyutu arttıkça aynı dosya daha az sayıda DATA paketiyle gönderilir. Bu durumda her paket için eklenen header yükünün toplam veriye oranı azalır. Bu nedenle kayıpsız veya düşük kayıplı ortamda throughput ve goodput değerlerinin artması beklenir. Ancak paket boyutu çok büyüdüğünde tek bir paket kaybının yeniden gönderim maliyeti de artar.

**Görsel Yerleşimi:** `outputs/analysis/charts/packet-size-throughput-goodput.svg` grafiğini bu alt başlığın altına koyun. Grafik altında şu yorumu ekleyin: "Payload boyutu arttığında protokol overhead'i azalmış, fakat kayıp durumunda büyük paketlerin yeniden gönderim maliyeti dikkate alınmalıdır."

### 10.2. Timeout Değerinin Etkisi

Timeout değeri düşük seçilirse, ACK gecikmeleri gerçek paket kaybı gibi algılanabilir. Bu durum gereksiz retransmission sayısını artırır. Timeout değeri çok yüksek seçilirse, gerçekten kaybolan paketler geç fark edilir ve completion time artar. Bu nedenle timeout değeri, ağ gecikmesi ile yeniden gönderim maliyeti arasında denge kurmalıdır.

**Görsel Yerleşimi:** `outputs/analysis/charts/timeout-retransmission-rate.svg` grafiğini bu alt başlığın altına koyun. Grafik altında timeout değerinin retransmission rate üzerindeki etkisini 3-4 cümleyle yorumlayın.

### 10.3. Yapay Kayıp Oranının Etkisi

Kayıp oranı arttıkça daha fazla DATA paketi ACK alamadan timeout'a düşer. Bu durum retransmission sayısını artırır, aktarım süresini uzatır ve goodput değerini düşürür. NetProbe bu davranışı packet_dropped_simulated, timeout ve packet_sent olayları üzerinden açıkça loglar.

**Görsel Yerleşimi:** `outputs/analysis/charts/loss-completion-time.svg` grafiğini bu alt başlığın altına koyun. Grafik altında yüksek loss rate değerlerinin completion time üzerindeki etkisini açıklayın.

### 10.4. Dosya Boyutunun Etkisi

Küçük dosyalarda START, END, RESULT ve ACK gibi kontrol paketlerinin toplam aktarıma oranı daha yüksektir. Büyük dosyalarda bu sabit maliyet daha geniş veri miktarına yayıldığı için goodput daha dengeli hale gelir. Ancak dosya boyutu arttıkça toplam completion time da doğal olarak artar.

**Görsel Yerleşimi:** `outputs/analysis/charts/file-size-goodput.svg` grafiğini bu alt başlığın altına koyun. Grafik altında küçük ve büyük dosya davranışını karşılaştırın.

### 10.5. Reliable UDP ve TCP Karşılaştırması

TCP, işletim sistemi tarafından optimize edilen olgun güvenilirlik mekanizmalarına sahiptir. NetProbe ise güvenilirliği uygulama katmanında gösterilebilir ve ölçülebilir şekilde kurar. Bu nedenle TCP karşılaştırması, NetProbe'un TCP'den hızlı olduğunu iddia etmek için değil; UDP üzerinde güvenilirlik mekanizmalarının nasıl tasarlandığını göstermek için kullanılmıştır.

**Görsel Yerleşimi:** `outputs/analysis/charts/reliable-udp-vs-tcp.svg` grafiğini bu alt başlığın altına koyun. Grafik altında TCP'nin yerleşik mekanizmaları ile uygulama katmanı reliable UDP yaklaşımı teknik olarak karşılaştırılmalıdır.

## 11. Sonuçlar ve Tartışma

Deneyler, UDP üzerinde güvenilir aktarım sağlamak için sequence number, ACK, timeout ve retransmission mekanizmalarının birlikte çalışması gerektiğini göstermiştir. Selective Repeat sliding window yaklaşımı, stop-and-wait'e göre aynı anda birden fazla paketin beklemede kalmasına izin verdiği için özellikle kayıpsız veya düşük kayıplı koşullarda daha yüksek verim sağlar.

Yapay kayıp oranı artırıldığında timeout ve retransmission olaylarının arttığı gözlemlenmiştir. Bu durum completion time değerini yükseltirken goodput değerini düşürür. Timeout parametresi ise protokolün tepkisini doğrudan etkiler. Çok küçük timeout gereksiz retransmission oluşturabilir; çok büyük timeout ise gerçek kayıpların geç fark edilmesine neden olur.

Paket boyutu deneyleri, header overhead'i ile yeniden gönderim maliyeti arasındaki dengeyi göstermiştir. Daha büyük payload değerleri kontrol yükünü azaltır, fakat kayıp durumunda daha büyük veri parçalarının tekrar gönderilmesine neden olur. Dosya boyutu deneyleri ise sabit kontrol maliyetlerinin büyük dosyalarda daha az etkili olduğunu göstermiştir.

**Görsel Yerleşimi:** Bu bölümde yeni grafik eklemek yerine önceki grafiklerden en önemli iki tanesine kısa referans verilebilir. Word raporunda bu bölüm metin ağırlıklı tutulmalıdır.

## 12. Karşılaşılan Sorunlar ve Çözüm Yaklaşımları

İlk önemli sorun, UDP'nin bağlantısız yapısı nedeniyle göndericinin paketin ulaşıp ulaşmadığını bilememesidir. Bu sorun ACK mekanizması ve timeout kontrolü ile çözülmüştür.

İkinci sorun, paketlerin sırasız veya tekrar gelebilmesidir. Bu durum sequence number ve sunucu tarafındaki session buffer yapısı ile çözülmüştür. Duplicate paket geldiğinde payload ikinci kez yazılmamış, sadece ACK tekrar gönderilmiştir.

Üçüncü sorun, deneylerin tekrar üretilebilir olmasıdır. Gerçek ağda paket kaybı kontrol edilemediği için yapay loss/delay simülatörü eklenmiştir. Bu sayede aynı kayıp oranı ve seed değeriyle benzer deney sonuçları alınabilir.

Dördüncü sorun, rapor için ölçüm ve görsel üretiminin manuel yapılmasının hata riski taşımasıdır. Bu nedenle deney sonuçları CSV/JSON olarak saklanmış, grafikler otomatik üretilmiş ve rapora aktarılacak görseller belirli klasörlerde toplanmıştır.

**Görsel Yerleşimi:** Bu bölümde max retry failure ekran görüntüsü kullanılmalıdır. Web panelde loss rate 1.0 ve max retry düşük seçilerek başarısız aktarım üretilir. Ekran görüntüsünde hata mesajı ve log tablosundaki timeout/transfer_failed olayları görünmelidir.

## 13. Sonuç ve Gelecekte Yapılabilecek Geliştirmeler

NetProbe projesi, UDP üzerinde güvenilir dosya aktarımı için gerekli temel mekanizmaları uygulama katmanında gerçekleştirmiştir. Sistem dosyayı parçalara ayırır, her parçayı sequence number ile takip eder, ACK yanıtlarını işler, timeout durumunda yeniden gönderim yapar, duplicate paketleri ayıklar ve aktarım sonunda SHA-256 ile bütünlük doğrulaması yapar.

Proje aynı zamanda ağ olaylarını loglayarak performans analizine temel oluşturur. Paket boyutu, timeout, loss rate, dosya boyutu ve TCP karşılaştırması gibi senaryolarla protokol davranışı ölçülebilir hale getirilmiştir. Web paneli sayesinde demo sırasında aktarım parametreleri değiştirilebilir ve log akışı canlı olarak izlenebilir.

Gelecekte yapılabilecek geliştirmeler arasında adaptif timeout hesaplama, congestion control yaklaşımı, çoklu istemci için daha gelişmiş session yönetimi, pcap/Wireshark entegrasyonu, şifreleme, sıkıştırma ve gerçek laboratuvar ağı üzerinde ek deneyler yer alabilir.

**Görsel Yerleşimi:** Son bölümde başarılı hash doğrulama ekran görüntüsü kullanılmalıdır. CLI veya web panelde status success, client SHA-256 ve server SHA-256 değerlerinin eşleştiği alan net görünmelidir.

## 14. Grup İçi Görev Dağılımı

| Üye | Sorumluluk |
| --- | --- |
| Üye 1 | UDP protokol tasarımı, client/server aktarım mantığı, sequence/ACK/timeout mekanizması |
| Üye 2 | Trafik loglama, deney otomasyonu, metrik hesaplama ve grafik üretimi |
| Üye 3 | Web UI, rapor düzeni, demo hazırlığı ve teslim paketi kontrolü |

Grup üyeleri geliştirme sürecinde ortak test ve doğrulama yapmıştır. Özellikle hash doğrulama, duplicate paket davranışı, max retry başarısızlığı ve deney grafiklerinin rapor yorumları tüm grup tarafından kontrol edilmiştir.

## 15. Ekler

Ek olarak README, komut satırı çıktıları, örnek JSONL log dosyaları, deney CSV dosyası ve web panel ekran görüntüleri teslim paketinde sunulmalıdır.

**Ek Görsel Listesi:**

1. Web dashboard genel görünümü
2. Transfer paneli başarılı aktarım ekran görüntüsü
3. Canlı log tablosu ekran görüntüsü
4. CLI başarılı aktarım ekran görüntüsü
5. Max retry failure ekran görüntüsü
6. Paket boyutu grafiği
7. Timeout grafiği
8. Loss rate grafiği
9. Dosya boyutu grafiği
10. Reliable UDP vs TCP grafiği
