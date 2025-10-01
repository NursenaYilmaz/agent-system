# Agent-to-Agent Duygu Analizi Sistemi

Metin verilerinin duygu durumunu analiz eden ve raporlayan çok agentlı bir sistem.

##  Özellikler

- **Duygu Analizi**: Metinlerin pozitif, negatif veya nötr duygularını tespit eder
- **Agent İletişimi**: İki agent arası mesajlaşma sistemi
- **Otomatik Raporlama**: Analiz sonuçlarını detaylı raporlar halinde sunar
- **Güven Skoru**: Her analiz için güvenilirlik yüzdesi hesaplar

##  Kullanılan Teknolojiler

- Python 3.x
- Transformers (Hugging Face)
- CardiffNLP Twitter RoBERTa Sentiment Model

##  Sistem Mimarisi

### Agent'lar

1. **TextAnalyzerAgent (Analiz Agent)**
   - Metin duygu analizini gerçekleştirir
   - Sentiment skorunu hesaplar
   - Sonuçları Rapor Agent'a iletir

2. **ReportGeneratorAgent (Rapor Agent)**
   - Analiz sonuçlarını alır
   - Detaylı rapor oluşturur
   - Sonuçları formatlar

3. **MessageQueue**
   - Agent'lar arası iletişimi yönetir
   - Mesaj geçmişini tutar
   - Zaman damgası ekler


