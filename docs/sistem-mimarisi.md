# Şekil 2. NetProbe Sistem Mimarisi

Bu diyagram, raporun **4. Sistem Mimarisi** bölümü için hazırlanmıştır. Word'e aktarırken Mermaid çıktısını görsel olarak dışa aktarabilir veya [mermaid.live](https://mermaid.live) üzerinden PNG/SVG üretebilirsiniz.

```mermaid
%%{init: {'flowchart': {'nodeSpacing': 36, 'rankSpacing': 48, 'padding': 16}, 'theme': 'base'}}%%
flowchart TB
    subgraph transfer["Veri Aktarım Katmanı"]
        direction LR
        client("Client")
        protocol{{"Reliable UDP Protocol<br/>+ Loss/Delay Simulator"}}
        server("Server")
        client <-->|"UDP"| protocol <-->|"ACK / DATA"| server
    end

    subgraph outputs["İzleme, Analiz ve Demo"]
        direction LR
        logs[("JSONL Logs")]
        metrics[["Metrics CSV/JSON"]]
        charts[/"Analysis Charts"/]
        dashboard(["Web Dashboard"])
    end

    protocol --> logs
    server --> logs
    client --> metrics
    metrics --> charts
    logs --> dashboard
    charts --> dashboard

    classDef clientNode fill:#2563eb,stroke:#1e40af,color:#ffffff,stroke-width:2px
    classDef serverNode fill:#059669,stroke:#047857,color:#ffffff,stroke-width:2px
    classDef protocolNode fill:#ea580c,stroke:#c2410c,color:#ffffff,stroke-width:2px
    classDef logNode fill:#7c3aed,stroke:#6d28d9,color:#ffffff,stroke-width:2px
    classDef metricNode fill:#0891b2,stroke:#0e7490,color:#ffffff,stroke-width:2px
    classDef chartNode fill:#db2777,stroke:#be185d,color:#ffffff,stroke-width:2px
    classDef dashNode fill:#4f46e5,stroke:#4338ca,color:#ffffff,stroke-width:2px

    class client clientNode
    class server serverNode
    class protocol protocolNode
    class logs logNode
    class metrics metricNode
    class charts chartNode
    class dashboard dashNode

    style transfer fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a
    style outputs fill:#f0fdf4,stroke:#22c55e,stroke-width:2px,color:#14532d
```

## Diyagram Açıklaması

- **Üst bant:** Client, Reliable UDP Protocol + Loss/Delay Simulator ve Server yatay aktarım hattını oluşturur.
- **Alt bant:** JSONL Logs, Metrics CSV/JSON, Analysis Charts ve Web Dashboard çıktıları yatay sıralanır.
- **Şekiller:** yuvarlak `( )` istemci/sunucu, altıgen `{ }` protokol katmanı, silindir `[( )]` log, dikdörtgen `[[ ]]` metrik, paralelkenar `/ /` grafik, stadium `([ ])` web paneli.
- **Renkler:** Mavi (client), turuncu (protokol), yeşil (server); alt katmanda mor, camgöbeği, pembe ve indigo tonları kullanılır.
