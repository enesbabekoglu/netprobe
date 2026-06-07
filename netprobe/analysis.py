from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path
from typing import Iterable

from .config import OUTPUT_DIR


def _read_results(results_path: Path) -> list[dict[str, str]]:
    if not results_path.exists():
        raise FileNotFoundError(f"experiment results not found: {results_path}")
    with results_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _num(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except ValueError:
        return default


def _filter(rows: list[dict[str, str]], scenario: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("scenario") == scenario]


def _scale(value: float, minimum: float, maximum: float, size: float) -> float:
    if maximum == minimum:
        return size / 2
    return ((value - minimum) / (maximum - minimum)) * size


def _svg_line_plot(
    rows: list[dict[str, str]],
    x_key: str,
    y_keys: list[str],
    title: str,
    xlabel: str,
    ylabel: str,
    output: Path,
) -> None:
    rows = sorted(rows, key=lambda row: _num(row, x_key))
    width, height = 900, 520
    left, right, top, bottom = 80, 30, 60, 70
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_values = [_num(row, x_key) for row in rows]
    y_values = [_num(row, key) for row in rows for key in y_keys]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = 0.0, max(y_values) * 1.1 if y_values and max(y_values) > 0 else 1.0
    colors = ["#111111", "#737373", "#a3a3a3"]

    parts = [_svg_header(width, height, title)]
    parts.append(_axes(left, top, plot_width, plot_height, title, xlabel, ylabel))
    for index in range(6):
        y = top + plot_height - (plot_height / 5) * index
        value = y_min + ((y_max - y_min) / 5) * index
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e5e5e5"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" class="tick">{value:.2f}</text>')
    for row in rows:
        x = left + _scale(_num(row, x_key), x_min, x_max, plot_width)
        parts.append(f'<text x="{x:.2f}" y="{top + plot_height + 24}" text-anchor="middle" class="tick">{_num(row, x_key):g}</text>')

    for key_index, key in enumerate(y_keys):
        points: list[str] = []
        color = colors[key_index % len(colors)]
        for row in rows:
            x = left + _scale(_num(row, x_key), x_min, x_max, plot_width)
            y = top + plot_height - _scale(_num(row, key), y_min, y_max, plot_height)
            points.append(f"{x:.2f},{y:.2f}")
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3"/>')
        label = html.escape(key.replace("_", " "))
        legend_y = top + 18 + key_index * 22
        parts.append(f'<rect x="{width - 210}" y="{legend_y - 12}" width="14" height="14" fill="{color}"/>')
        parts.append(f'<text x="{width - 188}" y="{legend_y}" class="legend">{label}</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def _svg_bar_plot(
    rows: list[dict[str, str]],
    x_key: str,
    y_key: str,
    title: str,
    xlabel: str,
    ylabel: str,
    output: Path,
) -> None:
    width, height = 900, 520
    left, right, top, bottom = 80, 30, 60, 100
    plot_width = width - left - right
    plot_height = height - top - bottom
    y_values = [_num(row, y_key) for row in rows]
    y_min, y_max = 0.0, max(y_values) * 1.15 if y_values and max(y_values) > 0 else 1.0
    bar_width = plot_width / max(len(rows), 1) * 0.62

    parts = [_svg_header(width, height, title)]
    parts.append(_axes(left, top, plot_width, plot_height, title, xlabel, ylabel))
    for index in range(6):
        y = top + plot_height - (plot_height / 5) * index
        value = y_min + ((y_max - y_min) / 5) * index
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e5e5e5"/>')
        parts.append(f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" class="tick">{value:.2f}</text>')

    for index, row in enumerate(rows):
        x_center = left + (plot_width / len(rows)) * (index + 0.5)
        bar_height = _scale(_num(row, y_key), y_min, y_max, plot_height)
        x = x_center - bar_width / 2
        y = top + plot_height - bar_height
        label = html.escape(str(row.get(x_key, "")))
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" fill="#111111"/>')
        parts.append(f'<text x="{x_center:.2f}" y="{top + plot_height + 26}" text-anchor="middle" class="tick">{label}</text>')
        parts.append(f'<text x="{x_center:.2f}" y="{y - 8:.2f}" text-anchor="middle" class="tick">{_num(row, y_key):.2f}</text>')
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def _svg_header(width: int, height: int, title: str) -> str:
    escaped = html.escape(title)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escaped}">
<style>
  .title {{ font: 700 22px Inter, Arial, sans-serif; fill: #111111; }}
  .axis {{ stroke: #111111; stroke-width: 1.5; }}
  .label {{ font: 600 13px Inter, Arial, sans-serif; fill: #404040; }}
  .tick {{ font: 400 12px Inter, Arial, sans-serif; fill: #737373; }}
  .legend {{ font: 600 13px Inter, Arial, sans-serif; fill: #262626; }}
</style>
<rect width="100%" height="100%" fill="#ffffff"/>
'''


def _axes(left: int, top: int, plot_width: int, plot_height: int, title: str, xlabel: str, ylabel: str) -> str:
    return f'''<text x="{left}" y="34" class="title">{html.escape(title)}</text>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" class="axis"/>
<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" class="axis"/>
<text x="{left + plot_width / 2:.2f}" y="{top + plot_height + 58}" text-anchor="middle" class="label">{html.escape(xlabel)}</text>
<text x="22" y="{top + plot_height / 2:.2f}" transform="rotate(-90 22 {top + plot_height / 2:.2f})" text-anchor="middle" class="label">{html.escape(ylabel)}</text>'''


def build_analysis(output_dir: str | Path = OUTPUT_DIR) -> Path:
    root = Path(output_dir)
    results_path = root / "experiments" / "results.csv"
    analysis_dir = root / "analysis"
    chart_dir = analysis_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_results(results_path)

    generated: list[Path] = []
    packet_rows = sorted(_filter(rows, "packet_size"), key=lambda row: _num(row, "payload_size"))
    if packet_rows:
        output = chart_dir / "packet-size-throughput-goodput.svg"
        _svg_line_plot(
            packet_rows,
            "payload_size",
            ["throughput_mbps", "goodput_mbps"],
            "Paket Boyutu Etkisi",
            "Payload boyutu (byte)",
            "Mbps",
            output,
        )
        generated.append(output)

    timeout_rows = sorted(_filter(rows, "timeout"), key=lambda row: _num(row, "timeout"))
    if timeout_rows:
        output = chart_dir / "timeout-retransmission-rate.svg"
        _svg_line_plot(
            timeout_rows,
            "timeout",
            ["retransmission_rate"],
            "Timeout Değerinin Retransmission Oranına Etkisi",
            "Timeout (saniye)",
            "Retransmission rate",
            output,
        )
        generated.append(output)

    loss_rows = sorted(_filter(rows, "loss_rate"), key=lambda row: _num(row, "loss_rate"))
    if loss_rows:
        output = chart_dir / "loss-completion-time.svg"
        _svg_line_plot(
            loss_rows,
            "loss_rate",
            ["completion_time"],
            "Yapay Paket Kaybının Tamamlanma Süresine Etkisi",
            "Loss rate",
            "Saniye",
            output,
        )
        generated.append(output)

    file_rows = _filter(rows, "file_size")
    if file_rows:
        for row in file_rows:
            row["file_label"] = row.get("source_sample", "")
        output = chart_dir / "file-size-goodput.svg"
        _svg_bar_plot(
            file_rows,
            "file_label",
            "goodput_mbps",
            "Dosya Boyutunun Goodput Üzerindeki Etkisi",
            "Dosya",
            "Goodput (Mbps)",
            output,
        )
        generated.append(output)

    compare_rows = [row for row in rows if row.get("scenario") in {"tcp_compare", "file_size"}]
    compare_rows = [row for row in compare_rows if row.get("source_sample") == "medium_128kb.bin"] or compare_rows[-2:]
    if compare_rows:
        for row in compare_rows:
            row["protocol_label"] = row.get("protocol", "")
        output = chart_dir / "reliable-udp-vs-tcp.svg"
        _svg_bar_plot(
            compare_rows,
            "protocol_label",
            "goodput_mbps",
            "Reliable UDP ve TCP Goodput Karşılaştırması",
            "Protokol",
            "Goodput (Mbps)",
            output,
        )
        generated.append(output)

    summary_path = analysis_dir / "analysis-summary.md"
    summary_path.write_text(_build_summary(rows, generated), encoding="utf-8")
    return summary_path


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _build_summary(rows: list[dict[str, str]], generated: list[Path]) -> str:
    successful = [row for row in rows if row.get("status") == "success"]
    avg_goodput = _mean(_num(row, "goodput_mbps") for row in successful)
    avg_retrans = _mean(_num(row, "retransmission_rate") for row in rows)
    chart_list = "\n".join(f"- `{path}`" for path in generated)
    return f"""# NetProbe Deney Analizi

Bu dosya `python -m netprobe.analysis build` komutu ile otomatik üretilmiştir. Grafikler Word raporuna aktarılmak üzere `outputs/analysis/charts/` klasöründe SVG olarak tutulur.

## Genel Özet

- Başarılı deney sayısı: {len(successful)} / {len(rows)}
- Ortalama goodput: {avg_goodput:.3f} Mbps
- Ortalama retransmission rate: {avg_retrans:.3f}

## Teknik Yorumlar

Paket boyutu arttıkça header yükü dosya verisine oranla azalır. Bu nedenle orta ve büyük payload değerlerinde goodput genellikle yükselir; ancak çok büyük paketlerde tek kaybın yeniden aktarım maliyeti arttığı için kayıplı ortamda kazanç sınırlanabilir.

Timeout değeri küçük seçildiğinde ACK gecikmeleri gerçek paket kaybı gibi algılanabilir ve gereksiz retransmission oluşabilir. Timeout çok büyük seçildiğinde ise gerçek kayıplar geç fark edilir; bu da completion time değerini artırır.

Yapay kayıp oranı arttıkça sender aynı sequence number için yeniden gönderim yapmak zorunda kalır. Bu durum bytes_on_wire ve completion_time değerlerini artırırken goodput değerini düşürür.

Dosya boyutu büyüdükçe başlangıç/bitiş kontrol paketlerinin etkisi azalır. Bu nedenle büyük dosyalarda protokol daha verimli görünür; fakat toplam aktarım süresi doğal olarak artar.

TCP karşılaştırması, işletim sisteminin olgun TCP kontrol mekanizmalarına karşı uygulama katmanında yazılan reliable UDP protokolünün davranışını yorumlamak için eklenmiştir. NetProbe'un amacı TCP'yi geçmek değil; UDP üzerinde ACK, timeout ve retransmission mekanizmalarının nasıl kurulduğunu göstermektir.

## Üretilen Grafikler

{chart_list}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build NetProbe analysis charts and Markdown summary")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="build charts from experiment results")
    build_parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    args = parser.parse_args()
    if args.command == "build":
        path = build_analysis(args.output_dir)
        print(f"analysis written to {path}")


if __name__ == "__main__":
    main()
