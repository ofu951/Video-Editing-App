# 🎬 AI-Powered Video Editing App

Bu proje, içerik üreticileri için geliştirilmiş, yapay zeka destekli kapsamlı bir video düzenleme ve analiz uygulamasıdır. PyQt6 ile geliştirilmiş modern bir kullanıcı arayüzüne sahip olan bu uygulama; otomatik altyazı analizi (SRT), SEO optimizasyonu, trend takibi, Shorts üretimi ve metrik analizi gibi özellikleri tek bir platformda sunar.

## ✨ Özellikler

- **Gelişmiş Kullanıcı Arayüzü:** PyQt6 tabanlı, sekmeli ve kullanıcı dostu arayüz.
- **Yapay Zeka Entegrasyonu:** SRT dosyalarını okuyarak AI ile video içerikleri üzerine etkileşime girme.
- **Modüler Yapı:** Dashboard, SEO, Shorts, Hafıza (Memory), Metrikler ve Trendler gibi özelleşmiş modüller.
- **Otomasyon:** Video düzenleme iş akışınızı hızlandıracak araçlar.

## 🚀 Kurulum

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla takip edebilirsiniz.

### Ön Koşullar

Bilgisayarınızda şunların kurulu olduğundan emin olun:
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### 1. Projeyi Bilgisayarınıza İndirin (Clone)

Terminalinizi (veya Komut İstemini) açın ve projeyi klonlamak istediğiniz dizine giderek aşağıdaki komutu çalıştırın:

```bash
git clone https://github.com/ofu951/Video-Editing-App.git
```

İndirme işlemi bittikten sonra proje klasörünün içine girin:

```bash
cd Video-Editing-App
```

### 2. Sanal Ortam (Virtual Environment) Oluşturun

Projenin bağımlılıklarının sisteminizdeki diğer projelerle çakışmaması için bir sanal ortam oluşturmanızı tavsiye ederiz.

**Windows için:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**macOS ve Linux için:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(Ortam aktifleştiğinde terminal satırınızın başında `(.venv)` yazısını göreceksiniz.)*

### 3. Gerekli Kütüphaneleri Yükleyin

Sanal ortamınız aktifken, projenin çalışması için gereken tüm kütüphaneleri tek bir komutla yükleyin:

```bash
pip install -r requirements.txt
```

## 🎮 Kullanım

Kurulum tamamlandıktan sonra uygulamayı başlatmak için ana dizindeyken şu komutu çalıştırmanız yeterlidir:

```bash
python GUI.py
```

## 📂 Proje Yapısı

Projedeki temel klasör ve dosya yapısı şu şekildedir:
- `GUI.py` - Uygulamanın ana başlatıcı dosyası.
- `app/` - Arayüz bileşenlerini, sekmeleri ve ana pencereleri içeren modül klasörü.
- `requirements.txt` - Proje bağımlılıklarının listesi.
- `.gitignore` - GitHub'a yüklenmeyecek (medya dosyaları, sanal ortam vb.) dosyaların kuralları.

---
*Not: Bu uygulama yerel video ve ses dosyaları (mp4, mp3) ile çalışacak şekilde tasarlanmıştır, ancak deponun boyutunu optimize etmek amacıyla örnek medya dosyaları GitHub'a dahil edilmemiştir.*
