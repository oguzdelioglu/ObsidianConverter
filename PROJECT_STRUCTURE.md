# ObsidianConverter Proje Yapısı

Bu belge, ObsidianConverter projesinin klasör yapısını ve ana bileşenlerini açıklar.

## Kök Dizin Yapısı

```
ObsidianConverter/
├── bin/                         # Çalıştırılabilir dosyalar
├── obsidian_converter/          # Ana kaynak kod klasörü
│   ├── __init__.py             # Paket tanımı ve versiyon bilgisi
│   ├── cli.py                  # Komut satırı arayüzü
│   ├── config.py               # Yapılandırma sistemi
│   ├── converter.py            # Ana dönüştürme motoru
│   ├── interactive.py          # Etkileşimli mod işlevselliği
│   ├── llm.py                  # LLM işleme ve içerik analizi
│   ├── llm_providers/          # LLM sağlayıcı uygulamaları
│   │   ├── __init__.py
│   │   ├── anthropic_provider.py
│   │   ├── base.py
│   │   ├── ollama_provider.py
│   │   ├── openai_provider.py
│   │   └── provider_factory.py
│   └── utils/                   # Yardımcı fonksiyonlar
│       ├── __init__.py
│       ├── performance.py       # Performans optimizasyonu araçları
│       ├── stats.py             # İstatistik toplama ve raporlama
│       └── text.py              # Metin işleme yardımcıları
├── tests/                       # Birim ve entegrasyon testleri
│   ├── __init__.py
│   ├── conftest.py              # Test konfigürasyonu
│   ├── test_converter.py        # Dönüştürücü testleri
│   ├── test_integration.py      # Entegrasyon testleri
│   └── test_utils.py            # Yardımcı fonksiyon testleri
├── txt/                         # Örnek giriş metinleri
├── vault/                       # Çıkış notları
├── .dockerignore                # Docker dışlama listesi
├── .gitignore                   # Git dışlama listesi
├── docker-compose.yml           # Docker Compose konfigürasyonu
├── Dockerfile                   # Docker imaj tanımı
├── logo.png                     # Proje logosu
├── PROJECT_STRUCTURE.md         # Bu dosya
├── pytest.ini                   # Pytest konfigürasyonu
├── README_DE.md                 # Almanca dökümantasyon
├── README_DOCKER.md             # Docker kullanım talimatları
├── README_ES.md                 # İspanyolca dökümantasyon
├── README_FR.md                 # Fransızca dökümantasyon
├── README.md                    # Ana dökümantasyon (İngilizce)
├── README_TR.md                 # Türkçe dökümantasyon
├── README_ZH.md                 # Çince dökümantasyon
├── requirements.txt             # Python bağımlılıkları
├── setup.py                     # Paket kurulum betikleri
└── TODO.md                      # Yapılacaklar listesi
```

## Ana Bileşenler

### Çekirdek Modüller

- `converter.py`: Ana dönüştürme mantığını içerir - metin dosyalarını okur, içeriği analiz eder ve yapılandırılmış Obsidian notları oluşturur.
- `llm.py`: İçerik işleme motoru - metinleri anlamlı parçalara bölmek ve meta veri oluşturmak için LLM'leri kullanır.
- `cli.py`: Komut satırı arayüzü ve alt komutları (files, list, config, clean) yönetir.
- `config.py`: Yapılandırma ayarlarını YAML dosyalarından yükler ve sistem genelinde kullanılabilir hale getirir.

### LLM Sağlayıcıları

- `llm_providers/base.py`: Tüm LLM sağlayıcıları için temel sınıf
- `llm_providers/ollama_provider.py`: Yerel Ollama modelleri için destek
- `llm_providers/openai_provider.py`: GPT modelleri için OpenAI API entegrasyonu
- `llm_providers/anthropic_provider.py`: Claude modelleri için Anthropic API entegrasyonu
- `llm_providers/provider_factory.py`: Yapılandırmaya dayalı uygun sağlayıcıları oluşturur

### Yardımcı Modüller

- `utils/text.py`: Metin işleme yardımcıları (URL dostu başlıklar, içerik karma değerleri)
- `utils/performance.py`: Paralel işleme, büyük dosyaların yığınlar halinde işlenmesi
- `utils/stats.py`: Dönüşüm istatistiklerini toplama ve raporlama
- `interactive.py`: Notların kaydedilmeden önce gözden geçirilmesi ve düzenlenmesi için etkileşimli mod

### Docker Desteği

- `Dockerfile`: Konteynerize edilmiş ortam için imaj tanımı
- `docker-compose.yml`: Hem Ollama hem de ObsidianConverter servislerini içeren hizmet tanımları
- `README_DOCKER.md`: Docker kullanımı için ayrıntılı talimatlar

### Testler

- `tests/test_utils.py`: Yardımcı işlevlerin birim testleri
- `tests/test_converter.py`: Ana dönüştürme işlevlerinin birim testleri
- `tests/test_integration.py`: Tam uçtan uca işlemi test eden entegrasyon testleri

## Akış Diyagramı

```
[Metin Dosyaları] → [Dosya Okuyucu] → [LLM İşlemcisi] → [Bölüm Ayırma] 
                                         ↓
[Obsidian Notları] ← [Not Yazıcı] ← [Benzerlik Bağlayıcı] ← [Meta Veri Oluşturma]
```

1. Metin dosyaları giriş dizininden okunur
2. LLM, içeriği mantıksal bölümlere ayırmak için kullanılır
3. Her bölüm için başlık, etiketler ve kategori oluşturulur
4. Benzerlik analizi, ilgili notlar arasında bağlantılar oluşturur
5. Notlar, Obsidian ön madde ve biçimlendirmesiyle yazılır
6. İsteğe bağlı olarak, notlar kaydedilmeden önce etkileşimli olarak gözden geçirilebilir