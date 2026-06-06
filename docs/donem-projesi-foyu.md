# Bilgisayar Ağları Dersi - Dönem Projesi

**Bursa Teknik Üniversitesi | Bilgisayar Mühendisliği Bölümü**

# BURSA TEKNİK ÜNİVERSİTESİ

## Bilgisayar Mühendisliği Bölümü

# BİLGİSAYAR AĞLARI DERSİ

# DÖNEM PROJESİ FÖYÜ

| Alan                     | Bilgi                                                                                           |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| **Ders**                 | Bilgisayar Ağları                                                                               |
| **Proje Türü**           | Dönem Projesi                                                                                   |
| **Proje Başlığı**        | NetProbe: UDP Tabanlı Güvenilir Dosya Aktarımı, Trafik İzleme ve Ağ Performans Analiz Platformu |
| **Teslim Şekli**         | .zip dosyası + GitHub bağlantısı + teknik rapor (PDF)                                           |
| **Önerilen Grup Yapısı** | 2-3 öğrenci                                                                                     |

Bu föy; UDP üzerinde güvenilir dosya aktarımı, trafik izleme ve performans ölçümü bileşenlerini tek bir sistem içinde birleştiren dönem projesinin kapsamını, teknik beklentilerini ve teslim koşullarını tanımlar.

## 1. Projenin Amacı

Bu projenin amacı, öğrencilerin bilgisayar ağları dersinde ele alınan temel kavramları uygulamalı olarak deneyimlemelerini sağlamaktır. Proje kapsamında öğrencilerden, UDP üzerinde çalışan güvenilir bir dosya aktarım sistemi geliştirmeleri; aktarım sürecindeki ağ olaylarını izlemeleri; ve topladıkları verileri kullanarak performans analizi yapmaları beklenmektedir.

* UDP ve TCP arasındaki temel farkların anlaşılması
* Güvenilir veri aktarımı için gerekli mekanizmaların tasarlanması
* İstemci-sunucu mimarisinin uygulanması
* Paket temelli uygulama katmanı protokolü geliştirilmesi
* Ağ performans metriklerinin ölçülmesi ve teknik olarak yorumlanması
* Deneysel sonuçların teknik rapor ve sunum ile sunulması

## 2. Projenin Kapsamı

### 2.1. UDP Üzerinde Güvenilir Dosya Aktarımı

Öğrenciler, UDP tabanlı bir istemci-sunucu sistemi geliştirecek ve UDP'nin doğasında bulunmayan güvenilirlik mekanizmalarını uygulama katmanında kendileri tasarlayacaktır.

* Dosyanın parçalara bölünmesi ve yeniden birleştirilmesi
* Paket numaralandırma (sequence number)
* ACK mekanizması
* Timeout yönetimi
* Yeniden gönderim (retransmission)
* Aktarım sonunda dosya bütünlüğünün doğrulanması

### 2.2. Trafik İzleme ve Olay Kayıt Sistemi

Dosya aktarımı sırasında meydana gelen ağ olaylarının kayıt altına alınması gerekmektedir. Böylece öğrenciler, geliştirdikleri protokolün çalışma davranışını gözlemleyebilecektir.

* Paket gönderim zamanı
* ACK alınma zamanı
* Timeout oluşumu
* Yeniden gönderim sayısı
* Toplam aktarım süresi
* Başarılı ve başarısız paket sayıları

### 2.3. Ağ Performans Ölçüm ve Karşılaştırma Sistemi

Toplanan veriler kullanılarak sistemin farklı koşullar altındaki performansı ölçülmeli ve analiz edilmelidir.

* Throughput
* Goodput
* Packet loss rate
* Retransmission count / rate
* Ortalama gecikme ve RTT benzeri ölçümler
* Dosya tamamlanma süresi

## 3. Beklenen Öğrenme Kazanımları

* Uygulama katmanında basit bir ağ protokolü tasarlayabilme
* UDP üzerinde güvenilir veri aktarım mekanizması geliştirebilme
* Ağ trafiğini kayıt altına alarak yorumlayabilme
* Deneysel ölçümler tasarlayabilme ve sonuçları karşılaştırabilme
* Teknik rapor ve sunum hazırlayabilme

## 4. Zorunlu Gereksinimler

### 4.1. Temel İletişim Mimarisi

* Sistem en az bir istemci (client) ve bir sunucu (server) içermelidir.
* İstemci ve sunucu arasındaki veri aktarımı UDP socket programming kullanılarak gerçekleştirilmelidir.

### 4.2. Güvenilir Aktarım Mekanizması

* Sequence number kullanılmalıdır.
* ACK mesajları üretilmeli ve yorumlanmalıdır.
* Timeout kontrolü yapılmalıdır.
* Kaybolan paketlerin yeniden gönderimi desteklenmelidir.
* Dosya parçaları doğru sırada yeniden birleştirilmelidir.

> **Teknik Netleştirme**
>
> * Her veri paketi için en fazla 5 yeniden gönderim denemesi yapılmalıdır. Bu sayı yapılandırılabilir olabilir; ancak varsayılan değer raporda açıkça belirtilmelidir.
> * Bir paket, maksimum yeniden deneme sayısına rağmen başarıyla iletilemiyorsa aktarım ilgili paket için başarısız kabul edilmeli; sistem bunu kullanıcıya ve log dosyalarına açık biçimde yansıtmalıdır.
> * Duplicate paket alınması durumunda alıcı, aynı veriyi dosyaya ikinci kez yazmamalı; uygun ACK'i tekrar göndererek paketi yok saymalıdır.

### 4.3. Dosya Aktarımı

* Sistem en az bir dosyanın istemciden sunucuya aktarımını desteklemelidir.
* Gönderilen dosyanın eksiksiz biçimde yeniden oluşturulduğu doğrulanmalıdır.
* Bütünlük kontrolü için checksum, hash veya benzeri bir mekanizma kullanılmalıdır.

### 4.4. Olay Kayıtları

* Gönderilen paket sayısı
* Alınan ACK sayısı
* Timeout sayısı
* Yeniden gönderilen paket sayısı
* Toplam aktarım süresi

### 4.5. Performans Analizi

* Throughput
* Goodput
* Completion time
* Retransmission rate

Yalnızca parametre değiştirip grafik üretmek yeterli değildir. Her deney sonucu, protokol davranışıyla ilişkilendirilerek teknik yorumlarla açıklanmalıdır. Öğrenciler; hangi parametrenin neden etki oluşturduğunu, bunun retransmission, bekleme süresi, goodput veya tamamlanma süresi üzerindeki sonucunu tartışmalıdır.

### 4.6. Karşılaştırmalı Deneyler

Her grup, sistemini en az üç farklı deney senaryosu altında test etmeli ve sonuçları karşılaştırmalıdır.

* Farklı dosya boyutları
* Farklı paket boyutları
* Farklı timeout değerleri
* Farklı yapay kayıp oranları

## 5. Teknik Tasarımda Beklenen Unsurlar

Öğrencilerin kendi uygulama katmanı protokollerini tasarlamaları beklenmektedir. Aşağıdaki örnek paket alanları rehber niteliğindedir; birebir kullanılması zorunlu değildir.

| Paket Türü      | Örnek Alanlar                                                                       |
| --------------- | ----------------------------------------------------------------------------------- |
| **Veri Paketi** | packet type, sequence number, total packet count, payload length, checksum, payload |
| **ACK Paketi**  | packet type, ack number, checksum                                                   |

## 6. Önerilen Teknoloji Yığını

Öğrenciler istedikleri programlama dilini kullanabilir. Ancak aşağıdaki teknoloji yığını önerilmektedir:

* Python: socket, threading / asyncio, time, hashlib, csv veya json, matplotlib, pandas
* Alternatif diller: Java, C/C++, Go veya Node.js

Kullanılan dil veya araçtan bağımsız olarak proje gereksinimlerinin eksiksiz karşılanması esastır.

## 7. Deneysel Çalışma İçin Önerilen Senaryolar

**Senaryo 1: Paket Boyutunun Etkisi** - Farklı paket boyutları kullanılarak throughput ve tamamlanma süresi karşılaştırılabilir.

**Senaryo 2: Timeout Değerinin Etkisi** - Farklı timeout değerlerinin gereksiz retransmission ve toplam gecikme üzerindeki etkisi incelenebilir.

**Senaryo 3: Kayıp Oranının Etkisi** - Simüle edilmiş paket kaybı koşullarında sistemin davranışı analiz edilebilir.

**Senaryo 4: Farklı Dosya Boyutlarının Etkisi** - Küçük ve büyük dosya aktarımında sistem verimliliği karşılaştırılabilir.

## 8. Bonus Özellikler

* Stop-and-wait yerine sliding window yaklaşımının geliştirilmesi
* Selective Repeat veya Go-Back-N benzeri mekanizmaların uygulanması
* Ağ koşullarını simüle eden loss veya delay modülü geliştirilmesi
* Gerçek zamanlı görselleştirme paneli hazırlanması
* Wireshark veya pcap tabanlı analiz desteği
* TCP ile karşılaştırmalı deney yapılması
* Çoklu istemci desteği
* Basit şifreleme veya sıkıştırma desteği
* Laboratuvar ortamında gerçek ağ üzerinde ek deney yapılması ve sonuçların rapora ayrı bir alt bölüm olarak eklenmesi

## 9. Grup Yapısı

* Proje, bireysel olarak veya grup halinde gerçekleştirilebilir.
* Grup çalışması yapılacaksa önerilen grup büyüklüğü 2-3 öğrencidir.
* Grup içi görev dağılımı raporda açıkça belirtilmelidir.

## 10. Teslim Edilecek Çıktılar

### 10.1. Kaynak Kod

* İstemci kodu
* Sunucu kodu
* Analiz veya grafik üretim kodu
* Gerekirse yardımcı betikler

### 10.2. Teknik Rapor

Raporda aşağıdaki bölümlerin yer alması beklenmektedir:

* Giriş
* Problem tanımı
* Sistem mimarisi
* Protokol tasarımı
* Gerçekleme detayları
* Deney ortamı
* Performans metrikleri
* Sonuçlar ve tartışma
* Karşılaşılan sorunlar ve çözüm yaklaşımları
* Sonuç ve gelecekte yapılabilecek geliştirmeler

Teknik rapor için önerilen uzunluk, ekler ve kapak hariç yaklaşık 8-12 sayfadır. Bu aralık, raporun gereksiz ayrıntıyla uzatılmasını değil; tasarım kararları ile deney sonuçlarının yeterli teknik açıklamayla sunulmasını hedeflemektedir.

Raporun PDF formatında teslim edilmesi beklenmektedir. Grafik, tablo ve ekran görüntülerinin okunabilir olması; ayrıca sonuç bölümünde teknik yorumların yer alması zorunludur.

### 10.3. Teslim Biçimi

* Tüm proje çıktıları tek bir .zip dosyası içinde teslim edilmelidir.
* .zip dosyası içinde en az şu içerikler bulunmalıdır: teknik rapor (PDF), kaynak kodlar, varsa ek veri veya log dosyaları, kısa README dosyası.
* Kodların ayrıca GitHub üzerine yüklenmesi ve depo bağlantısının README dosyasında açık biçimde verilmesi beklenmektedir.
* README dosyasında proje yapısı, çalıştırma adımları, bağımlılıklar ve GitHub bağlantısı kısa ve açık şekilde açıklanmalıdır.

### 10.4. Sunum ve Demo

* Dönem sonunda her grup proje sunumu yapacaktır.
* Sunumda proje amacı, mimari tasarım, protokol mantığı, demo veya ekran görüntüleri, deney sonuçları ve genel değerlendirme bulunmalıdır.
* Canlı demo veya kayıtlı video demo kabul edilebilir.

## 11. Değerlendirme Rubriği

Aşağıdaki dağılım, öğretim elemanının tercihine göre küçük farklılıklar gösterebilir; ancak genel değerlendirme yapısı aşağıdaki gibidir.

| Değerlendirme Boyutu              | Ağırlık | Açıklama                                                                                         | Puan |
| --------------------------------- | ------: | ------------------------------------------------------------------------------------------------ | ---- |
| **Temel sistemin çalışması**      |     %20 | UDP istemci-sunucu yapısının doğru kurulması ve dosya aktarımının temel olarak çalışması         |      |
| **Güvenilir aktarım mekanizması** |     %20 | Sequence number, ACK, timeout ve retransmission mekanizmalarının doğru çalışması                 |      |
| **Trafik izleme ve loglama**      |     %15 | Olayların kaydedilmesi ve anlamlı ölçümlerin çıkarılması                                         |      |
| **Performans analizi**            |     %20 | Throughput, goodput, completion time ve benzeri metriklerin teknik yorumlarla birlikte sunulması |      |
| **Kod kalitesi**                  |     %10 | Modüler yapı, yorum satırları ve okunabilirlik                                                   |      |
| **Rapor kalitesi**                |     %10 | Teknik anlatım, tablo veya grafik kullanımı ve yorum kalitesi                                    |      |
| **Sunum ve demo**                 |      %5 | Çalışan demo, açık sunum ve kısa soru-cevap başarısı                                             |      |

## 12. Önemli Notlar

* Hazır bir dosya aktarım kütüphanesinin doğrudan kullanılması kabul edilmeyecektir.
* Projede geliştirilen güvenilirlik mekanizmasının öğrenciler tarafından tasarlanması beklenmektedir.
* Kodun çalışır durumda teslim edilmesi zorunludur.
* Kopya, intihal veya başka bir projeden aşırı derecede alınmış çalışmalar başarısız sayılacaktır.
* Projede kullanılan dış kütüphaneler ve kaynaklar raporda belirtilmelidir.
