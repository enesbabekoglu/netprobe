# Şekil 3. NetProbe Paket ve ACK Akışı

Bu diyagram, raporun **5. Protokol Tasarımı** bölümü için hazırlanmıştır. Paket formatı tablosunun hemen altına yerleştirilebilir. Word'e aktarırken [mermaid.live](https://mermaid.live) üzerinden PNG/SVG üretebilirsiniz.

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 18, 'rankSpacing': 10, 'padding': 6, 'curve': 'basis'}, 'theme': 'base', 'themeVariables': {'fontSize': '13px'}}}%%
flowchart LR
    subgraph p1["① Oturum"]
        direction LR
        start(["START"]):::client --> ack1{{ACK}}:::server
    end
    subgraph p2["② Veri i=0..n"]
        direction LR
        data[/DATA i/]:::data --> ackn{{"ACK i"}}:::server
    end
    subgraph p3["③ Sonuç"]
        direction LR
        endp(END):::client --> result[(RESULT)]:::server
    end

    p1 --> p2 --> p3

    classDef client fill:#3b82f6,stroke:#1d4ed8,color:#ffffff,stroke-width:1.5px
    classDef server fill:#10b981,stroke:#059669,color:#ffffff,stroke-width:1.5px
    classDef data fill:#f97316,stroke:#ea580c,color:#ffffff,stroke-width:1.5px

    style p1 fill:#eff6ff,stroke:#60a5fa,stroke-width:1.5px,color:#1e40af
    style p2 fill:#fff7ed,stroke:#fb923c,stroke-width:1.5px,color:#c2410c
    style p3 fill:#ecfdf5,stroke:#34d399,stroke-width:1.5px,color:#047857
```

Word'e aktarırken [mermaid.live](https://mermaid.live) üzerinde genişliği **720–780 px** olacak şekilde PNG/SVG dışa aktarın; metin ile sayfa numarası arasındaki alana sığar.

## Diyagram Açıklaması

**Şekiller:** stadium başlangıç, altıgen onay, paralelkenar veri, yuvarlak bitiş, silindir sonuç. Ok etiketleri: metadata+SHA-256 → her parça onaylanır → hash doğrulama.

| Adım | Paket | Gönderen | Açıklama |
| --- | --- | --- | --- |
| 1 | START | Client | Dosya metadata bilgisi gönderilir |
| 2 | ACK | Server | Oturum onaylanır |
| 3–4 | DATA[i] / ACK[i] | Client / Server | Parçalar sırayla aktarılır ve onaylanır |
| 5 | END | Client | Aktarım sonlandırılır |
| 6 | RESULT | Server | Dosya birleştirilir, SHA-256 doğrulanır |
