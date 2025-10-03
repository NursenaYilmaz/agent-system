from transformers import pipeline
from queue import Queue, Empty
from threading import Thread, Event
import time
import uuid

def create_message(sender, receiver, type_, payload, correlation_id=None, schema_version="1.0"):
    #standart mesaj formatı
    return {
        "message_id": str(uuid.uuid4()),
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "schema_version": schema_version,
        "timestamp": time.time(),
        "sender": sender,
        "receiver": receiver,
        "type": type_,
        "payload": payload,
    }

class MessageBus:                                                   #agentlar arası haberleşme için 
    
    
    def __init__(self):
        self.queues = {}
    
    def register_agent(self, agent_name):
        if agent_name not in self.queues: 
            self.queues[agent_name] = Queue()# her agent için bir kuyruk oluşturma
    
    def send_message(self, receiver, message):
        if receiver not in self.queues:
            self.register_agent(receiver)
        self.queues[receiver].put(message) # mesajı alıcının kuyruğuna koyar.
    
    def receive_message(self, receiver, timeout=0.2):
        if receiver not in self.queues:
            self.register_agent(receiver) 
        
        try:
            return self.queues[receiver].get(timeout=timeout) #0.2 sn bekler mesaj varsa alır yoksa hata fırlatır.
        except Empty:
            return None


class BaseAgent(Thread): #Thread sınıfından türüyor, yani her agent ayrı bir thread'de çalışabilir
    
    def __init__(self, name, bus, stop_event):
        super().__init__(daemon=True) #daemon=True: Ana program biterse bu thread'ler de otomatik kapanır
        self.name = name
        self.bus = bus
        self.stop_event = stop_event # Thread'i durdurmak için sinyal sistemi
        self.bus.register_agent(name)
    
    def run(self): #Thread başlatıldığında otomatik çalışır.
        while not self.stop_event.is_set():  # Dur sinyali gelene kadar sürekli döngüde kal
#Sürekli kendi kuyruğunu kontrol eder
            message = self.bus.receive_message(self.name)
            if message:
                try:
                    self.handle_message(message)
                except Exception as e:
                    print(f"[{self.name}] Hata: {e}")
    
    def handle_message(self, message):
        raise NotImplementedError #Alt sınıflar bunu override etmek zorunda


class TextAnalysisAgent(BaseAgent):
    
    def __init__(self, name, bus, stop_event):
        super().__init__(name, bus, stop_event)
        
        print(f"[{self.name}] Sentiment model yükleniyor...")
        self.classifier = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest"
        )
        print(f"[{self.name}] Model hazır!")
    
    def handle_message(self, message):
        if message["type"] != "ANALYZE_REQUEST":
            return
        
        text = message["payload"].get("text", "")
        correlation_id = message.get("correlation_id")

        if not text.strip():
            error_msg = {
                "type": "ERROR",
                "sender": self.name,
                "payload": {"error": "Boş metin gönderildi."},
                "correlation_id": correlation_id
            }

            error_msg = create_message(
                sender=self.name,
                receiver="Manager",
                type_="ERROR",
                payload=error_msg["payload"],
                correlation_id=correlation_id
            )
            self.bus.send_message(error_msg["receiver"], error_msg)
            return
        
        print(f"[{self.name}] Analiz Ediliyor: '{text[:50]}...'")
        

        result = self.classifier(text)[0]
        label = result["label"]
        score = result["score"]
        

        sentiment_map = {
            "positive": "Pozitif",
            "negative": "Negatif", 
            "neutral": "Nötr"
        }
        sentiment_tr = sentiment_map.get(label.lower(), "Bilinmiyor")
        

        response = {
            "type": "ANALYSIS_COMPLETE",
            "sender": self.name,
            "payload": {
                "text": text,
                "label": label,
                "score": score,
                "sentiment_tr": sentiment_tr
            },
            "correlation_id": correlation_id
        }

        response = create_message(
            sender=self.name,
            receiver="ReportAgent",
            type_="ANALYSIS_COMPLETE",
            payload=response["payload"],
            correlation_id=correlation_id
        )
        self.bus.send_message(response["receiver"], response)


class ReportAgent(BaseAgent):

    
    def handle_message(self, message):

        if message["type"] != "ANALYSIS_COMPLETE":
            return
        
        data = message["payload"]
        correlation_id = message.get("correlation_id")
        

        report = (
    "\n"
    "============================================================\n"
    "SENTIMENT ANALYSIS REPORT\n"
    "============================================================\n"
    f"Text      : {data['text']}\n"
    f"Sentiment : {data['sentiment_tr']} ({data['label']})\n"
    f"Confidence: {round(data['score'] * 100, 2)}%\n"
)


        
        print(f"[{self.name}] Rapor oluşturuldu")
        

        report_msg = {
            "type": "REPORT_READY",
            "sender": self.name,
            "payload": {
                "report": report,
                "raw_data": data
            },
            "correlation_id": correlation_id
        }

        report_msg = create_message(
            sender=self.name,
            receiver="Manager",
            type_="REPORT_READY",
            payload=report_msg["payload"],
            correlation_id=correlation_id
        )
        self.bus.send_message(report_msg["receiver"], report_msg)


class Manager:

    
    def __init__(self):
        print("[Manager] A2A sistemi başlatılıyor")
        
        self.bus = MessageBus() 
        self.stop_event = Event() #üm thread'lere "dur" sinyali göndermek için
        

        self.text_agent = TextAnalysisAgent("TextAgent", self.bus, self.stop_event)
        self.report_agent = ReportAgent("ReportAgent", self.bus, self.stop_event)
        
        self.bus.register_agent("Manager")
        
        self.text_agent.start() #Thread'leri başlatır (her biri kendi run() methodunu çalıştırır)
        self.report_agent.start()
        
        print("[Manager] Tüm Agentlar başarıyla başlatıldı.\n")
    
    def analyze_text(self, text, timeout=5.0):

        correlation_id = str(uuid.uuid4()) #Her istek için unique bir ID üretir.
        

        request = {
            "type": "ANALYZE_REQUEST",
            "sender": "Manager",
            "payload": {"text": text},
            "correlation_id": correlation_id
        }

        request = create_message(
            sender="Manager",
            receiver="TextAgent",
            type_="ANALYZE_REQUEST",
            payload=request["payload"],
            correlation_id=correlation_id
        )
        self.bus.send_message(request["receiver"], request)
        

        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.bus.receive_message("Manager")
            
            if response and response.get("correlation_id") == correlation_id:
                if response["type"] == "REPORT_READY":
                    return response["payload"]
                elif response["type"] == "ERROR":
                    return {"error": response["payload"]["error"]}
        
        return {"error": "Zaman aşımı - Yanıt alınamadı"}
    
    def shutdown(self):

        print("\n[Manager] Sistem kapatılıyor.")
        self.stop_event.set()
        self.text_agent.join(timeout=1.0)
        self.report_agent.join(timeout=1.0)
        print("[Manager] Sistem durduruldu")


if __name__ == "__main__":
    manager = Manager()
    
    try:
        test_texts = [
            "I love this beautiful day!",
            "I hate you, you are stupid!",
            "I went to the store yesterday.",
            "This is amazing! I'm so happy and excited!",
            "This is terrible and awful. I'm so disappointed."
        ]
        
        for text in test_texts:
            print(f"\n İşleniyor: '{text}'")
            result = manager.analyze_text(text, timeout=8.0)
            
            if "report" in result:
                print(result["report"])
            elif "error" in result:
                print(f"[ERROR] {result['error']}")
        
    finally:
        manager.shutdown()
